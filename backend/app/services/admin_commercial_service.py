"""Branch-bound commercial administration with transactional audit receipts."""

from collections.abc import Iterator
from contextlib import contextmanager

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.admin_roles import AdminPermission, AdminRole, permits
from backend.app.core.config import AdminAuthSettings
from backend.app.core.exceptions import (
    AdminAuthorizationError,
    AdminCommercialConflictError,
    AdminCommercialNotFoundError,
    InvalidRequestError,
    ServiceUnavailableError,
)
from backend.app.db.models.admin_commercial import AdminCommercialAudit, ManagedFAQ
from backend.app.db.models.admin_user import AdminUser
from backend.app.db.models.branch import Branch
from backend.app.db.models.price import Price
from backend.app.db.models.product import Product
from backend.app.repositories.branch_repository import BranchRepository
from backend.app.repositories.price_repository import PriceRepository
from backend.app.repositories.product_repository import ProductRepository
from backend.app.schemas.admin_commercial import BranchUpdate, FAQWrite, PriceWrite, ProductUpdate
from backend.app.schemas.branch import BranchData
from backend.app.schemas.price import PriceData, normalize_price_unit
from backend.app.schemas.product import ProductData
from backend.app.services.admin_auth_service import AdminSessionInfo
from backend.app.services.branch_scope import BranchScope
from backend.app.services.branch_service import BranchService
from backend.app.services.faq_service import normalize_faq_question


class AdminCommercialService:
    """Never accept branch identity from an HTTP payload, path, or model call."""

    def __init__(self, sessions: sessionmaker[Session], *, settings: AdminAuthSettings) -> None:
        self._sessions = sessions
        self._scope = BranchScope.from_settings(settings)

    @contextmanager
    def _context(
        self, principal: AdminSessionInfo, permission: AdminPermission
    ) -> Iterator[tuple[Session, Branch]]:
        try:
            with self._sessions.begin() as session:
                branch = BranchService(
                    BranchRepository(session), assistant_branch_code=self._scope.branch_code
                ).get_current_branch()
                if branch.id != principal.branch_id:
                    raise AdminAuthorizationError()
                role = session.scalar(
                    select(AdminUser.role).where(
                        AdminUser.id == principal.user_id,
                        AdminUser.branch_id == branch.id,
                        AdminUser.is_active.is_(True),
                    )
                )
                if role is None or not permits(AdminRole(role), permission):
                    raise AdminAuthorizationError()
                yield session, branch
        except IntegrityError:
            raise AdminCommercialConflictError() from None
        except SQLAlchemyError:
            raise ServiceUnavailableError("commercial persistence failed") from None

    @staticmethod
    def _audit(
        session: Session,
        principal: AdminSessionInfo,
        resource: str,
        resource_id: int,
        action: str,
        *,
        product_id: int | None = None,
        unit: str | None = None,
        old_amount: object = None,
        new_amount: object = None,
    ) -> None:
        session.add(
            AdminCommercialAudit(
                branch_id=principal.branch_id,
                actor_user_id=principal.user_id,
                resource=resource,
                resource_id=resource_id,
                action=action,
                product_id=product_id,
                unit=unit,
                old_amount=old_amount,
                new_amount=new_amount,
            )
        )
        try:
            session.flush()
        except SQLAlchemyError:
            raise ServiceUnavailableError("commercial audit failed") from None

    @staticmethod
    def _product(session: Session, branch: Branch, product_id: int) -> Product:
        if product_id < 1:
            raise AdminCommercialNotFoundError()
        product = ProductRepository(session, branch=branch).get_by_id(product_id)
        if product is None:
            raise AdminCommercialNotFoundError()
        return product

    def get_branch(self, principal: AdminSessionInfo) -> Branch:
        with self._context(principal, AdminPermission.COMMERCIAL_READ) as (_, branch):
            return branch

    def update_branch(self, principal: AdminSessionInfo, data: BranchUpdate) -> Branch:
        with self._context(principal, AdminPermission.BRANCH_WRITE) as (session, branch):
            validated = BranchData(code=branch.code, **data.model_dump())
            old = (branch.name, branch.address, branch.phone, branch.business_hours)
            new = (validated.name, validated.address, validated.phone, validated.business_hours)
            if old != new:
                BranchRepository(session).update(branch, validated)
                self._audit(session, principal, "branch", branch.id, "update")
            return branch

    def list_products(self, principal: AdminSessionInfo) -> tuple[Product, ...]:
        with self._context(principal, AdminPermission.COMMERCIAL_READ) as (session, branch):
            return ProductRepository(session, branch=branch).list_all()

    def create_product(self, principal: AdminSessionInfo, data: ProductData) -> Product:
        with self._context(principal, AdminPermission.COMMERCIAL_WRITE) as (session, branch):
            product = ProductRepository(session, branch=branch).create(data)
            self._audit(session, principal, "product", product.id, "create")
            return product

    def update_product(
        self, principal: AdminSessionInfo, product_id: int, data: ProductUpdate
    ) -> Product:
        with self._context(principal, AdminPermission.COMMERCIAL_WRITE) as (session, branch):
            repo = ProductRepository(session, branch=branch)
            product = self._product(session, branch, product_id)
            if (product.name, product.category, product.is_active) != (
                data.name,
                data.category,
                data.is_active,
            ):
                repo.update(product, ProductData(name=data.name, category=data.category))
                repo.set_active(product, is_active=data.is_active)
                self._audit(session, principal, "product", product.id, "update")
            return product

    def deactivate_product(self, principal: AdminSessionInfo, product_id: int) -> None:
        with self._context(principal, AdminPermission.COMMERCIAL_WRITE) as (session, branch):
            repo = ProductRepository(session, branch=branch)
            product = self._product(session, branch, product_id)
            if product.is_active:
                repo.set_active(product, is_active=False)
                self._audit(session, principal, "product", product.id, "deactivate")

    def list_prices(self, principal: AdminSessionInfo, product_id: int) -> tuple[Price, ...]:
        with self._context(principal, AdminPermission.COMMERCIAL_READ) as (session, branch):
            product = self._product(session, branch, product_id)
            return PriceRepository(session, branch=branch).list_for_product(product)

    @staticmethod
    def _unit_data(unit: str, amount: object) -> PriceData:
        try:
            return PriceData(amount=amount, unit=normalize_price_unit(unit))
        except (ValueError, ValidationError):
            raise InvalidRequestError("invalid price") from None

    def put_price(
        self, principal: AdminSessionInfo, product_id: int, unit: str, data: PriceWrite
    ) -> Price:
        price_data = self._unit_data(unit, data.amount)
        with self._context(principal, AdminPermission.COMMERCIAL_WRITE) as (session, branch):
            product = self._product(session, branch, product_id)
            repo = PriceRepository(session, branch=branch)
            price = repo.get_for_product(product, unit=price_data.unit)
            if price is None:
                price = repo.create(product, price_data)
                self._audit(
                    session,
                    principal,
                    "price",
                    price.id,
                    "create",
                    product_id=product.id,
                    unit=price.unit,
                    new_amount=price.amount,
                )
            elif price.amount != price_data.amount:
                old_amount = price.amount
                repo.update(price, price_data)
                self._audit(
                    session,
                    principal,
                    "price",
                    price.id,
                    "update",
                    product_id=product.id,
                    unit=price.unit,
                    old_amount=old_amount,
                    new_amount=price.amount,
                )
            return price

    def delete_price(self, principal: AdminSessionInfo, product_id: int, unit: str) -> None:
        data = self._unit_data(unit, "0")
        with self._context(principal, AdminPermission.COMMERCIAL_WRITE) as (session, branch):
            product = self._product(session, branch, product_id)
            repo = PriceRepository(session, branch=branch)
            price = repo.get_for_product(product, unit=data.unit)
            if price is None:
                raise AdminCommercialNotFoundError()
            old_amount = price.amount
            price_id = price.id
            repo.delete(price)
            self._audit(
                session,
                principal,
                "price",
                price_id,
                "delete",
                product_id=product.id,
                unit=price.unit,
                old_amount=old_amount,
            )

    def list_faqs(self, principal: AdminSessionInfo) -> tuple[ManagedFAQ, ...]:
        with self._context(principal, AdminPermission.COMMERCIAL_READ) as (session, branch):
            return tuple(
                session.scalars(
                    select(ManagedFAQ)
                    .where(ManagedFAQ.branch_id == branch.id)
                    .order_by(ManagedFAQ.category, ManagedFAQ.question, ManagedFAQ.id)
                )
            )

    @staticmethod
    def _faq(session: Session, branch: Branch, faq_id: int) -> ManagedFAQ:
        faq = session.scalar(
            select(ManagedFAQ).where(ManagedFAQ.id == faq_id, ManagedFAQ.branch_id == branch.id)
        )
        if faq is None:
            raise AdminCommercialNotFoundError()
        return faq

    def create_faq(self, principal: AdminSessionInfo, data: FAQWrite) -> ManagedFAQ:
        with self._context(principal, AdminPermission.COMMERCIAL_WRITE) as (session, branch):
            faq = ManagedFAQ(
                branch_id=branch.id,
                category=data.category.value,
                question=data.question,
                question_key=normalize_faq_question(data.question),
                answer=data.answer,
                is_active=data.is_active,
            )
            session.add(faq)
            session.flush()
            self._audit(session, principal, "faq", faq.id, "create")
            return faq

    def update_faq(self, principal: AdminSessionInfo, faq_id: int, data: FAQWrite) -> ManagedFAQ:
        with self._context(principal, AdminPermission.COMMERCIAL_WRITE) as (session, branch):
            faq = self._faq(session, branch, faq_id)
            new_values = (
                data.category.value,
                data.question,
                normalize_faq_question(data.question),
                data.answer,
                data.is_active,
            )
            if (
                faq.category,
                faq.question,
                faq.question_key,
                faq.answer,
                faq.is_active,
            ) != new_values:
                faq.category, faq.question, faq.question_key, faq.answer, faq.is_active = new_values
                session.flush()
                self._audit(session, principal, "faq", faq.id, "update")
            return faq

    def deactivate_faq(self, principal: AdminSessionInfo, faq_id: int) -> None:
        with self._context(principal, AdminPermission.COMMERCIAL_WRITE) as (session, branch):
            faq = self._faq(session, branch, faq_id)
            if faq.is_active:
                faq.is_active = False
                session.flush()
                self._audit(session, principal, "faq", faq.id, "deactivate")
