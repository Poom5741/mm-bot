# Plan 02-A Summary — Config Extension & Agent Approval Script

**Status:** Complete
**Wave:** 1

## What was built

- `src/mgw_mm/config.py` — Added `main_wallet_address: str` as a required field to `Settings` (no default, plain string, fail-fast on missing)
- `.env.example` — Added `MAIN_WALLET_ADDRESS=0xYOUR_MAIN_WALLET_ADDRESS_HERE` with explanatory comment
- `scripts/approve_agent.py` — Standalone one-time agent approval script: `getpass` for hidden main wallet key input, confirmation prompt before submitting, calls `approve_agent(name=agent_name)`, prints `AGENT_PRIVATE_KEY` and `MAIN_WALLET_ADDRESS` for copying into `.env`
- `scripts/README.md` — Brief ops note for the scripts directory
- `tests/test_config.py` — Updated all fixtures with `MAIN_WALLET_ADDRESS`, added `test_missing_main_wallet_address_exits`
- `tests/test_smoke.py` — Added `MAIN_WALLET_ADDRESS` to `_make_settings` helper

## Requirements covered

- CON-01: Dedicated bot wallet (AGENT_PRIVATE_KEY + MAIN_WALLET_ADDRESS both required in config)
- CON-02: Named API Agent setup procedure (scripts/approve_agent.py)

## Decisions implemented

- D-01–04: One-time setup script, standalone, interactive prompts via getpass
- D-05–08: MAIN_WALLET_ADDRESS required str, fail-fast on missing, setup script prints both values
