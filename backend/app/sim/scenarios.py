"""Scenario engine for scripted simulation disasters and state replays."""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class ScenarioEvent(BaseModel):
    t: float
    cmd: str
    args: Dict[str, Any] = {}


class Scenario(BaseModel):
    name: str
    title: str
    description: str
    duration_s: float = 300.0
    seed: int = 42
    config_overrides: Dict[str, Any] = {}
    events: List[ScenarioEvent] = []


SCENARIOS_DIR = os.path.join(os.path.dirname(__file__), "..", "scenarios")


def list_scenarios() -> List[Dict[str, Any]]:
    """List all available built-in and uploaded scenarios."""
    scenarios = []
    if not os.path.exists(SCENARIOS_DIR):
        return scenarios

    for fname in sorted(os.listdir(SCENARIOS_DIR)):
        if fname.endswith(".json"):
            path = os.path.join(SCENARIOS_DIR, fname)
            try:
                with open(path, "r") as f:
                    data = json.load(f)
                    scenarios.append({
                        "name": data.get("name", fname[:-5]),
                        "title": data.get("title", fname[:-5]),
                        "description": data.get("description", ""),
                        "duration_s": data.get("duration_s", 300.0),
                    })
            except Exception:
                continue
    return scenarios


def load_scenario(name: str) -> Optional[Scenario]:
    """Load a scenario definition by name."""
    path = os.path.join(SCENARIOS_DIR, f"{name}.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r") as f:
            data = json.load(f)
            return Scenario.model_validate(data)
    except Exception:
        return None


def save_scenario(scenario: Scenario) -> None:
    """Save or upload custom scenario definition."""
    os.makedirs(SCENARIOS_DIR, exist_ok=True)
    path = os.path.join(SCENARIOS_DIR, f"{scenario.name}.json")
    with open(path, "w") as f:
        json.dump(scenario.model_dump(), f, indent=2)

