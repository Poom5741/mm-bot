---
wave: 1
depends_on: []
files_modified:
  - pyproject.toml
  - requirements.txt
  - requirements-dev.txt
  - .gitignore
  - .env.example
  - src/mgw_mm/__init__.py
  - src/mgw_mm/exchange.py
  - src/mgw_mm/market_data.py
  - src/mgw_mm/quoting.py
  - src/mgw_mm/risk.py
  - src/mgw_mm/pnl.py
  - src/mgw_mm/telegram.py
  - src/mgw_mm/ai_guardrail.py
  - tests/__init__.py
autonomous: true
requirements_addressed:
  - FND-01
  - FND-03
---

# Plan A: Project Scaffolding

## Objective

Create the repository skeleton: Python package structure under `src/mgw_mm/`, project metadata (`pyproject.toml`), pinned dependency files, `.gitignore` (with `.env` excluded from the first commit), `.env.example` (documents all variables), and stub module files for all 8 non-entry-point components.

## Must Haves

<must_haves>
<truths>
- `.env` is listed in `.gitignore` before any secrets could be added — verified by `git check-ignore .env` returning `.env`
- `.env.example` documents every env variable with placeholder values and comments
- All stub modules (`exchange.py`, `market_data.py`, `quoting.py`, `risk.py`, `pnl.py`, `telegram.py`, `ai_guardrail.py`) can be imported without raising `ImportError` or `ModuleNotFoundError`
- `pyproject.toml` declares `[tool.setuptools.packages.find] where = ["src"]` so `python -m mgw_mm` resolves the package
- `requirements.txt` pins all 6 runtime deps; `requirements-dev.txt` pins pytest and related tools
- FND-01 addressed: service runs as Python 3.11+ with pinned deps and documented setup
- FND-03 addressed: `.env` gitignored, no secrets in code
</truths>
</must_haves>

## Tasks

### Task A1: Create pyproject.toml and package metadata

<read_first>
- `CLAUDE.md` — project conventions
- `.planning/phases/01-project-foundation-config/01-CONTEXT.md` — D-05, D-06 layout decisions
- `.planning/phases/01-project-foundation-config/01-RESEARCH.md` — pyproject.toml template
</read_first>

<action>
Create `pyproject.toml` at project root with:
- `[build-system]` requires `setuptools>=68`, backend `setuptools.backends.legacy:build`
- `[project]` name `mgw-mm`, version `0.1.0`, requires-python `>=3.11`, description "Hyperliquid MGW/USDC Volume Market-Maker Bot"
- `[tool.setuptools.packages.find]` where `["src"]` — this is mandatory for `python -m mgw_mm` to resolve correctly
- `[tool.pytest.ini_options]` testpaths `["tests"]`, asyncio_mode `"auto"`
</action>

<acceptance_criteria>
- `pyproject.toml` exists at project root
- File contains `[tool.setuptools.packages.find]` with `where = ["src"]`
- File contains `requires-python = ">=3.11"`
- `python -c "import tomllib; tomllib.loads(open('pyproject.toml').read())"` exits 0 (valid TOML)
</acceptance_criteria>

---

### Task A2: Create requirements.txt and requirements-dev.txt

<read_first>
- `.planning/research/STACK.md` — verified library choices
- `.planning/phases/01-project-foundation-config/01-RESEARCH.md` — dependency list with rationale
</read_first>

<action>
Create `requirements.txt` with runtime deps (one per line, with `>=` version pins):
- `hyperliquid-python-sdk>=0.9.0`
- `eth-account>=0.12.0`
- `pydantic>=2.0.0`
- `pydantic-settings>=2.0.0`
- `structlog>=24.0.0`
- `python-telegram-bot>=21.0.0`

Create `requirements-dev.txt` with:
- `-r requirements.txt`
- `pytest>=8.0.0`
- `pytest-asyncio>=0.23.0`
- `python-dotenv>=1.0.0`
</action>

<acceptance_criteria>
- `requirements.txt` exists with all 6 runtime deps listed
- `requirements-dev.txt` exists and starts with `-r requirements.txt`
- Both files have no blank lines between deps (clean format)
- Running `pip install -r requirements.txt --dry-run` (or equivalent) resolves without conflict errors
</acceptance_criteria>

---

### Task A3: Create .gitignore with .env excluded

<read_first>
- `.planning/phases/01-project-foundation-config/01-CONTEXT.md` — D-03 and Specific Ideas: `.env` must be in `.gitignore` from the first commit
</read_first>

<action>
Create `.gitignore` at project root. Must include these entries:
- `.env` — critical: secrets file
- `.env.local`
- `__pycache__/`
- `*.py[cod]`
- `*.egg-info/`
- `dist/`
- `build/`
- `.venv/`
- `venv/`
- `*.log`
- `.pytest_cache/`
- `.mypy_cache/`
- `*.sqlite`
- `*.db`
</action>

<acceptance_criteria>
- `.gitignore` exists at project root
- `.env` is listed in `.gitignore`
- `git check-ignore -v .env` outputs `.gitignore` as the matching file (run from project root after `git init` if not already a repo)
- `.env.example` is NOT in `.gitignore` (it must be committed)
</acceptance_criteria>

---

### Task A4: Create .env.example with all variables documented

<read_first>
- `.planning/phases/01-project-foundation-config/01-CONTEXT.md` — D-08, D-09 for all config field names and defaults
- `.planning/phases/01-project-foundation-config/01-RESEARCH.md` — `.env.example` template
</read_first>

<action>
Create `.env.example` at project root documenting every env variable. Include section comments and placeholder values:

Section: Network
- `NETWORK=testnet` (comment: `# testnet | mainnet`)

Section: Trading
- `TARGET_PAIR=PURR/USDC` (comment: `# Use PURR/USDC for testnet validation; flip to MGW/USDC when listed`)
- `ORDER_SIZE_USDC=10`
- `TICK_OFFSET=2`
- `QUOTE_INTERVAL_SEC=30`

Section: Risk Caps
- `MAX_INVENTORY_USDC=100`
- `MAX_CAPITAL_USDC=200`
- `MIN_SPREAD_TICKS=1`
- `MAX_SPREAD_TICKS=10`
- `KILL_SWITCH_VOL_THRESHOLD=0.05`

Section: Logging
- `LOG_LEVEL=INFO` (comment: `# DEBUG | INFO | WARNING | ERROR`)

Section: Secrets — with warning comment
- `AGENT_PRIVATE_KEY=0xYOUR_AGENT_PRIVATE_KEY_HERE`
- `TELEGRAM_BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN_HERE`
- `TELEGRAM_OWNER_CHAT_ID=YOUR_TELEGRAM_CHAT_ID_HERE`
</action>

<acceptance_criteria>
- `.env.example` exists at project root
- File contains all 13 variable names listed above
- Secrets section has a comment warning never to commit real values
- `AGENT_PRIVATE_KEY` has a placeholder (not a real key)
- `NETWORK` has a comment explaining valid values
</acceptance_criteria>

---

### Task A5: Create src/mgw_mm/ package directory and __init__.py

<read_first>
- `.planning/phases/01-project-foundation-config/01-CONTEXT.md` — D-05, D-06
</read_first>

<action>
Create directory structure:
- `src/mgw_mm/__init__.py` — contains only `__version__ = "0.1.0"` and a module docstring: `"""Hyperliquid MGW/USDC Volume Market-Maker Bot."""`
- `src/__init__.py` — do NOT create this; `src/` is not a package, only `src/mgw_mm/` is
- `tests/__init__.py` — empty file to make tests a package
</action>

<acceptance_criteria>
- `src/mgw_mm/__init__.py` exists and contains `__version__ = "0.1.0"`
- `tests/__init__.py` exists (can be empty)
- `python -c "import sys; sys.path.insert(0, 'src'); from mgw_mm import __version__; print(__version__)"` prints `0.1.0`
</acceptance_criteria>

---

### Task A6: Create stub modules for all 8 non-entry-point components

<read_first>
- `.planning/phases/01-project-foundation-config/01-CONTEXT.md` — D-07 module list, D-08 config slices
- `.planning/phases/01-project-foundation-config/01-PATTERNS.md` — module signature conventions
- `.planning/research/ARCHITECTURE.md` — component descriptions and data flow
</read_first>

<action>
Create the following stub files in `src/mgw_mm/`. Each stub must:
1. Have a module-level docstring describing the component's role
2. Import `structlog` and define `logger = structlog.get_logger(__name__)`
3. Define the main class with an `__init__` that accepts the appropriate config type (use `Any` type hint since config.py doesn't exist yet — will be replaced in Plan B)
4. Have a `# TODO: implement in Phase N` comment in the class body

Files to create:
- `src/mgw_mm/exchange.py` — class `HyperliquidClient`; role: Hyperliquid Info+Exchange wrapper
- `src/mgw_mm/market_data.py` — class `MarketData`; role: L2 book, mid price, volatility
- `src/mgw_mm/quoting.py` — class `QuotingEngine`; role: deterministic two-sided quote computation
- `src/mgw_mm/risk.py` — class `RiskManager`; role: order veto, inventory caps, kill-switch
- `src/mgw_mm/pnl.py` — class `PnLTracker`; role: inventory, realized/unrealized PnL, fees
- `src/mgw_mm/telegram.py` — class `TelegramBot`; role: command handlers and push alerts
- `src/mgw_mm/ai_guardrail.py` — class `AIGuardrail`; role: advisory spread/size/pause suggestions and reports

Each `__init__` should accept `config` as a keyword argument and store it as `self.config = config`.
</action>

<acceptance_criteria>
- All 7 stub files exist in `src/mgw_mm/`
- Each file imports `structlog` and defines `logger = structlog.get_logger(__name__)`
- Each file defines the named class with `__init__(self, config)` or `__init__(self, **kwargs)`
- `python -c "import sys; sys.path.insert(0,'src'); import mgw_mm.exchange, mgw_mm.market_data, mgw_mm.quoting, mgw_mm.risk, mgw_mm.pnl, mgw_mm.telegram, mgw_mm.ai_guardrail"` exits 0 with no ImportError
</acceptance_criteria>

---

## Verification

```bash
# Verify package structure
ls src/mgw_mm/
# Expected: __init__.py, __main__.py (from Plan B), config.py (from Plan B), exchange.py, market_data.py, quoting.py, risk.py, pnl.py, telegram.py, ai_guardrail.py, orchestrator.py

# Verify .gitignore covers .env
git check-ignore -v .env

# Verify all stubs import cleanly
python -c "
import sys; sys.path.insert(0, 'src')
import mgw_mm
import mgw_mm.exchange
import mgw_mm.market_data
import mgw_mm.quoting
import mgw_mm.risk
import mgw_mm.pnl
import mgw_mm.telegram
import mgw_mm.ai_guardrail
print('All stubs imported OK')
"
```

## ## PLANNING COMPLETE
