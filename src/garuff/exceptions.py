"""garuff's exception hierarchy — every custom error derives from GaruffException."""


class GaruffException(Exception):  # noqa: N818 — base is deliberately "Exception"
    """Base class for every error garuff raises."""


class ProjectNotFoundError(GaruffException):
    """No pyproject.toml was found walking up from the starting directory."""


class DuplicateRuleCodeError(GaruffException):
    """Two rules were registered under the same code."""


class UnknownRuleCodeError(GaruffException):
    """A rule code was requested that no registered rule provides."""
