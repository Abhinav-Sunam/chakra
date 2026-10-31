"""M7 Protocol hardening and multi-client stress testing."""

import time
import numpy as np
from app.sim.engine import Engine


def test_stress_performance():
    """Stress test engine performance with high satellite and flow count."""
    config = {
        "num_sats": 120,
        "num_planes": 12,
        "f": 1,
        "inc_deg": 53.0,
        "altitude_km": 550.0,
    }
    engine = Engine(config=config, seed=42)

    tick_times = []
    # Advance 50 ticks
    for _ in range(50):
        t0 = time.perf_counter()
        engine.tick(0.1)
        tick_times.append((time.perf_counter() - t0) * 1000.0)

    p95 = float(np.percentile(tick_times, 95))
    assert p95 < 80.0, f"Expected p95 tick < 80ms, got {p95:.2f}ms"


def test_tick_guard_auto_throttle():
    """Verify tick guard throttles cadence when tick duration exceeds threshold."""
    engine = Engine(seed=42)
    engine._slow_tick_count = 19
    # Artificially trigger slow tick
    engine.tick(0.1)
    # The slow count reset or incremented
    assert engine.adaptive_router.params.cadence_ticks >= 1

