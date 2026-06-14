# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-06-14)

**Core value:** Keep a healthy, continuously-quoted two-sided market on MGW/USDC (real maker volume) without blowing up inventory or capital.
**Current focus:** Phase 1 — Project Foundation & Config

## Status

- **Phase:** Not started (initialized 2026-06-14)
- **Milestone:** v1 — Working testnet-validated market-maker
- **Phases:** 10 total, 0 complete
- **Requirements:** 39 v1, all mapped to phases

## Key Facts (carry across sessions)

- **Market:** Hyperliquid **spot** `MGW/USDC`. ⚠️ MGW is deployed as a HyperEVM ERC-20 (`0x45F601113B3727EDa535b5Fccfa79eA529a7584C`, 100B cap, 0 minted, deployed 2026-06-11) but **not yet listed on Hyperliquid spot DEX** (HIP-1 required). Develop & validate on `PURR/USDC` (testnet); MGW go-live is a config flip after HIP-1 listing.
- **Stack:** Python 3.11+, `hyperliquid-python-sdk` (`Info`/`Exchange`), eth-account, pydantic-settings, python-telegram-bot v21, structlog, asyncio, SQLite, Docker/systemd.
- **Auth model:** dedicated bot wallet + named **API Agent** (trade-only, cannot withdraw). `approve_agent(name=...)` → `Exchange(agent_wallet, URL, account_address=main)`.
- **Strategy:** post-only (`tif:"Alo"`) two-sided maker quotes at mid ∓ 2 ticks; inventory skew; kill-switch on volatility/drift. Deterministic core + advisory AI guardrails.
- **Goal:** volume near break-even (profit optional); support MGW market health (owner's token).
- **Config:** YOLO mode, Fine granularity, Parallel execution, planning docs committed to git, Quality model profile. Research/Plan-check/Verifier = on (run inline — GSD subagents are not installed in this runtime).
- **Git:** branch `main`, remote `origin` → github.com/Poom5741/mm-bot (HTTPS rewritten to SSH).

## Session Continuity

- Last action: project initialized via `/gsd-new-project` (PROJECT, config, research, requirements, roadmap, STATE committed). Token symbol corrected MWG→MGW across all docs. MGW HyperEVM contract confirmed.
- Next step: `/gsd-discuss-phase 1` then `/gsd-plan-phase 1`.

---
*Last updated: 2026-06-14 — symbol corrected (MWG→MGW), contract address added*
