"""branding.py derives every brand literal from NAME (the one-edit rebrand seam)."""

from garuff import branding


def test_program_name_derives_from_name() -> None:
    """The CLI program name follows NAME, so a rebrand is a one-line edit."""
    assert branding.PROGRAM_NAME == branding.NAME
