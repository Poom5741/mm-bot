---
wave: 1
depends_on: []
files_modified:
  - src/mgw_mm/config.py
autonomous: true
requirements_addressed:
  - FND-02
  - FND-03
  - FND-04
---

# Plan B: Typed Config System

## Objective

Implement the full pydantic-settings config system: four nested config sections (`NetworkConfig`, `TradingConfig`, `RiskConfig`, `TelegramConfig`) composing into a top-level `Settings` class; conservative defaults baked in (D-09); fail-fast validation on missing secrets (D-10, D-11); and a `load_settings()` factory function that catches `ValidationError` and exits with clear error messages.

## Must Haves

<must_haves>
<truths>
- `Settings` composes `NetworkConfig`, `TradingConfig`, `RiskConfig`, and `TelegramConfig` as fields
- All D-09 defaults are present: `ORDER_SIZE_USDC=10`, `TICK_OFFSET=2`, `MAX_INVENTORY_USDC=100`, `MAX_CAPITAL_USDC=200`, `QUOTE_INTERVAL_SEC=30`
- Missing `AGENT_PRIVATE_KEY` causes startup to exit with code 1 and print a clear error naming the missing field
- Missing `TELEGRAM_BOT_TOKEN` causes startup to exit with code 1 and print a clear error
- `AGENT_PRIVATE_KEY` is consumed to create the wallet object; the raw key string is never stored as an attribute of `Settings` or any config model
- `NETWORK` field accepts only `"testnet"` or `"mainnet"` as valid values (validated by pydantic `Literal` or `validator`)
- FND-02 addressed: all parameters load from typed config + `.env` with conservative safe defaults
- FND-03 addressed: secrets load from env only; keys are never logged or hardcoded
- FND-04 addressed: `NETWORK` field drives endpoint selection
</truths>
</must_haves>

## Tasks

### Task B1: Implement NetworkConfig

<read_first>
- `.planning/phases/01-project-foundation-config/01-CONTEXT.md` — D-08: NetworkConfig fields
- `.planning/research/STACK.md` — verified endpoint URLs: `MAINNET_API_URL`, `TESTNET_API_URL`
</read_first>

<action>
Create/update `src/mgw_mm/config.py`. Implement `NetworkConfig` as a pydantic `BaseModel` (not a Settings class itself — it is a composed sub-model):
- Field `network: Literal["testnet", "mainnet"]` with default `"testnet"`
- Property `api_url: str` that returns `"https://api.hyperliquid-testnet.xyz"` for testnet and `"https://api.hyperliquid.xyz"` for mainnet
- No pydantic-settings inheritance for this sub-model (it is embedded in the parent `Settings` class which handles env loading)
</action>

<acceptance_criteria>
- `NetworkConfig` class defined in `config.py`
- `NetworkConfig(network="testnet").api_url == "https://api.hyperliquid-testnet.xyz"`
- `NetworkConfig(network="mainnet").api_url == "https://api.hyperliquid.xyz"`
- `NetworkConfig(network="invalid")` raises `ValidationError`
- `NetworkConfig()` (no args) defaults to `network="testnet"`
</acceptance_criteria>

---

### Task B2: Implement TradingConfig

<read_first>
- `.planning/phases/01-project-foundation-config/01-CONTEXT.md` — D-08 TradingConfig fields, D-09 defaults
</read_first>

<action>
Implement `TradingConfig` as a pydantic `BaseModel` in `config.py`:
- `target_pair: str` default `"PURR/USDC"` — the trading pair; configurable to `MGW/USDC` once listed
- `order_size_usdc: float` default `10.0` — size of each side in USDC notional
- `tick_offset: int` default `2` — number of ticks from mid for initial quotes
- `quote_interval_sec: float` default `30.0` — seconds between re-quote cycles
- All numeric fields must have `gt=0` validators (positive values only)
</action>

<acceptance_criteria>
- `TradingConfig()` (no args) produces `order_size_usdc=10.0`, `tick_offset=2`, `quote_interval_sec=30.0`, `target_pair="PURR/USDC"`
- `TradingConfig(order_size_usdc=0)` raises `ValidationError` (gt=0 violated)
- `TradingConfig(tick_offset=-1)` raises `ValidationError`
</acceptance_criteria>

---

### Task B3: Implement RiskConfig

<read_first>
- `.planning/phases/01-project-foundation-config/01-CONTEXT.md` — D-08 RiskConfig fields, D-09 defaults
</read_first>

<action>
Implement `RiskConfig` as a pydantic `BaseModel` in `config.py`:
- `max_inventory_usdc: float` default `100.0` — maximum net inventory (one-sided) in USDC
- `max_capital_usdc: float` default `200.0` — maximum total capital deployed at any time
- `min_spread_ticks: int` default `1` — minimum spread (must be ≥1)
- `max_spread_ticks: int` default `10` — maximum spread
- `kill_switch_vol_threshold: float` default `0.05` — volatility ratio that triggers auto-pause (5%)
- Validator: `max_spread_ticks > min_spread_ticks`
- All numeric fields positive (gt=0)
</action>

<acceptance_criteria>
- `RiskConfig()` defaults: `max_inventory_usdc=100.0`, `max_capital_usdc=200.0`, `min_spread_ticks=1`, `max_spread_ticks=10`, `kill_switch_vol_threshold=0.05`
- `RiskConfig(min_spread_ticks=5, max_spread_ticks=3)` raises `ValidationError` (spread range invalid)
- `RiskConfig(max_inventory_usdc=0)` raises `ValidationError`
</acceptance_criteria>

---

### Task B4: Implement TelegramConfig

<read_first>
- `.planning/phases/01-project-foundation-config/01-CONTEXT.md` — D-08 TelegramConfig fields, D-11 required secrets
</read_first>

<action>
Implement `TelegramConfig` as a pydantic `BaseModel` in `config.py`:
- `bot_token: str` — required, no default (missing = fail-fast)
- `owner_chat_id: int` — required, no default (missing = fail-fast)

These fields have no default values, making them required. The pydantic-settings `Settings` parent class handles loading from env.
</action>

<acceptance_criteria>
- `TelegramConfig(bot_token="abc", owner_chat_id=123)` succeeds
- `TelegramConfig()` raises `ValidationError` naming `bot_token` as missing
- `TelegramConfig(bot_token="abc")` raises `ValidationError` naming `owner_chat_id` as missing
</acceptance_criteria>

---

### Task B5: Implement top-level Settings with secret handling and env loading

<read_first>
- `.planning/phases/01-project-foundation-config/01-CONTEXT.md` — D-08, D-10, D-11
- `.planning/phases/01-project-foundation-config/01-RESEARCH.md` — pydantic-settings setup, fail-fast pattern
- `.planning/research/STACK.md` — verified SDK: eth-account for wallet creation
</read_first>

<action>
Implement `Settings` as a pydantic-settings `BaseSettings` class in `config.py`:

Fields:
- `network_config: NetworkConfig` — embed with `model_validator` or `Field(default_factory=NetworkConfig)`; `NETWORK` env var maps to `network_config.network` via env alias or explicit field
- `trading: TradingConfig` — embed similarly
- `risk: RiskConfig` — embed similarly
- `telegram: TelegramConfig` — embed similarly
- `log_level: str` default `"INFO"` — `LOG_LEVEL` env var

Secret field — CRITICAL design:
- `agent_private_key: SecretStr` — required, no default; load from `AGENT_PRIVATE_KEY` env var using pydantic `SecretStr` type so the value is never printed in repr or logs
- After validation, expose a `agent_wallet` property (computed once) that returns an `eth_account.Account` object created from the private key. The `SecretStr` value is accessed only once via `.get_secret_value()` to create the wallet.

`model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore")`

For nested models, use `env_nested_delimiter='__'` OR use explicit `model_validator(mode='before')` to pluck the right env vars. Simpler approach: define each nested field directly in `Settings` as individual fields, then construct sub-models in a `@model_validator(mode='after')`. This avoids double-underscore notation in `.env`.

Implement `load_settings()` factory function:
```python
def load_settings() -> Settings:
    try:
        return Settings()
    except ValidationError as e:
        for error in e.errors():
            field = " -> ".join(str(loc) for loc in error["loc"])
            msg = error["msg"]
            print(f"Config error [{field}]: {msg}", file=sys.stderr)
        sys.exit(1)
```
</action>

<acceptance_criteria>
- `Settings` is a pydantic-settings `BaseSettings` subclass
- With env vars `AGENT_PRIVATE_KEY=0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80` (Hardhat test key — safe for testing) and `TELEGRAM_BOT_TOKEN=test:token`, `TELEGRAM_OWNER_CHAT_ID=123`, `Settings()` succeeds
- With `AGENT_PRIVATE_KEY` unset, `Settings()` raises `ValidationError`
- `repr(settings)` does NOT contain the raw private key value (SecretStr masks it)
- `settings.agent_wallet` returns an `eth_account.Account` object with a `.address` property
- `load_settings()` exits with code 1 when required fields are missing, printing field names to stderr
- `settings.network_config.api_url` returns the correct URL based on `NETWORK` env var
- Default `settings.trading.order_size_usdc == 10.0` when `ORDER_SIZE_USDC` env is not set
</acceptance_criteria>

---

### Task B6: Write config unit tests

<read_first>
- `src/mgw_mm/config.py` — the implementation just created
- `.planning/phases/01-project-foundation-config/01-RESEARCH.md` — Nyquist test coverage requirements
</read_first>

<action>
Create `tests/test_config.py` with unit tests using pytest and `monkeypatch` (or `os.environ` manipulation) to set env vars. Test cases:

1. `test_defaults_load` — set minimum required env vars; assert all D-09 defaults are correct values
2. `test_missing_agent_key_exits` — unset `AGENT_PRIVATE_KEY`; call `load_settings()`; assert `SystemExit` with code 1
3. `test_missing_telegram_token_exits` — unset `TELEGRAM_BOT_TOKEN`; assert `SystemExit`
4. `test_network_testnet_default` — with `NETWORK` unset; assert `settings.network_config.network == "testnet"` and `api_url` contains `testnet`
5. `test_network_mainnet` — with `NETWORK=mainnet`; assert `api_url == "https://api.hyperliquid.xyz"`
6. `test_network_invalid_rejected` — with `NETWORK=devnet`; assert `ValidationError` or `SystemExit`
7. `test_secret_not_in_repr` — assert raw private key string does not appear in `repr(settings)` or `str(settings)`
8. `test_agent_wallet_created` — assert `settings.agent_wallet.address` is a valid hex address (starts with `0x`, length 42)
9. `test_risk_defaults` — assert `max_inventory_usdc=100.0`, `max_capital_usdc=200.0`
10. `test_spread_validation` — assert `RiskConfig(min_spread_ticks=10, max_spread_ticks=5)` raises error

Use a Hardhat/Foundry test private key for test assertions: `0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80`
</action>

<acceptance_criteria>
- `tests/test_config.py` exists with all 10 test functions
- `pytest tests/test_config.py -v` exits 0 (all tests pass)
- No test imports real secrets or uses production-like keys
- Tests use `monkeypatch.setenv` or `pytest`'s `tmp_path` + `.env` file injection (not hardcoded os.environ modifications that persist)
</acceptance_criteria>

---

## Verification

```bash
# Run config tests
pytest tests/test_config.py -v

# Verify defaults without real .env
python -c "
import sys, os
sys.path.insert(0, 'src')
os.environ.setdefault('AGENT_PRIVATE_KEY', '0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80')
os.environ.setdefault('TELEGRAM_BOT_TOKEN', 'test:token')
os.environ.setdefault('TELEGRAM_OWNER_CHAT_ID', '123')
from mgw_mm.config import load_settings
s = load_settings()
assert s.trading.order_size_usdc == 10.0, f'Expected 10.0, got {s.trading.order_size_usdc}'
assert s.risk.max_inventory_usdc == 100.0
print('Config defaults verified OK')
"
```

## ## PLANNING COMPLETE
