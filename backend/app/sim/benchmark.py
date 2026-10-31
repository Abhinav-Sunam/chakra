"""Multi-seed Monte Carlo benchmark runner for constellation simulation.

Runs headless simulations across multiple seeds (optionally with a scenario)
and produces aggregated statistics suitable for charting.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

import numpy as np

from app.sim.engine import Engine


def run_single_seed(
    seed: int,
    duration_s: float = 300.0,
    sim_dt: float = 2.0,
    scenario_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Run one headless simulation seed, optionally loading a scenario."""
    engine = Engine(seed=seed)

    if scenario_name:
        engine.apply_command("load_scenario", {"name": scenario_name})

    n_ticks = int(duration_s / sim_dt)
    tick_times: List[float] = []
    timeseries: List[Dict[str, Any]] = []

    for i in range(n_ticks):
        t0 = time.perf_counter()
        engine.tick(sim_dt)
        tick_ms = (time.perf_counter() - t0) * 1000.0
        tick_times.append(tick_ms)

        # Sample timeseries every 10 ticks (~20s sim-time)
        if i % 10 == 0:
            a_snap = engine.metrics_adaptive.snapshot_frame()
            s_snap = engine.metrics_static.snapshot_frame()
            timeseries.append({
                "t": round(engine.t, 2),
                "adaptive_lat": a_snap.get("latMs", 0.0),
                "adaptive_pdr": a_snap.get("pdr", 0.0),
                "adaptive_thr": a_snap.get("thrMbps", 0.0),
                "static_lat": s_snap.get("latMs", 0.0),
                "static_pdr": s_snap.get("pdr", 0.0),
                "static_thr": s_snap.get("thrMbps", 0.0),
            })

    # Final snapshots
    adaptive_snap = engine.metrics_adaptive.snapshot()
    static_snap = engine.metrics_static.snapshot()
    network_snap = engine.network_tracker.snapshot()

    tick_p95 = float(np.percentile(tick_times, 95)) if tick_times else 0.0
    tick_mean = float(np.mean(tick_times)) if tick_times else 0.0

    return {
        "seed": seed,
        "adaptive": {
            "latMs_mean": adaptive_snap.get("cum_lat_ms", adaptive_snap.get("latMs", 0.0)),
            "pdr_mean": adaptive_snap.get("cum_pdr", adaptive_snap.get("pdr", 0.0)),
            "throughput_mbps": (
                engine.metrics_adaptive.cum_delivered_mb / duration_s
                if duration_s > 0
                else 0.0
            ),
            "reroutes": engine.adaptive_router.proactive_reroutes + engine.adaptive_router.reactive_reroutes,
            "proactive_reroutes": engine.adaptive_router.proactive_reroutes,
            "reactive_reroutes": engine.adaptive_router.reactive_reroutes,
            "avg_stretch": adaptive_snap.get("avgStretch", 1.0),
        },
        "static": {
            "latMs_mean": static_snap.get("cum_lat_ms", static_snap.get("latMs", 0.0)),
            "pdr_mean": static_snap.get("cum_pdr", static_snap.get("pdr", 0.0)),
            "throughput_mbps": (
                engine.metrics_static.cum_delivered_mb / duration_s
                if duration_s > 0
                else 0.0
            ),
            "reroutes": engine.static_router.reroutes,
        },
        "network": {
            "link_uptime": network_snap.get("linkUptime", 0.0),
            "active_failures": network_snap.get("activeFailures", 0),
        },
        "tick_ms_p95": tick_p95,
        "tick_ms_mean": tick_mean,
        "failure_events": len([
            e for e in engine.all_events if e.get("kind") == "link_fail"
        ]),
        "timeseries": timeseries,
    }


def run_benchmark(
    scenario_name: Optional[str] = None,
    n_seeds: int = 5,
    duration_s: float = 300.0,
    sim_dt: float = 2.0,
) -> Dict[str, Any]:
    """Run multi-seed Monte Carlo benchmark and aggregate results.

    Returns per-seed results and aggregated mean/std/p95 statistics.
    """
    t_start = time.perf_counter()
    seeds = list(range(42, 42 + n_seeds))
    per_seed: List[Dict[str, Any]] = []

    for seed in seeds:
        result = run_single_seed(
            seed=seed,
            duration_s=duration_s,
            sim_dt=sim_dt,
            scenario_name=scenario_name,
        )
        per_seed.append(result)

    wall_time_s = time.perf_counter() - t_start

    # Aggregate statistics
    def agg(values: List[float]) -> Dict[str, float]:
        arr = np.array(values)
        return {
            "mean": round(float(np.mean(arr)), 4),
            "std": round(float(np.std(arr)), 4),
            "min": round(float(np.min(arr)), 4),
            "max": round(float(np.max(arr)), 4),
            "p95": round(float(np.percentile(arr, 95)), 4),
        }

    aggregate = {
        "adaptive": {
            "latMs": agg([s["adaptive"]["latMs_mean"] for s in per_seed]),
            "pdr": agg([s["adaptive"]["pdr_mean"] for s in per_seed]),
            "throughput_mbps": agg([s["adaptive"]["throughput_mbps"] for s in per_seed]),
            "reroutes": agg([float(s["adaptive"]["reroutes"]) for s in per_seed]),
            "proactive_reroutes": agg([float(s["adaptive"]["proactive_reroutes"]) for s in per_seed]),
            "reactive_reroutes": agg([float(s["adaptive"]["reactive_reroutes"]) for s in per_seed]),
        },
        "static": {
            "latMs": agg([s["static"]["latMs_mean"] for s in per_seed]),
            "pdr": agg([s["static"]["pdr_mean"] for s in per_seed]),
            "throughput_mbps": agg([s["static"]["throughput_mbps"] for s in per_seed]),
        },
        "tick_ms_p95": agg([s["tick_ms_p95"] for s in per_seed]),
        "tick_ms_mean": agg([s["tick_ms_mean"] for s in per_seed]),
    }

    # Merge timeseries from first seed as representative
    representative_timeseries = per_seed[0]["timeseries"] if per_seed else []

    return {
        "scenario": scenario_name or "baseline",
        "n_seeds": n_seeds,
        "duration_s": duration_s,
        "sim_dt": sim_dt,
        "wall_time_s": round(wall_time_s, 2),
        "aggregate": aggregate,
        "per_seed": per_seed,
        "timeseries": representative_timeseries,
    }


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Constellation benchmark runner")
    parser.add_argument("--scenario", type=str, default=None, help="Scenario name to load")
    parser.add_argument("--seeds", type=int, default=5, help="Number of RNG seeds")
    parser.add_argument("--duration", type=float, default=300.0, help="Simulation duration (s)")
    parser.add_argument("--sim-dt", type=float, default=2.0, help="Tick step size (s)")
    parser.add_argument("--output", type=str, default=None, help="Output JSON file path")
    args = parser.parse_args()

    print(f"Running benchmark: scenario={args.scenario}, seeds={args.seeds}, duration={args.duration}s")
    result = run_benchmark(
        scenario_name=args.scenario,
        n_seeds=args.seeds,
        duration_s=args.duration,
        sim_dt=args.sim_dt,
    )

    if args.output:
        with open(args.output, "w") as f:
            json.dump(result, f, indent=2, default=str)
        print(f"Results written to {args.output}")
    else:
        # Print summary
        agg = result["aggregate"]
        print(f"\n{'='*60}")
        print(f"Benchmark: {result['scenario']} ({result['n_seeds']} seeds, {result['duration_s']}s)")
        print(f"Wall time: {result['wall_time_s']:.1f}s")
        print(f"{'='*60}")
        print(f"\n{'Metric':<25} {'Adaptive':>15} {'Static':>15}")
        print(f"{'-'*55}")
        print(f"{'Latency (ms)':<25} {agg['adaptive']['latMs']['mean']:>12.2f}ms {agg['static']['latMs']['mean']:>12.2f}ms")
        print(f"{'PDR':<25} {agg['adaptive']['pdr']['mean']:>14.4f} {agg['static']['pdr']['mean']:>14.4f}")
        print(f"{'Throughput (Mbps)':<25} {agg['adaptive']['throughput_mbps']['mean']:>12.2f} {agg['static']['throughput_mbps']['mean']:>12.2f}")
        print(f"{'Reroutes':<25} {agg['adaptive']['reroutes']['mean']:>15.1f} {'N/A':>15}")
        print(f"\nTick time: mean={agg['tick_ms_mean']['mean']:.2f}ms, p95={agg['tick_ms_p95']['mean']:.2f}ms")

