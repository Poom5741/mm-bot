# Research: Stack — Hyperliquid MWG/USDC Market-Maker

**Domain:** Algorithmic spot market-making bot on Hyperliquid DEX, Python, AI-assisted, Telegram-controlled, VPS-deployed.
**Confidence:** High on core SDK (verified against live API + official docs); Medium on AI-layer choices (design-dependent).

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

Pin `hyperliquid-python-sdk` to a specific version in `requirements.txt` and re-verify `tif: "Alo"` and `approve_agent(name=...)` signatures against the installed version during Phase 0/1 (API surface evolves).
