"""garuff's exception hierarchy — every custom error derives from GaruffError."""


class GaruffError(Exception):
    """Base class for every error garuff raises."""


class ProjectNotFoundError(GaruffError):
    """No pyproject.toml was found walking up from the starting directory."""


class DuplicateRuleCodeError(GaruffError):
    """Two rules were registered under the same code."""


class UnknownRuleCodeError(GaruffError):
    """A rule code was requested that no registered rule provides."""


class ConfigError(GaruffError):
    """The tool's configuration table is invalid; linting must not proceed."""
