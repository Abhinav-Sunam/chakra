"""FastAPI application for SatRoute simulation backend."""

from __future__ import annotations

import asyncio
import copy
import logging
import time
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Set

import numpy as np
import orjson
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.config import DEFAULT_CONFIG, SimConfig
from app.schemas import parse_command
from app.sim.engine import Engine
from app.sim.orbit import ground_track, rephase_to, split_antimeridian
from app.sim.scenarios import list_scenarios
from app.sim.scenarios import load_scenario as load_scenario_def

logger = logging.getLogger("satroute.main")
logging.basicConfig(level=logging.INFO)

# Global engine instance initialized with seed 42
engine: Engine = Engine(seed=42)
current_config: SimConfig = DEFAULT_CONFIG.model_copy(deep=True)


class ConnectionManager:
    """Manages active client WebSocket connections and broadcast dispatch."""

    def __init__(self) -> None:
        self.active_connections: Set[WebSocket] = set()
        self.consecutive_failures: Dict[WebSocket, int] = {}

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.add(websocket)
        self.consecutive_failures[websocket] = 0

    def disconnect(self, websocket: WebSocket) -> None:
        self.active_connections.discard(websocket)
        self.consecutive_failures.pop(websocket, None)

    async def broadcast_text(self, text: str) -> None:
        """Broadcast serialized frame text with per-client timeout guard."""
        if not self.active_connections:
            return

        dead_sockets: Set[WebSocket] = set()
        for ws in list(self.active_connections):
            try:
                # Per-client guard: skip/drop slow sends instead of queuing
                await asyncio.wait_for(ws.send_text(text), timeout=0.05)
                self.consecutive_failures[ws] = 0
            except (asyncio.TimeoutError, Exception) as exc:
                failures = self.consecutive_failures.get(ws, 0) + 1
                self.consecutive_failures[ws] = failures
                logger.debug("Broadcast send error/timeout to client (%d failures): %s", failures, exc)
                # Drop client after repeated failures or disconnects
                if failures >= 3 or isinstance(exc, (WebSocketDisconnect, RuntimeError)):
                    dead_sockets.add(ws)

        for ws in dead_sockets:
            self.disconnect(ws)


manager = ConnectionManager()


async def simulation_loop() -> None:
    """Background simulation task running at 10 Hz with drift correction."""
    tick_interval = 0.1
    next_tick = time.perf_counter()

    while True:
        try:
            now = time.perf_counter()
            # If we fall more than 1 second behind, reset drift
            if now - next_tick > 1.0:
                next_tick = now

            next_tick += tick_interval
            delay = next_tick - time.perf_counter()
            if delay > 0:
                await asyncio.sleep(delay)

            # Advance simulation step (synchronous on same event loop thread)
            frame_data = engine.step(0.1)

            # Serialise frame ONCE with orjson and broadcast to all connected clients
            frame_bytes = orjson.dumps(frame_data)
            frame_text = frame_bytes.decode("utf-8")
            await manager.broadcast_text(frame_text)

        except asyncio.CancelledError:
            break
        except Exception as exc:
            logger.exception("Unexpected error in simulation loop: %s", exc)
            await asyncio.sleep(0.01)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan managing background simulation loop task."""
    loop_task = asyncio.create_task(simulation_loop())
    yield
    loop_task.cancel()
    try:
        await loop_task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="SatRoute Backend", lifespan=lifespan)

# CORS configuration for Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check() -> Dict[str, bool]:
    """Health check endpoint."""
    return {"ok": True}


@app.get("/api/config")
async def get_config() -> Dict[str, Any]:
    """Return current centralized simulation configuration."""
    return current_config.model_dump()


@app.post("/api/config")
async def update_config(update_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Validated partial update of configuration that resets the engine safely."""
    global engine, current_config
    existing_dict = current_config.model_dump()

    # Deep merge update_dict into existing_dict
    def deep_update(d: Dict[str, Any], u: Dict[str, Any]) -> Dict[str, Any]:
        for k, v in u.items():
            if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                d[k] = deep_update(d[k], v)
            else:
                d[k] = v
        return d

    merged = deep_update(existing_dict, update_dict)
    new_cfg = SimConfig.model_validate(merged)
    current_config = new_cfg

    # Reset engine safely with new config
    seed = new_cfg.sim.seed
    engine = Engine(seed=seed, sim_config=new_cfg)
    logger.info("Engine re-initialized with new configuration")
    return {"ok": True, "config": current_config.model_dump()}


@app.get("/api/state")
async def get_state() -> Dict[str, Any]:
    """Return snapshot of engine simulation state."""
    return engine.snapshot()


@app.post("/api/reset")
async def reset_simulation() -> Dict[str, bool]:
    """Reset engine simulation state to initial conditions."""
    # Commands touching the engine cannot run concurrently with step():
    # both run on the same event loop thread and step() is synchronous, so this is safe.
    engine.apply_command("reset", {})
    return {"ok": True}


@app.get("/api/scenarios")
async def get_scenarios() -> List[Dict[str, Any]]:
    """Return list of available scenario definitions."""
    return list_scenarios()


@app.post("/api/scenarios/{name}/start")
async def start_scenario(name: str) -> Dict[str, Any]:
    """Load and start a named scenario, resetting the engine."""
    global engine
    scenario = load_scenario_def(name)
    if scenario is None:
        return {"ok": False, "error": f"Scenario not found: {name}"}
    engine.apply_command("load_scenario", {"name": name})
    return {"ok": True, "scenario": name, "duration_s": scenario.duration_s, "events_count": len(scenario.events)}


@app.post("/api/benchmark")
async def run_benchmark(body: Dict[str, Any]) -> Dict[str, Any]:
    """Run headless benchmark with specified scenario and parameters.

    Body: {"scenario"?: str, "seeds": int, "duration_s"?: float, "sim_dt"?: float}
    Returns aggregated statistics across seeds.
    """
    from app.sim.benchmark import run_benchmark as _run_benchmark
    scenario_name = body.get("scenario")
    seeds = int(body.get("seeds", 5))
    duration_s = float(body.get("duration_s", 300.0))
    sim_dt = float(body.get("sim_dt", 2.0))

    result = _run_benchmark(
        scenario_name=scenario_name,
        n_seeds=seeds,
        duration_s=duration_s,
        sim_dt=sim_dt,
    )
    return result


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """Live WebSocket stream for constellation simulation frames and control commands."""
    await manager.connect(websocket)

    try:
        # Send initial static metadata frame
        init_data = engine.init_message()
        init_text = orjson.dumps(init_data).decode("utf-8")
        await websocket.send_text(init_text)

        # Loop receiving incoming JSON text commands
        while True:
            text = await websocket.receive_text()
            try:
                msg = orjson.loads(text)
            except Exception as exc:
                err_msg = {"type": "error", "msg": f"Invalid JSON payload: {exc}"}
                await websocket.send_text(orjson.dumps(err_msg).decode("utf-8"))
                continue

            req_id = msg.get("id")
            try:
                parsed_cmd = parse_command(msg)
                cmd_name = parsed_cmd.cmd
                args_dict = (
                    parsed_cmd.args.model_dump()
                    if hasattr(parsed_cmd.args, "model_dump")
                    else (parsed_cmd.args if isinstance(parsed_cmd.args, dict) else {})
                )

                # Special command: preview_orbit
                # reply {"type":"orbit_preview","id":id,"inc_deg":...,"period_s":...,"track":[[lon,lat],...],"segments":[[[lon,lat],...]]}
                # using a COPY of the constellation (never modify the real one)
                if cmd_name == "preview_orbit":
                    sat_id = int(args_dict.get("id", 0) if args_dict.get("id") is not None else 0)
                    lat = float(args_dict.get("lat", 0.0) if args_dict.get("lat") is not None else 0.0)
                    lon = float(args_dict.get("lon", 0.0) if args_dict.get("lon") is not None else 0.0)

                    c_copy = copy.deepcopy(engine.constellation)
                    rephase_to(c_copy, sat_id, lat, lon, engine.t)
                    # Compute next 95 min ground track (30 s steps = 190 points)
                    period_s = float(2.0 * 3.141592653589793 / c_copy.n[sat_id])
                    inc_deg = float(np.degrees(c_copy.inc[sat_id]))
                    duration_s = 95.0 * 60.0
                    raw_track = ground_track(c_copy, sat_id, engine.t, engine.t + duration_s, 30.0)
                    # Output [[lon, lat], ...]
                    track_coords = [[round(p_lon, 4), round(p_lat, 4)] for p_lat, p_lon in raw_track]
                    segments = split_antimeridian(track_coords)

                    resp = {
                        "type": "orbit_preview",
                        "id": sat_id,
                        "inc_deg": round(inc_deg, 2),
                        "period_s": round(period_s, 1),
                        "track": track_coords,
                        "segments": segments,
                    }
                    await websocket.send_text(orjson.dumps(resp).decode("utf-8"))

                else:
                    # Commands touching the engine cannot run concurrently with step():
                    # both run on the same event loop thread and step() is synchronous, so this is safe.
                    engine.apply_command(cmd_name, args_dict)
                    ack_resp = {"type": "ack", "id": req_id}
                    await websocket.send_text(orjson.dumps(ack_resp).decode("utf-8"))

            except (ValueError, Exception) as exc:
                err_resp = {"type": "error", "msg": str(exc), "id": req_id}
                await websocket.send_text(orjson.dumps(err_resp).decode("utf-8"))

    except WebSocketDisconnect:
        logger.debug("WebSocket client disconnected")
    except Exception as exc:
        logger.debug("WebSocket handler exception: %s", exc)
    finally:
        manager.disconnect(websocket)
