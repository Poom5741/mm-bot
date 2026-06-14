# Roadmap: Hyperliquid MGW/USDC Volume Market-Maker Bot

**Created:** 2026-06-14
**Mode:** Vertical MVP (each phase delivers a working end-to-end capability)
**Core Value:** Keep a healthy, continuously-quoted two-sided market on MGW/USDC (real maker volume) without blowing up inventory or capital.

> ⚠️ **MGW is not yet listed on Hyperliquid** (verified absent on mainnet spot, perps, and testnet). All phases develop and validate against an existing pair (default `PURR/USDC` on testnet) with the target pair fully configurable. Going live on `MGW/USDC` is a config flip once MGW is listed via HIP-1 (the listing itself is out of scope — see REQUIREMENTS.md).

---

### Phase 1: Project Foundation & Config
**Goal:** A runnable Python service skeleton with typed config, safe secret handling, a testnet/mainnet network switch, and structured logging.
**Mode:** mvp
**Requirements:** FND-01, FND-02, FND-03, FND-04, FND-05
**Depends on:** —
**Success Criteria:**
1. Service starts via a documented command and loads typed config + `.env` with conservative defaults
2. Missing/invalid secrets cause a clear startup failure; `.env` is gitignored and keys are never logged
3. The active network (testnet/mainnet) is logged prominently on startup from a single switch
4. Every significant event writes a structured log line

### Phase 2: Connectivity & API Agent Auth
**Goal:** An authenticated Hyperliquid connection on testnet using a dedicated bot wallet and a named, persistent API Agent (trade-only).
**Mode:** mvp
**Requirements:** CON-01, CON-02, CON-03
**Depends on:** Phase 1
**Success Criteria:**
1. Bot authenticates with the dedicated bot wallet on testnet
2. A named API Agent is approved and used (`account_address` wired); it can place/cancel but cannot withdraw
3. Agent auth failure/expiry is detected and alerted, with a re-approval runbook documented

### Phase 3: Market Data & Metadata
**Goal:** Resolve the configured pair's specs, read the live book, compute mid + volatility, and round all values to exchange-valid precision.
**Mode:** mvp
**Requirements:** MKT-01, MKT-02, MKT-03, MKT-04, MKT-05
**Depends on:** Phase 2
**Success Criteria:**
1. Pair metadata (index/name, size decimals, price precision, min size) resolves at startup
2. Bot fails gracefully with a clear message if the configured pair is unlisted (e.g. MGW)
3. Best bid/ask, mid, and a rolling volatility estimate are computed from live L2 data
4. Price/size rounding to exchange precision is centralized and unit-tested

### Phase 4: First Live Quote Loop (MVP slice)
**Goal:** The "it trades" moment — place a single pair of post-only two-sided maker orders 2 ticks off mid on testnet, then cancel all.
**Mode:** mvp
**Requirements:** QTE-01, QTE-02, QTE-04, ORD-01, ORD-04
**Depends on:** Phase 3
**Success Criteria:**
1. Bot computes target prices = mid ∓ (tick × offset, default 2) via a pure, unit-tested function
2. Bot places paired buy+sell orders as post-only (`Alo`) that rest as maker (never cross as taker)
3. Order submission is throttled to respect rate limits
4. Orders are confirmed resting on testnet and can be cancelled on demand

### Phase 5: Continuous Quoting & Order Lifecycle
**Goal:** A resilient continuous re-quoting loop with cancel-replace on market moves and idempotent restart.
**Mode:** mvp
**Requirements:** ORD-02, ORD-03
**Depends on:** Phase 4
**Success Criteria:**
1. The loop re-quotes each interval and cancels-and-replaces stale quotes when the market moves beyond a threshold
2. Bot cancels all orders on shutdown and on startup, reconciling existing open orders before quoting
3. A restart produces no duplicate or orphaned orders
4. The bot runs continuously on testnet without manual intervention

### Phase 6: Inventory & PnL Tracking
**Goal:** Track balances, net exposure, and realized/unrealized PnL (with fees), persisted across restarts; use inventory to skew quotes.
**Mode:** mvp
**Requirements:** PNL-01, PNL-02, PNL-03, QTE-03
**Depends on:** Phase 5
**Success Criteria:**
1. Bot tracks base + quote balances and net exposure for the configured pair
2. Realized and unrealized PnL (unrealized marked at mid) are computed including fees
3. State persists and periodically reconciles against on-chain balances; survives restart
4. Inventory skew nudges net inventory toward a configured target

### Phase 7: Risk Management & Kill-Switch
**Goal:** Hard risk limits and an auto-pausing kill-switch, with the Risk Manager holding final veto over every order.
**Mode:** mvp
**Requirements:** RSK-01, RSK-02, RSK-03, RSK-04, RSK-05
**Depends on:** Phase 6
**Success Criteria:**
1. Over-cap inventory side stops adding; capital-deployed limit is enforced
2. Minimum/maximum spread bounds are enforced
3. The kill-switch auto-pauses (and can flatten/cancel-all) on a volatility spike or sustained one-sided drift
4. No order is sent without passing the Risk Manager veto

### Phase 8: Telegram Control & Reporting
**Goal:** Owner controls and monitors the bot entirely from Telegram, with owner-only access.
**Mode:** mvp
**Requirements:** TGM-01, TGM-02, TGM-03, TGM-04, TGM-05
**Depends on:** Phase 7
**Success Criteria:**
1. Owner can start/stop the bot and change runtime params (size, offset, pair) via Telegram
2. Owner can query status, inventory, and PnL via Telegram
3. Alerts (kill-switch, auth failure, errors) are pushed to the owner
4. Control commands are restricted to an allowlisted owner chat id

### Phase 9: AI Guardrail Layer
**Goal:** An advisory AI layer that adapts spread/size and pause/resume within clamped safe ranges, and writes plain-language reports.
**Mode:** mvp
**Requirements:** AIG-01, AIG-02
**Depends on:** Phase 8
**Success Criteria:**
1. AI suggests spread/size multipliers and pause/resume from market features as advisory input only
2. AI outputs are clamped to safe ranges and always subject to Risk Manager veto
3. AI generates readable status/risk reports delivered via Telegram

### Phase 10: Deployment, Ops & Testnet Validation
**Goal:** A containerized, resilient deployment with a runbook, validated end-to-end on testnet before any mainnet use.
**Mode:** mvp
**Requirements:** OPS-01, OPS-02, OPS-03
**Depends on:** Phase 9
**Success Criteria:**
1. Bot runs as a Docker/`systemd`-managed long-running service with auto-restart on a VPS
2. An ops runbook documents VPS setup, secrets, agent approval, start/stop, and recovery
3. The full loop is validated on testnet over a sustained run before mainnet cutover

---

## Post-v1 (gated, not scheduled)

- **Mainnet MGW cutover** — flip `NETWORK=mainnet` + target pair to `MGW/USDC` with tiny size and tight caps. **Blocked on MGW being listed on Hyperliquid (HIP-1).**
- See REQUIREMENTS.md v2 for multi-pair, dashboard, backtesting, and advanced fair-value model.

---
*Last updated: 2026-06-14 after roadmap creation*
