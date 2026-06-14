# Phase 2: Connectivity & API Agent Auth - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-14
**Phase:** 2-Connectivity & API Agent Auth
**Areas discussed:** Agent approval flow, Main wallet address sourcing, Auth failure detection

---

## Agent Approval Flow

### How agent key is created

| Option | Description | Selected |
|--------|-------------|----------|
| One-time setup script | scripts/approve_agent.py, owner runs manually, bot never sees main key | ✓ |
| Bot auto-approves on first run | Bot prompts for main wallet key, calls approve_agent(), writes to .env | |

**User's choice:** One-time setup script
**Notes:** Security preference — main wallet private key never passes through bot process.

### Setup script interaction style

| Option | Description | Selected |
|--------|-------------|----------|
| Interactive prompts | getpass for main key, agent name default mgw-bot, prints result | ✓ |
| Env-driven (.env.setup file) | Reads from separate secrets file, more scriptable | |

**User's choice:** Interactive prompts
**Notes:** Simpler, no extra secrets file to manage.

---

## Main Wallet Address Sourcing

### Where MAIN_WALLET_ADDRESS comes from

| Option | Description | Selected |
|--------|-------------|----------|
| MAIN_WALLET_ADDRESS env var | Plain public address (0x...) in .env, required | ✓ |
| Derive from agent key lookup | API call to get_agent_details() on startup | |

**User's choice:** MAIN_WALLET_ADDRESS env var
**Notes:** Simpler, no extra API call, public address not sensitive.

### Required vs optional

| Option | Description | Selected |
|--------|-------------|----------|
| Required (fail-fast) | Missing triggers startup exit(1) alongside AGENT_PRIVATE_KEY | ✓ |
| Optional with auto-derive fallback | Attempt API derivation if missing | |

**User's choice:** Required
**Notes:** No point starting without it — consistent with fail-fast pattern from Phase 1.

---

## Auth Failure Detection

### Startup auth probe

| Option | Description | Selected |
|--------|-------------|----------|
| Live API probe (spot_user_state) | Confirms connectivity + address reachable before quoting loop | ✓ |
| Trust key format only | Validate private key format, no live check | |

**User's choice:** Live API probe
**Notes:** Catches revoked/expired agents before quoting starts.

### Mid-run auth failure response

| Option | Description | Selected |
|--------|-------------|----------|
| Cancel all, log error, exit(1) | Safest — systemd/Docker restarts, fails fast until re-approved | ✓ |
| Pause and retry with backoff | Keep process alive, retry every N seconds | |

**User's choice:** Cancel all, log error, exit(1)
**Notes:** Relies on process supervisor for recovery, avoids confused state.

### Re-approval documentation location

| Option | Description | Selected |
|--------|-------------|----------|
| docs/runbook.md | Clear numbered procedure, seeds Phase 10 ops docs | ✓ |
| Inline in bot error output | Self-documenting but verbose in logs | |

**User's choice:** docs/runbook.md
**Notes:** Runbook started in Phase 2, completed in Phase 10.

---

## Claude's Discretion

- Exact SDK exception classes to catch for auth failure
- Whether startup probe does a signed noop or read-only spot_user_state only
- scripts/approve_agent.py UX details and output formatting
- Whether main_wallet_address goes in NetworkConfig or a new AuthConfig section

## Deferred Ideas

None — discussion stayed within phase scope.
