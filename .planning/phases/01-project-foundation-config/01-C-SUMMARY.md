---
plan: 01-C
plan_name: Logging Setup, Startup Banner & Entry Point
phase: 1
status: complete
completed: 2026-06-14
---

# Plan C: Logging Setup, Startup Banner & Entry Point — Execution Summary

## What Was Built

structlog JSON logging pipeline, ASCII startup banner with mainnet warning, asyncio orchestrator skeleton, `__main__.py` entry point, and 8 tests covering logging and smoke behavior.

## Key Files Created

- `src/mgw_mm/logging_setup.py` — `configure_logging(log_level)` with JSON-always structlog pipeline
- `src/mgw_mm/orchestrator.py` — `async def run(settings)` skeleton emitting structured log events
- `src/mgw_mm/__main__.py` — startup sequence: config → logging → banner → mainnet pause → asyncio.run()
- `tests/test_logging.py` — 3 logging tests
- `tests/test_smoke.py` — 5 smoke tests

## Structlog Pipeline (D-01 to D-04)

```
merge_contextvars → add_log_level → _add_logger_name → TimeStamper(iso,utc=True)
→ StackInfoRenderer → format_exc_info → JSONRenderer
```
Factory: `PrintLoggerFactory()` (stdout only, no file). Level via `make_filtering_bound_logger`.

## Startup Banner (D-12 to D-15)

```
╔══════════════════════════════════════════╗
║  MGW/USDC Market-Maker Bot v0.1.0        ║
╠══════════════════════════════════════════╣
║  NETWORK:      TESTNET                   ║
║  PAIR:         PURR/USDC                 ║
║  ORDER SIZE:   10.00 USDC                ║
║  TICK OFFSET:  2                         ║
║  MAX INV:      100.00 USDC               ║
║  MAX CAPITAL:  200.00 USDC               ║
╚══════════════════════════════════════════╝
```

- Mainnet: `!!! WARNING: MAINNET MODE — REAL FUNDS AT RISK !!!` block prepended + `time.sleep(3)`
- Testnet: banner only, no pause
- Agent wallet address NOT shown anywhere in output

## End-to-End Smoke Verification

```
$ PYTHONPATH=src python -m mgw_mm  # (with testnet env vars)
[banner printed to stdout]
{"network":"testnet","pair":"PURR/USDC","api_url":"...","event":"orchestrator_starting",...}
{"status":"skeleton_mode","event":"orchestrator_ready",...}
[exit 0]
```

- JSON logs parseable by `json.loads()`
- `grep ac0974 output` → 0 matches (private key not leaked)

## Acceptance Criteria — Verified

- [x] `python -m mgw_mm` exits 0 with required env vars set
- [x] First banner line contains "TESTNET" / "MAINNET"
- [x] JSON log lines contain `event`, `level`, `timestamp` keys
- [x] No private key hex pattern in any output
- [x] `configure_logging("GARBAGE")` raises `ValueError`
- [x] All 8 tests pass (3 logging + 5 smoke)
- [x] Full suite 30/30 pass

## Self-Check: PASSED

## Requirements Addressed

- FND-04: `NETWORK` switch selects endpoints; network logged prominently at startup
- FND-05: structlog writes structured JSON log line for every significant event
