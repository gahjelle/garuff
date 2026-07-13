"""branding.py derives every brand literal from NAME (the one-edit rebrand seam)."""

from garuff import branding


def test_program_name_derives_from_name() -> None:
    """The CLI program name follows NAME, so a rebrand is a one-line edit."""
    assert branding.PROGRAM_NAME == branding.NAME


def test_config_table_derives_from_name() -> None:
    """The `tool.<name>` config table follows NAME, so a rebrand stays one line."""
    assert f"tool.{branding.NAME}" == branding.CONFIG_TABLE


def test_config_table_path_splits_the_dotted_table() -> None:
    """CONFIG_TABLE_PATH is the dotted table split into keys for walking pyproject."""
    assert branding.CONFIG_TABLE_PATH == ["tool", branding.NAME]


def test_directive_marker_derives_from_name() -> None:
    """The inline directive is namespaced by NAME, so a rebrand renames it too."""
    assert f"{branding.NAME}: ignore" == branding.DIRECTIVE_MARKER
