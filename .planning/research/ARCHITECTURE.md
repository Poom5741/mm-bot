# Research: Architecture — Hyperliquid MGW/USDC Market-Maker

## Component Map

```
                         ┌──────────────────────────┐
                         │   Telegram Control Bot    │  commands / alerts
                         │ (start/stop, set, status) │◄────────────────┐
                         └────────────┬──────────────┘                 │
                                      │ control intents                 │ reports
                                      ▼                                 │
┌──────────────┐   config   ┌──────────────────┐   decisions   ┌───────┴───────┐
│ Config/Secrets│──────────►│  Orchestrator     │──────────────►│ Risk Manager   │
│ (pydantic/env)│           │  (asyncio loop)   │◄──────────────│ caps/kill-sw   │
└──────────────┘           └───┬───────────┬───┘   gate         └───────────────┘
                               │           │
                  market data  │           │ orders/cancels
                               ▼           ▼
                      ┌────────────┐  ┌──────────────────┐
                      │ Market Data │  │ Quoting Engine    │
                      │ (L2/mid/vol)│─►│ (deterministic +  │
                      └─────┬───────┘  │  inventory skew)  │
                            │          └────────┬──────────┘
                            │                   │
                            ▼                   ▼
                      ┌─────────────────────────────────────┐
                      │ Hyperliquid Client Wrapper           │
                      │ Info (data) + Exchange (signed/agent) │
                      └────────────────┬─────────────────────┘
                                       │
                            ┌──────────▼───────────┐
                            │ Inventory & PnL Tracker│  + State store (SQLite)
                            └────────────────────────┘
                                       ▲
                            ┌──────────┴───────────┐
                            │ AI Guardrail (optional)│ regime/volatility advice
                            └────────────────────────┘
```

## Components

1. **Config/Secrets** — Typed settings (pydantic-settings). Loads pair, tick offset, size, interval, risk caps, endpoints (testnet/mainnet), and secrets (agent key) from env/`.env`. Validates on startup; refuses unsafe values.
2. **Hyperliquid Client Wrapper** — Thin wrapper over `Info` + `Exchange`. Centralizes endpoint selection, agent-account wiring (`account_address=main`), price/size rounding (to `szDecimals` and price sig-figs), retry/backoff, and rate-limit throttling. Single choke-point for all API calls.
3. **Market Data** — Pulls `l2_snapshot` (and/or websocket), computes best bid/ask, mid, microprice, and a rolling volatility estimate.
4. **Quoting Engine (deterministic core)** — Computes target buy/sell prices = mid ∓ (tick × offset), adjusted by inventory skew; computes sizes within limits. Pure function of inputs → desired quotes (easily unit-tested).
5. **Risk Manager** — Gatekeeper before any order: enforces max inventory, max capital, min/max spread, and the kill-switch (pause on volatility spike / adverse one-sided drift). Can flatten or cancel-all.
6. **Inventory & PnL Tracker** — Reconciles `spot_user_state` balances + fills; computes realized/unrealized PnL and fees; persists state for restart safety.
7. **AI Guardrail (optional layer)** — Given market features, suggests spread/size multipliers, pause/resume, and authors human-readable Telegram reports. Advisory only — never bypasses Risk Manager.
8. **Telegram Control Bot** — Command handlers (start/stop/set/status/pnl) + push alerts. Auth-restricted to owner chat id.
9. **Orchestrator (asyncio loop)** — Ties it together: each tick → fetch data → (AI advice) → quoting engine → risk gate → reconcile orders (cancel-replace) → update PnL → sleep(interval). Handles graceful shutdown (cancel-all).

## Data Flow (one quoting cycle)

market data → volatility/mid → (AI advice) → desired quotes → risk gate → diff vs resting orders → cancel stale + place new (ALO) → record fills → update inventory/PnL → maybe Telegram report → sleep.

## Suggested Build Order (dependency-driven)

1. **Foundation:** repo, config/secrets, logging, client wrapper, testnet connectivity (read-only).
2. **Market data + metadata resolution + rounding** (correctness-critical math).
3. **Order placement/cancel (ALO) on testnet** — single quote, then cancel-all.
4. **Quoting engine + inventory skew** (pure, unit-tested).
5. **Risk manager + kill-switch.**
6. **Inventory/PnL tracker + state persistence + restart reconciliation.**
7. **Orchestrator loop** (continuous quoting, rate-limit safe).
8. **Telegram control + reporting.**
9. **AI guardrail layer.**
10. **Packaging + VPS deploy (Docker/systemd) + ops/runbook.**
11. **Mainnet cutover for MGW/USDC** (gated on MGW listing).
