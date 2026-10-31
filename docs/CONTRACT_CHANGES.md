v1 contract frozen

## Differences and Confirmations (Engine Implementation vs SPEC Section 12)

1. **`Init.config` dictionary**:
   - The engine produces `config` with keys `{"num_sats": int, "time_scale": float, "cadence_ticks": int}`.
   - Handled via `SimConfig` with `extra="allow"` to support loose/extensible configuration dictionaries.

2. **Link state (`links[].up`)**:
   - Represented as integer `1` (link operational) or `0` (link down) in `Engine.step()` output.
   - `LinkOut.up` model specifies `int` (1 / 0).

3. **Satellite status (`sats[].st`)**:
   - Represented as integer `0` (operational), `1` (failed node), `2` (eclipse shadow), `3` (pinned / manual).
   - `SatOut.st` model specifies `int` (0, 1, 2, 3).

4. **Flow structure (`flows[]`)**:
   - Each entry has `id: str`, `adaptive: FlowEval`, and `static: FlowEval`.
   - Each `FlowEval` contains `paths` (list of `{"nodes": list[int], "mbps": float}`), `ms: float`, `pdr: float`, and `blackholed: bool`.

5. **Client Commands & Responses (Sync S1 / M1 additions)**:
   - Command models extend `BaseCmd` supporting optional request tracking `id` and `type` tag.
   - `add_sat`: `{"cmd": "add_sat", "args": {"lat": float, "lon": float, "inc_deg"?: float, "alt_km"?: float}}` -> creates satellite, rephases to (lat, lon), re-indexes ground station ids (N_current + g), keeps stable `gs_id`.
   - `remove_sat`: `{"cmd": "remove_sat", "args": {"id": int}}` -> marks removed while preserving array indexing.
   - `pin_sat`: `{"cmd": "pin_sat", "args": {"id": int, "pinned": bool}}` -> freezes satellite ECEF position across ticks (`st=3`). Unpin rephases at current position.
   - `preview_orbit`: `{"cmd": "preview_orbit", "args": {"id"?: int, "lat"?: float, "lon"?: float}}` -> returns `{"type": "orbit_preview", "id": int, "inc_deg": float, "period_s": float, "track": [[lon, lat], ...], "segments": [[[lon, lat], ...]]}`.
