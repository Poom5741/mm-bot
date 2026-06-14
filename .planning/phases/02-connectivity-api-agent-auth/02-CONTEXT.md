# Phase 2: Connectivity & API Agent Auth - Context

**Gathered:** 2026-06-14
**Status:** Ready for planning

<domain>
## Phase Boundary

Wire up the actual Hyperliquid connection using the official Python SDK (`Info` + `Exchange` objects), implement API Agent authentication via a dedicated bot wallet, and prove the agent can authenticate and place/cancel a test order on testnet. Includes a one-time agent approval setup script and a startup auth probe. No quoting logic — just "can we talk to the exchange and sign an order?"

</domain>

<decisions>
## Implementation Decisions

### Agent Approval Flow
- **D-01:** Agent key is created by a **one-time setup script** (`scripts/approve_agent.py`) that the owner runs manually. The bot itself never handles the main wallet private key.
- **D-02:** The setup script uses **interactive prompts** — asks for main wallet private key (hidden `getpass` input), agent name (default: `mgw-bot`), and target network. It calls `approve_agent(name=...)` and prints the generated agent private key + main wallet address to copy into `.env`.
- **D-03:** The setup script runs on **whichever network the user specifies** (testnet default). Approve once per network (testnet agent ≠ mainnet agent).
- **D-04:** The setup script is in `scripts/approve_agent.py` — separate from the main bot, never imported by the quoting loop.

### Main Wallet Address Sourcing
- **D-05:** `MAIN_WALLET_ADDRESS` is a **required env var** containing the main wallet's public address (`0x...`). Never a private key.
- **D-06:** The setup script prints `MAIN_WALLET_ADDRESS` alongside `AGENT_PRIVATE_KEY` so the owner can copy both into `.env` in one step.
- **D-07:** Missing `MAIN_WALLET_ADDRESS` triggers **fail-fast** at startup alongside `AGENT_PRIVATE_KEY`. Neither can be absent.
- **D-08:** `config.py` must be updated (from Phase 1) to add `main_wallet_address: str` to `NetworkConfig` (or a new `AuthConfig` section). It is a plain `str` — not a secret, just an address.

### Auth Failure Detection
- **D-09:** On startup, the bot performs a **connectivity + auth probe** before entering the quoting loop:
  1. Call `info.spot_user_state(main_wallet_address)` — confirms connectivity and that the address is reachable.
  2. Optionally attempt a minimal signed noop or verify the agent address appears in the account's approved agents list.
  3. Log the probe result at INFO level. Failure → structured error + `exit(1)`.
- **D-10:** During the quoting loop, auth failure is detected by catching **SDK exceptions on order placement/cancellation** (specific exception classes to be identified by the researcher from the SDK source). On detection: cancel all open orders (best-effort), emit a structured `auth_failure` log event, then `exit(1)`.
- **D-11:** Systemd/Docker `restart: unless-stopped` policy handles recovery — the bot restarts, hits the startup probe, fails fast again until the owner re-approves the agent.
- **D-12:** Re-approval procedure is **documented in a `docs/runbook.md`** file written in this phase. Content: stop bot → run `scripts/approve_agent.py` → copy new key to `.env` → restart bot. This runbook is the seed for Phase 10's full ops docs.

### HyperliquidClient structure
- **D-13:** `HyperliquidClient` owns **both** `info: Info` and `exchange: Exchange` — single class, single point of entry for all exchange operations.
- **D-14:** `HyperliquidClient.__init__` accepts the full `Settings` (or just the relevant config slices) and builds `Info` + `Exchange` internally. Callers get one object back.
- **D-15:** The `exchange` object is constructed as: `Exchange(agent_wallet, api_url, account_address=main_wallet_address)` where `agent_wallet = Account.from_key(settings.agent_private_key.get_secret_value())`.

### Claude's Discretion
- Exact exception classes to catch for auth failure (researcher should check SDK source).
- Whether the startup probe does a noop signed call or only the `spot_user_state` read (read-only is safer).
- `scripts/approve_agent.py` UX details (confirmation prompt before submitting, output formatting).
- Whether `main_wallet_address` goes in `NetworkConfig` or a new `AuthConfig` section in `config.py`.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Context
- `.planning/PROJECT.md` — security model, constraints (agent cannot withdraw)
- `.planning/REQUIREMENTS.md` — CON-01, CON-02, CON-03 (the requirements this phase implements)
- `.planning/ROADMAP.md` — Phase 2 success criteria

### Phase 1 Output (what this phase builds on)
- `src/mgw_mm/config.py` — existing `NetworkConfig`, `Settings`, `load_settings()` with fail-fast; Phase 2 must extend `config.py` to add `main_wallet_address`
- `src/mgw_mm/exchange.py` — existing `HyperliquidClient` stub to implement
- `.env.example` — existing documented env vars; Phase 2 adds `MAIN_WALLET_ADDRESS`

### Stack & API Reference
- `.planning/research/STACK.md` — verified API facts: `Exchange(agent_wallet, URL, account_address=main.address)`, `approve_agent(name=...)`, `Info`/`Exchange` constructor patterns
- `.planning/research/PITFALLS.md` — Pitfall #8 (secret leakage), #7 (agent auth expiry), #9 (testnet/mainnet mix-up)
- `.planning/research/ARCHITECTURE.md` — component diagram (HyperliquidClient is the exchange interface for all other components)

### No external specs beyond the above
All auth patterns are fully captured here and in STACK.md verified API facts.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/mgw_mm/config.py`: `load_settings()`, `NetworkConfig.api_url`, `Settings.agent_wallet` (already builds `Account.from_key`) — directly usable in `HyperliquidClient.__init__`
- `src/mgw_mm/logging_setup.py`: `configure_logging()` — call before any auth probe in `__main__.py` (already done by Phase 1)
- `src/mgw_mm/exchange.py`: `HyperliquidClient` stub with correct class name and docstring — implement in-place

### Established Patterns (from Phase 1)
- Structured logging: `logger = structlog.get_logger(__name__)` in every module
- Fail-fast pattern: validate → list errors → `sys.exit(1)` (see `load_settings()`)
- `SecretStr.get_secret_value()` to access raw key value

### Integration Points
- `__main__.py` calls `HyperliquidClient(settings)` after config + logging are set up. Phase 2 makes this call real (not a stub).
- `orchestrator.py` will later hold a reference to the client — but Phase 2 only needs to prove auth works in `__main__.py` or a test.

</code_context>

<specifics>
## Specific Ideas

- The setup script (`scripts/approve_agent.py`) should clearly warn before submitting: "This will approve a new API agent on TESTNET — continue? [y/N]". Prevents accidents.
- `docs/runbook.md` should be started in this phase even if brief — it becomes the ops runbook in Phase 10.
- The startup auth probe log line should include: network, main_wallet_address (truncated: first 6 + last 4 chars), agent_address (same truncation), probe status. This is the one place addresses appear in logs — truncation prevents full address leakage.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 2-Connectivity & API Agent Auth*
*Context gathered: 2026-06-14*
