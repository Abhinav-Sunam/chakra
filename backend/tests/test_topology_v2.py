"""Unit tests for Phase M2: Topology v2, plane/region failures, link TTL, and partition detection."""


from app.sim.engine import Engine
from app.sim.topology import link_ttl


def test_fail_plane():
    """Verify failing a plane downs all its satellites (10 sats) and removes them from routing."""
    engine = Engine(seed=42)
    target_plane = 3
    sats_in_plane_expected = [i for i, p in enumerate(engine.constellation.plane_index) if p == target_plane]
    assert len(sats_in_plane_expected) == 10

    # Fail plane 3
    evts = engine.apply_command("fail_plane", {"plane": target_plane})
    assert len(evts) == 1
    assert "Plane 3 lost — 10 satellites offline" in evts[0]["msg"]

    # All 10 satellites must be marked failed
    for sat_id in sats_in_plane_expected:
        assert sat_id in engine.cond.failed_nodes

    # Step simulation and check frame
    frame = engine.step(0.05)
    for sat in frame["sats"]:
        if sat["id"] in sats_in_plane_expected:
            assert sat["st"] == 1  # down

    # Restore all
    engine.apply_command("restore_all", {})
    assert len(engine.cond.failed_nodes) == 0


def test_fail_region():
    """Verify fail_region selects and disables satellites within the target radius."""
    engine = Engine(seed=42)
    # Target near Singapore: lat 1.35, lon 103.82, radius 2500 km
    evts = engine.apply_command("fail_region", {"lat": 1.35, "lon": 103.82, "radius_km": 2500.0})
    assert len(evts) == 1
    assert "Solar/debris event" in evts[0]["msg"]

    failed_count = len(engine.cond.failed_nodes)
    assert failed_count > 0, "At least some satellites should be in the 2500 km radius"

    # Step frame
    frame = engine.step(0.05)
    assert frame["metrics"]["activeFailures"] >= failed_count


def test_link_ttl():
    """Verify link_ttl computes remaining time to link expiration."""
    engine = Engine(seed=42)
    pos_now = engine.last_pos
    # Generate 12 future steps (+5s..+60s)
    future_dt = 5.0
    pos_future_list = [
        engine._get_sat_positions(engine.t + (k + 1) * future_dt)
        for k in range(12)
    ]
    links = engine.prev_topo.isl[:10]
    ttls = link_ttl(
        pos_now=pos_now,
        pos_future_list=pos_future_list,
        links=links,
        ground=engine.ground,
        params=engine.topo_params,
        future_dt_s=future_dt,
    )

    assert len(ttls) == len(links)
    for link_k, ttl_val in ttls.items():
        assert 0.0 <= ttl_val <= 60.0


def test_partition_detection():
    """Verify partition detection and isolated_stations reporting."""
    engine = Engine(seed=42)
    # Fail all links touching the first ground station
    gs0 = engine.ground[0]
    for sat_id, st_id in engine.prev_topo.gsl:
        if st_id == gs0.id:
            engine.cond.fail_link(sat_id, st_id, engine.t)

    frame = engine.step(0.05)
    assert frame["graph_partitioned"] is True
    assert gs0.id in frame["isolated_stations"]

