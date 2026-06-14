# Research: Features — Hyperliquid MGW/USDC Market-Maker

Categorized for a spot volume/market-making bot. Table stakes = must-have or the bot is unsafe/useless. Differentiators = adaptive edge. Anti-features = deliberately excluded.

## Table Stakes (must have)

| Feature | Notes | Complexity |
|---|---|---|
| Connect + authenticate (bot wallet / API agent) | EIP-712 signing via SDK; agent cannot withdraw | M |
| Resolve market metadata at runtime | Asset index, `szDecimals`, price precision, min size for the target pair | M |
| Read L2 order book | Best bid/ask/mid; depth for sanity checks | S |
| Place two-sided maker limit orders (ALO) | Buy and sell ~N ticks off market; post-only | M |
| Order lifecycle management | Track resting oids, cancel-and-replace stale quotes, cancel-all on stop/crash | M |
| Inventory tracking | MGW + USDC balances; net exposure vs caps | M |
| PnL accounting | Realized + unrealized (mark = mid); fees included | M |
| Risk controls | Max inventory cap, max capital deployed, min/max spread, kill-switch on adverse move/volatility | L |
| Rate-limit safety | Throttle/backoff, batch orders, avoid API ban | M |
| Config-driven parameters | Pair, size, spread ticks, interval, limits — all from config/env, conservative defaults | S |
| Secret handling | Keys via env/secret store, never in code/git | S |
| Structured logging + audit trail | Every order/fill/cancel logged for post-mortem | S |
| Resilient run loop | Reconnect, restart-safe, idempotent startup (reconcile open orders) | M |

## Differentiators (the AI-assisted edge)

| Feature | Notes | Complexity |
|---|---|---|
| Volatility-adaptive spread/size | Widen spread or shrink size when volatility rises | M |
| Auto-pause / resume | Stop quoting on volatility spikes or one-sided drift, resume when calm | M |
| Inventory skew quoting | Skew quotes to mean-revert inventory toward target (helps break-even) | M |
| AI guardrail layer | LLM classifies market regime / sanity-checks actions / writes plain-language reports | M |
| Telegram control & reporting | start/stop, set size/spread/pair, status, PnL, alerts | M |
| Multi-pair support | Quote several pairs from one process (post-MGW) | L |

## Anti-Features (deliberately NOT built)

| Excluded | Reason |
|---|---|
| Self-trading / wash trading | Blocked by Hyperliquid; volume must come from real fills |
| Leverage / perps | Spot-only; avoid liquidation risk |
| Withdrawal / transfer capability in the bot | Agent wallet is trade-only by design |
| Multi-exchange / CEX integration | Hyperliquid-only for v1 |
| Web GUI/dashboard | Telegram is the control surface for v1 |
| Guaranteed-profit promises | Target is volume near break-even, not alpha |

## Hard dependency / sequencing note

⚠️ **MGW is not yet listed on Hyperliquid (verified absent on mainnet spot, perps, and testnet).** Listing a spot token requires the **HIP-1** deployment (Dutch auction) — a prerequisite owned outside this bot. Therefore: build & validate against an existing pair (e.g. `PURR/USDC`), keep the target market fully configurable, and the bot must **fail gracefully** if the configured pair is not found.
