"""Tests for scenario engine — loading, event dispatch, and REST endpoints."""

from __future__ import annotations

import pytest
from app.sim.engine import Engine
from app.sim.scenarios import list_scenarios, load_scenario


class TestScenarioLoading:
    """Tests for scenario file discovery and parsing."""

    def test_list_scenarios_returns_builtin(self) -> None:
        """list_scenarios() should find the 6 built-in scenario JSON files."""
        scenarios = list_scenarios()
        assert len(scenarios) >= 6
        names = [s["name"] for s in scenarios]
        assert "solar_storm" in names
        assert "calm_baseline" in names
        assert "flash_crowd" in names

    def test_load_scenario_solar_storm(self) -> None:
        """load_scenario('solar_storm') should parse all fields correctly."""
        sc = load_scenario("solar_storm")
        assert sc is not None
        assert sc.name == "solar_storm"
        assert sc.title == "Solar Storm & EMP"
        assert sc.duration_s == 360
        assert len(sc.events) == 4
        # First event at t=30
        assert sc.events[0].t == 30.0
        assert sc.events[0].cmd == "set_params"

    def test_load_scenario_not_found(self) -> None:
        """load_scenario with unknown name returns None."""
        assert load_scenario("nonexistent_scenario_xyz") is None


class TestScenarioPlayback:
    """Tests for scenario event dispatch inside the engine."""

    def test_load_scenario_command(self) -> None:
        """Engine should accept load_scenario command and queue events."""
        eng = Engine(seed=42)
        result = eng.apply_command("load_scenario", {"name": "calm_baseline"})
        assert result is not None
        assert len(result) > 0
        assert result[0]["kind"] == "scenario"
        assert eng.active_scenario is not None
        assert eng.active_scenario.name == "calm_baseline"

    def test_scenario_events_fire_at_correct_time(self) -> None:
        """Scenario events should fire when sim time reaches their scheduled time."""
        eng = Engine(seed=42)
        eng.apply_command("load_scenario", {"name": "solar_storm"})

        # solar_storm has first event at t=30 (set_params intensity=10.0)
        # Tick until t > 30
        dt = 2.0
        while eng.t < 35.0:
            eng.tick(dt)

        # After t=30, intensity should have been set to 10.0
        assert eng.cond.params.intensity == 10.0

    def test_scenario_invalid_name_raises(self) -> None:
        """Engine should raise ValueError for unknown scenario name."""
        eng = Engine(seed=42)
        with pytest.raises(ValueError, match="Scenario not found"):
            eng.apply_command("load_scenario", {"name": "does_not_exist"})

    def test_scenario_events_all_fire(self) -> None:
        """All scenario events should eventually fire when sim runs long enough."""
        eng = Engine(seed=42)
        eng.apply_command("load_scenario", {"name": "calm_baseline"})

        # Run for the full duration
        sc = eng.active_scenario
        assert sc is not None
        dt = 5.0
        while eng.t < sc.duration_s + 10.0:
            eng.tick(dt)

        # All events should have been dispatched
        assert len(eng.scenario_queue) == 0

    def test_scenario_reset_clears_state(self) -> None:
        """Resetting engine after scenario should clear scenario state."""
        eng = Engine(seed=42)
        eng.apply_command("load_scenario", {"name": "solar_storm"})
        assert eng.active_scenario is not None

        eng.apply_command("reset")
        assert eng.active_scenario is None
        assert len(eng.scenario_queue) == 0

