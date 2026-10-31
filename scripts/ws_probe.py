"""WebSocket probe script for SatRoute simulation server."""

import asyncio
import json
import sys
import time
import websockets


async def run_probe():
    uri = "ws://localhost:8000/ws"
    print(f"Connecting to {uri}...")

    async with websockets.connect(uri) as ws:
        # 1. Receive init frame
        init_raw = await ws.recv()
        init_data = json.loads(init_raw)
        assert init_data.get("type") == "init", f"Expected init type, got {init_data.get('type')}"
        n_sats = init_data.get("nSats", 0)
        n_ground = len(init_data.get("ground", []))
        n_flows = len(init_data.get("flows", []))
        print(f"Init received: nSats={n_sats}, ground_stations={n_ground}, flows={n_flows}")

        # Track link to fail from static path
        fail_link_target = None
        cmd_sent = False
        invalid_cmd_sent = False
        ack_received = False
        event_received = False

        # 2. Monitor for 10 seconds, printing one line per second
        start_time = time.perf_counter()
        second_start = start_time
        frames_this_sec = 0
        last_t = 0.0
        last_tick_ms = 0.0
        last_links_count = 0
        last_frame_size_kb = 0.0

        for second_idx in range(1, 11):
            target_time = start_time + second_idx
            frames_this_sec = 0

            while time.perf_counter() < target_time:
                timeout = max(0.001, target_time - time.perf_counter())
                try:
                    msg_raw = await asyncio.wait_for(ws.recv(), timeout=timeout)
                except asyncio.TimeoutError:
                    break

                msg = json.loads(msg_raw)
                msg_type = msg.get("type")

                if msg_type == "frame":
                    frames_this_sec += 1
                    last_t = msg.get("t", 0.0)
                    last_tick_ms = msg.get("tickMs", 0.0)
                    last_links_count = len(msg.get("links", []))
                    last_frame_size_kb = len(msg_raw.encode("utf-8")) / 1024.0

                    # Find a static path link to fail if not yet selected
                    if fail_link_target is None and msg.get("flows"):
                        first_flow = msg["flows"][0]
                        static_paths = first_flow.get("static", {}).get("paths", [])
                        if static_paths and len(static_paths[0].get("nodes", [])) >= 2:
                            nodes = static_paths[0]["nodes"]
                            fail_link_target = (nodes[0], nodes[1])

                    # Check for link_fail event
                    events = msg.get("events", [])
                    for e in events:
                        if e.get("kind") == "link_fail":
                            event_received = True
                            print(f"[EVENT] Received event: kind={e.get('kind')}, msg='{e.get('msg')}'")

                elif msg_type == "ack":
                    ack_received = True
                    print(f"[ACK] Received ack: {msg}")

                elif msg_type == "error":
                    print(f"[ERROR] Received error response: {msg}")

            # Print one line per second
            print(
                f"Sec {second_idx:2d}: t={last_t:6.2f}s | tickMs={last_tick_ms:5.2f} | "
                f"links={last_links_count:4d} | size={last_frame_size_kb:5.2f} KB | fps={frames_this_sec:2d}"
            )

            # After 3 seconds, send fail_link command and invalid command
            if second_idx == 3 and not cmd_sent:
                if fail_link_target is None:
                    fail_link_target = (0, 55)

                cmd_payload = {
                    "type": "cmd",
                    "cmd": "fail_link",
                    "args": {"a": fail_link_target[0], "b": fail_link_target[1]},
                    "id": "probe-fail-1",
                }
                print(f"[COMMAND] Sending fail_link for hop {fail_link_target}...")
                await ws.send(json.dumps(cmd_payload))
                cmd_sent = True

            if second_idx == 4 and not invalid_cmd_sent:
                invalid_payload = {
                    "cmd": "invalid_probe_action",
                    "args": {"bad": True},
                    "id": "probe-err-1",
                }
                print("[COMMAND] Sending invalid command...")
                await ws.send(json.dumps(invalid_payload))
                invalid_cmd_sent = True

        print("Probe finished successfully.")
        return 0


def main():
    try:
        exit_code = asyncio.run(run_probe())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as exc:
        print(f"Probe failed: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
