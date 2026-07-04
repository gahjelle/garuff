"""Smoke test: the package imports cleanly."""

import garuff


def test_smoke() -> None:
    """Test that garuff exposes its entry point."""
    assert callable(garuff.main)
