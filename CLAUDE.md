<!-- GSD:project-start source:PROJECT.md -->

## Project

**Hyperliquid MWG/USDC Volume Market-Maker Bot**

An AI-assisted market-making bot that continuously places two-sided limit (maker) orders on the Hyperliquid **spot** pair **MWG/USDC** to generate trading volume and support the market health of MWG (the owner's own project token). It runs as a long-running service on a VPS, is controlled via a Telegram bot, and uses a deterministic rule-based quoting core with an AI guardrail layer for volatility adaptation, auto-pausing, and reporting.

**Core Value:** The bot keeps a healthy, continuously-quoted two-sided market on MWG/USDC (real maker orders that generate genuine volume) **without blowing up inventory or capital** — volume with disciplined risk control is the one thing that must work.

### Constraints

- **Tech stack**: Python — Hyperliquid has an official, well-documented Python SDK; AI/LLM and Telegram libraries are mature in Python.
- **Market**: Hyperliquid spot, pair MWG/USDC — set by the owner; tick/lot sizes are dictated by the exchange and must be fetched at runtime.
- **Security**: Dedicated bot wallet + API Agent delegation; secrets only via env vars / secret store — non-negotiable to protect funds.
- **Rate limits**: Hyperliquid enforces API rate limits — quoting loop must throttle (sleep / backoff) to avoid bans.
- **Environment**: Testnet-first for validation; MWG likely exists only on mainnet, so loop logic is proven on testnet then pointed at mainnet MWG/USDC.
- **Deployment**: VPS, long-running resilient process with logging and auto-restart.
- **Risk**: Spot inventory (no liquidation) but real price exposure — hard inventory and capital caps plus a kill-switch are required.

<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->

## Technology Stack

## Recommended Stack

| Concern | Choice | Why | Confidence |
|---|---|---|---|
| Language | **Python 3.11+** | Official Hyperliquid SDK; mature async, Telegram, AI libs | High |
| Exchange SDK | **hyperliquid-python-sdk** (`Info`, `Exchange`, `constants`) | Official, verified spot order + agent support | High |
| Signing / wallet | **eth-account** | Used by SDK to sign L1 actions; needed for agent key handling | High |
| Config & secrets | **pydantic-settings** + `.env` (dotenv) | Typed config, env-var secrets, validation, safe defaults | High |
| Async runtime | **asyncio** (stdlib) | Single event loop for quoting + Telegram + websockets | High |
| Telegram control | **python-telegram-bot v21+** (async) | Most mature; command handlers + push notifications | High |
| Logging | **structlog** or **loguru** | Structured JSON logs for a long-running trading service | High |
| Scheduling/cadence | asyncio loop + `asyncio.sleep` (optionally **APScheduler**) | Re-quote interval, throttling, periodic reports | High |
| AI guardrail (optional) | Rule-based first; optional **anthropic**/**openai** client for volatility-regime classification | Keep deterministic core; AI only adapts/pauses/reports | Medium |
| Persistence/state | SQLite (stdlib `sqlite3`) or JSON state file | Track orders, fills, PnL across restarts | Medium |
| Testing | **pytest** + testnet integration tests | Unit-test math/rounding; integration on testnet | High |
| Packaging/deploy | **Docker** + `docker compose` (restart: unless-stopped) OR **systemd** unit | Resilient long-running process on VPS, auto-restart | High |
| Dependency mgmt | `uv` or `pip` + pinned `requirements.txt` | Reproducible installs on VPS | High |

## Verified API facts (live + official docs)

- **Endpoints (`constants`):** `MAINNET_API_URL = https://api.hyperliquid.xyz`, `TESTNET_API_URL = https://api.hyperliquid-testnet.xyz`.
- **Spot order:** `exchange.order(name="PURR/USDC", is_buy=True, sz=100, limit_px=0.5, order_type={"limit": {"tif": "Gtc"}})`. Spot pair name is `"BASE/QUOTE"` for canonical pairs or `"@{index}"` for non-canonical pairs.
- **Maker-only:** use `tif: "Alo"` (Add-Liquidity-Only / post-only) to **guarantee maker** and avoid accidental taker fees. (`Gtc`, `Ioc`, `Alo` are the tif options.)
- **Cancel:** `exchange.cancel("PURR/USDC", oid)`; bulk via `exchange.bulk_cancel([{ "coin": "PURR/USDC", "oid": 123 }])`.
- **Order book:** `info.l2_snapshot(coin)` → `bids`/`asks` with `[px, sz]`.
- **Spot balances:** `info.spot_user_state(address)["balances"]` → `{coin, hold, total}`.
- **Spot metadata:** `info.spot_meta()` → `tokens[]` (with `name`, `index`, `szDecimals`, `weiDecimals`) and `universe[]` (pairs with `name`, `index`, `tokens:[baseIdx, quoteIdx]`).
- **API Agent:** `approve_result, agent_key = main_exchange.approve_agent(name="mwg-bot")`; then `Exchange(agent_wallet, URL, account_address=main_wallet.address)`. Agent can trade but **cannot withdraw/transfer**. Use a **named** agent for persistence (unnamed/temporary agents expire).

## Do NOT use

- ❌ Perp/leverage endpoints — project is spot-only (no liquidation risk).
- ❌ Custom raw HTTP signing — the official SDK handles EIP-712 L1 signing correctly; rolling your own invites nonce/signature bugs.
- ❌ Hardcoded private keys / committing `.env` — secrets via env only.
- ❌ `ethers.js`/Node stack — Python SDK is first-class here.

## Open version note

<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->

## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->

## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->

## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->

## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:

- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->

## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
