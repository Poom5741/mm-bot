"""Typed configuration system for the MGW/USDC Market-Maker Bot.

Loads all configuration from environment variables / .env file using
pydantic-settings. Missing required secrets (AGENT_PRIVATE_KEY,
TELEGRAM_BOT_TOKEN) cause a fail-fast exit with a clear error message.

Config sections:
    NetworkConfig  — NETWORK field, API URL selection
    TradingConfig  — pair, order size, tick offset, quote interval
    RiskConfig     — inventory caps, spread limits, kill-switch threshold
    TelegramConfig — bot token and owner chat ID
    Settings       — composes all sections; loaded from .env

Usage:
    from mgw_mm.config import load_settings
    settings = load_settings()
"""

import sys
from typing import Literal

from eth_account import Account
from pydantic import BaseModel, Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# ---------------------------------------------------------------------------
# Sub-models (BaseModel, not BaseSettings — they are embedded in Settings)
# ---------------------------------------------------------------------------


class NetworkConfig(BaseModel):
    """Network selection: testnet or mainnet, with derived API URL."""

    network: Literal["testnet", "mainnet"] = "testnet"

    @property
    def api_url(self) -> str:
        """Return the Hyperliquid REST endpoint for the active network."""
        if self.network == "mainnet":
            return "https://api.hyperliquid.xyz"
        return "https://api.hyperliquid-testnet.xyz"


class TradingConfig(BaseModel):
    """Trading parameters: pair, size, tick offset, and quote cadence."""

    target_pair: str = "PURR/USDC"
    order_size_usdc: float = Field(default=10.0, gt=0)
    tick_offset: int = Field(default=2, gt=0)
    quote_interval_sec: float = Field(default=30.0, gt=0)


class RiskConfig(BaseModel):
    """Risk limits: inventory caps, spread bounds, and kill-switch threshold."""

    max_inventory_usdc: float = Field(default=100.0, gt=0)
    max_capital_usdc: float = Field(default=200.0, gt=0)
    min_spread_ticks: int = Field(default=1, gt=0)
    max_spread_ticks: int = Field(default=10, gt=0)
    kill_switch_vol_threshold: float = Field(default=0.05, gt=0)

    @model_validator(mode="after")
    def spread_range_valid(self) -> "RiskConfig":
        if self.max_spread_ticks <= self.min_spread_ticks:
            raise ValueError(
                f"max_spread_ticks ({self.max_spread_ticks}) must be greater than "
                f"min_spread_ticks ({self.min_spread_ticks})"
            )
        return self


class TelegramConfig(BaseModel):
    """Telegram credentials: bot token and owner chat ID (both required)."""

    bot_token: str
    owner_chat_id: int


# ---------------------------------------------------------------------------
# Top-level Settings — handles env file loading and secret management
# ---------------------------------------------------------------------------


class Settings(BaseSettings):
    """Top-level configuration loaded from environment variables / .env file.

    Required secrets (fail-fast if missing):
        AGENT_PRIVATE_KEY — the bot wallet agent private key (hex, 0x-prefixed)
        TELEGRAM_BOT_TOKEN — Telegram bot token from @BotFather
        TELEGRAM_OWNER_CHAT_ID — Telegram chat ID of the operator
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Network ---
    network: Literal["testnet", "mainnet"] = "testnet"

    # --- Trading ---
    target_pair: str = "PURR/USDC"
    order_size_usdc: float = Field(default=10.0, gt=0)
    tick_offset: int = Field(default=2, gt=0)
    quote_interval_sec: float = Field(default=30.0, gt=0)

    # --- Risk ---
    max_inventory_usdc: float = Field(default=100.0, gt=0)
    max_capital_usdc: float = Field(default=200.0, gt=0)
    min_spread_ticks: int = Field(default=1, gt=0)
    max_spread_ticks: int = Field(default=10, gt=0)
    kill_switch_vol_threshold: float = Field(default=0.05, gt=0)

    # --- Telegram ---
    telegram_bot_token: str
    telegram_owner_chat_id: int

    # --- Logging ---
    log_level: str = "INFO"

    # --- Secrets (SecretStr prevents raw value appearing in repr/logs) ---
    agent_private_key: SecretStr

    # --- Computed sub-models (built from flat fields after validation) ---
    _network_config: NetworkConfig | None = None
    _trading: TradingConfig | None = None
    _risk: RiskConfig | None = None
    _telegram: TelegramConfig | None = None
    _agent_wallet: object | None = None

    @model_validator(mode="after")
    def build_sub_models(self) -> "Settings":
        """Construct typed sub-models and the agent wallet from flat env fields."""
        object.__setattr__(self, "_network_config", NetworkConfig(network=self.network))
        object.__setattr__(
            self,
            "_trading",
            TradingConfig(
                target_pair=self.target_pair,
                order_size_usdc=self.order_size_usdc,
                tick_offset=self.tick_offset,
                quote_interval_sec=self.quote_interval_sec,
            ),
        )
        # Build RiskConfig — will raise ValidationError if spread range invalid
        object.__setattr__(
            self,
            "_risk",
            RiskConfig(
                max_inventory_usdc=self.max_inventory_usdc,
                max_capital_usdc=self.max_capital_usdc,
                min_spread_ticks=self.min_spread_ticks,
                max_spread_ticks=self.max_spread_ticks,
                kill_switch_vol_threshold=self.kill_switch_vol_threshold,
            ),
        )
        object.__setattr__(
            self,
            "_telegram",
            TelegramConfig(
                bot_token=self.telegram_bot_token,
                owner_chat_id=self.telegram_owner_chat_id,
            ),
        )
        # Build agent wallet from the secret key — accessed exactly once here
        raw_key = self.agent_private_key.get_secret_value()
        object.__setattr__(self, "_agent_wallet", Account.from_key(raw_key))
        return self

    @property
    def network_config(self) -> NetworkConfig:
        """Typed network config sub-model."""
        assert self._network_config is not None
        return self._network_config

    @property
    def trading(self) -> TradingConfig:
        """Typed trading config sub-model."""
        assert self._trading is not None
        return self._trading

    @property
    def risk(self) -> RiskConfig:
        """Typed risk config sub-model."""
        assert self._risk is not None
        return self._risk

    @property
    def telegram(self) -> TelegramConfig:
        """Typed Telegram config sub-model."""
        assert self._telegram is not None
        return self._telegram

    @property
    def agent_wallet(self) -> object:
        """eth_account.Account object created from the agent private key."""
        assert self._agent_wallet is not None
        return self._agent_wallet


def load_settings() -> Settings:
    """Load and validate settings from environment / .env file.

    On validation failure: prints each missing/invalid field to stderr
    and exits with code 1. Never returns a partially-configured Settings.
    """
    from pydantic import ValidationError

    try:
        return Settings()
    except ValidationError as e:
        print("Configuration errors — fix these before starting:", file=sys.stderr)
        for error in e.errors():
            field = " -> ".join(str(loc) for loc in error["loc"])
            msg = error["msg"]
            print(f"  [{field}]: {msg}", file=sys.stderr)
        sys.exit(1)
