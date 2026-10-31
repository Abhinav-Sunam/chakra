"""Tests for the multi-seed Monte Carlo benchmark runner."""

from __future__ import annotations

from app.sim.benchmark import run_benchmark, run_single_seed


class TestBenchmarkRunner:
    """Tests for benchmark execution and result structure."""

    def test_run_single_seed_baseline(self) -> None:
        """Single seed run should produce valid result structure."""
        result = run_single_seed(seed=42, duration_s=20.0, sim_dt=2.0)
        assert result["seed"] == 42
        assert "adaptive" in result
        assert "static" in result
        assert "tick_ms_p95" in result
        assert result["adaptive"]["latMs_mean"] >= 0
        assert result["static"]["latMs_mean"] >= 0
        assert len(result["timeseries"]) > 0

    def test_run_single_seed_with_scenario(self) -> None:
        """Single seed run with a scenario should load and execute it."""
        result = run_single_seed(
            seed=42, duration_s=40.0, sim_dt=2.0, scenario_name="calm_baseline"
        )
        assert result["seed"] == 42
        assert result["adaptive"]["latMs_mean"] >= 0

    def test_run_benchmark_aggregates(self) -> None:
        """Multi-seed benchmark should produce aggregated statistics."""
        result = run_benchmark(n_seeds=2, duration_s=20.0, sim_dt=2.0)
        assert result["n_seeds"] == 2
        assert result["scenario"] == "baseline"
        assert "aggregate" in result
        agg = result["aggregate"]

        # Check structure
        assert "adaptive" in agg
        assert "static" in agg
        assert "latMs" in agg["adaptive"]
        assert "mean" in agg["adaptive"]["latMs"]
        assert "std" in agg["adaptive"]["latMs"]
        assert "p95" in agg["adaptive"]["latMs"]

        assert len(result["per_seed"]) == 2
        assert result["wall_time_s"] > 0

    def test_run_benchmark_with_scenario(self) -> None:
        """Benchmark with scenario should work end to end."""
        result = run_benchmark(
            scenario_name="calm_baseline",
            n_seeds=2,
            duration_s=20.0,
            sim_dt=2.0,
        )
        assert result["scenario"] == "calm_baseline"
        assert result["n_seeds"] == 2
        assert len(result["per_seed"]) == 2

    def test_timeseries_has_data_points(self) -> None:
        """Timeseries output should have sampled data points."""
        result = run_single_seed(seed=42, duration_s=40.0, sim_dt=2.0)
        ts = result["timeseries"]
        assert len(ts) > 0
        assert "t" in ts[0]
        assert "adaptive_lat" in ts[0]
        assert "static_lat" in ts[0]
        assert "adaptive_pdr" in ts[0]

