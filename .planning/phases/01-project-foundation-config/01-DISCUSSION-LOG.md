# Phase 1: Project Foundation & Config - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-14
**Phase:** 1-Project Foundation & Config
**Areas discussed:** Logging library, Project layout, Config model design, Startup output

---

## Logging Library

| Option | Description | Selected |
|--------|-------------|----------|
| structlog | Structured JSON output by default, composable processor pipeline, designed for long-running services | ✓ |
| loguru | Simpler DX, decorator-friendly, human-readable by default with optional JSON serialization | |

**User's choice:** structlog
**Notes:** No additional notes.

---

## Log Format

| Option | Description | Selected |
|--------|-------------|----------|
| JSON always | Machine-parseable, works directly with log aggregators. Consistent between dev and prod. | ✓ |
| Human-readable in dev, JSON in prod | Pretty colored output locally, JSON when deployed. Slightly more config, nicer local DX. | |

**User's choice:** JSON always
**Notes:** No additional notes.

---

## Default Log Level

| Option | Description | Selected |
|--------|-------------|----------|
| INFO | Order placed, fill received, cancel sent, risk check. Quiet enough for production, complete enough for audit. | ✓ |
| DEBUG | Everything including internal state. Verbose. | |

**User's choice:** INFO
**Notes:** No additional notes.

---

## Log Destination

| Option | Description | Selected |
|--------|-------------|----------|
| stdout only | Let the container/systemd capture and rotate logs. Standard 12-factor pattern. | ✓ |
| stdout + rotating log file | Keeps a local logs/ file alongside stdout. | |

**User's choice:** stdout only
**Notes:** No additional notes.

---

## Project Layout

| Option | Description | Selected |
|--------|-------------|----------|
| src/ package layout | All bot code lives in src/mgw_mm/. Entry point: python -m mgw_mm. Cleaner imports. | ✓ |
| Flat root layout | Modules directly at root. Simple for small projects. | |

**User's choice:** src/ package layout
**Notes:** No additional notes.

---

## Package Name

| Option | Description | Selected |
|--------|-------------|----------|
| bot | src/bot/ — short, readable | |
| mm_bot | src/mm_bot/ — more descriptive | |
| mgw_mm | src/mgw_mm/ — token-specific, makes purpose explicit | ✓ |

**User's choice:** mgw_mm
**Notes:** No additional notes.

---

## Module Organization

| Option | Description | Selected |
|--------|-------------|----------|
| By component role | One module per architectural component (config.py, exchange.py, quoting.py, etc.) | ✓ |
| By layer (core/infra/api) | More Java-like structure, more dirs to navigate | |
| You decide | Let Claude pick the module structure | |

**User's choice:** By component role
**Notes:** No additional notes.

---

## Config Model Organization

| Option | Description | Selected |
|--------|-------------|----------|
| Nested sections | NetworkConfig, TradingConfig, RiskConfig, TelegramConfig composed in Settings | ✓ |
| One flat Settings class | All params in a single class. Simpler to start, unwieldy at scale. | |

**User's choice:** Nested sections
**Notes:** No additional notes.

---

## Default Safe Values

| Option | Description | Selected |
|--------|-------------|----------|
| Very conservative | ORDER_SIZE_USDC=10, TICK_OFFSET=2, MAX_INVENTORY_USDC=100, MAX_CAPITAL_USDC=200, QUOTE_INTERVAL_SEC=30 | ✓ |
| Moderate | ORDER_SIZE_USDC=50, TICK_OFFSET=2, MAX_INVENTORY_USDC=500, MAX_CAPITAL_USDC=1000, QUOTE_INTERVAL_SEC=15 | |
| You decide | Let Claude pick sensible defaults | |

**User's choice:** Very conservative
**Notes:** No additional notes.

---

## Missing Secrets Behavior

| Option | Description | Selected |
|--------|-------------|----------|
| Crash immediately with a clear error list | Fail fast: list every missing/invalid field, then exit(1) | ✓ |
| Log a warning and continue with defaults | Only crash if absolutely nothing is usable | |

**User's choice:** Crash immediately with clear error list
**Notes:** No additional notes.

---

## Startup Output Format

| Option | Description | Selected |
|--------|-------------|----------|
| ASCII banner + config summary | Short ASCII banner with active network, target pair, and key params | ✓ |
| Structured log lines only | Pure JSON log events | |

**User's choice:** ASCII banner + config summary
**Notes:** No additional notes.

---

## MAINNET Warning Behavior

| Option | Description | Selected |
|--------|-------------|----------|
| Big visual warning + 3-second pause | Red/uppercase WARNING block when NETWORK=mainnet. Makes accidental mainnet runs hard to miss. | ✓ |
| Just log the active network | Log the network as a field in the startup event | |

**User's choice:** Big visual warning for MAINNET (with 3-second pause)
**Notes:** No additional notes.

---

## Banner Content

| Option | Description | Selected |
|--------|-------------|----------|
| Network + target pair | TESTNET/MAINNET and trading pair | ✓ |
| Order size + tick offset | ORDER_SIZE_USDC and TICK_OFFSET | ✓ |
| Risk caps | MAX_INVENTORY_USDC and MAX_CAPITAL_USDC | ✓ |
| API agent address (truncated) | First 6 + last 4 chars of agent wallet address | |

**User's choice:** Network + target pair, Order size + tick offset, Risk caps (agent address excluded)
**Notes:** Agent address omitted — security preference (avoid leaking address in screenshots).

---

## Claude's Discretion

- Exact ASCII banner style (border style, layout)
- `__main__.py` vs root `main.py` entry point
- `.env.example` content and format
- Whether `requirements.txt` is flat or split (base + dev)

## Deferred Ideas

None — discussion stayed within phase scope.
