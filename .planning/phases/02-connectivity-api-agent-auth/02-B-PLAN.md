---
plan: 02-B
title: "HyperliquidClient Implementation"
wave: 1
depends_on: []
phase: 2
requirements:
  - CON-01
  - CON-02
files_modified:
  - src/mgw_mm/exchange.py
autonomous: true
---

# Plan 02-B: HyperliquidClient Implementation

## Objective

Implement `HyperliquidClient` in `src/mgw_mm/exchange.py` — replacing the Phase 1 stub. The class owns both `Info` and `Exchange` (D-13, D-14, D-15), constructs them from `Settings`, and provides the connection interface that all other phases will use.

## Context

The existing stub is:
```python
class HyperliquidClient:
    def __init__(self, config: Any = None) -> None:
        self.config = config
        # TODO: implement in Phase 2
```

This plan implements the constructor, exposes `self.info` and `self.exchange`, and provides a `probe_auth()` method for the startup connectivity check (consumed by Plan 02-C). The Exchange SDK constructor is `Exchange(agent_wallet, base_url, account_address=main_wallet_address)`.

## Tasks

---

### Task B-1: Implement `HyperliquidClient.__init__`

<read_first>
- `src/mgw_mm/exchange.py` — read the current stub before replacing it
- `src/mgw_mm/config.py` — read `Settings`, `NetworkConfig.api_url`, and `Settings.agent_wallet` property (returns `eth_account.Account` object); read `Settings.main_wallet_address` (added in Plan 02-A)
- `.venv/lib/python3.11/site-packages/hyperliquid/exchange.py` — read `Exchange.__init__` signature (lines 83–99): `Exchange(wallet: LocalAccount, base_url: Optional[str], ..., account_address: Optional[str], ...)` 
- `.venv/lib/python3.11/site-packages/hyperliquid/info.py` — read `Info.__init__` signature (lines 17–71): `Info(base_url, skip_ws=False, ...)`; note `skip_ws=True` is needed for bot use (no WebSocket needed in Phase 2)
- `.planning/research/STACK.md` — verified API facts for constructor patterns
</read_first>

<action>
Replace the stub in `src/mgw_mm/exchange.py` with a full implementation. Do NOT keep the `config: Any` parameter — use `settings: Settings` with proper type annotation.

Imports to add at top of file:
```python
from hyperliquid.info import Info
from hyperliquid.exchange import Exchange as HLExchange
from hyperliquid.utils.error import ClientError, ServerError
from mgw_mm.config import Settings
```

The class body:

```python
class HyperliquidClient:
    """Wraps Hyperliquid Info and Exchange SDK objects for spot trading.

    Owns both Info (read-only queries) and Exchange (signed L1 actions).
    All phases that need exchange access go through this class.

    Attributes:
        info: Info — read-only queries (L2 book, balances, metadata)
        exchange: Exchange — signed actions (order, cancel, approve_agent)
    """

    def __init__(self, settings: Settings) -> None:
        """Construct Info + Exchange from settings.

        Args:
            settings: Fully validated Settings from load_settings().
        """
        api_url = settings.network_config.api_url
        agent_wallet = settings.agent_wallet  # eth_account.Account
        main_wallet_address = settings.main_wallet_address

        logger.info(
            "hyperliquid_client_init",
            network=settings.network_config.network,
            api_url=api_url,
            main_wallet=f"{main_wallet_address[:6]}...{main_wallet_address[-4:]}",
        )

        # Info: read-only queries; skip_ws=True avoids a background WebSocket
        # thread that would complicate the asyncio event loop in later phases.
        self.info: Info = Info(base_url=api_url, skip_ws=True)

        # Exchange: signed L1 actions (order, cancel, etc.)
        # account_address routes signed actions to the main wallet's account
        # even though the signing key is the agent key. This is the API Agent
        # pattern from the SDK docs (D-15).
        self.exchange: HLExchange = HLExchange(
            wallet=agent_wallet,
            base_url=api_url,
            account_address=main_wallet_address,
        )

        logger.info("hyperliquid_client_ready", status="connected")
```

Keep the existing `logger = structlog.get_logger(__name__)` line at module level.

Do NOT expose the agent wallet, api_url, or main_wallet_address as public instance attributes beyond `self.info` and `self.exchange`. The Settings object should NOT be stored as `self.config` or `self.settings`.
</action>

<acceptance_criteria>
- `src/mgw_mm/exchange.py` no longer contains `# TODO: implement in Phase 2`
- `HyperliquidClient.__init__` accepts `settings: Settings` (not `config: Any`)
- `self.info` is set to a `hyperliquid.info.Info` instance with `skip_ws=True`
- `self.exchange` is set to a `hyperliquid.exchange.Exchange` instance with `account_address=main_wallet_address`
- The `exchange` is constructed with `wallet=agent_wallet` (from `settings.agent_wallet`) and `base_url=api_url`
- Two `logger.info` calls are present: `hyperliquid_client_init` and `hyperliquid_client_ready`
- The log line for `hyperliquid_client_init` includes `main_wallet` with the truncated pattern `{addr[:6]}...{addr[-4:]}`
- `python3 -m py_compile src/mgw_mm/exchange.py` exits 0
- `ClientError` and `ServerError` are imported from `hyperliquid.utils.error` (needed by Plan 02-C's `probe_auth`)
</acceptance_criteria>

---

### Task B-2: Add `probe_auth()` Method to `HyperliquidClient`

<read_first>
- `src/mgw_mm/exchange.py` — read the updated file from Task B-1
- `.venv/lib/python3.11/site-packages/hyperliquid/info.py` — find `spot_user_state` method; it accepts an address string and returns a dict with `"balances"` key
- `.venv/lib/python3.11/site-packages/hyperliquid/utils/error.py` — `ClientError` and `ServerError` class definitions
- `.planning/phases/02-connectivity-api-agent-auth/02-CONTEXT.md` — D-09 for probe spec; D-10 for exception classes
</read_first>

<action>
Add `probe_auth(self) -> None` method to `HyperliquidClient`. This method is called once on startup (before entering the quoting loop). It confirms connectivity and that the main wallet address is reachable.

Method behavior:
1. Call `self.info.spot_user_state(self.exchange.account_address)` — read-only, no signing.
2. If the call returns a response (any dict), log `auth_probe_ok` at INFO level with `network`, `main_wallet` (truncated), and `balances_count` (number of entries in `response["balances"]` — may be 0 for an empty wallet, which is fine).
3. If the call raises `ClientError`, `ServerError`, or any `Exception`, log `auth_probe_failed` at ERROR level with `error=str(e)` and then re-raise the exception so the caller can handle it and exit.

The method must NOT attempt any signed action (no order, no noop) — read-only probe only (per D-09 "read-only is safer").

```python
def probe_auth(self) -> None:
    """Startup connectivity and auth probe (read-only).

    Calls spot_user_state() on the main wallet address to confirm
    the Info endpoint is reachable and the address is valid.

    Raises:
        ClientError: on API-level rejection (4xx)
        ServerError: on server-side failure (5xx)
        Exception: on network/timeout errors
    """
```
</action>

<acceptance_criteria>
- `HyperliquidClient.probe_auth` method exists in `src/mgw_mm/exchange.py`
- Method calls `self.info.spot_user_state(self.exchange.account_address)` — not a signed call
- On success: `logger.info("auth_probe_ok", ...)` is called with `network`, `main_wallet` (truncated), and `balances_count`
- On any exception: `logger.error("auth_probe_failed", error=str(e))` is called and the exception is re-raised
- The method signature is `def probe_auth(self) -> None:`
- `python3 -m py_compile src/mgw_mm/exchange.py` exits 0 after this task
</acceptance_criteria>

---

### Task B-3: Unit Tests for `HyperliquidClient`

<read_first>
- `tests/test_config.py` — read for fixture patterns (`monkeypatch`, env var mocking) to replicate in the new test file
- `src/mgw_mm/exchange.py` — read the final file from Tasks B-1 and B-2
- `tests/__init__.py` — verify it exists (empty is fine)
</read_first>

<action>
Create `tests/test_exchange.py` with unit tests for `HyperliquidClient`. All tests must mock the SDK imports — do NOT make real network calls.

Use `unittest.mock.patch` or `pytest-monkeypatch` to mock:
- `hyperliquid.info.Info.__init__` → returns None (constructor no-op)
- `hyperliquid.exchange.Exchange.__init__` → returns None (constructor no-op)
- `hyperliquid.info.Info.spot_user_state` → returns `{"balances": []}` (empty wallet)

Tests to implement:

**test_client_init_stores_info_and_exchange**:
- Construct `HyperliquidClient(settings)` with a minimal mock Settings
- Assert `client.info` is not None
- Assert `client.exchange` is not None

**test_client_init_uses_agent_wallet_and_main_address**:
- Mock `HLExchange.__init__` to capture constructor kwargs
- Assert it was called with `account_address=settings.main_wallet_address`
- Assert it was called with `wallet=settings.agent_wallet`

**test_client_init_uses_api_url**:
- Mock `Info.__init__` to capture constructor args
- Assert it was called with `base_url=settings.network_config.api_url`
- Assert `skip_ws=True` was passed

**test_probe_auth_ok_logs_balances**:
- Mock `self.info.spot_user_state` to return `{"balances": [{"coin": "USDC", "total": "100"}]}`
- Call `client.probe_auth()`
- Assert no exception raised

**test_probe_auth_raises_client_error**:
- Mock `self.info.spot_user_state` to raise `ClientError(400, None, "invalid address", {})`
- Assert `client.probe_auth()` raises `ClientError`

**test_probe_auth_raises_server_error**:
- Mock `self.info.spot_user_state` to raise `ServerError(500, "internal error")`
- Assert `client.probe_auth()` raises `ServerError`

Fixture for Settings mock:
```python
@pytest.fixture
def mock_settings(monkeypatch):
    # Return a simple namespace or MagicMock with the required attributes
    ...
```
</action>

<acceptance_criteria>
- `tests/test_exchange.py` exists
- `PYTHONPATH=src python -m pytest tests/test_exchange.py -q` exits 0 with all 6 tests passing
- No real network calls are made (all Info/Exchange constructors are mocked)
- `test_probe_auth_raises_client_error` and `test_probe_auth_raises_server_error` pass — confirming the re-raise behavior
</acceptance_criteria>

---

## Verification

```bash
# Syntax check
python3 -m py_compile src/mgw_mm/exchange.py

# Unit tests — no network
PYTHONPATH=src python -m pytest tests/test_exchange.py -q

# All tests still pass
PYTHONPATH=src python -m pytest tests/ -q
```

## must_haves

```yaml
truths:
  - "HyperliquidClient.__init__ accepts Settings, not Any"
  - "self.info is Info(base_url=api_url, skip_ws=True)"
  - "self.exchange is Exchange(wallet=agent_wallet, base_url=api_url, account_address=main_wallet_address)"
  - "probe_auth() calls info.spot_user_state(account_address) — read-only, no signed action"
  - "probe_auth() re-raises on any exception after logging auth_probe_failed"
  - "Unit tests mock all SDK constructors — no real network calls"
  - "Both ClientError and ServerError from hyperliquid.utils.error are imported and handled"
```
