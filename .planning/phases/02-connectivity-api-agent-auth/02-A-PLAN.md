---
plan: 02-A
title: "Config Extension & Agent Approval Script"
wave: 1
depends_on: []
phase: 2
requirements:
  - CON-01
  - CON-02
files_modified:
  - src/mgw_mm/config.py
  - .env.example
  - scripts/approve_agent.py
autonomous: true
---

# Plan 02-A: Config Extension & Agent Approval Script

## Objective

Add `MAIN_WALLET_ADDRESS` to `Settings` (fail-fast if missing), and create `scripts/approve_agent.py` — the one-time interactive script that approves a named, persistent API Agent and prints both `AGENT_PRIVATE_KEY` and `MAIN_WALLET_ADDRESS` for the operator to copy into `.env`.

## Context

Phase 1 built `config.py` with `AGENT_PRIVATE_KEY` as a `SecretStr`. This plan adds the companion env var (`MAIN_WALLET_ADDRESS`) required by `Exchange(agent_wallet, URL, account_address=main_wallet_address)` (D-05 through D-08), and creates the one-time approval script (D-01 through D-04) that generates the agent key in the first place.

## Tasks

---

### Task A-1: Extend `config.py` — Add `main_wallet_address` Field

<read_first>
- `src/mgw_mm/config.py` — read the full file before editing; understand existing `Settings`, `NetworkConfig`, `model_validator`, and fail-fast pattern
- `.env.example` — see existing env var naming conventions
</read_first>

<action>
Add `main_wallet_address: str` as a required field to the `Settings` class in `src/mgw_mm/config.py`.

Placement: after `agent_private_key: SecretStr`, before the computed sub-models block.

Field definition:
```
main_wallet_address: str
```

No default — pydantic-settings will raise `ValidationError` if the env var `MAIN_WALLET_ADDRESS` is absent, triggering the existing `load_settings()` fail-fast path, which prints:
```
  [main_wallet_address]: Field required
```

Do NOT add `SecretStr` — address is not a secret; it appears in logs (truncated) and is the `account_address` argument for the Exchange constructor.

Do NOT add `main_wallet_address` to `NetworkConfig` — it belongs flat on `Settings` alongside `agent_private_key`.

Add a comment above the field:
```python
# --- Main wallet address (public 0x address, not a key) ---
```
</action>

<acceptance_criteria>
- `src/mgw_mm/config.py` contains `main_wallet_address: str` in the `Settings` class body
- The field has no default value (required, not Optional)
- Running `python -c "from mgw_mm.config import Settings; s = Settings()"` without `MAIN_WALLET_ADDRESS` set raises `ValidationError` and the `load_settings()` wrapper prints `[main_wallet_address]: Field required` to stderr and exits 1
- The field is a plain `str`, not `SecretStr`
- Existing tests pass: `PYTHONPATH=src python -m pytest tests/test_config.py -q` (tests that set `MAIN_WALLET_ADDRESS` now required — adjust in Task A-1b below)
</acceptance_criteria>

---

### Task A-1b: Update Tests for `main_wallet_address`

<read_first>
- `tests/test_config.py` — read entire file; understand all fixtures and env-var mocking patterns before editing
</read_first>

<action>
Every test that constructs `Settings` or calls `load_settings()` (directly or via fixtures) must now also supply `MAIN_WALLET_ADDRESS`. Add `MAIN_WALLET_ADDRESS=0x000000000000000000000000000000000000dEaD` (a recognizable placeholder) to the `monkeypatch.setenv` calls, or to the `os.environ` patches used by each test.

Do NOT change test logic — only add the missing env var to existing fixture/mock setups.
</action>

<acceptance_criteria>
- `PYTHONPATH=src python -m pytest tests/test_config.py -q` exits 0 with no failures
- The test for missing required secrets (`AGENT_PRIVATE_KEY` absent) still passes — `MAIN_WALLET_ADDRESS` present does not suppress that error
- Add one new test: when `MAIN_WALLET_ADDRESS` is absent from env (but all other required vars are set), `load_settings()` exits 1 and stderr contains `[main_wallet_address]: Field required`
</acceptance_criteria>

---

### Task A-2: Update `.env.example` — Add `MAIN_WALLET_ADDRESS`

<read_first>
- `.env.example` — read the full file to understand comment style and section ordering
</read_first>

<action>
Add `MAIN_WALLET_ADDRESS` to `.env.example` in the `# --- Secrets` section, immediately after the `AGENT_PRIVATE_KEY` line.

Add the following two lines:
```
MAIN_WALLET_ADDRESS=0xYOUR_MAIN_WALLET_ADDRESS_HERE
```

Add a comment above the line:
```
# The main wallet's PUBLIC address (0x...). Not a secret. Printed by scripts/approve_agent.py.
```

Do NOT add the actual address of any wallet.
</action>

<acceptance_criteria>
- `.env.example` contains `MAIN_WALLET_ADDRESS=0xYOUR_MAIN_WALLET_ADDRESS_HERE`
- The comment above the line reads: `# The main wallet's PUBLIC address (0x...). Not a secret. Printed by scripts/approve_agent.py.`
- The line appears in the `# --- Secrets` section, after `AGENT_PRIVATE_KEY`
</acceptance_criteria>

---

### Task A-3: Create `scripts/approve_agent.py` — One-Time Agent Approval Script

<read_first>
- `src/mgw_mm/config.py` — understand `NetworkConfig.api_url` property; do NOT import this module in the script (script is standalone)
- `.planning/research/STACK.md` — verified API facts section; the approve_agent call and Exchange constructor signature
- `.venv/lib/python3.11/site-packages/hyperliquid/exchange.py` — `approve_agent(name)` method (lines 635–657); it creates a new key internally and returns `(result, agent_key)`
- `.venv/lib/python3.11/site-packages/hyperliquid/utils/constants.py` — endpoint URLs
</read_first>

<action>
Create `scripts/approve_agent.py` as a standalone script (NOT importable by the bot). The script must:

1. **Network selection**: prompt `"Network? [testnet/mainnet] (default: testnet): "` with `input()`. Accept `testnet` or `mainnet`; default to `testnet` on empty Enter. Map to:
   - `testnet` → `https://api.hyperliquid-testnet.xyz`
   - `mainnet` → `https://api.hyperliquid.xyz`

2. **Agent name**: prompt `"Agent name (default: mgw-bot): "` via `input()`. Default to `mgw-bot`.

3. **Main wallet private key**: read via `getpass.getpass("Main wallet private key (hidden): ")`. Construct `main_wallet = Account.from_key(raw_key)` via `eth_account`.

4. **Confirmation prompt before submitting**:
   ```
   About to approve agent '{name}' on TESTNET/MAINNET for wallet {main_wallet.address[:6]}...{main_wallet.address[-4:]}
   Continue? [y/N]:
   ```
   Accept `y` or `Y` only. Any other input (including empty Enter) → print `"Aborted."` and `sys.exit(0)`.

5. **Approve agent**:
   ```python
   from hyperliquid.exchange import Exchange
   tmp_exchange = Exchange(main_wallet, base_url)
   result, agent_key = tmp_exchange.approve_agent(name=agent_name)
   ```

6. **On success**: print the output block clearly:
   ```
   ====================================================
    Agent approved successfully!
   ====================================================

   Copy these into your .env file:

   AGENT_PRIVATE_KEY={agent_key}
   MAIN_WALLET_ADDRESS={main_wallet.address}

   ====================================================
    KEEP AGENT_PRIVATE_KEY SECRET. Never commit to git.
   ====================================================
   ```

7. **On failure**: print `"Error approving agent: {result}"` and `sys.exit(1)`.

8. **Top of file**: add a shebang and a module docstring:
   ```python
   #!/usr/bin/env python3
   """One-time setup script: approve a named Hyperliquid API Agent.

   Run this ONCE per network (testnet and mainnet use separate agents).
   The script prints AGENT_PRIVATE_KEY and MAIN_WALLET_ADDRESS to copy into .env.

   This script is standalone — never imported by the bot.
   """
   ```

9. **No .env reading** — the script takes all input interactively. No pydantic-settings, no dotenv.

10. **Guard**: `if __name__ == "__main__": main()` at the end.
</action>

<acceptance_criteria>
- File `scripts/approve_agent.py` exists and is executable (`chmod +x` not required, but file must have valid Python syntax)
- Running `python3 scripts/approve_agent.py --help` does NOT crash (the script uses `if __name__ == "__main__"` guard)
- Running `python3 -c "import scripts.approve_agent"` raises `ImportError` or does not trigger `main()` (standalone guard works — or it simply won't be on the module path, which is fine)
- The script does NOT import from `mgw_mm.*` — it is fully standalone
- `getpass.getpass` is used for the private key prompt (verified by reading the source: `import getpass` present, `getpass.getpass(` present)
- The confirmation prompt includes the truncated wallet address pattern `{addr[:6]}...{addr[-4:]}`
- The printed output block contains `AGENT_PRIVATE_KEY=` and `MAIN_WALLET_ADDRESS=` on separate lines
- `python3 -m py_compile scripts/approve_agent.py` exits 0 (syntax check)
</acceptance_criteria>

---

### Task A-4: Create `scripts/` Directory with README

<read_first>
- `scripts/` — check if directory already exists (`ls scripts/ 2>/dev/null || echo "absent"`)
</read_first>

<action>
Create `scripts/` directory if not already present.

Create `scripts/README.md` (3–5 lines) explaining:
- `approve_agent.py` — one-time setup; run once per network before starting the bot
- Never import any script here from the main bot package
</action>

<acceptance_criteria>
- `scripts/` directory exists
- `scripts/approve_agent.py` exists (created in Task A-3)
- `scripts/README.md` exists and contains `approve_agent.py` in its text
</acceptance_criteria>

---

## Verification

```bash
# Syntax check all modified/created files
python3 -m py_compile src/mgw_mm/config.py
python3 -m py_compile scripts/approve_agent.py

# Config tests pass (includes new MAIN_WALLET_ADDRESS tests)
PYTHONPATH=src python -m pytest tests/test_config.py -q

# Spot check: MAIN_WALLET_ADDRESS required
PYTHONPATH=src python -c "
import os, sys
# remove MAIN_WALLET_ADDRESS if set
os.environ.pop('MAIN_WALLET_ADDRESS', None)
os.environ['AGENT_PRIVATE_KEY'] = '0x' + 'aa' * 32
os.environ['TELEGRAM_BOT_TOKEN'] = 'x'
os.environ['TELEGRAM_OWNER_CHAT_ID'] = '123'
from mgw_mm.config import load_settings
load_settings()  # should exit 1
" && echo "FAIL: should have exited" || echo "PASS: exited 1 as expected"

# env.example has the new var
grep -q 'MAIN_WALLET_ADDRESS' .env.example && echo "PASS: .env.example updated" || echo "FAIL"
```

## must_haves

```yaml
truths:
  - "Settings.main_wallet_address is a required str field (no default, no SecretStr)"
  - "scripts/approve_agent.py uses getpass for the main wallet private key"
  - "scripts/approve_agent.py calls approve_agent(name=agent_name) — named, persistent agent (D-02)"
  - "scripts/approve_agent.py prints both AGENT_PRIVATE_KEY and MAIN_WALLET_ADDRESS for copying"
  - "scripts/approve_agent.py has confirmation prompt before submitting (D-02 specifics)"
  - "scripts/approve_agent.py does NOT import from mgw_mm.* (D-04 — standalone)"
  - ".env.example documents MAIN_WALLET_ADDRESS"
  - "All existing config tests still pass"
```
