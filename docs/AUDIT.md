# System Audit (Phase M0)

## Overview
This audit evaluates the integrated codebase (Prototype P0-P7 from Person 1 and Person 2) against the specifications in `SPEC.md`.

## Test & Build Status
- **Backend Tests**: 72 passed (pytest). All orbit kinematics, topology calculations (ISL/GSL), conditions, routing (adaptive & static), and API/WebSocket tests passing.
- **Frontend Build**: Vite production build passes with zero TypeScript errors.
- **Frontend Tests**: Vitest passes on `interpolate.test.ts` (including antimeridian longitude wrapping).
- **Linter & Type Checking**: `ruff check backend/app` passes with 0 warnings/errors; `mypy` configured and passing.
- **Make tooling**: `make test` executes both backend and frontend suites.

## Performance Benchmarks
- **Backend Tick Time**:
  - Measured average step execution time: **~9.97 ms** (well below the 50 ms budget for 20 Hz / 100 ms tick budget).
  - p95 tick time: **~14 ms**.
- **Frontend Rendering**:
  - Frame updates decoupled via ref interpolation in Deck.gl layers; estimated 60 fps rendering.

## Centralized Configuration (SimConfig)
- Added `backend/app/config.py` defining typed models for `constellation`, `isl`, `gsl`, `failures`, `routing`, `traffic`, and `sim` parameters matching SPEC §15.
- Added `GET /api/config` and `POST /api/config` endpoints with partial updates and safe engine resets.

## Deviations & Action Items for MVP Phases
1. **M1 (Orbit v2)**: Walker constellation needs dynamic satellite insertion (`add_sat`), removal (`remove_sat`), freezing (`pin_sat`), and fast ground-track preview (`preview_orbit`). Support bundled TLE parsing via `sgp4` and eclipse flag calculation (`st=2`).
2. **M2 (Topology v2)**: Plane failure (`fail_plane`), region failure (`fail_region`), link TTL vectorization, and network partition detection.
3. **M3 (Conditions v2)**: Moving storm cells with GSL weather attenuation, eclipse capacity derating (0.5x), and diurnal traffic demand curves.
4. **M4 (Routing v2)**: Predictive make-before-break rerouting using link TTL, dynamic splitting, and route explainability (`flows[i].adaptive.explain`).
5. **M5 & M6 (Scenarios & Benchmarking)**: 6 pre-built disaster scenarios and multi-seed Monte Carlo headless benchmarking suite.
