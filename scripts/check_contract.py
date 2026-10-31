"""Contract verification script for SatRoute simulation engine output and schemas."""

import sys
import os

# Ensure backend root is in sys.path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.sim.engine import Engine
from app.schemas import (
    Init,
    Frame,
    parse_command,
)


def main():
    try:
        # 1. Initialize Engine(seed=42) and validate init_message
        engine = Engine(seed=42)
        init_data = engine.init_message()
        init_obj = Init.model_validate(init_data)
        assert init_obj.type == "init", f"Unexpected type: {init_obj.type}"
        assert init_obj.nSats == 120, f"Expected 120 sats, got {init_obj.nSats}"
        assert len(init_obj.ground) == 10, f"Expected 10 ground stations, got {len(init_obj.ground)}"
        assert len(init_obj.flows) == 8, f"Expected 8 flows, got {len(init_obj.flows)}"
        assert len(init_obj.planes) == 120, f"Expected 120 planes, got {len(init_obj.planes)}"

        # 2. Advance 20 steps and validate each frame
        for step_idx in range(20):
            frame_data = engine.step(0.1)
            frame_obj = Frame.model_validate(frame_data)
            assert frame_obj.type == "frame"
            assert len(frame_obj.sats) == 120
            assert len(frame_obj.flows) == 8
            assert len(frame_obj.links) > 0
            assert frame_obj.metrics.linkUptime >= 0.0

        # 3. Test parse_command on valid and invalid examples for every command
        command_tests = [
            # cmd_name, valid_msg, invalid_msg
            ("play", {"cmd": "play"}, {"cmd": "play", "args": "not_a_dict"}),
            ("pause", {"cmd": "pause"}, {"cmd": "pause", "args": "not_a_dict"}),
            ("reset", {"cmd": "reset"}, {"cmd": "reset", "args": "not_a_dict"}),
            ("set_scale", {"cmd": "set_scale", "args": {"scale": 30.0}}, {"cmd": "set_scale", "args": {"scale": "invalid"}}),
            ("set_weights", {"cmd": "set_weights", "args": {"a": 1.0, "b": 2.0, "c": 3.0}}, {"cmd": "set_weights", "args": {"a": "invalid"}}),
            ("set_params", {"cmd": "set_params", "args": {"intensity": 1.5}}, {"cmd": "set_params", "args": {"intensity": "invalid"}}),
            ("fail_link", {"cmd": "fail_link", "args": {"a": 0, "b": 1}}, {"cmd": "fail_link", "args": {"a": "not_int"}}),
            ("restore_link", {"cmd": "restore_link", "args": {"a": 0, "b": 1}}, {"cmd": "restore_link", "args": {"b": "not_int"}}),
            ("fail_sat", {"cmd": "fail_sat", "args": {"id": 5}}, {"cmd": "fail_sat", "args": {"id": "invalid"}}),
            ("restore_sat", {"cmd": "restore_sat", "args": {"id": 5}}, {"cmd": "restore_sat", "args": {"id": "invalid"}}),
            ("move_sat", {"cmd": "move_sat", "args": {"id": 5, "lat": 12.0, "lon": 34.0}}, {"cmd": "move_sat", "args": {"id": 5, "lat": "invalid", "lon": 34.0}}),
            ("move_gs", {"cmd": "move_gs", "args": {"id": 120, "lat": 12.0, "lon": 34.0}}, {"cmd": "move_gs", "args": {"id": 120, "lat": "invalid", "lon": 34.0}}),
            ("preview_orbit", {"cmd": "preview_orbit", "args": {"num_sats": 120}}, {"cmd": "preview_orbit", "args": {"num_sats": "invalid"}}),
            ("set_flow_scale", {"cmd": "set_flow_scale", "args": {"factor": 1.5}}, {"cmd": "set_flow_scale", "args": {"factor": "invalid"}}),
            ("add_flow", {"cmd": "add_flow", "args": {"src": 120, "dst": 121, "mbps": 500.0}}, {"cmd": "add_flow", "args": {"src": "invalid", "dst": 121, "mbps": 500.0}}),
            ("remove_flow", {"cmd": "remove_flow", "args": {"id": "DEL-LON"}}, {"cmd": "remove_flow", "args": {}}),
        ]

        for cmd_name, valid_msg, invalid_msg in command_tests:
            # Valid test
            parsed = parse_command(valid_msg)
            assert parsed.cmd == cmd_name, f"Expected cmd {cmd_name}, got {parsed.cmd}"

            # Invalid test
            invalid_failed = False
            try:
                parse_command(invalid_msg)
            except ValueError:
                invalid_failed = True
            assert invalid_failed, f"Expected ValueError for invalid {cmd_name} command: {invalid_msg}"

        # Test unknown command
        unknown_failed = False
        try:
            parse_command({"cmd": "unknown_command_foo"})
        except ValueError:
            unknown_failed = True
        assert unknown_failed, "Expected ValueError for unknown command"

        print("OK")
    except Exception as exc:
        print(f"Error: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
