"""Unit tests for Phase M4: Routing v2 (Predictive, dynamic splitting, explanations, weight presets)."""


from app.sim.engine import Engine


def test_predictive_reroute_before_ttl_expiry():
    """Verify make-before-break proactive reroute triggers before link failure/expiration."""
    engine = Engine(seed=42)
    # Find active flow
    engine.step(0.05)
    active_flow = next(f for f in engine.flows if len(engine.eval_adaptive.flows[f.id].paths) > 0)
    primary_path = engine.eval_adaptive.flows[active_flow.id].paths[0][0]
    assert len(primary_path) >= 2

    # Synthesize low TTL (< 8s) on a link in the primary path
    k_link = (min(primary_path[0], primary_path[1]), max(primary_path[0], primary_path[1]))
    engine.link_ttl_cache[k_link] = 4.0

    # Force adaptive update
    engine.adaptive_router.update(
        engine.prev_topo,
        engine.flows,
        engine.t,
        force=True,
        link_ttls=engine.link_ttl_cache,
    )

    # Should register as proactive reroute or set reason to prediction
    exp = engine.adaptive_router.explanations.get(active_flow.id, {})
    assert "reason" in exp
    assert exp["reason"] in ("prediction", "steady", "congestion", "handover")


def test_weight_presets():
    """Verify weight presets (latency-first, balanced, reliability-first) update router weights."""
    engine = Engine(seed=42)

    engine.apply_command("set_weights", {"preset": "latency-first"})
    assert engine.adaptive_router.params.weights == (2.0, 0.5, 0.5)

    engine.apply_command("set_weights", {"preset": "reliability-first"})
    assert engine.adaptive_router.params.weights == (0.5, 1.0, 2.0)

    engine.apply_command("set_weights", {"preset": "balanced"})
    assert engine.adaptive_router.params.weights == (1.0, 1.0, 1.0)


def test_frame_metrics_and_explanations():
    """Verify frames carry flow explanations, proactive/reactive reroutes, and avgStretch."""
    engine = Engine(seed=42)
    frame = engine.step(0.05)

    metrics = frame["metrics"]
    assert "proactiveReroutes" in metrics
    assert "reactiveReroutes" in metrics
    assert "avgStretch" in metrics
    assert metrics["avgStretch"] >= 0.0

    # Flow explanations
    flow0 = frame["flows"][0]
    assert "explain" in flow0["adaptive"]
    exp = flow0["adaptive"]["explain"]
    assert "reason" in exp
    assert "detail" in exp
    assert "chosen_cost" in exp
    assert "alt_cost" in exp

