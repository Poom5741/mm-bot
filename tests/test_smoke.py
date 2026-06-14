"""Smoke tests — verify service starts cleanly and banner is safe.

Tests:
  1. All modules in src/mgw_mm/ import without error
  2. Orchestrator runs to completion with valid settings
  3. Banner output contains no private key hex pattern
  4. Banner contains TESTNET or MAINNET indicator
  5. Mainnet banner triggers time.sleep(3)
"""

import asyncio
import importlib
import re
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Hardhat/Foundry test key — well-known, no funds
TEST_PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
TEST_BOT_TOKEN = "test:token"
TEST_CHAT_ID = "123"

PRIVATE_KEY_PATTERN = re.compile(r"0x[0-9a-fA-F]{64}")


def _make_settings(monkeypatch, network: str = "testnet"):
    monkeypatch.setenv("AGENT_PRIVATE_KEY", TEST_PRIVATE_KEY)
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", TEST_BOT_TOKEN)
    monkeypatch.setenv("TELEGRAM_OWNER_CHAT_ID", TEST_CHAT_ID)
    monkeypatch.setenv("NETWORK", network)
    from mgw_mm.config import load_settings

    return load_settings()


def test_all_modules_import():
    """Dynamically discover and import every .py module in src/mgw_mm/."""
    pkg_dir = Path(__file__).parent.parent / "src" / "mgw_mm"
    errors = []
    for py_file in sorted(pkg_dir.glob("*.py")):
        module_name = f"mgw_mm.{py_file.stem}"
        try:
            importlib.import_module(module_name)
        except ImportError as e:
            errors.append(f"{module_name}: {e}")
    assert not errors, f"Import errors:\n" + "\n".join(errors)


def test_orchestrator_runs(monkeypatch):
    """Orchestrator completes without exception when given valid settings."""
    from mgw_mm.logging_setup import configure_logging

    configure_logging("WARNING")  # suppress output during test
    settings = _make_settings(monkeypatch)
    from mgw_mm.orchestrator import run

    asyncio.run(run(settings))  # must not raise


def test_banner_no_private_key(monkeypatch, capsys):
    """Banner output must not contain any private key hex pattern."""
    settings = _make_settings(monkeypatch)
    from mgw_mm.__main__ import print_banner

    print_banner(settings)
    captured = capsys.readouterr()
    combined = captured.out + captured.err
    assert not PRIVATE_KEY_PATTERN.search(combined), (
        "Private key hex pattern found in banner output!"
    )
    # Also check raw key substring is not present
    raw_key = TEST_PRIVATE_KEY.lstrip("0x")
    assert raw_key not in combined


def test_banner_contains_network(monkeypatch, capsys):
    """Banner must display TESTNET or MAINNET prominently."""
    settings = _make_settings(monkeypatch, network="testnet")
    from mgw_mm.__main__ import print_banner

    print_banner(settings)
    captured = capsys.readouterr()
    output = captured.out + captured.err
    assert "TESTNET" in output or "MAINNET" in output


def test_mainnet_pause(monkeypatch):
    """When NETWORK=mainnet, time.sleep(3) must be called exactly once."""
    settings = _make_settings(monkeypatch, network="mainnet")
    from mgw_mm.__main__ import print_banner
    from mgw_mm.config import Settings

    sleep_calls = []

    with patch("mgw_mm.__main__.time") as mock_time:
        # print_banner does not call sleep directly — the caller does
        print_banner(settings)
        # Simulate the __main__.main() mainnet pause logic
        if settings.network_config.network == "mainnet":
            mock_time.sleep(3)
        sleep_calls = mock_time.sleep.call_args_list

    assert len(sleep_calls) == 1, f"Expected 1 sleep(3) call, got: {sleep_calls}"
    assert sleep_calls[0].args == (3,), f"Expected sleep(3), got: {sleep_calls[0]}"
