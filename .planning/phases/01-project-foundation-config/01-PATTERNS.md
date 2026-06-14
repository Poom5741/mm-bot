# Phase 1 Patterns

**Phase:** 01 — Project Foundation & Config
**Date:** 2026-06-14

## Existing Code Analogs

None — this is a fresh project with no existing code. Phase 1 establishes the patterns that all subsequent phases follow.

## Files to Create (Phase 1)

| File | Role | Pattern Source |
|------|------|---------------|
| `pyproject.toml` | Project metadata, build system | Python packaging standard (PEP 517/518) |
| `requirements.txt` | Runtime dependencies | Plain pinned deps list |
| `requirements-dev.txt` | Dev/test dependencies | Plain pinned deps list |
| `.env.example` | Secret/config documentation | 12-factor env documentation |
| `.gitignore` | Git exclusions | Standard Python .gitignore |
| `src/mgw_mm/__init__.py` | Package root | Empty or `__version__` |
| `src/mgw_mm/__main__.py` | Entry point | `asyncio.run()` pattern |
| `src/mgw_mm/config.py` | Typed config | pydantic-settings nested models |
| `src/mgw_mm/exchange.py` | Exchange client stub | Class with `__init__(config: NetworkConfig)` |
| `src/mgw_mm/market_data.py` | Market data stub | Class with `__init__(config: TradingConfig)` |
| `src/mgw_mm/quoting.py` | Quoting engine stub | Class with `__init__(config: TradingConfig)` |
| `src/mgw_mm/risk.py` | Risk manager stub | Class with `__init__(config: RiskConfig)` |
| `src/mgw_mm/pnl.py` | PnL tracker stub | Class with `__init__(config: TradingConfig)` |
| `src/mgw_mm/telegram.py` | Telegram bot stub | Class with `__init__(config: TelegramConfig)` |
| `src/mgw_mm/ai_guardrail.py` | AI guardrail stub | Class stub only |
| `src/mgw_mm/orchestrator.py` | Main async loop stub | `async def run(settings: Settings)` |
| `tests/__init__.py` | Test package root | Empty |
| `tests/test_config.py` | Config unit tests | pytest with env monkeypatching |

## Established Conventions (set by Phase 1 for all subsequent phases)

1. **Logging pattern:** Every module — `logger = structlog.get_logger(__name__)` at module top level.
2. **Config slice pattern:** Each component receives its config slice, not the full `Settings` object.
3. **Module signature:** Classes accept typed config slices in `__init__`, use `logger.info(...)` for events.
4. **Secret handling:** Private keys are consumed immediately to create wallet objects; raw key strings are discarded and never stored as attributes.

## ## PATTERN MAPPING COMPLETE
