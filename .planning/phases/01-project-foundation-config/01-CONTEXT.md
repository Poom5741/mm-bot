# Phase 1: Project Foundation & Config - Context

**Gathered:** 2026-06-14
**Status:** Ready for planning

<domain>
## Phase Boundary

Set up the service chassis — the runnable Python skeleton that every subsequent phase builds on. No trading logic. Deliverables: project directory structure, typed config loading from `.env`, safe secret handling (fail-fast on missing secrets), testnet/mainnet network switch, structured logging wired up, startup banner. The service must start cleanly and be documented for setup.

</domain>

<decisions>
## Implementation Decisions

### Logging
- **D-01:** Use **structlog** as the logging library (not loguru).
- **D-02:** Output format is **JSON always** — no human-readable mode, even in development. Consistent across environments.
- **D-03:** Default log level is **INFO**. Configurable via `LOG_LEVEL` env var.
- **D-04:** Log destination is **stdout only** (12-factor). Container/systemd captures and rotates. No file writing in application code.

### Project Layout
- **D-05:** Use **`src/` package layout** — all bot code lives in `src/mgw_mm/`.
- **D-06:** Package name is `mgw_mm` (run as `python -m mgw_mm` or via a `main.py` shim at root).
- **D-07:** Modules organized **by component role**, one module per architectural component:
  - `config.py` — pydantic-settings config models
  - `exchange.py` — Hyperliquid client wrapper
  - `market_data.py` — L2 book, mid, volatility
  - `quoting.py` — pure quoting engine
  - `risk.py` — Risk Manager
  - `pnl.py` — Inventory & PnL tracker
  - `telegram.py` — Telegram control bot
  - `ai_guardrail.py` — AI advisory layer
  - `orchestrator.py` — asyncio loop, ties everything together

### Config Model Design
- **D-08:** Config uses **nested pydantic-settings sections** (not one flat class):
  - `NetworkConfig` — NETWORK, API URLs
  - `TradingConfig` — TARGET_PAIR, ORDER_SIZE_USDC, TICK_OFFSET, QUOTE_INTERVAL_SEC
  - `RiskConfig` — MAX_INVENTORY_USDC, MAX_CAPITAL_USDC, MIN_SPREAD_TICKS, MAX_SPREAD_TICKS, KILL_SWITCH_VOL_THRESHOLD
  - `TelegramConfig` — BOT_TOKEN, OWNER_CHAT_ID
  - Top-level `Settings` composes all sections. Each component receives its config slice.
- **D-09:** **Conservative safe defaults** baked into the model:
  - `ORDER_SIZE_USDC = 10`
  - `TICK_OFFSET = 2`
  - `MAX_INVENTORY_USDC = 100`
  - `MAX_CAPITAL_USDC = 200`
  - `QUOTE_INTERVAL_SEC = 30`
- **D-10:** **Fail-fast on missing/invalid secrets** — startup validates all required fields, lists every missing/invalid field, then exits with code 1. No partial starts.
- **D-11:** The `AGENT_PRIVATE_KEY` (and `BOT_TOKEN`) are the only secrets required at runtime. Both are required — missing either triggers fail-fast.

### Startup Output
- **D-12:** On clean startup: print an **ASCII banner** followed by a config summary. Then begin structured JSON logs.
- **D-13:** Config summary shows: network + target pair, order size + tick offset, risk caps (MAX_INVENTORY_USDC, MAX_CAPITAL_USDC). Agent wallet address is NOT shown in the banner (security — don't leak address in screenshots).
- **D-14:** When `NETWORK=mainnet`: display a **prominent WARNING block** (all-caps, visually distinct) and pause for **3 seconds** before continuing. Makes accidental mainnet runs impossible to miss.
- **D-15:** When `NETWORK=testnet`: normal banner, no pause.

### Claude's Discretion
- Exact ASCII banner style (single or double border, content layout) — keep it simple and readable.
- Whether to use a `__main__.py` inside `src/mgw_mm/` or a separate `main.py` at root — pick whichever is cleaner for `python -m mgw_mm`.
- `.env.example` content and format.
- Whether `requirements.txt` is flat or split (base + dev).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Context
- `.planning/PROJECT.md` — project vision, constraints, security model, key decisions
- `.planning/REQUIREMENTS.md` — FND-01 through FND-05 (the requirements this phase implements)
- `.planning/ROADMAP.md` — Phase 1 success criteria and dependency chain

### Stack & Architecture
- `.planning/research/STACK.md` — verified API facts, library choices, "Do NOT use" list
- `.planning/research/ARCHITECTURE.md` — component diagram and build order; module names from D-07 must align with this
- `.planning/research/PITFALLS.md` — top pitfalls relevant to Phase 1: secrets (#8), testnet/mainnet mix-up (#9)

### No external specs
No external ADRs or third-party specs beyond the above. All requirements are fully captured in this file and REQUIREMENTS.md.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- None — fresh project, no existing code.

### Established Patterns
- None yet — this phase establishes the patterns that all subsequent phases follow.

### Integration Points
- `src/mgw_mm/orchestrator.py` will be the entry point that imports all other modules. Design each module so it can be imported cleanly by the orchestrator.
- `src/mgw_mm/config.py` exports `Settings` — every other module imports its config slice from here (not from the full Settings object).

</code_context>

<specifics>
## Specific Ideas

- The startup banner should clearly show "TESTNET" or "MAINNET" as the first prominent item — before anything else. It's the most safety-critical piece of information at startup.
- The 3-second mainnet pause is intentional UX friction, not a bug.
- `.env` must be in `.gitignore` from the first commit. `.env.example` should document every variable with placeholder values and comments.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 1-Project Foundation & Config*
*Context gathered: 2026-06-14*
