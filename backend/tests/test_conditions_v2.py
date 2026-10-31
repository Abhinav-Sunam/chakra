"""Unit tests for Phase M3: Conditions v2 (Storm cells, eclipse derate, diurnal traffic, hotspots)."""


from app.sim.engine import Engine
from app.sim.traffic import diurnal_factor


def test_storm_weather_reduces_gsl_survival():
    """Verify storm cell over ground station reduces survive on GSLs and not on ISLs."""
    engine = Engine(seed=42)
    # Find a ground station that currently has active GSL connections
    frame0 = engine.step(0.05)
    gsl_links = [lnk for lnk in frame0["links"] if lnk["k"] == 1]
    assert len(gsl_links) > 0, "Expected at least one active GSL link in frame"

    # Identify the station from the first GSL link (node id >= 120)
    target_link = gsl_links[0]
    st_id = max(target_link["a"], target_link["b"])
    target_gs = next(gs for gs in engine.ground if gs.id == st_id)
    loss0 = target_link["loss"]

    # Add storm directly over this connected ground station
    engine.apply_command("add_storm", {
        "id": "target_storm",
        "lat": target_gs.lat,
        "lon": target_gs.lon,
        "radius_km": 1000.0,
        "intensity": 1.0,
    })

    # Step frame
    frame1 = engine.step(0.05)
    updated_gsl = next(
        lnk for lnk in frame1["links"]
        if (lnk["a"] == target_link["a"] and lnk["b"] == target_link["b"])
    )
    loss1 = updated_gsl["loss"]

    # Storm weather must increase GSL packet loss (decrease survival)
    assert loss1 > loss0, f"Expected loss1 ({loss1}) > loss0 ({loss0})"

    # Verify frame exposes storms list
    assert len(frame1.get("storms", [])) == 1
    assert frame1["storms"][0]["id"] == "target_storm"


def test_eclipse_derates_isl_capacity():
    """Verify ISL capacity is halved for links touching a satellite in shadow."""
    engine = Engine(seed=42)
    # Step engine to populate eclipsed_sats
    engine.step(0.05)
    eclipsed = engine.cond.eclipsed_sats
    assert len(eclipsed) > 0, "At least some satellites must be in eclipse"

    eclipsed_sat = next(iter(eclipsed))
    # Check link_props with one endpoint eclipsed
    props = engine.cond.link_props(engine.prev_topo, eclipsed_sat, (eclipsed_sat + 1) % 120)
    # ISL normal capacity is 2000 Mbps -> derated is 1000 Mbps
    assert props["capacity_mbps"] == 1000.0


def test_diurnal_bounds_and_hotspot_expiration():
    """Verify diurnal variation bounds [0.4, 1.0] and flash crowd hotspot expiration."""
    # Diurnal factor check across 24 hours
    for t_hour in range(24):
        val = diurnal_factor(t_hour * 3600.0, src_lon=77.21)
        assert 0.4 <= val <= 1.0

    # Hotspot test
    engine = Engine(seed=42)
    gs_id = engine.ground[0].id
    engine.apply_command("set_hotspot", {"gs_id": gs_id, "factor": 4.0, "duration_s": 50.0})
    assert gs_id in engine.hotspots

    # Advance 60s -> should expire
    engine.tick(60.0)
    assert gs_id not in engine.hotspots
