# QA Validation & System Checklist (Chakravyuh MVP)

## 1. System Health & Cold Start
- [x] Backend FastAPI startup `< 1.5s`
- [x] WebSocket handshake `/ws` succeeds and yields `init` metadata within 50ms
- [x] Initial Walker-Delta constellation initialized with 120 satellites in 12 planes
- [x] 8 Ground stations positioned globally with valid ECEF and coordinates
- [x] 8 Default cross-continental traffic flows active

## 2. Dynamic Failure & Disaster Scenarios
- [x] `solar_storm`: Region failure + plane down + intensity multiplier executes deterministically
- [x] `flash_crowd`: Traffic hotspot 3x/4x multipliers scale station flow loads
- [x] `monsoon_storm`: Atmospheric storm cells induce localized GSL rain fade attenuation
- [x] `gateway_down`: Station disconnection and graceful flow rerouting
- [x] `cascade`: Stochastic progressive failure propagation & recovery
- [x] `calm_baseline`: Stable steady-state baseline

## 3. Autonomous Adaptive Routing (Cost Function)
- [x] Multi-objective routing: $C(e) = \alpha \cdot \text{latency} + \beta \cdot \text{congestion} + \gamma \cdot \text{risk}$
- [x] Pre-computed link TTL forward propagation (predictive handover before expiration)
- [x] Multipath load splitting for links with load $\rho \ge 0.60$
- [x] Make-before-break proactive rerouting
- [x] Explainability payload on each flow frame (`explain.reason`, `explain.detail`)

## 4. UI & Dashboard
- [x] 2D Map with Deck.gl rendering satellites, ISL links, GSLs, and flow lines
- [x] Real-time latency & PDR sparklines with 120-frame rolling window
- [x] Dynamic chaos injection drawer (break links, break satellites, trigger scenarios)
- [x] Satellite inspector overlay (telemetry, coordinates, failure toggle, pin/unpin)
- [x] Multi-client support & role separation (`viewer` vs `controller`)

## 5. Deployment & Reliability
- [x] 100/100 pytest test suite passing
- [x] Zero ruff lint errors (`ruff check app/ tests/`)
- [x] Clean TypeScript build (`npm run build`)
- [x] Standalone multi-stage `Dockerfile` and `docker-compose.yml`
- [x] Zero-dependency runner script `scripts/run_prod.sh`

