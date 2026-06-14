# Phase 1 Research: Project Foundation & Config

**Phase:** 01 — Project Foundation & Config
**Research date:** 2026-06-14
**Scope:** "What do I need to know to PLAN Phase 1 well?"

---

## Summary

Phase 1 is a pure infrastructure phase — no trading logic. The deliverables are: a `src/mgw_mm/` Python package skeleton, a typed pydantic-settings config system loading from `.env`, fail-fast secret validation, a testnet/mainnet network switch, and structlog JSON logging. All subsequent phases build directly on top of what Phase 1 establishes, so correctness and completeness of conventions here matters disproportionately.

---

## Key Technical Facts

### Package Layout — `src/` layout with `python -m mgw_mm`

- Use `src/mgw_mm/` package layout (D-05, D-06).
- The idiomatic Python entry point for `python -m mgw_mm` requires a `src/mgw_mm/__main__.py` file.
- Alternatively, a root `main.py` that calls `from mgw_mm.orchestrator import main; main()` works but is less clean for `-m` invocation.
- **Decision (Claude's discretion):** Use `src/mgw_mm/__main__.py` — it's the correct Python idiom for runnable packages, keeps the root directory clean.
- `setup.cfg` or `pyproject.toml` must declare `packages = find:` with `package_dir = {"": "src"}` so the package installs correctly (needed for future Docker image building).

### pydantic-settings — Nested Config Sections (D-08)

- pydantic-settings v2 (pydantic v2 backend) uses `model_config = SettingsConfigDict(env_nested_delimiter='__')` to parse `NETWORK_CONFIG__NETWORK=mainnet` style vars.
- Alternatively, top-level `Settings` composes nested models with `env_prefix` per model — each component explicitly reads its own prefix.
- **Recommended approach for this project:** Flat-prefix per section is more readable in `.env.example`:
  - `NETWORK=testnet` (read by `NetworkConfig`)
  - `TARGET_PAIR=PURR/USDC` (read by `TradingConfig`)
  - `AGENT_PRIVATE_KEY=0x...` (read by `Settings` directly, not a sub-model)
- The `Settings` top-level model composes nested models via `model_validator(mode='before')` or via field default_factory that instantiates sub-models from env.
- **Alternative (simpler for Phase 1):** Single flat `Settings` class with all fields, grouped by comment blocks. Refactor to nested sections if needed in a later phase. → Keep nested as per D-08 but use pydantic `model_config` with `env_nested_delimiter='__'` only for nested models.

### Secrets & Fail-Fast (D-10, D-11)

- `AGENT_PRIVATE_KEY` and `TELEGRAM_BOT_TOKEN` are both required fields with no default — pydantic-settings will raise `ValidationError` on startup if either is missing.
- The fail-fast pattern: catch `ValidationError` in `__main__.py`, print all missing fields clearly (field name + validation error message), then `sys.exit(1)`.
- `AGENT_PRIVATE_KEY` must NEVER appear in logs. structlog's `bind_contextvars` must exclude it. A helper that loads the key and immediately creates the wallet object (discarding the raw string) is safer.
- `.env` must be in `.gitignore` from the first commit (before any secrets could be added).

### structlog — JSON Always (D-01 through D-04)

- structlog with `JSONRenderer` as the final processor outputs JSON to stdout.
- Standard setup:
  ```python
  structlog.configure(
      processors=[
          structlog.stdlib.add_log_level,
          structlog.stdlib.add_logger_name,
          structlog.processors.TimeStamper(fmt="iso"),
          structlog.processors.JSONRenderer(),
      ],
      wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
      logger_factory=structlog.PrintLoggerFactory(),
  )
  ```
- Log level controlled by `LOG_LEVEL` env var; parse with `logging.getLevelName()`.
- Every module should use `logger = structlog.get_logger(__name__)` at module level.
- **Important:** Wire structlog BEFORE any module-level loggers are created. Init in `__main__.py` before importing other modules.

### Startup Banner & Mainnet Warning (D-12 through D-15)

- Print ASCII banner to **stdout** (not via structlog — it's human-readable, not JSON).
- After the banner, switch to JSON-only structlog output.
- Mainnet warning: `time.sleep(3)` blocks the asyncio event loop only if called before loop start. Since the banner runs before `asyncio.run(main())`, this is safe.
- Banner content: Network (TESTNET/MAINNET), target pair, order size, tick offset, risk caps (MAX_INVENTORY_USDC, MAX_CAPITAL_USDC).
- **Security:** Agent wallet address must NOT appear in the banner (D-13).

### Module Skeleton — All 9 modules (D-07)

Each module needs a minimal skeleton that:
1. Can be imported without errors
2. Defines the module's public interface (class or functions)
3. Uses structlog at module level
4. Accepts a config slice (not the full `Settings` object)

**Module stubs needed:**
- `config.py` — `Settings`, `NetworkConfig`, `TradingConfig`, `RiskConfig`, `TelegramConfig`
- `exchange.py` — `HyperliquidClient` class stub (init only)
- `market_data.py` — `MarketData` class stub
- `quoting.py` — `QuotingEngine` class stub
- `risk.py` — `RiskManager` class stub
- `pnl.py` — `PnLTracker` class stub
- `telegram.py` — `TelegramBot` class stub
- `ai_guardrail.py` — `AIGuardrail` class stub
- `orchestrator.py` — `async def run()` function (entry point)
- `__init__.py` — empty or version string
- `__main__.py` — `asyncio.run(run())` after config init and banner

### Dependencies — `requirements.txt`

Phase 1 requirements (pinned to tested versions):
```
hyperliquid-python-sdk>=0.9.0   # official SDK — pin to specific version after install
eth-account>=0.12.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
structlog>=24.0.0
python-telegram-bot>=21.0.0
```

Dev dependencies (separate `requirements-dev.txt`):
```
pytest>=8.0.0
pytest-asyncio>=0.23.0
python-dotenv>=1.0.0  # for loading .env in tests
```

### `.env.example` — every variable with comments

Required fields:
```
# Network: testnet | mainnet
NETWORK=testnet

# Trading
TARGET_PAIR=PURR/USDC
ORDER_SIZE_USDC=10
TICK_OFFSET=2
QUOTE_INTERVAL_SEC=30

# Risk caps
MAX_INVENTORY_USDC=100
MAX_CAPITAL_USDC=200
MIN_SPREAD_TICKS=1
MAX_SPREAD_TICKS=10
KILL_SWITCH_VOL_THRESHOLD=0.05

# Secrets — NEVER commit actual values
AGENT_PRIVATE_KEY=0x...
TELEGRAM_BOT_TOKEN=...
TELEGRAM_OWNER_CHAT_ID=...
```

### Project Packaging — `pyproject.toml` vs `setup.cfg`

- Modern Python (3.11+) prefers `pyproject.toml` for project metadata.
- Minimal `pyproject.toml`:
  ```toml
  [build-system]
  requires = ["setuptools>=68"]
  build-backend = "setuptools.backends.legacy:build"

  [project]
  name = "mgw-mm"
  version = "0.1.0"
  requires-python = ">=3.11"

  [tool.setuptools.packages.find]
  where = ["src"]
  ```
- This is needed so `python -m mgw_mm` resolves the package from `src/`.

### Testing Setup (pytest)

Phase 1 test scope:
- `tests/test_config.py` — verify defaults load, fail-fast on missing secrets, NETWORK validation
- No integration tests in Phase 1 (no exchange connection yet)
- `pytest.ini` or `pyproject.toml [tool.pytest.ini_options]` to set `testpaths = ["tests"]` and `asyncio_mode = "auto"` for future async tests

---

## Validation Architecture

### Nyquist Test Coverage Requirements (Phase 1)

| Component | Test Type | What to Test |
|-----------|-----------|--------------|
| Config loading | Unit | Defaults load correctly from env |
| Config loading | Unit | Missing `AGENT_PRIVATE_KEY` → exits 1 |
| Config loading | Unit | Missing `TELEGRAM_BOT_TOKEN` → exits 1 |
| Config loading | Unit | `NETWORK=mainnet` accepted; invalid `NETWORK=xyz` → error |
| Config defaults | Unit | All conservative defaults match D-09 values |
| Structlog setup | Unit | Logger emits valid JSON (parse-check) |
| Banner output | Unit | Contains "TESTNET" or "MAINNET" prominently |
| Import smoke test | Unit | All 9 modules import without error |

---

## Pitfalls Relevant to Phase 1

From PITFALLS.md:

**#8 — Secret leakage (HIGH)**
- Prevention: env-only secrets; `.gitignore` `.env`; never log keys; commit `.env.example` not `.env`.
- Concrete action: Add `.env` to `.gitignore` in the FIRST commit (before adding any secrets).

**#9 — Testnet/mainnet mix-up (HIGH)**
- Prevention: Single `NETWORK` env var drives endpoint selection; loud ASCII banner showing active network; require `NETWORK=mainnet` to switch.
- The 3-second pause on mainnet start is intentional UX friction (D-14).

---

## Open Questions (Resolved)

1. **`__main__.py` vs root `main.py`?** → `src/mgw_mm/__main__.py` (per Claude's discretion). Both work; `__main__.py` is idiomatically correct for `-m` invocation.
2. **Flat or nested config?** → Nested sections as per D-08, using `model_config` with `env_nested_delimiter='__'` for sub-models, or explicit env-prefix mapping. Use flat env vars (no double-underscore notation) for readability.
3. **`requirements.txt` split?** → Two files: `requirements.txt` (runtime deps) + `requirements-dev.txt` (test/lint deps). Simple and explicit.
4. **pydantic v1 vs v2?** → pydantic v2 / pydantic-settings v2. The hyperliquid SDK may have pydantic as a transitive dep — check for conflicts on install.

---

## ## RESEARCH COMPLETE

Phase 1 research is complete. All technical decisions for planning are resolved:
- Package layout: `src/mgw_mm/` with `__main__.py` entry point
- Config: nested pydantic-settings with flat env vars
- Logging: structlog JSONRenderer, stdout only, INFO default
- Startup: ASCII banner → 3s mainnet pause → asyncio.run()
- Secrets: fail-fast via pydantic ValidationError, never logged
- Testing: pytest unit tests for config and module imports
- Files to create: ~15 files (package structure + config + logging + stubs + tests + env + docker-stub)
