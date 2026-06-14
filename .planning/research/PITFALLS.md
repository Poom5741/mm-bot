# Research: Pitfalls — Hyperliquid MGW/USDC Market-Maker

Domain-specific traps, with prevention and the phase that should own each.

| # | Pitfall | Warning signs | Prevention | Phase |
|---|---|---|---|---|
| 1 | **MGW not listed on Hyperliquid** (verified absent on mainnet/testnet) | `spot_meta` has no MGW; orders rejected "unknown asset" | Make target pair fully configurable; validate pair exists on startup and **fail gracefully**; develop/validate on `PURR/USDC`; mainnet MGW gated on HIP-1 listing | Foundation + Cutover |
| 2 | **Accidental taker fees** | Fills at worse-than-quote price; fee ≈ 0.035% eating capital | Use `tif: "Alo"` (post-only) so orders never cross; reject/replace if would-cross | Order placement |
| 3 | **Price/size rounding errors** | Order rejected for bad precision; silent truncation | Round size to `szDecimals`; round price to allowed sig-figs (spot ≤ 8 significant figures); centralize in client wrapper; unit-test | Market data/rounding |
| 4 | **Inventory risk in a trend** | One side keeps filling; growing net MGW or USDC | Inventory caps + **inventory skew** quoting + kill-switch to pause/flatten on one-sided drift | Risk manager |
| 5 | **Rate-limit ban** | 429s / dropped requests / IP or address throttled | Throttle loop (sleep), batch place/cancel, backoff on errors, avoid over-frequent re-quotes | Orchestrator |
| 6 | **Orphan/stale orders on crash** | Resting orders left after process dies; double-quoting on restart | Cancel-all on shutdown **and** on startup; reconcile open orders before quoting (idempotent start) | Order mgmt / restart |
| 7 | **Agent auth expiry / misconfig** | Orders rejected "agent not approved"; signature errors | Use **named** persistent agent; pass `account_address=main`; monitor for auth errors and alert; document re-approval runbook | Foundation |
| 8 | **Secret leakage** | Key in code, logs, or git history | Env/secret store only; `.gitignore` `.env`; never log keys; agent (not master) key on the VPS | Foundation |
| 9 | **Testnet/mainnet mix-up** | Trading real funds while "testing" | Single env switch drives endpoint + a loud banner/log of active network; require explicit `NETWORK=mainnet` to go live | Foundation/config |
| 10 | **PnL/fee miscalc → false confidence** | Reported PnL drifts from actual balances | Reconcile against `spot_user_state` periodically; include fees; mark unrealized at mid | PnL tracker |
| 11 | **Quoting through thin/illiquid book** (likely for a new token like MGW) | Wide spreads, gaps, your orders are the whole book | Cap size relative to book depth; widen offset in low liquidity; min-spread floor | Quoting/risk |
| 12 | **Clock/nonce issues** | "nonce too old/new", signature rejects | Keep system clock NTP-synced on VPS; let SDK manage nonces; don't run two instances on one agent | Deploy |
| 13 | **Telegram command from stranger** | Unauthorized control attempts | Restrict handlers to owner chat id allowlist | Telegram |
| 14 | **AI layer making unsafe calls** | LLM suggests oversized/again-the-trend orders | AI is advisory only; Risk Manager has final veto; clamp AI outputs to safe ranges | AI guardrail |
| 15 | **Wash-trading perception/compliance** | — | Design only places real two-sided maker quotes filled by third parties; no self-cross; document intent (market health for own token) | Project-wide |
