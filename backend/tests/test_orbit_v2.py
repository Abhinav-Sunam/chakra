"""Unit tests for Phase M1 Orbit v2 features."""

import numpy as np
import pytest

from app.sim.constants import R_EARTH
from app.sim.engine import Engine
from app.sim.orbit import ground_track, in_shadow, propagate_eci, walker_delta
from app.sim.tle import parse_tle_file, TLEConstellation


def test_add_remove_stable_ids():
    """Verify add_sat and remove_sat keeps satellite IDs stable."""
    engine = Engine(seed=42)
    initial_count = len(engine.constellation)
    assert initial_count == 120

    # Add a satellite over Singapore (lat 1.35, lon 103.82)
    res = engine.apply_command("add_sat", {"lat": 1.35, "lon": 103.82, "inc_deg": 53.0, "alt_km": 550.0})
    new_id = res["id"]
    assert new_id == 120
    assert len(engine.constellation) == 121

    # Ground stations should have re-indexed IDs starting from 121, but stable gs_id
    assert engine.ground[0].id == 121
    assert engine.ground[0].gs_id == 0

    frame = engine.step(0.05)
    sats = frame["sats"]
    sat_ids = [s["id"] for s in sats]
    assert 120 in sat_ids
    assert len(sats) == 121

    # Remove satellite 50
    engine.apply_command("remove_sat", {"id": 50})
    frame2 = engine.step(0.05)
    sats2 = frame2["sats"]
    sat_ids2 = [s["id"] for s in sats2]
    assert 50 not in sat_ids2
    # ID of newly added satellite is still 120
    assert 120 in sat_ids2
    assert len(sats2) == 120


def test_pin_sat_freezes_across_1000s():
    """Verify pinned satellite does not move across 1000 seconds."""
    engine = Engine(seed=42)
    sat_id = 10

    # Step to t=10s
    engine.tick(10.0)
    pos_before = engine._get_sat_positions(engine.t)[sat_id].copy()

    # Pin satellite
    engine.apply_command("pin_sat", {"id": sat_id, "pinned": True})

    # Advance 1000 seconds
    engine.tick(1000.0)
    pos_after = engine._get_sat_positions(engine.t)[sat_id].copy()

    # ECEF position must not change
    np.testing.assert_allclose(pos_before, pos_after, atol=1e-5)

    # Frame status for pinned sat should be 3
    frame = engine.step(0.05)
    sat_entry = next(s for s in frame["sats"] if s["id"] == sat_id)
    assert sat_entry["st"] == 3
    assert sat_entry["vlat"] == 0.0
    assert sat_entry["vlon"] == 0.0


def test_preview_orbit_track_190_points():
    """Verify ground track for 95 minutes with 30s step yields 191 points starting at target."""
    c = walker_delta(120, 12, 1, 53.0, 550.0)
    track = ground_track(c, 0, 0.0, 95.0 * 60.0, 30.0)
    # 95 * 60 / 30 = 190 intervals -> 191 points
    assert len(track) == 191


def test_eclipse_fraction():
    """Verify eclipse fraction for 550 km LEO is between 25% and 40% over one orbit."""
    c = walker_delta(120, 12, 1, 53.0, 550.0)
    period = 2.0 * np.pi / c.n[0]
    times = np.linspace(0, period, 200)
    fractions = []
    for t in times:
        r_eci = propagate_eci(c, t)
        sh = in_shadow(r_eci)
        fractions.append(np.mean(sh))
    avg_frac = np.mean(fractions)
    assert 0.25 <= avg_frac <= 0.40, f"Expected eclipse between 25% and 40%, got {avg_frac*100:.1f}%"


def test_tle_parsing_and_propagation():
    """Verify TLE sample file parsing and SGP4 propagation."""
    sats = parse_tle_file("data/starlink_sample.tle")
    assert len(sats) == 10

    const = TLEConstellation(sats)
    pos = const.positions_ecef(0.0)
    assert pos.shape == (10, 3)
    # Norm should be approximate LEO radius (~6900 km)
    radii = np.linalg.norm(pos, axis=-1)
    for r in radii:
        assert 6700.0 <= r <= 7200.0
