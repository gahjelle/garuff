"""The tool's brand identity — the single edit point for a rebranded fork.

garuff's engine is opinion-agnostic (see ADR-0005). A rebranded (Level B) fork
renames the package directory by hand, then edits NAME here; every in-code brand
literal derives from NAME, so the rebrand stays a one-line change. As the config
table (#4) and inline directive (#5) land, each derives its literal from NAME.
"""

NAME = "garuff"
"""The tool's name — the one literal a rebranded fork edits."""

PROGRAM_NAME = NAME
"""The CLI program name (argparse `prog`); equals NAME by derivation."""

CONFIG_TABLE = f"tool.{NAME}"
"""The dotted config table config is read from (`tool.<name>`), derived from NAME."""

CONFIG_TABLE_PATH = CONFIG_TABLE.split(".")
"""CONFIG_TABLE split into keys, for walking into the parsed `pyproject.toml`."""
