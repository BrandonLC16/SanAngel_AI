"""Trusted immutable branch scope injected from backend configuration."""

from dataclasses import dataclass

from backend.app.core.config import AssistantSettings, validate_branch_code


@dataclass(frozen=True, slots=True)
class BranchScope:
    """The only branch one assistant installation is authorized to query."""

    branch_code: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "branch_code", validate_branch_code(self.branch_code))

    @classmethod
    def from_settings(cls, settings: AssistantSettings) -> "BranchScope":
        """Create the scope only from validated backend-owned settings."""

        return cls(branch_code=settings.assistant_branch_code)
