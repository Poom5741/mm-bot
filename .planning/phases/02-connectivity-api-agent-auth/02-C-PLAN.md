---
plan: 02-C
title: "Orchestrator Wiring, Auth Probe, Mid-Run Guard & Runbook"
wave: 2
depends_on:
  - 02-A
  - 02-B
phase: 2
requirements:
  - CON-01
  - CON-02
  - CON-03
files_modified:
  - src/mgw_mm/orchestrator.py
  - docs/runbook.md
autonomous: true
---

# Plan 02-C: Orchestrator Wiring, Auth Probe, Mid-Run Guard & Runbook

## Objective

Wire `HyperliquidClient` into `orchestrator.py`, add a startup auth probe that `exit(1)` on failure, add a mid-run auth-failure detection pattern (exception handler template for future order placement calls), and write the initial `docs/runbook.md` with the re-approval procedure (CON-03).

## Context

Plans 02-A and 02-B must be complete before this plan executes (Wave 2). After 02-A and 02-B:
- `Settings.main_wallet_address` exists (Plan 02-A)
- `HyperliquidClient(settings)` is fully implemented with `probe_auth()` (Plan 02-B)
- `orchestrator.py` still has `# TODO Phase 2: Initialize HyperliquidClient and authenticate agent wallet`

This plan makes that TODO real, adds the auth guard pattern, and documents the re-approval runbook.

## Tasks

---

### Task C-1: Wire `HyperliquidClient` into `orchestrator.py`

<read_first>
- `src/mgw_mm/orchestrator.py` — read the full file; understand the startup sequence and TODO comments
- `src/mgw_mm/exchange.py` — confirm `HyperliquidClient` signature (accepts `Settings`) and `probe_auth()` exists
- `src/mgw_mm/config.py` — confirm `Settings` has `main_wallet_address`
</read_first>

<action>
In `src/mgw_mm/orchestrator.py`, replace the `# TODO Phase 2` comment with the actual client construction and startup auth probe. The change is in the `run(settings: Settings)` async function.

After the existing `logger.info("orchestrator_starting", ...)` call, add:

```python
# Phase 2: Initialize HyperliquidClient and authenticate agent wallet
from mgw_mm.exchange import HyperliquidClient
from hyperliquid.utils.error import ClientError, ServerError

client = HyperliquidClient(settings)

# Startup auth probe — confirms connectivity before the quoting loop starts.
# Failure exits immediately; systemd/Docker restart policy handles recovery.
try:
    client.probe_auth()
except (ClientError, ServerError, Exception) as exc:
    logger.error(
        "startup_auth_probe_failed",
        error=str(exc),
        action="exiting — re-approve the agent using scripts/approve_agent.py",
    )
    sys.exit(1)
```

Add `import sys` at the top of `orchestrator.py` if not already present.

Keep all existing TODO comments for Phases 3–9 in place. Replace ONLY the Phase 2 TODO.

Update the `orchestrator_ready` log event at the bottom:
```python
logger.info(
    "orchestrator_ready",
    status="connected_to_exchange",
    network=settings.network_config.network,
    pair=settings.trading.target_pair,
)
```
(Remove the `note="No trading components initialized — Phase 1 skeleton only"` part.)
</action>

<acceptance_criteria>
- `src/mgw_mm/orchestrator.py` contains `client = HyperliquidClient(settings)`
- `probe_auth()` is called inside a try/except block
- The except block catches `ClientError`, `ServerError`, and `Exception`
- The except block calls `sys.exit(1)` after logging `startup_auth_probe_failed`
- `import sys` is present in `orchestrator.py`
- The `# TODO Phase 2` comment is removed; TODOs for Phases 3–9 remain
- `orchestrator_ready` log event no longer says `skeleton_mode`
- `python3 -m py_compile src/mgw_mm/orchestrator.py` exits 0
</acceptance_criteria>

---

### Task C-2: Add Mid-Run Auth-Failure Detection Pattern (Comment Template)

<read_first>
- `src/mgw_mm/orchestrator.py` — read the updated file from Task C-1
- `.planning/phases/02-connectivity-api-agent-auth/02-CONTEXT.md` — D-10: mid-run auth failure detected by catching SDK exceptions on order placement/cancellation; cancel all + exit(1)
- `.venv/lib/python3.11/site-packages/hyperliquid/utils/error.py` — `ClientError` and `ServerError` class definitions; `ClientError.error_message` contains the rejection reason as a string
</read_first>

<action>
In `orchestrator.py`, after the auth probe block and before the Phase 3 TODO, add a comment block that defines the auth-failure guard pattern for future order placement. This is a template/documentation comment, NOT executable code yet (the quoting loop is Phase 4).

```python
# Mid-run auth-failure guard pattern (implemented in Phase 4 quoting loop):
#
#   try:
#       result = client.exchange.order(...)
#   except ClientError as e:
#       if "agent" in e.error_message.lower() or "unauthorized" in e.error_message.lower():
#           logger.error("mid_run_auth_failure", error=e.error_message)
#           # Best-effort cancel all open orders before exit
#           # (cancel_all implemented in Phase 5)
#           sys.exit(1)
#       raise  # re-raise non-auth errors for the quoting loop to handle
#   except ServerError as e:
#       logger.error("exchange_server_error", status=e.status_code, message=e.message)
#       raise
```

This ensures Phase 4's executor knows the auth-failure detection contract before implementing the order loop.
</action>

<acceptance_criteria>
- `src/mgw_mm/orchestrator.py` contains the comment block with `mid_run_auth_failure` label
- The comment references `ClientError`, `e.error_message`, and `sys.exit(1)`
- No new executable code is introduced by this task — the comment is documentation only
- `python3 -m py_compile src/mgw_mm/orchestrator.py` exits 0
</acceptance_criteria>

---

### Task C-3: Write `docs/runbook.md` — Re-Approval Procedure

<read_first>
- `.planning/phases/02-connectivity-api-agent-auth/02-CONTEXT.md` — D-11 (recovery via restart policy), D-12 (runbook content: stop → re-approve → copy key → restart)
- `.planning/phases/02-connectivity-api-agent-auth/02-CONTEXT.md` — `<specifics>` section: startup auth probe log format
- `.env.example` — confirm env var names (`AGENT_PRIVATE_KEY`, `MAIN_WALLET_ADDRESS`)
</read_first>

<action>
Create `docs/runbook.md`. This is the seed runbook that Phase 10 will expand into a full ops guide.

Content structure:
```markdown
# MGW/USDC Market-Maker Bot — Operations Runbook

> Seed runbook created in Phase 2. Expanded to full ops guide in Phase 10.

## Agent Re-Approval Procedure

The bot uses a named Hyperliquid API Agent (`mgw-bot`) for all trading. Agents
can expire or become invalid after certain account operations. When the startup
auth probe fails with `startup_auth_probe_failed`, follow this procedure:

### Symptoms

- Bot exits at startup with `startup_auth_probe_failed` in the log
- Or bot exits mid-run with `mid_run_auth_failure` in the log
- Log event includes `action: "exiting — re-approve the agent using scripts/approve_agent.py"`

### Steps

1. **Stop the bot**
   ```
   docker compose stop   # Docker
   # OR
   sudo systemctl stop mgw-mm   # systemd
   ```

2. **Re-approve the agent**
   ```
   cd /path/to/mm-bot
   python3 scripts/approve_agent.py
   ```
   When prompted:
   - Network: `testnet` or `mainnet` (match your current deployment)
   - Agent name: `mgw-bot` (press Enter to accept default)
   - Main wallet private key: enter and press Enter (input is hidden)
   - Confirm: type `y`

3. **Copy the new credentials into `.env`**
   The script prints:
   ```
   AGENT_PRIVATE_KEY=0x...
   MAIN_WALLET_ADDRESS=0x...
   ```
   Update both values in your `.env` file. `MAIN_WALLET_ADDRESS` will be
   the same as before (it's the main wallet's public address, not a secret).
   Only `AGENT_PRIVATE_KEY` changes.

4. **Restart the bot**
   ```
   docker compose up -d   # Docker
   # OR
   sudo systemctl start mgw-mm   # systemd
   ```

5. **Verify startup**
   Check logs for `auth_probe_ok` within the first few seconds.
   ```
   docker compose logs -f   # Docker
   # OR
   sudo journalctl -u mgw-mm -f   # systemd
   ```

### Notes

- **Each network requires a separate agent**: testnet and mainnet agents are
  independent. Re-approve on the network where the failure occurred.
- **The agent cannot withdraw funds**: the agent key is trade-only by design.
  Even if the agent key is compromised, funds cannot be withdrawn without
  the main wallet's private key.
- **Named agents are persistent**: the agent named `mgw-bot` remains
  approved until explicitly revoked or a new agent with the same name is
  approved.

---

*Runbook seed: Phase 2. See Phase 10 for full deployment, VPS setup, and recovery procedures.*
```
</action>

<acceptance_criteria>
- `docs/runbook.md` exists
- File contains `## Agent Re-Approval Procedure` as a heading
- File contains `scripts/approve_agent.py` reference (step 2)
- File contains `AGENT_PRIVATE_KEY` and `MAIN_WALLET_ADDRESS` in step 3
- File contains `auth_probe_ok` (for verifying restart in step 5)
- File contains the note that the agent cannot withdraw funds
- `docs/` directory created if it did not exist
</acceptance_criteria>

---

### Task C-4: Integration Smoke Test — Full Startup Sequence (Mocked)

<read_first>
- `tests/test_smoke.py` — read the Phase 1 smoke test to understand the mocking pattern used for `asyncio.run` and `Settings`
- `src/mgw_mm/orchestrator.py` — read the updated orchestrator from Tasks C-1 and C-2
- `src/mgw_mm/exchange.py` — read `HyperliquidClient.__init__` and `probe_auth()` signatures
</read_first>

<action>
Add two integration smoke tests to `tests/test_smoke.py` (or create `tests/test_orchestrator.py` if the smoke test file is too specialized):

**test_orchestrator_calls_probe_auth_on_startup**:
- Mock `HyperliquidClient.__init__` to return None (no network)
- Mock `HyperliquidClient.probe_auth` to return None (success)
- Call `asyncio.run(orchestrator.run(mock_settings))`
- Assert `HyperliquidClient` was instantiated exactly once
- Assert `probe_auth()` was called exactly once

**test_orchestrator_exits_on_auth_probe_failure**:
- Mock `HyperliquidClient.__init__` to return None
- Mock `HyperliquidClient.probe_auth` to raise `ClientError(401, None, "agent not approved", {})`
- Assert that `asyncio.run(orchestrator.run(mock_settings))` raises `SystemExit` with code 1

Both tests must mock the SDK at the module level (patch `mgw_mm.orchestrator.HyperliquidClient`) so no real network calls are made.
</action>

<acceptance_criteria>
- `test_orchestrator_calls_probe_auth_on_startup` passes: `probe_auth()` is called once during `orchestrator.run()`
- `test_orchestrator_exits_on_auth_probe_failure` passes: `SystemExit(1)` is raised when `probe_auth()` raises `ClientError`
- `PYTHONPATH=src python -m pytest tests/ -q` exits 0 with all tests passing (Phases 1 + 2 combined)
- No real network calls in any test
</acceptance_criteria>

---

## Verification

```bash
# Syntax checks
python3 -m py_compile src/mgw_mm/orchestrator.py

# Docs dir
ls docs/runbook.md

# All tests pass
PYTHONPATH=src python -m pytest tests/ -q

# Full startup sanity (will fail at exchange connection — that's expected without real env)
# Just verify it reaches the HyperliquidClient init attempt, not a config error:
AGENT_PRIVATE_KEY=$(python3 -c "import secrets; print('0x'+secrets.token_hex(32))") \
  MAIN_WALLET_ADDRESS=0x000000000000000000000000000000000000dEaD \
  TELEGRAM_BOT_TOKEN=placeholder \
  TELEGRAM_OWNER_CHAT_ID=123 \
  PYTHONPATH=src timeout 5 python -m mgw_mm 2>&1 | grep -E "hyperliquid_client|auth_probe|startup" | head -10
```

## must_haves

```yaml
truths:
  - "orchestrator.py constructs HyperliquidClient(settings) before entering the quoting loop"
  - "orchestrator.py calls client.probe_auth() inside try/except that catches ClientError, ServerError, Exception"
  - "Probe failure logs startup_auth_probe_failed and calls sys.exit(1)"
  - "docs/runbook.md exists with the 5-step re-approval procedure"
  - "Mid-run auth failure comment template is present in orchestrator.py for Phase 4's reference"
  - "All tests pass: PYTHONPATH=src python -m pytest tests/ -q exits 0"
  - "No real network calls in any test"
```
