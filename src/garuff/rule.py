"""Rule base classes — the self-describing unit garuff enforces.

`Rule` holds the scope-independent identity and explanation; each scope subclass
adds a `check` for the kind of input it consumes. See ADR-0003.
"""

import abc
from dataclasses import asdict, dataclass
from inspect import cleandoc
from pathlib import Path
from string import Template
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    import ast
    from collections.abc import Iterator

    from garuff.schemas import Edit, Violation


@dataclass(kw_only=True)
class Explanation:
    """A rule's agent-facing text, with its option values substituted in."""

    code: str
    summary: str
    rationale: str
    fix: str


@dataclass(kw_only=True)
class Rule:
    """A single convention garuff enforces, identified by a stable code.

    Carries the rule's agent-facing text in three required parts: `summary`
    (the terse default per-violation line), `rationale` (why the convention
    exists), and `fix` (the prescribed correct form). All three are
    `inspect.cleandoc`-normalized in `__post_init__`, so an author writes an
    indented triple-quoted literal and never imports `cleandoc`. A subclass that
    adds its own `__post_init__` must call `super().__post_init__()`.

    A rule may also carry an optional `edits` method — its *presence* is what
    marks the rule auto-fixable under `garuff check --fix`; a rule without one is
    report-only. This fixer mirrors `check`, walking the same input and yielding
    one `Edit` per repairable occurrence (see `SourceFixer`/`TextFixer` and
    ADR-0017). It is deliberately *not* named `fix`: that name is already the
    prose `fix` field above (the correct-form part of the Explanation), and a
    dataclass field would shadow a same-named method on every instance. The
    abstract bases do not declare `edits`, so presence stays a genuine signal.
    """

    code: str
    summary: str
    rationale: str
    fix: str

    def __post_init__(self) -> None:
        """Normalize the agent-facing text to print-ready form."""
        self.summary = cleandoc(self.summary)
        self.rationale = cleandoc(self.rationale)
        self.fix = cleandoc(self.fix)

    @property
    def option_values(self) -> dict[str, object]:
        """The option values this rule's explanation templates may reference."""
        options = getattr(self, "options", None)
        return {} if options is None else asdict(options)

    @property
    def explanation(self) -> Explanation:
        """Render this rule's text with its own option values substituted in.

        The three fields are `string.Template` templates rendered at *render*
        time — after `config.load` has baked in the project's option values
        (ADR-0007, ADR-0014). `safe_substitute` prints an unresolvable `$name`
        verbatim rather than raising inside a user's run; a registry-wide test
        guards against a typo'd placeholder slipping out.
        """
        values = self.option_values

        def fill(text: str) -> str:
            """Substitute this rule's option values into one template field."""
            return Template(text).safe_substitute(values)

        return Explanation(
            code=self.code,
            summary=fill(self.summary),
            rationale=fill(self.rationale),
            fix=fill(self.fix),
        )


@dataclass(kw_only=True)
class SourceRule(Rule, abc.ABC):
    """A rule that consumes one parsed Python module (AST) at a time."""

    @abc.abstractmethod
    def check(self, module: ast.Module, *, path: Path) -> Iterator[Violation]:
        """Yield a violation for each place this rule is broken in the module."""


@dataclass(kw_only=True)
class TextRule(Rule, abc.ABC):
    """A rule that consumes the raw text of one linted file, any extension."""

    @abc.abstractmethod
    def check(self, text: str, *, path: Path) -> Iterator[Violation]:
        """Yield a violation for each place this rule is broken in the text."""


@dataclass(kw_only=True)
class ProjectRule(Rule, abc.ABC):
    """A rule that consumes the gathered project file list, checked once."""

    @abc.abstractmethod
    def check(self, project_files: list[Path]) -> Iterator[Violation]:
        """Yield a violation for each place this rule is broken in the project."""


@runtime_checkable
class SourceFixer(Protocol):
    """A `SourceRule` that also carries a fixer (its presence marks fixability).

    `@runtime_checkable` checks only method *presence*, which is exactly the
    fixability signal — the runner narrows a source rule to this to decide
    whether it can be fixed. The fixer's `edits` takes the raw `text` too (beyond
    the AST `check` sees), because it needs character offsets and the `original`
    guard. Named `edits`, not `fix`, to avoid the prose `fix` field's shadow.
    """

    def edits(self, module: ast.Module, *, text: str, path: Path) -> Iterator[Edit]:
        """Yield one Edit per repairable occurrence found in the module."""


@runtime_checkable
class TextFixer(Protocol):
    """A `TextRule` that also carries a fixer (its presence marks fixability).

    Defined for symmetry with `SourceFixer`; no text fixer ships yet. A text
    fixer already has the raw text `check` consumes, so its `edits` takes no
    extra `text`.
    """

    def edits(self, text: str, *, path: Path) -> Iterator[Edit]:
        """Yield one Edit per repairable occurrence found in the text."""
