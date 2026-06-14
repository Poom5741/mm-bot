# Requirements: Hyperliquid MWG/USDC Volume Market-Maker Bot

**Defined:** 2026-06-14
**Core Value:** Keep a healthy, continuously-quoted two-sided market on MWG/USDC (real maker volume) without blowing up inventory or capital.

## v1 Requirements

Requirements for the initial release. Each maps to a roadmap phase.

### Foundation

- [ ] **FND-01**: Project runs as a Python 3.11+ service with pinned dependencies (`requirements.txt`) and a documented setup
- [ ] **FND-02**: All parameters (target pair, tick offset, order size, interval, risk caps, network) load from typed config + `.env`, with conservative safe defaults
- [ ] **FND-03**: Secrets (agent key) load only from environment/secret store; `.env` is gitignored and keys are never logged
- [ ] **FND-04**: A single `NETWORK` switch selects testnet vs mainnet endpoints and logs the active network prominently on startup
- [ ] **FND-05**: Structured logging writes an auditable trail of every order, fill, and cancel

### Connectivity & Auth

- [ ] **CON-01**: Bot authenticates to Hyperliquid using a dedicated bot wallet
- [ ] **CON-02**: Bot trades via a Hyperliquid **API Agent** (named, persistent) that can place/cancel orders but cannot withdraw or transfer funds
- [ ] **CON-03**: Bot detects and alerts on agent auth failure/expiry with a documented re-approval runbook

### Market Data & Metadata

- [ ] **MKT-01**: Bot resolves the configured pair's metadata (asset index/name, size decimals, price precision, min size) at startup
- [ ] **MKT-02**: Bot fails gracefully with a clear message if the configured pair is not listed (e.g. MWG not yet on Hyperliquid)
- [ ] **MKT-03**: Bot reads the live L2 order book and computes best bid/ask and mid price
- [ ] **MKT-04**: Bot computes a rolling volatility estimate from recent prices
- [ ] **MKT-05**: All prices and sizes are rounded to exchange-valid precision before any order is sent

### Quoting Engine

- [ ] **QTE-01**: Bot computes two-sided target prices = mid ∓ (tick × configurable offset, default 2 ticks)
- [ ] **QTE-02**: Bot places orders as post-only (`tif: "Alo"`) so they are always maker and never cross as taker
- [ ] **QTE-03**: Bot applies inventory skew to nudge net inventory back toward a configured target
- [ ] **QTE-04**: Quoting logic is a pure, unit-tested function of its inputs

### Order Management

- [ ] **ORD-01**: Bot places paired buy+sell maker orders each cycle
- [ ] **ORD-02**: Bot cancels and replaces stale quotes when the market moves beyond a threshold
- [ ] **ORD-03**: Bot cancels all open orders on shutdown and on startup, and reconciles existing open orders before quoting (idempotent restart)
- [ ] **ORD-04**: Order placement throttles to respect Hyperliquid rate limits, with backoff on errors

### Risk Management

- [ ] **RSK-01**: Bot enforces a maximum net inventory cap and stops adding to an over-cap side
- [ ] **RSK-02**: Bot enforces a maximum capital-deployed limit
- [ ] **RSK-03**: Bot enforces minimum/maximum spread bounds
- [ ] **RSK-04**: A kill-switch auto-pauses quoting on a volatility spike or sustained one-sided drift, and can flatten/cancel-all
- [ ] **RSK-05**: Risk Manager has final veto over every order (including AI suggestions)

### Inventory & PnL

- [ ] **PNL-01**: Bot tracks MWG and USDC balances and net exposure
- [ ] **PNL-02**: Bot computes realized and unrealized PnL (unrealized marked at mid), including fees
- [ ] **PNL-03**: Bot persists state (orders, fills, PnL) so it survives restarts, and periodically reconciles against on-chain balances

### AI Guardrail Layer

- [ ] **AIG-01**: An AI guardrail suggests spread/size multipliers and pause/resume from market features, as advisory input only (clamped to safe ranges, never bypassing Risk Manager)
- [ ] **AIG-02**: The AI layer generates plain-language status/risk reports for Telegram

### Telegram Control

- [ ] **TGM-01**: Owner can start and stop the bot via Telegram
- [ ] **TGM-02**: Owner can change runtime parameters (size, spread/offset, target pair) via Telegram
- [ ] **TGM-03**: Owner can query status, inventory, and PnL via Telegram
- [ ] **TGM-04**: Bot pushes alerts (kill-switch, auth failure, errors) to the owner
- [ ] **TGM-05**: Telegram control is restricted to an allowlisted owner chat id

### Deployment & Ops

- [ ] **OPS-01**: Bot ships as a containerized/`systemd`-managed long-running service with auto-restart
- [ ] **OPS-02**: A deployment + ops runbook documents VPS setup, secrets, agent approval, start/stop, and recovery
- [ ] **OPS-03**: The full loop is validated on Hyperliquid **testnet** (using an available pair) before any mainnet run

## v2 Requirements

Deferred to a future release. Tracked but not in the current roadmap.

### Scaling & UX

- **MUL-01**: Quote multiple pairs concurrently from one process
- **MUL-02**: Web dashboard for monitoring
- **MUL-03**: Backtesting / simulation harness for strategy tuning
- **MUL-04**: Advanced fair-value model (microprice, trade-flow) beyond mid

## Out of Scope

Explicitly excluded to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Perpetuals / leverage | Spot-only; avoid liquidation risk |
| Self-trading / wash trading | Blocked by Hyperliquid; volume must be real fills |
| Withdrawal/transfer ability in the bot | Agent wallet is trade-only by design |
| Multi-exchange / CEX support | Hyperliquid-only for v1 |
| Listing MWG on Hyperliquid (HIP-1 auction) | Prerequisite owned by the team, outside the bot |
| Guaranteed-profit / alpha strategies | Target is volume near break-even, not alpha |

## Traceability

Populated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| (to be mapped by roadmap) | — | Pending |

**Coverage:**
- v1 requirements: 35 total
- Mapped to phases: TBD
- Unmapped: TBD

---
*Requirements defined: 2026-06-14*
*Last updated: 2026-06-14 after initial definition*
