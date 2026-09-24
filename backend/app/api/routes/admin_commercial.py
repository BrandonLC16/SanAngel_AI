"""Authenticated CRUD for the configured installation's commercial data."""

import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends, Response

from backend.app.api.admin_authorization import require_admin_csrf, require_permission
from backend.app.core.admin_roles import AdminPermission
from backend.app.core.config import get_admin_auth_settings
from backend.app.db.session import get_database_session_factory
from backend.app.schemas.admin_commercial import (
    BranchUpdate,
    BranchView,
    FAQView,
    FAQWrite,
    PriceView,
    PriceWrite,
    ProductUpdate,
    ProductView,
)
from backend.app.schemas.product import ProductData
from backend.app.services.admin_auth_service import AdminSessionInfo
from backend.app.services.admin_commercial_service import AdminCommercialService

router = APIRouter(prefix="/api/v1/admin/commercial", tags=["admin-commercial"])


def get_admin_commercial_service() -> AdminCommercialService:
    return AdminCommercialService(
        get_database_session_factory(), settings=get_admin_auth_settings()
    )


def _no_store(response: Response) -> None:
    response.headers["Cache-Control"] = "no-store"


@router.get("/branch", response_model=BranchView)
async def get_branch(
    response: Response,
    principal: Annotated[
        AdminSessionInfo, Depends(require_permission(AdminPermission.COMMERCIAL_READ))
    ],
    service: Annotated[AdminCommercialService, Depends(get_admin_commercial_service)],
) -> BranchView:
    branch = await asyncio.to_thread(service.get_branch, principal)
    _no_store(response)
    return BranchView.model_validate(branch, from_attributes=True)


@router.put("/branch", response_model=BranchView)
async def update_branch(
    payload: BranchUpdate,
    response: Response,
    principal: Annotated[
        AdminSessionInfo, Depends(require_permission(AdminPermission.BRANCH_WRITE))
    ],
    service: Annotated[AdminCommercialService, Depends(get_admin_commercial_service)],
    _csrf: Annotated[str, Depends(require_admin_csrf)],
) -> BranchView:
    branch = await asyncio.to_thread(service.update_branch, principal, payload)
    _no_store(response)
    return BranchView.model_validate(branch, from_attributes=True)


@router.get("/products", response_model=list[ProductView])
async def list_products(
    response: Response,
    principal: Annotated[
        AdminSessionInfo, Depends(require_permission(AdminPermission.COMMERCIAL_READ))
    ],
    service: Annotated[AdminCommercialService, Depends(get_admin_commercial_service)],
) -> list[ProductView]:
    products = await asyncio.to_thread(service.list_products, principal)
    _no_store(response)
    return [ProductView.model_validate(item, from_attributes=True) for item in products]


@router.post("/products", response_model=ProductView, status_code=201)
async def create_product(
    payload: ProductData,
    response: Response,
    principal: Annotated[
        AdminSessionInfo, Depends(require_permission(AdminPermission.COMMERCIAL_WRITE))
    ],
    service: Annotated[AdminCommercialService, Depends(get_admin_commercial_service)],
    _csrf: Annotated[str, Depends(require_admin_csrf)],
) -> ProductView:
    product = await asyncio.to_thread(service.create_product, principal, payload)
    _no_store(response)
    return ProductView.model_validate(product, from_attributes=True)


@router.put("/products/{product_id}", response_model=ProductView)
async def update_product(
    product_id: int,
    payload: ProductUpdate,
    response: Response,
    principal: Annotated[
        AdminSessionInfo, Depends(require_permission(AdminPermission.COMMERCIAL_WRITE))
    ],
    service: Annotated[AdminCommercialService, Depends(get_admin_commercial_service)],
    _csrf: Annotated[str, Depends(require_admin_csrf)],
) -> ProductView:
    product = await asyncio.to_thread(service.update_product, principal, product_id, payload)
    _no_store(response)
    return ProductView.model_validate(product, from_attributes=True)


@router.delete("/products/{product_id}", status_code=204)
async def deactivate_product(
    product_id: int,
    response: Response,
    principal: Annotated[
        AdminSessionInfo, Depends(require_permission(AdminPermission.COMMERCIAL_WRITE))
    ],
    service: Annotated[AdminCommercialService, Depends(get_admin_commercial_service)],
    _csrf: Annotated[str, Depends(require_admin_csrf)],
) -> None:
    await asyncio.to_thread(service.deactivate_product, principal, product_id)
    _no_store(response)


@router.get("/products/{product_id}/prices", response_model=list[PriceView])
async def list_prices(
    product_id: int,
    response: Response,
    principal: Annotated[
        AdminSessionInfo, Depends(require_permission(AdminPermission.COMMERCIAL_READ))
    ],
    service: Annotated[AdminCommercialService, Depends(get_admin_commercial_service)],
) -> list[PriceView]:
    prices = await asyncio.to_thread(service.list_prices, principal, product_id)
    _no_store(response)
    return [PriceView.model_validate(item, from_attributes=True) for item in prices]


@router.put("/products/{product_id}/prices/{unit}", response_model=PriceView)
async def put_price(
    product_id: int,
    unit: str,
    payload: PriceWrite,
    response: Response,
    principal: Annotated[
        AdminSessionInfo, Depends(require_permission(AdminPermission.COMMERCIAL_WRITE))
    ],
    service: Annotated[AdminCommercialService, Depends(get_admin_commercial_service)],
    _csrf: Annotated[str, Depends(require_admin_csrf)],
) -> PriceView:
    price = await asyncio.to_thread(service.put_price, principal, product_id, unit, payload)
    _no_store(response)
    return PriceView.model_validate(price, from_attributes=True)


@router.delete("/products/{product_id}/prices/{unit}", status_code=204)
async def delete_price(
    product_id: int,
    unit: str,
    response: Response,
    principal: Annotated[
        AdminSessionInfo, Depends(require_permission(AdminPermission.COMMERCIAL_WRITE))
    ],
    service: Annotated[AdminCommercialService, Depends(get_admin_commercial_service)],
    _csrf: Annotated[str, Depends(require_admin_csrf)],
) -> None:
    await asyncio.to_thread(service.delete_price, principal, product_id, unit)
    _no_store(response)


@router.get("/faqs", response_model=list[FAQView])
async def list_faqs(
    response: Response,
    principal: Annotated[
        AdminSessionInfo, Depends(require_permission(AdminPermission.COMMERCIAL_READ))
    ],
    service: Annotated[AdminCommercialService, Depends(get_admin_commercial_service)],
) -> list[FAQView]:
    faqs = await asyncio.to_thread(service.list_faqs, principal)
    _no_store(response)
    return [FAQView.model_validate(item, from_attributes=True) for item in faqs]


@router.post("/faqs", response_model=FAQView, status_code=201)
async def create_faq(
    payload: FAQWrite,
    response: Response,
    principal: Annotated[
        AdminSessionInfo, Depends(require_permission(AdminPermission.COMMERCIAL_WRITE))
    ],
    service: Annotated[AdminCommercialService, Depends(get_admin_commercial_service)],
    _csrf: Annotated[str, Depends(require_admin_csrf)],
) -> FAQView:
    faq = await asyncio.to_thread(service.create_faq, principal, payload)
    _no_store(response)
    return FAQView.model_validate(faq, from_attributes=True)


@router.put("/faqs/{faq_id}", response_model=FAQView)
async def update_faq(
    faq_id: int,
    payload: FAQWrite,
    response: Response,
    principal: Annotated[
        AdminSessionInfo, Depends(require_permission(AdminPermission.COMMERCIAL_WRITE))
    ],
    service: Annotated[AdminCommercialService, Depends(get_admin_commercial_service)],
    _csrf: Annotated[str, Depends(require_admin_csrf)],
) -> FAQView:
    faq = await asyncio.to_thread(service.update_faq, principal, faq_id, payload)
    _no_store(response)
    return FAQView.model_validate(faq, from_attributes=True)


@router.delete("/faqs/{faq_id}", status_code=204)
async def deactivate_faq(
    faq_id: int,
    response: Response,
    principal: Annotated[
        AdminSessionInfo, Depends(require_permission(AdminPermission.COMMERCIAL_WRITE))
    ],
    service: Annotated[AdminCommercialService, Depends(get_admin_commercial_service)],
    _csrf: Annotated[str, Depends(require_admin_csrf)],
) -> None:
    await asyncio.to_thread(service.deactivate_faq, principal, faq_id)
    _no_store(response)
