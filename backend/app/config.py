"""Centralized simulation configuration holding SPEC §15 defaults."""

from typing import Literal, Tuple

from pydantic import BaseModel, Field


class ConstellationConfig(BaseModel):
    mode: Literal["walker", "tle"] = "walker"
    T: int = Field(default=120, description="Total satellites")
    P: int = Field(default=12, description="Number of orbital planes")
    F: int = Field(default=1, description="Walker phasing factor")
    inc_deg: float = Field(default=53.0, description="Inclination in degrees")
    alt_km: float = Field(default=550.0, description="Altitude in km")


class IslConfig(BaseModel):
    max_range_km: float = Field(default=5000.0, description="Max ISL communication range")
    build_frac: float = Field(default=0.92, description="Fraction of max range for building links")
    max_deg: int = Field(default=4, description="Max ISL degree per satellite")
    capacity_mbps: float = Field(default=2000.0, description="ISL link capacity in Mbps")


class GslConfig(BaseModel):
    el_min_deg: float = Field(default=10.0, description="Min ground elevation angle in degrees")
    drop_margin_deg: float = Field(default=2.0, description="Drop margin in degrees")
    k: int = Field(default=3, description="Max simultaneous GSL links per ground station")
    capacity_mbps: float = Field(default=1000.0, description="GSL link capacity in Mbps")


class FailuresConfig(BaseModel):
    mtbf_link_s: float = Field(default=6000.0, description="Mean time between link failures")
    down_s: Tuple[float, float] = Field(default=(20.0, 90.0), description="Down duration range (min, max)")
    intensity: float = Field(default=1.0, description="Failure rate multiplier")
    detect_delay_s: float = Field(default=1.0, description="Detection delay in seconds")


class RoutingConfig(BaseModel):
    weights: Tuple[float, float, float] = Field(default=(1.0, 1.0, 1.0), description="(a_lat, b_cong, c_risk)")
    chunks: int = Field(default=4, description="Traffic splitting chunks")
    stickiness: float = Field(default=0.9, description="Hysteresis stickiness factor")
    cadence_ticks: int = Field(default=5, description="Routing update cadence in ticks")


class TrafficConfig(BaseModel):
    flow_scale: float = Field(default=1.0, description="Global flow scale multiplier")
    diurnal: bool = Field(default=True, description="Enable diurnal demand variation")


class SimParamsConfig(BaseModel):
    tick_s: float = Field(default=0.1, description="Sim step dt in seconds")
    time_scale: float = Field(default=20.0, description="Simulation speedup factor")
    seed: int = Field(default=42, description="Random seed")


class SimConfig(BaseModel):
    """Unified configuration for SatRoute simulation."""
    constellation: ConstellationConfig = Field(default_factory=ConstellationConfig)
    isl: IslConfig = Field(default_factory=IslConfig)
    gsl: GslConfig = Field(default_factory=GslConfig)
    failures: FailuresConfig = Field(default_factory=FailuresConfig)
    routing: RoutingConfig = Field(default_factory=RoutingConfig)
    traffic: TrafficConfig = Field(default_factory=TrafficConfig)
    sim: SimParamsConfig = Field(default_factory=SimParamsConfig)


# Global default configuration instance
DEFAULT_CONFIG = SimConfig()
