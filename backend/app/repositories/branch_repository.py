"""Parameterized SQLAlchemy operations for branches."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db.models.branch import Branch
from backend.app.schemas.branch import BranchData


class BranchRepository:
    """Internal CRUD repository; assistant reads must use the scoped service."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, data: BranchData) -> Branch:
        branch = Branch(**data.model_dump(), is_active=True)
        self._session.add(branch)
        self._session.flush()
        return branch

    def get_by_code(self, code: str) -> Branch | None:
        return self._session.scalar(select(Branch).where(Branch.code == code))

    def list_all(self) -> tuple[Branch, ...]:
        statement = select(Branch).order_by(Branch.code)
        return tuple(self._session.scalars(statement))

    def update(self, branch: Branch, data: BranchData) -> Branch:
        if branch.code != data.code:
            raise ValueError("branch code is immutable")
        branch.name = data.name
        branch.address = data.address
        branch.phone = data.phone
        branch.business_hours = data.business_hours
        self._session.flush()
        return branch

    def delete(self, branch: Branch) -> None:
        self._session.delete(branch)
        self._session.flush()
