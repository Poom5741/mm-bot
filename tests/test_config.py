"""Unit tests for mgw_mm.config — typed pydantic-settings configuration.

Uses the Hardhat/Foundry test private key for wallet assertions:
  0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80
This is a well-known public test key with no funds — safe to use in tests.
"""

import pytest
from pydantic import ValidationError

# Hardhat/Foundry test private key — well-known, no funds
TEST_PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
TEST_BOT_TOKEN = "test:token"
TEST_CHAT_ID = "123"


def _set_required(monkeypatch):
    """Set all required env vars to valid test values."""
    monkeypatch.setenv("AGENT_PRIVATE_KEY", TEST_PRIVATE_KEY)
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", TEST_BOT_TOKEN)
    monkeypatch.setenv("TELEGRAM_OWNER_CHAT_ID", TEST_CHAT_ID)


# ---------------------------------------------------------------------------
# NetworkConfig tests
# ---------------------------------------------------------------------------


def test_network_config_testnet_default():
    from mgw_mm.config import NetworkConfig

    cfg = NetworkConfig()
    assert cfg.network == "testnet"
    assert cfg.api_url == "https://api.hyperliquid-testnet.xyz"


def test_network_config_mainnet():
    from mgw_mm.config import NetworkConfig

    cfg = NetworkConfig(network="mainnet")
    assert cfg.api_url == "https://api.hyperliquid.xyz"


def test_network_config_invalid_rejected():
    from mgw_mm.config import NetworkConfig

    with pytest.raises(ValidationError):
        NetworkConfig(network="devnet")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# TradingConfig tests
# ---------------------------------------------------------------------------


def test_trading_defaults():
    from mgw_mm.config import TradingConfig

    cfg = TradingConfig()
    assert cfg.order_size_usdc == 10.0
    assert cfg.tick_offset == 2
    assert cfg.quote_interval_sec == 30.0
    assert cfg.target_pair == "PURR/USDC"


def test_trading_rejects_zero_size():
    from mgw_mm.config import TradingConfig

    with pytest.raises(ValidationError):
        TradingConfig(order_size_usdc=0)


def test_trading_rejects_negative_tick():
    from mgw_mm.config import TradingConfig

    with pytest.raises(ValidationError):
        TradingConfig(tick_offset=-1)


# ---------------------------------------------------------------------------
# RiskConfig tests
# ---------------------------------------------------------------------------


def test_risk_defaults(monkeypatch, tmp_path):
    from mgw_mm.config import RiskConfig

    cfg = RiskConfig()
    assert cfg.max_inventory_usdc == 100.0
    assert cfg.max_capital_usdc == 200.0
    assert cfg.min_spread_ticks == 1
    assert cfg.max_spread_ticks == 10
    assert cfg.kill_switch_vol_threshold == 0.05


def test_risk_defaults_via_settings(monkeypatch):
    _set_required(monkeypatch)
    from mgw_mm.config import load_settings

    s = load_settings()
    assert s.risk.max_inventory_usdc == 100.0
    assert s.risk.max_capital_usdc == 200.0


def test_spread_validation():
    from mgw_mm.config import RiskConfig

    with pytest.raises(ValidationError):
        RiskConfig(min_spread_ticks=5, max_spread_ticks=3)


def test_spread_equal_rejected():
    from mgw_mm.config import RiskConfig

    with pytest.raises(ValidationError):
        RiskConfig(min_spread_ticks=5, max_spread_ticks=5)


def test_risk_rejects_zero_inventory():
    from mgw_mm.config import RiskConfig

    with pytest.raises(ValidationError):
        RiskConfig(max_inventory_usdc=0)


# ---------------------------------------------------------------------------
# TelegramConfig tests
# ---------------------------------------------------------------------------


def test_telegram_config_valid():
    from mgw_mm.config import TelegramConfig

    cfg = TelegramConfig(bot_token="abc", owner_chat_id=123)
    assert cfg.bot_token == "abc"
    assert cfg.owner_chat_id == 123


def test_telegram_config_missing_token():
    from mgw_mm.config import TelegramConfig

    with pytest.raises((ValidationError, TypeError)):
        TelegramConfig(owner_chat_id=123)  # type: ignore[call-arg]


def test_telegram_config_missing_chat_id():
    from mgw_mm.config import TelegramConfig

    with pytest.raises((ValidationError, TypeError)):
        TelegramConfig(bot_token="abc")  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# Settings / load_settings tests
# ---------------------------------------------------------------------------


def test_defaults_load(monkeypatch):
    """With minimum required env vars, all D-09 defaults are present."""
    _set_required(monkeypatch)
    from mgw_mm.config import load_settings

    s = load_settings()
    assert s.trading.order_size_usdc == 10.0
    assert s.trading.tick_offset == 2
    assert s.trading.quote_interval_sec == 30.0
    assert s.risk.max_inventory_usdc == 100.0
    assert s.risk.max_capital_usdc == 200.0


def test_missing_agent_key_exits(monkeypatch):
    """Missing AGENT_PRIVATE_KEY causes load_settings() to sys.exit(1)."""
    monkeypatch.delenv("AGENT_PRIVATE_KEY", raising=False)
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", TEST_BOT_TOKEN)
    monkeypatch.setenv("TELEGRAM_OWNER_CHAT_ID", TEST_CHAT_ID)
    from mgw_mm.config import load_settings

    with pytest.raises(SystemExit) as exc_info:
        load_settings()
    assert exc_info.value.code == 1


def test_missing_telegram_token_exits(monkeypatch):
    """Missing TELEGRAM_BOT_TOKEN causes load_settings() to sys.exit(1)."""
    monkeypatch.setenv("AGENT_PRIVATE_KEY", TEST_PRIVATE_KEY)
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.setenv("TELEGRAM_OWNER_CHAT_ID", TEST_CHAT_ID)
    from mgw_mm.config import load_settings

    with pytest.raises(SystemExit) as exc_info:
        load_settings()
    assert exc_info.value.code == 1


def test_network_testnet_default(monkeypatch):
    """Without NETWORK env var, defaults to testnet."""
    _set_required(monkeypatch)
    monkeypatch.delenv("NETWORK", raising=False)
    from mgw_mm.config import load_settings

    s = load_settings()
    assert s.network_config.network == "testnet"
    assert "testnet" in s.network_config.api_url


def test_network_mainnet(monkeypatch):
    """NETWORK=mainnet resolves to mainnet API URL."""
    _set_required(monkeypatch)
    monkeypatch.setenv("NETWORK", "mainnet")
    from mgw_mm.config import load_settings

    s = load_settings()
    assert s.network_config.api_url == "https://api.hyperliquid.xyz"


def test_network_invalid_rejected(monkeypatch):
    """NETWORK=devnet causes exit or ValidationError."""
    _set_required(monkeypatch)
    monkeypatch.setenv("NETWORK", "devnet")
    from mgw_mm.config import load_settings

    with pytest.raises((SystemExit, Exception)):
        load_settings()


def test_secret_not_in_repr(monkeypatch):
    """Raw private key must not appear in repr(settings) or str(settings)."""
    _set_required(monkeypatch)
    from mgw_mm.config import load_settings

    s = load_settings()
    raw_key = TEST_PRIVATE_KEY.lstrip("0x")
    assert raw_key not in repr(s)
    assert raw_key not in str(s)
    assert TEST_PRIVATE_KEY not in repr(s)
    assert TEST_PRIVATE_KEY not in str(s)


def test_agent_wallet_created(monkeypatch):
    """settings.agent_wallet returns an Account with a valid hex .address."""
    _set_required(monkeypatch)
    from mgw_mm.config import load_settings

    s = load_settings()
    wallet = s.agent_wallet
    assert hasattr(wallet, "address")
    address = wallet.address
    assert isinstance(address, str)
    assert address.startswith("0x")
    assert len(address) == 42
