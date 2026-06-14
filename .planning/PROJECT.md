# Hyperliquid MGW/USDC Volume Market-Maker Bot

## What This Is

An AI-assisted market-making bot that continuously places two-sided limit (maker) orders on the Hyperliquid **spot** pair **MGW/USDC** to generate trading volume and support the market health of MGW (the owner's own project token). It runs as a long-running service on a VPS, is controlled via a Telegram bot, and uses a deterministic rule-based quoting core with an AI guardrail layer for volatility adaptation, auto-pausing, and reporting.

## Core Value

The bot keeps a healthy, continuously-quoted two-sided market on MGW/USDC (real maker orders that generate genuine volume) **without blowing up inventory or capital** — volume with disciplined risk control is the one thing that must work.

## Requirements

### Validated

<!-- Shipped and confirmed valuable. -->

(None yet — ship to validate)

### Active

<!-- Current scope. Building toward these. Hypotheses until shipped. -->

- [ ] Connect to Hyperliquid API (info + exchange) for spot trading using a dedicated bot wallet
- [ ] Authorize the bot via a Hyperliquid **API Agent** (trade-only approved wallet, cannot withdraw)
- [ ] Resolve MGW/USDC spot market metadata (asset index, tick size, lot/size decimals, min order) from the API
- [ ] Read live L2 order book (best bid/ask, mid) for MGW/USDC
- [ ] Place two-sided limit orders ~2 ticks off the market as configurable Maker (GTC/ALO) orders
- [ ] Run a continuous quoting loop: re-quote, cancel stale orders, respect rate limits
- [ ] Track inventory (MGW + USDC) and realized/unrealized PnL
- [ ] Enforce risk controls: max inventory cap, max capital deployed, kill-switch / auto-pause on adverse moves or volatility spikes
- [ ] AI guardrail layer: adjust spread/size on volatility, decide pause/resume, generate human-readable reports
- [ ] Telegram control: start/stop, change size/spread/coin, query status & PnL, receive alerts
- [ ] Fully config-driven parameters (capital, order size, spread ticks, intervals, risk limits) with conservative safe defaults
- [ ] Secure secret handling: private key / API agent key via environment variables, never in code or git
- [ ] Run validated on Hyperliquid **testnet** (loop logic on an available pair), then operate on **mainnet** for MGW/USDC
- [ ] Deployable on a VPS as a resilient long-running process (auto-restart, logging)

### Out of Scope

<!-- Explicit boundaries. Includes reasoning to prevent re-adding. -->

- Perpetual futures / leveraged trading — project targets the MGW/USDC **spot** market; no leverage means no liquidation risk
- Self-trading / wash trading to fake volume — blocked by Hyperliquid and pointless; volume must come from real counterparty fills
- Multi-exchange support (Binance, etc.) — Hyperliquid-only for v1
- Web dashboard / GUI — Telegram is the control surface for v1
- Custodial handling of user funds beyond the single dedicated bot wallet — owner funds and controls one bot wallet only
- Guaranteed profit — profit is a bonus; staying near break-even with healthy volume is the target

## Context

- **Platform:** Hyperliquid is a high-performance L1 DEX. Trading is authenticated by signing with an EVM wallet's private key. Spot pairs (e.g. MGW/USDC) use a different asset-naming/indexing scheme than perps and have per-token tick/lot sizes that must be read from the API.
- **MGW token contract (HyperEVM Mainnet):** `0x45F601113B3727EDa535b5Fccfa79eA529a7584C` — ERC-20, 100B cap, 0 minted (deployed 2026-06-11). This is the HyperEVM deployment; spot DEX listing via HIP-1 is a separate step still required before MGW/USDC can be traded on the orderbook.
- **Official SDK:** `hyperliquid-python-sdk` (`pip install hyperliquid-python-sdk`) provides `Info` (market data) and `Exchange` (signed orders), with mainnet/testnet endpoints in `constants`.
- **Strategy reality:** Placing buy below best bid and sell above best ask (2 ticks outside) = passive maker quoting. Volume is generated when real takers fill the orders. Maker orders earn rebates / low fees; an accidental Taker fill costs ~0.035%. The main risk is **inventory risk** — a one-sided fill in a trending market leaves the bot holding MGW (or USDC) at a loss.
- **Security model:** Reference docs (provided by owner) stress: never use the main wallet; create a dedicated bot wallet (MetaMask/Rabby); fund only with what the bot should trade; prefer Hyperliquid's **API Agent** delegation so the trading key cannot withdraw funds.
- **Owner motivation:** MGW is the owner's/team's own token — the bot exists to keep MGW's market liquid and active, with volume + break-even as success, not aggressive profit extraction.
- **Reference:** Hyperliquid API docs — https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api

## Constraints

- **Tech stack**: Python — Hyperliquid has an official, well-documented Python SDK; AI/LLM and Telegram libraries are mature in Python.
- **Market**: Hyperliquid spot, pair MGW/USDC — set by the owner; tick/lot sizes are dictated by the exchange and must be fetched at runtime.
- **Security**: Dedicated bot wallet + API Agent delegation; secrets only via env vars / secret store — non-negotiable to protect funds.
- **Rate limits**: Hyperliquid enforces API rate limits — quoting loop must throttle (sleep / backoff) to avoid bans.
- **Environment**: Testnet-first for validation; MGW likely exists only on mainnet, so loop logic is proven on testnet then pointed at mainnet MGW/USDC.
- **Deployment**: VPS, long-running resilient process with logging and auto-restart.
- **Risk**: Spot inventory (no liquidation) but real price exposure — hard inventory and capital caps plus a kill-switch are required.

## Key Decisions

<!-- Decisions that constrain future work. Add throughout project lifecycle. -->

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Spot MGW/USDC, not perps | Owner's token is a spot asset; avoid leverage/liquidation risk | — Pending |
| Deterministic core + AI guardrails (not AI-driven quoting) | Predictable, auditable behavior; AI only adapts spread/size, pauses, and reports | — Pending |
| Python + official `hyperliquid-python-sdk` | First-class SDK, good docs, strong AI/Telegram ecosystem | — Pending |
| Hyperliquid API Agent + dedicated bot wallet | Trade-only delegation that cannot withdraw — safest funds model | — Pending |
| Telegram as the control surface | Remote start/stop and reporting from phone; no GUI needed for v1 | — Pending |
| Fully config-driven with conservative defaults | Owner sets real numbers; safe defaults reduce blow-up risk | — Pending |
| Testnet-first, then mainnet MGW | Validate the loop without risking capital before live trading | — Pending |
| Goal = volume near break-even (profit optional) | Support MGW market health; risk discipline over profit chasing | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-06-14 after initialization*
