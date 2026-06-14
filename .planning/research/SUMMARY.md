# Research Summary — Hyperliquid MWG/USDC Market-Maker

**Researched:** 2026-06-14 (inline; live API verified + official Python SDK docs)

## Stack (the short version)

Python 3.11+ • **hyperliquid-python-sdk** (`Info`/`Exchange`) • eth-account • pydantic-settings + `.env` • python-telegram-bot v21 (async) • structlog • asyncio loop • SQLite state • pytest + testnet • Docker/systemd on VPS. Spot-only, no leverage.

## Table Stakes

Authenticated connection via **API agent** (trade-only) → resolve market metadata → read L2 book → place **post-only (ALO)** two-sided maker quotes ~N ticks off mid → manage order lifecycle (cancel-replace, cancel-all on stop/start) → track inventory + PnL → enforce risk caps + kill-switch → rate-limit safety → config-driven + secret-safe → structured logging → resilient restart-safe loop. Telegram control + reports.

## Watch Out For (top risks)

1. **MWG is NOT listed on Hyperliquid** (verified: absent on mainnet spot, perps, and testnet). Listing needs HIP-1 (Dutch auction) first — outside the bot. → Build configurable, validate on `PURR/USDC`, gate mainnet MWG on listing.
2. **Taker fees** — always use `tif: "Alo"` (post-only) to stay maker.
3. **Inventory risk** in trends → caps + inventory skew + kill-switch.
4. **Rounding** to `szDecimals` / price sig-figs (≤8 for spot) → centralize + unit-test.
5. **Rate limits** → throttle + batch + backoff.
6. **Orphan orders / restart** → cancel-all + reconcile on startup.
7. **Secrets & testnet/mainnet mix-up** → env-only secrets, explicit network switch, agent (not master) key on VPS.

## Verified API quick-reference

- Endpoints: `constants.MAINNET_API_URL` / `constants.TESTNET_API_URL`.
- Spot order: `exchange.order("PURR/USDC", is_buy, sz, limit_px, {"limit":{"tif":"Alo"}})`; pair = `"BASE/QUOTE"` or `"@index"`.
- Cancel: `exchange.cancel(pair, oid)` / `exchange.bulk_cancel([...])`.
- Book: `info.l2_snapshot(coin)`. Balances: `info.spot_user_state(addr)`. Meta: `info.spot_meta()`.
- Agent: `approve_result, agent_key = main_exchange.approve_agent(name="mwg-bot")` → `Exchange(agent_wallet, URL, account_address=main.address)`; agent can trade, not withdraw.

## Architecture (build order)

Foundation/config/client → market data + rounding → testnet order/cancel → quoting engine + skew → risk manager/kill-switch → inventory/PnL + state → orchestrator loop → Telegram control → AI guardrail → VPS deploy → mainnet MWG cutover.

## Strategy reality

"Volume near break-even" = genuine post-only market making filled by real counterparties (not self-trades). Profit is a bonus; the discipline (inventory + risk caps) is what keeps it safe. For a thin new-token book (MWG), size relative to depth and floor the spread.
