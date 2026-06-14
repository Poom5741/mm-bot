---
wave: 2
depends_on:
  - 01-PLAN-A-scaffold
  - 01-PLAN-B-config
files_modified:
  - src/mgw_mm/__main__.py
  - src/mgw_mm/orchestrator.py
  - src/mgw_mm/logging_setup.py
  - tests/test_logging.py
  - tests/test_smoke.py
autonomous: true
requirements_addressed:
  - FND-04
  - FND-05
---

# Plan C: Logging Setup, Startup Banner & Entry Point

## Objective

Wire up structlog JSON logging (D-01 through D-04), implement the startup ASCII banner with the mainnet warning block and 3-second pause (D-12 through D-15), create the asyncio orchestrator skeleton, and create the `__main__.py` entry point that loads config, initializes logging, shows the banner, and runs the orchestrator. Add smoke tests confirming the service starts cleanly.

## Must Haves

<must_haves>
<truths>
- `python -m mgw_mm` (with required env vars set) starts cleanly and prints the ASCII banner then exits 0 (not hangs)
- The startup banner shows "TESTNET" or "MAINNET" as the first prominent item (D-12, D-15)
- Banner config summary shows: network + target pair, order size + tick offset, MAX_INVENTORY_USDC, MAX_CAPITAL_USDC — and does NOT show agent wallet address (D-13)
- When `NETWORK=mainnet`, a WARNING block (visually distinct, all-caps) is printed and a 3-second pause occurs before the asyncio loop starts (D-14)
- When `NETWORK=testnet`, no pause occurs (D-15)
- All structlog output is valid JSON (parseable with `json.loads()`)
- Log level is controlled by `LOG_LEVEL` env var (default INFO); `LOG_LEVEL=DEBUG` increases verbosity (D-03)
- The agent wallet address does NOT appear in any log line or banner output (D-13)
- FND-04 addressed: `NETWORK` switch selects endpoints and logs the active network prominently
- FND-05 addressed: structlog writes a structured JSON log line for every significant event
</truths>
</must_haves>

## Tasks

### Task C1: Implement logging_setup.py

<read_first>
- `.planning/phases/01-project-foundation-config/01-CONTEXT.md` — D-01 through D-04 logging decisions
- `.planning/phases/01-project-foundation-config/01-RESEARCH.md` — structlog configuration template
</read_first>

<action>
Create `src/mgw_mm/logging_setup.py` with a single public function `configure_logging(log_level: str = "INFO") -> None`.

The function must:
1. Parse `log_level` using `logging.getLevelName(log_level.upper())` and validate it is an integer (not the string `"Level <N>"` which indicates an invalid level)
2. Configure stdlib `logging` root logger to the specified level (so third-party libs use the same level)
3. Call `structlog.configure()` with these processors (in order):
   - `structlog.contextvars.merge_contextvars` — merges bound context vars
   - `structlog.stdlib.add_log_level` — adds `level` key
   - `structlog.stdlib.add_logger_name` — adds `logger` key
   - `structlog.processors.TimeStamper(fmt="iso", utc=True)` — adds ISO 8601 UTC `timestamp` key
   - `structlog.processors.StackInfoRenderer()` — renders stack info if present
   - `structlog.processors.format_exc_info` — formats exception info
   - `structlog.processors.JSONRenderer()` — final: emits JSON to stdout
4. Set `wrapper_class=structlog.make_filtering_bound_logger(log_level_int)`
5. Set `logger_factory=structlog.PrintLoggerFactory()` — stdout only, no file
6. Set `cache_logger_on_first_use=True` for performance

The function should be idempotent (safe to call twice).
</action>

<acceptance_criteria>
- `src/mgw_mm/logging_setup.py` exists with `configure_logging()` function
- After calling `configure_logging("INFO")`, `structlog.get_logger("test").info("hello", x=1)` emits a string parseable by `json.loads()` containing keys `level`, `logger`, `timestamp`, `event`
- After calling `configure_logging("DEBUG")`, DEBUG-level messages appear; after `configure_logging("WARNING")`, INFO messages are suppressed
- `configure_logging("INVALID_LEVEL")` raises `ValueError` with a descriptive message
</acceptance_criteria>

---

### Task C2: Implement startup banner function

<read_first>
- `.planning/phases/01-project-foundation-config/01-CONTEXT.md` — D-12 through D-15, Specific Ideas
- `.planning/phases/01-project-foundation-config/01-RESEARCH.md` — banner design notes
- `src/mgw_mm/config.py` — `Settings` model (read to understand config fields available at banner time)
</read_first>

<action>
Add `print_banner(settings: Settings) -> None` function to `src/mgw_mm/__main__.py` (or a `startup.py` helper module imported by `__main__.py`).

The function must:
1. Print an ASCII banner to stdout (NOT via structlog — this is human-readable)
2. First line of content: `NETWORK: TESTNET` or `NETWORK: MAINNET` in all caps — the most prominent item
3. Also show: target pair, order size (USDC), tick offset, risk caps (MAX_INVENTORY_USDC, MAX_CAPITAL_USDC)
4. Do NOT show: agent wallet address, private key, Telegram token
5. If `settings.network_config.network == "mainnet"`:
   - Print a WARNING block BEFORE the banner — visually distinct (e.g., `!!! WARNING: MAINNET MODE — REAL FUNDS AT RISK !!!`), all-caps, surrounded by `!` or `*` characters
   - Call `time.sleep(3)` BEFORE `asyncio.run()` is called (after the banner print, before the loop)
6. If testnet: print banner normally, no pause

Banner example structure (exact style at Claude's discretion — simple and readable):
```
╔══════════════════════════════════════╗
║  MGW/USDC Market-Maker Bot v0.1.0   ║
╠══════════════════════════════════════╣
║  NETWORK:     TESTNET               ║
║  PAIR:        PURR/USDC             ║
║  ORDER SIZE:  10.00 USDC            ║
║  TICK OFFSET: 2                     ║
║  MAX INV:     100.00 USDC           ║
║  MAX CAPITAL: 200.00 USDC           ║
╚══════════════════════════════════════╝
```
</action>

<acceptance_criteria>
- `print_banner()` prints to stdout (not stderr)
- Output contains the string `TESTNET` or `MAINNET` (all caps) as the network indicator
- Output contains `ORDER SIZE` or equivalent label and the configured value
- Output contains `MAX` inventory and capital values
- Output does NOT contain any substring matching `0x[0-9a-fA-F]{64}` (private key pattern)
- When `network == "mainnet"`, output contains `WARNING` in the banner/pre-banner block
- `time.sleep(3)` is called when network is mainnet (testable by mocking `time.sleep`)
</acceptance_criteria>

---

### Task C3: Implement orchestrator.py skeleton

<read_first>
- `.planning/phases/01-project-foundation-config/01-CONTEXT.md` — Phase Boundary, integration points
- `.planning/research/ARCHITECTURE.md` — Orchestrator role: asyncio loop, ties everything together
- `src/mgw_mm/config.py` — `Settings` type
</read_first>

<action>
Create/update `src/mgw_mm/orchestrator.py` with:

```python
async def run(settings: Settings) -> None:
    """Main asyncio event loop. Ties all components together."""
    logger = structlog.get_logger(__name__)
    logger.info("orchestrator_starting", network=settings.network_config.network, pair=settings.trading.target_pair)
    
    # TODO Phase 2: Initialize HyperliquidClient and authenticate
    # TODO Phase 3: Initialize MarketData
    # TODO Phase 4: Initialize QuotingEngine
    # TODO Phase 6: Initialize PnLTracker
    # TODO Phase 7: Initialize RiskManager
    # TODO Phase 8: Initialize TelegramBot
    # TODO Phase 9: Initialize AIGuardrail
    
    logger.info("orchestrator_ready", status="skeleton_mode")
    # Placeholder: just log and exit cleanly for Phase 1
```

The function must use `structlog.get_logger(__name__)` and emit at least one `logger.info()` event showing `network` and `pair`. This proves FND-05 (structured logging of significant events).
</action>

<acceptance_criteria>
- `src/mgw_mm/orchestrator.py` exists with `async def run(settings: Settings) -> None`
- Function imports `structlog` and calls `structlog.get_logger(__name__)`
- Function emits at least one `logger.info()` call with `event="orchestrator_starting"` (or equivalent) containing `network` and `pair` keys
- Function completes and returns without error when called with a valid `Settings` object
</acceptance_criteria>

---

### Task C4: Implement __main__.py entry point

<read_first>
- `.planning/phases/01-project-foundation-config/01-CONTEXT.md` — D-06, D-12
- `src/mgw_mm/config.py` — `load_settings()` function
- `src/mgw_mm/logging_setup.py` — `configure_logging()` function
- `src/mgw_mm/orchestrator.py` — `run()` function
</read_first>

<action>
Create `src/mgw_mm/__main__.py` with the following sequence:

```python
import asyncio
import sys
import time

def main():
    # 1. Load config (fail-fast if missing secrets — exits before any logging)
    from mgw_mm.config import load_settings
    settings = load_settings()
    
    # 2. Configure logging (after config so log_level is available)
    from mgw_mm.logging_setup import configure_logging
    configure_logging(settings.log_level)
    
    # 3. Print startup banner (human-readable, to stdout, before JSON logs begin)
    print_banner(settings)
    
    # 4. Mainnet pause (3 seconds) — before asyncio loop
    if settings.network_config.network == "mainnet":
        time.sleep(3)
    
    # 5. Run async orchestrator
    from mgw_mm.orchestrator import run
    asyncio.run(run(settings))

if __name__ == "__main__":
    main()
```

Also define `print_banner(settings)` in this file (or import from a `startup.py` module if cleaner). The ordering is critical:
- Config load FIRST (before any import that might initialize a logger)
- Logging configure SECOND (before any structlog calls)
- Banner THIRD (human-readable, then switches to JSON)
- Asyncio loop LAST
</action>

<acceptance_criteria>
- `src/mgw_mm/__main__.py` exists
- `python -m mgw_mm --help` or just `python -m mgw_mm` (with required env vars set) runs without `ImportError` or `ModuleNotFoundError`
- With `NETWORK=testnet`, `AGENT_PRIVATE_KEY=<test key>`, `TELEGRAM_BOT_TOKEN=test:token`, `TELEGRAM_OWNER_CHAT_ID=123`: service starts, prints banner, logs one JSON line, and exits cleanly
- The first output line contains `TESTNET` (network indicator)
- No private key or wallet address appears in stdout or stderr
</acceptance_criteria>

---

### Task C5: Write logging and smoke tests

<read_first>
- `src/mgw_mm/logging_setup.py`
- `src/mgw_mm/__main__.py`
- `.planning/phases/01-project-foundation-config/01-RESEARCH.md` — Nyquist test coverage requirements
</read_first>

<action>
Create `tests/test_logging.py`:
1. `test_json_output` — call `configure_logging("INFO")`, capture stdout, emit one log line, parse with `json.loads()`, assert `event` and `level` keys present
2. `test_log_level_filtering` — configure at WARNING, emit INFO, assert no output
3. `test_invalid_log_level` — assert `configure_logging("GARBAGE")` raises `ValueError`

Create `tests/test_smoke.py`:
1. `test_all_modules_import` — assert all 9 `src/mgw_mm/*.py` modules import without error
2. `test_orchestrator_runs` — with env vars set, call `asyncio.run(run(settings))` and assert it completes without exception
3. `test_banner_no_private_key` — call `print_banner(settings)`, capture stdout, assert no private key hex pattern appears
4. `test_banner_contains_network` — assert output contains `TESTNET` or `MAINNET`
5. `test_mainnet_pause` — mock `time.sleep`, set `NETWORK=mainnet`, call entry point banner logic, assert `time.sleep(3)` was called once
</action>

<acceptance_criteria>
- `tests/test_logging.py` and `tests/test_smoke.py` exist with the listed test functions
- `pytest tests/ -v` exits 0 (all tests pass)
- `test_json_output` uses `capsys` or `StringIO` capture — no hardcoded output comparison
- `test_all_modules_import` dynamically discovers all `.py` files in `src/mgw_mm/` and imports each
</acceptance_criteria>

---

## Verification

```bash
# Run the full test suite
pytest tests/ -v

# End-to-end smoke: start the service
export AGENT_PRIVATE_KEY="0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
export TELEGRAM_BOT_TOKEN="test:token"
export TELEGRAM_OWNER_CHAT_ID="123"
export NETWORK="testnet"
PYTHONPATH=src python -m mgw_mm

# Verify JSON log output is parseable
PYTHONPATH=src python -m mgw_mm 2>&1 | grep '^{' | python -c "
import sys, json
for line in sys.stdin:
    line = line.strip()
    if line.startswith('{'):
        d = json.loads(line)
        assert 'event' in d or 'level' in d, f'Missing keys in: {d}'
        print('JSON log verified:', list(d.keys()))
"

# Verify .env excluded from git
git check-ignore -v .env

# Verify no private key in output
PYTHONPATH=src python -m mgw_mm 2>&1 | grep -c "ac0974" && echo "FAIL: private key leaked" || echo "PASS: no key in output"
```

## ## PLANNING COMPLETE
