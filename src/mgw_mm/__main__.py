"""Entry point for the MGW/USDC Market-Maker Bot.

Run with:
    python -m mgw_mm

Startup sequence (order is critical):
    1. Load config (fail-fast if secrets missing — before any logging)
    2. Configure structured logging (after config so log_level is known)
    3. Print startup banner (human-readable, to stdout, before JSON logs)
    4. Mainnet 3-second pause (if NETWORK=mainnet)
    5. Run async orchestrator
"""

import asyncio
import sys
import time


# ---------------------------------------------------------------------------
# Startup banner
# ---------------------------------------------------------------------------


def print_banner(settings) -> None:  # type: ignore[no-untyped-def]
    """Print ASCII startup banner to stdout.

    Shows network, pair, order sizing, and risk caps.
    Does NOT show the agent wallet address or any secret values (D-13).
    When NETWORK=mainnet, prepends a prominent WARNING block (D-14).
    """
    from mgw_mm import __version__

    network = settings.network_config.network.upper()
    pair = settings.trading.target_pair
    order_size = settings.trading.order_size_usdc
    tick_offset = settings.trading.tick_offset
    max_inv = settings.risk.max_inventory_usdc
    max_cap = settings.risk.max_capital_usdc

    # Mainnet warning block — printed BEFORE the banner box (D-14)
    if settings.network_config.network == "mainnet":
        print()
        print("!" * 54)
        print("!!  WARNING: MAINNET MODE — REAL FUNDS AT RISK       !!")
        print("!!  Verify all settings before the bot starts trading !!")
        print("!" * 54)
        print()

    # ASCII banner box
    width = 42
    border_top = "╔" + "═" * width + "╗"
    border_sep = "╠" + "═" * width + "╣"
    border_bot = "╚" + "═" * width + "╝"

    def row(label: str, value: str) -> str:
        content = f"  {label:<14}{value}"
        padded = content.ljust(width)
        return f"║{padded}║"

    title = f"  MGW/USDC Market-Maker Bot v{__version__}"
    title_padded = title.ljust(width)

    print(border_top)
    print(f"║{title_padded}║")
    print(border_sep)
    print(row("NETWORK:", network))
    print(row("PAIR:", pair))
    print(row("ORDER SIZE:", f"{order_size:.2f} USDC"))
    print(row("TICK OFFSET:", str(tick_offset)))
    print(row("MAX INV:", f"{max_inv:.2f} USDC"))
    print(row("MAX CAPITAL:", f"{max_cap:.2f} USDC"))
    print(border_bot)
    print()


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Load config, configure logging, print banner, and run orchestrator."""
    # 1. Load config first — fail-fast exits here if secrets are missing
    from mgw_mm.config import load_settings

    settings = load_settings()

    # 2. Configure logging — must happen before any structlog calls
    from mgw_mm.logging_setup import configure_logging

    configure_logging(settings.log_level)

    # 3. Print human-readable startup banner (switches to JSON logs after this)
    print_banner(settings)

    # 4. Mainnet safety pause — 3 seconds of intentional friction (D-14)
    if settings.network_config.network == "mainnet":
        time.sleep(3)

    # 5. Run the async orchestrator event loop
    from mgw_mm.orchestrator import run

    asyncio.run(run(settings))


if __name__ == "__main__":
    main()
