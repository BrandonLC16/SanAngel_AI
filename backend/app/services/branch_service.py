"""Branch-scoped application services."""

from dataclasses import dataclass
from typing import Literal

from backend.app.core.config import validate_branch_code
from backend.app.core.exceptions import BranchNotConfiguredError, BranchScopeMismatchError
from backend.app.db.models.branch import Branch
from backend.app.repositories.branch_repository import BranchRepository
from backend.app.schemas.branch import AssistantProfile


@dataclass(frozen=True, slots=True)
class BranchProvisioningResult:
    action: Literal["created", "updated", "unchanged"]
    branch: Branch


class BranchService:
    """Expose only the branch assigned by trusted deployment configuration."""

    def __init__(self, repository: BranchRepository, *, assistant_branch_code: str) -> None:
        self._repository = repository
        self._assistant_branch_code = validate_branch_code(assistant_branch_code)

    def get_current_branch(self) -> Branch:
        branch = self._repository.get_by_code(self._assistant_branch_code)
        if branch is None or not branch.is_active:
            raise BranchNotConfiguredError("assistant branch is missing or inactive")
        return branch

    def provision(self, profile: AssistantProfile) -> BranchProvisioningResult:
        data = profile.branch
        if data.code != self._assistant_branch_code:
            raise BranchScopeMismatchError("profile branch does not match assistant installation")

        branch = self._repository.get_by_code(self._assistant_branch_code)
        if branch is None:
            return BranchProvisioningResult("created", self._repository.create(data))

        changed = any(
            (
                branch.name != data.name,
                branch.address != data.address,
                branch.phone != data.phone,
                branch.business_hours != data.business_hours,
                not branch.is_active,
            )
        )
        if not changed:
            return BranchProvisioningResult("unchanged", branch)

        branch.is_active = True
        return BranchProvisioningResult("updated", self._repository.update(branch, data))
