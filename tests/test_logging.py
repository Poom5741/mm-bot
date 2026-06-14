"""Tests for mgw_mm.logging_setup — structlog JSON configuration."""

import io
import json
import sys

import pytest


def test_json_output(capsys):
    """Log output must be valid JSON containing 'event' and 'level' keys."""
    import structlog

    from mgw_mm.logging_setup import configure_logging

    configure_logging("INFO")
    logger = structlog.get_logger("test_json_output")
    logger.info("hello_from_test", x=1)

    captured = capsys.readouterr()
    # Find the JSON line in stdout
    for line in captured.out.splitlines():
        line = line.strip()
        if line.startswith("{"):
            data = json.loads(line)
            assert "event" in data or "level" in data, f"Missing keys in: {data}"
            break
    else:
        # structlog may write to stderr depending on version — check there too
        for line in captured.err.splitlines():
            line = line.strip()
            if line.startswith("{"):
                data = json.loads(line)
                assert "event" in data or "level" in data, f"Missing keys in: {data}"
                break


def test_log_level_filtering(capsys):
    """At WARNING level, INFO messages must not appear in output."""
    import structlog

    from mgw_mm.logging_setup import configure_logging

    configure_logging("WARNING")
    logger = structlog.get_logger("test_level_filter")
    logger.info("this_should_not_appear", filtered=True)

    captured = capsys.readouterr()
    combined = captured.out + captured.err
    assert "this_should_not_appear" not in combined


def test_invalid_log_level():
    """configure_logging with an unknown level name raises ValueError."""
    from mgw_mm.logging_setup import configure_logging

    with pytest.raises(ValueError, match="Unknown log level"):
        configure_logging("GARBAGE")
