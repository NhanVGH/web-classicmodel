from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.reporting import (
    SalesFilters,
    get_chart_payload,
    get_customer_matches,
    get_dashboard_summary,
    get_metadata,
    get_pivot_dataset,
    get_product_matches,
    get_sales_details,
)


router = APIRouter()


def _filters(
    date_from: date | None = None,
    date_to: date | None = None,
    customer_number: int | None = None,
    customer_keyword: str | None = None,
    product_keyword: str | None = None,
    product_code: str | None = None,
    product_line: str | None = None,
    country: str | None = None,
    status: str | None = None,
) -> SalesFilters:
    return SalesFilters(
        date_from=date_from,
        date_to=date_to,
        customer_number=customer_number,
        customer_keyword=customer_keyword,
        product_keyword=product_keyword,
        product_code=product_code,
        product_line=product_line,
        country=country,
        status=status,
    )


@router.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/metadata")
def metadata(db: Session = Depends(get_db)) -> dict[str, list[str]]:
    return get_metadata(db)


@router.get("/customers")
def customers(
    q: str = "",
    country: str | None = None,
    limit: int = Query(default=20, ge=1, le=50),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    return {"items": get_customer_matches(db, keyword=q, country=country, limit=limit)}


@router.get("/products")
def products(
    q: str = "",
    product_line: str | None = None,
    limit: int = Query(default=20, ge=1, le=50),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    return {"items": get_product_matches(db, keyword=q, product_line=product_line, limit=limit)}


@router.get("/dashboard/summary")
def dashboard_summary(
    date_from: date | None = None,
    date_to: date | None = None,
    customer_number: int | None = None,
    customer_keyword: str | None = None,
    product_keyword: str | None = None,
    product_code: str | None = None,
    product_line: str | None = None,
    country: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    filters = _filters(
        date_from,
        date_to,
        customer_number,
        customer_keyword,
        product_keyword,
        product_code,
        product_line,
        country,
        status,
    )
    return get_dashboard_summary(db, filters)


@router.get("/dashboard/charts")
def dashboard_charts(
    date_from: date | None = None,
    date_to: date | None = None,
    customer_number: int | None = None,
    customer_keyword: str | None = None,
    product_keyword: str | None = None,
    product_code: str | None = None,
    product_line: str | None = None,
    country: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    filters = _filters(
        date_from,
        date_to,
        customer_number,
        customer_keyword,
        product_keyword,
        product_code,
        product_line,
        country,
        status,
    )
    return get_chart_payload(db, filters)


@router.get("/dashboard/details")
def dashboard_details(
    date_from: date | None = None,
    date_to: date | None = None,
    customer_number: int | None = None,
    customer_keyword: str | None = None,
    product_keyword: str | None = None,
    product_code: str | None = None,
    product_line: str | None = None,
    country: str | None = None,
    status: str | None = None,
    limit: int = Query(default=25, ge=1, le=250),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    filters = _filters(
        date_from,
        date_to,
        customer_number,
        customer_keyword,
        product_keyword,
        product_code,
        product_line,
        country,
        status,
    )
    return get_sales_details(db, filters, limit=limit, offset=offset)


@router.get("/dashboard/pivot")
def dashboard_pivot(
    date_from: date | None = None,
    date_to: date | None = None,
    customer_number: int | None = None,
    customer_keyword: str | None = None,
    product_keyword: str | None = None,
    product_code: str | None = None,
    product_line: str | None = None,
    country: str | None = None,
    status: str | None = None,
    limit: int = Query(default=1500, ge=50, le=5000),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    filters = _filters(
        date_from,
        date_to,
        customer_number,
        customer_keyword,
        product_keyword,
        product_code,
        product_line,
        country,
        status,
    )
    return get_pivot_dataset(db, filters, limit=limit)
