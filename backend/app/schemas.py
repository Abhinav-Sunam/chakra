"""Pydantic v2 schemas for simulation frames, metadata, and control commands."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict

# ---------------------------------------------------------------------------
# Output Schemas (Engine.init_message and Engine.step)
# ---------------------------------------------------------------------------

class SimConfig(BaseModel):
    """Loose configuration model for simulation init parameters."""
    model_config = ConfigDict(extra="allow")

    num_sats: Optional[int] = None
    time_scale: Optional[float] = None
    cadence_ticks: Optional[int] = None


class GroundOut(BaseModel):
    """Ground station description."""
    id: int
    gs_id: Optional[int] = None
    name: str
    lat: float
    lon: float

    def model_post_init(self, __context: Any) -> None:
        if self.gs_id is None:
            self.gs_id = self.id


# Alias for backward compatibility
GroundStation = GroundOut


class FlowDef(BaseModel):
    """Flow definition."""
    id: str
    src: Optional[int] = None
    dst: Optional[int] = None
    src_gs: Optional[int] = None
    dst_gs: Optional[int] = None
    mbps: float

    def model_post_init(self, __context: Any) -> None:
        if self.src is None and self.src_gs is not None:
            self.src = self.src_gs
        elif self.src_gs is None and self.src is not None:
            self.src_gs = self.src
        if self.dst is None and self.dst_gs is not None:
            self.dst = self.dst_gs
        elif self.dst_gs is None and self.dst is not None:
            self.dst_gs = self.dst


# Alias for backward compatibility
Flow = FlowDef


class Init(BaseModel):
    """Initialization frame emitted on connection."""
    type: Literal["init"] = "init"
    config: SimConfig
    ground: List[GroundOut]
    flows: List[FlowDef]
    nSats: int
    planes: List[int]


class SatOut(BaseModel):
    """Per-satellite telemetry in simulation frame."""
    id: int
    lat: float
    lon: float
    alt: float
    vlat: float
    vlon: float
    st: int


class LinkOut(BaseModel):
    """Per-link state and metrics."""
    a: int
    b: int
    k: int
    up: int
    rho: float
    ms: float
    loss: float


class PathOut(BaseModel):
    """Multipath chunk route and bandwidth."""
    nodes: List[int]
    mbps: float


class FlowEval(BaseModel):
    """Routing performance evaluation for a single flow."""
    paths: List[PathOut]
    ms: float
    pdr: float
    blackholed: bool


class FlowFrame(BaseModel):
    """Flow state comparison block (adaptive vs static)."""
    id: str
    adaptive: FlowEval
    static: FlowEval


class Metrics(BaseModel):
    """Algorithm-level tracking metrics."""
    latMs: float
    pdr: float
    thrMbps: float
    reroutes: int
    rerouteRate: int
    recoverS: float


class MetricsBlock(BaseModel):
    """Constellation-wide metrics container."""
    adaptive: Metrics
    static: Metrics
    linkUptime: float
    activeFailures: int


class SimEvent(BaseModel):
    """Event log record."""
    model_config = ConfigDict(extra="allow")

    t: float
    level: Literal["info", "warn", "crit"]
    kind: str
    msg: str


class Frame(BaseModel):
    """Live simulation frame emitted on every tick."""
    type: Literal["frame"] = "frame"
    t: float
    scale: float
    running: bool
    tickMs: float
    sats: List[SatOut]
    links: List[LinkOut]
    flows: List[FlowFrame]
    metrics: MetricsBlock
    events: List[SimEvent]


class Ack(BaseModel):
    """Command acknowledgment."""
    model_config = ConfigDict(extra="allow")

    type: Literal["ack"] = "ack"
    cmd: Optional[str] = None
    id: Optional[Union[str, int]] = None
    ok: bool = True
    details: Optional[Dict[str, Any]] = None


class ErrorMsg(BaseModel):
    """Error message."""
    model_config = ConfigDict(extra="allow")

    type: Literal["error"] = "error"
    error: Optional[str] = None
    msg: Optional[str] = None
    cmd: Optional[str] = None
    id: Optional[Union[str, int]] = None


class OrbitPreview(BaseModel):
    """Orbit preview response."""
    model_config = ConfigDict(extra="allow")

    type: Literal["orbit_preview"] = "orbit_preview"
    id: Optional[int] = None
    track: Optional[List[List[float]]] = None
    points: Optional[List[Dict[str, float]]] = None


# Aliases for backward compatibility
InitMessage = Init
FrameMessage = Frame
SatState = SatOut
LinkState = LinkOut
FlowPair = FlowFrame
PathChunk = PathOut
OverallMetrics = MetricsBlock
AckResponse = Ack
ErrorResponse = ErrorMsg
OrbitPreviewResponse = OrbitPreview


# ---------------------------------------------------------------------------
# Client Command Models
# ---------------------------------------------------------------------------

class BaseCmd(BaseModel):
    """Base client command model with optional request tracking id and type tag."""
    model_config = ConfigDict(extra="allow")

    type: Optional[str] = None
    id: Optional[Union[str, int]] = None


class PlayCmd(BaseCmd):
    cmd: Literal["play"]
    args: Optional[Dict[str, Any]] = None


class PauseCmd(BaseCmd):
    cmd: Literal["pause"]
    args: Optional[Dict[str, Any]] = None


class ResetCmd(BaseCmd):
    cmd: Literal["reset"]
    args: Optional[Dict[str, Any]] = None


class SetScaleArgs(BaseModel):
    scale: float


class SetScaleCmd(BaseCmd):
    cmd: Literal["set_scale"]
    args: SetScaleArgs


class SetWeightsArgs(BaseModel):
    a: float = 1.0
    b: float = 1.0
    c: float = 1.0


class SetWeightsCmd(BaseCmd):
    cmd: Literal["set_weights"]
    args: SetWeightsArgs


class SetParamsArgs(BaseModel):
    intensity: Optional[float] = None
    model_config = ConfigDict(extra="allow")


class SetParamsCmd(BaseCmd):
    cmd: Literal["set_params"]
    args: SetParamsArgs


class FailLinkArgs(BaseModel):
    a: int
    b: int


class FailLinkCmd(BaseCmd):
    cmd: Literal["fail_link"]
    args: FailLinkArgs


class RestoreLinkArgs(BaseModel):
    a: int
    b: int


class RestoreLinkCmd(BaseCmd):
    cmd: Literal["restore_link"]
    args: RestoreLinkArgs


class FailSatArgs(BaseModel):
    id: int


class FailSatCmd(BaseCmd):
    cmd: Literal["fail_sat"]
    args: FailSatArgs


class RestoreSatArgs(BaseModel):
    id: int


class RestoreSatCmd(BaseCmd):
    cmd: Literal["restore_sat"]
    args: RestoreSatArgs


class MoveSatArgs(BaseModel):
    id: int
    lat: float
    lon: float


class MoveSatCmd(BaseCmd):
    cmd: Literal["move_sat"]
    args: MoveSatArgs


class MoveGsArgs(BaseModel):
    id: int
    lat: float
    lon: float


class MoveGsCmd(BaseCmd):
    cmd: Literal["move_gs"]
    args: MoveGsArgs


class PreviewOrbitArgs(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: Optional[int] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    num_sats: Optional[int] = None
    num_planes: Optional[int] = None
    f: Optional[int] = None
    inc_deg: Optional[float] = None
    altitude_km: Optional[float] = None


class PreviewOrbitCmd(BaseCmd):
    cmd: Literal["preview_orbit"]
    args: Optional[PreviewOrbitArgs] = None


class SetFlowScaleArgs(BaseModel):
    factor: float


class SetFlowScaleCmd(BaseCmd):
    cmd: Literal["set_flow_scale"]
    args: SetFlowScaleArgs


class AddFlowArgs(BaseModel):
    src: int
    dst: int
    mbps: float
    id: Optional[str] = None


class AddFlowCmd(BaseCmd):
    cmd: Literal["add_flow"]
    args: AddFlowArgs


class RemoveFlowArgs(BaseModel):
    id: str


class RemoveFlowCmd(BaseCmd):
    cmd: Literal["remove_flow"]
    args: RemoveFlowArgs


class AddSatArgs(BaseModel):
    lat: float
    lon: float
    inc_deg: Optional[float] = 53.0
    alt_km: Optional[float] = 550.0


class AddSatCmd(BaseCmd):
    cmd: Literal["add_sat"]
    args: AddSatArgs


class RemoveSatArgs(BaseModel):
    id: int


class RemoveSatCmd(BaseCmd):
    cmd: Literal["remove_sat"]
    args: RemoveSatArgs


class PinSatArgs(BaseModel):
    id: int
    pinned: bool


class PinSatCmd(BaseCmd):
    cmd: Literal["pin_sat"]
    args: PinSatArgs


class OrbitPreviewResponse(BaseModel):
    type: Literal["orbit_preview"] = "orbit_preview"
    id: int
    inc_deg: float
    period_s: float
    track: List[List[float]]  # Flat list of [lon, lat] or segmented
    segments: Optional[List[List[List[float]]]] = None


class FailPlaneArgs(BaseModel):
    plane: int
    duration: Optional[float] = None


class FailPlaneCmd(BaseCmd):
    cmd: Literal["fail_plane"]
    args: FailPlaneArgs


class FailRegionArgs(BaseModel):
    lat: float
    lon: float
    radius_km: Optional[float] = 2000.0
    duration: Optional[float] = None


class FailRegionCmd(BaseCmd):
    cmd: Literal["fail_region"]
    args: FailRegionArgs


class RestoreAllCmd(BaseCmd):
    cmd: Literal["restore_all"]
    args: Optional[Dict[str, Any]] = None


ClientCmd = Union[
    PlayCmd,
    PauseCmd,
    ResetCmd,
    SetScaleCmd,
    SetWeightsCmd,
    SetParamsCmd,
    FailLinkCmd,
    RestoreLinkCmd,
    FailSatCmd,
    RestoreSatCmd,
    MoveSatCmd,
    MoveGsCmd,
    PreviewOrbitCmd,
    SetFlowScaleCmd,
    AddFlowCmd,
    RemoveFlowCmd,
    AddSatCmd,
    RemoveSatCmd,
    PinSatCmd,
    FailPlaneCmd,
    FailRegionCmd,
    RestoreAllCmd,
]

COMMAND_MODEL_MAP = {
    "play": PlayCmd,
    "pause": PauseCmd,
    "reset": ResetCmd,
    "set_scale": SetScaleCmd,
    "set_weights": SetWeightsCmd,
    "set_params": SetParamsCmd,
    "fail_link": FailLinkCmd,
    "restore_link": RestoreLinkCmd,
    "fail_sat": FailSatCmd,
    "restore_sat": RestoreSatCmd,
    "move_sat": MoveSatCmd,
    "move_gs": MoveGsCmd,
    "preview_orbit": PreviewOrbitCmd,
    "set_flow_scale": SetFlowScaleCmd,
    "add_flow": AddFlowCmd,
    "remove_flow": RemoveFlowCmd,
    "add_sat": AddSatCmd,
    "remove_sat": RemoveSatCmd,
    "pin_sat": PinSatCmd,
    "fail_plane": FailPlaneCmd,
    "fail_region": FailRegionCmd,
    "restore_all": RestoreAllCmd,
}


def parse_command(msg: Dict[str, Any]) -> ClientCmd:
    """Parse and validate incoming client command dictionary.

    Raises ValueError with a clear message if cmd is unknown or arguments are invalid.
    """
    if not isinstance(msg, dict):
        raise ValueError(f"Command message must be a dictionary, got {type(msg).__name__}")

    raw_cmd = msg.get("cmd")
    if not raw_cmd or not isinstance(raw_cmd, str):
        raise ValueError("Missing or invalid 'cmd' field in message")

    cmd_lower = raw_cmd.lower()
    model_cls = COMMAND_MODEL_MAP.get(cmd_lower)
    if model_cls is None:
        raise ValueError(f"Unknown command: '{raw_cmd}'")

    try:
        return model_cls.model_validate(msg)
    except Exception as exc:
        raise ValueError(f"Invalid arguments for command '{raw_cmd}': {exc}") from exc
