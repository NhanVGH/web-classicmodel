from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import Select, extract, func, literal, or_, select
from sqlalchemy.orm import Session

from app.models import Customer, Employee, Order, OrderDetail, Product


@dataclass
class SalesFilters:
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    customer_number: Optional[int] = None
    customer_keyword: Optional[str] = None
    product_keyword: Optional[str] = None
    product_code: Optional[str] = None
    product_line: Optional[str] = None
    country: Optional[str] = None
    status: Optional[str] = None


def _float(value: Decimal | float | int | None) -> float:
    return round(float(value or 0), 2)


def _base_sales_select() -> Select[Any]:
    revenue_expr = (OrderDetail.quantity_ordered * OrderDetail.price_each).label("revenue")
    order_year = extract("year", Order.order_date).label("order_year")
    order_month = extract("month", Order.order_date).label("order_month")

    return (
        select(
            Order.order_number.label("order_number"),
            Order.order_date.label("order_date"),
            Order.status.label("status"),
            Customer.customer_number.label("customer_number"),
            Customer.customer_name.label("customer_name"),
            Customer.country.label("country"),
            Product.product_code.label("product_code"),
            Product.product_name.label("product_name"),
            Product.product_line.label("product_line"),
            OrderDetail.quantity_ordered.label("quantity"),
            OrderDetail.price_each.label("unit_price"),
            revenue_expr,
            order_year,
            order_month,
        )
        .join(Order.customer)
        .join(Order.order_details)
        .join(OrderDetail.product)
    )


def _apply_filters(statement: Select[Any], filters: SalesFilters) -> Select[Any]:
    if filters.date_from:
        statement = statement.where(Order.order_date >= filters.date_from)
    if filters.date_to:
        statement = statement.where(Order.order_date <= filters.date_to)
    if filters.customer_number:
        statement = statement.where(Customer.customer_number == filters.customer_number)
    if filters.customer_keyword:
        pattern = f"%{filters.customer_keyword.strip()}%"
        statement = statement.where(
            or_(
                Customer.customer_name.ilike(pattern),
                Customer.contact_first_name.ilike(pattern),
                Customer.contact_last_name.ilike(pattern),
                Customer.country.ilike(pattern),
            )
        )
    if filters.product_keyword:
        pattern = f"%{filters.product_keyword.strip()}%"
        statement = statement.where(
            or_(
                Product.product_name.ilike(pattern),
                Product.product_code.ilike(pattern),
                Product.product_vendor.ilike(pattern),
            )
        )
    if filters.product_code:
        statement = statement.where(Product.product_code == filters.product_code)
    if filters.product_line:
        statement = statement.where(Product.product_line == filters.product_line)
    if filters.country:
        statement = statement.where(Customer.country == filters.country)
    if filters.status:
        statement = statement.where(Order.status == filters.status)
    return statement


def get_customer_matches(db: Session, keyword: str = "", country: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
    statement = (
        select(
            Customer.customer_number,
            Customer.customer_name,
            Customer.contact_first_name,
            Customer.contact_last_name,
            Customer.city,
            Customer.country,
            Customer.phone,
            (Employee.first_name + literal(" ") + Employee.last_name).label("sales_rep"),
        )
        .select_from(Customer)
        .join(Customer.sales_rep, isouter=True)
        .order_by(Customer.customer_name)
        .limit(min(limit, 50))
    )
    if keyword:
        pattern = f"%{keyword.strip()}%"
        statement = statement.where(
            or_(
                Customer.customer_name.ilike(pattern),
                Customer.contact_first_name.ilike(pattern),
                Customer.contact_last_name.ilike(pattern),
                Customer.phone.ilike(pattern),
            )
        )
    if country:
        statement = statement.where(Customer.country == country)

    rows = db.execute(statement).all()
    return [
        {
            "customer_number": row.customer_number,
            "customer_name": row.customer_name,
            "contact_name": f"{row.contact_first_name} {row.contact_last_name}",
            "city": row.city,
            "country": row.country,
            "phone": row.phone,
            "sales_rep": row.sales_rep,
        }
        for row in rows
    ]


def get_product_matches(
    db: Session,
    keyword: str = "",
    product_line: str | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    statement = (
        select(
            Product.product_code,
            Product.product_name,
            Product.product_line,
            Product.product_vendor,
            Product.quantity_in_stock,
            Product.buy_price,
            Product.msrp,
        )
        .order_by(Product.product_name)
        .limit(min(limit, 50))
    )
    if keyword:
        pattern = f"%{keyword.strip()}%"
        statement = statement.where(
            or_(
                Product.product_name.ilike(pattern),
                Product.product_code.ilike(pattern),
                Product.product_vendor.ilike(pattern),
            )
        )
    if product_line:
        statement = statement.where(Product.product_line == product_line)

    rows = db.execute(statement).all()
    return [
        {
            "product_code": row.product_code,
            "product_name": row.product_name,
            "product_line": row.product_line,
            "product_vendor": row.product_vendor,
            "quantity_in_stock": row.quantity_in_stock,
            "buy_price": _float(row.buy_price),
            "msrp": _float(row.msrp),
        }
        for row in rows
    ]


def get_metadata(db: Session) -> dict[str, list[str]]:
    product_lines = db.execute(select(Product.product_line).distinct().order_by(Product.product_line)).scalars().all()
    countries = db.execute(select(Customer.country).distinct().order_by(Customer.country)).scalars().all()
    statuses = db.execute(select(Order.status).distinct().order_by(Order.status)).scalars().all()
    return {
        "product_lines": product_lines,
        "countries": countries,
        "statuses": statuses,
    }


def get_dashboard_summary(db: Session, filters: SalesFilters) -> dict[str, Any]:
    revenue_expr = OrderDetail.quantity_ordered * OrderDetail.price_each
    statement = (
        select(
            func.coalesce(func.sum(revenue_expr), 0).label("total_revenue"),
            func.coalesce(func.sum(OrderDetail.quantity_ordered), 0).label("total_quantity"),
            func.count(func.distinct(Order.order_number)).label("order_count"),
            func.count(func.distinct(Customer.customer_number)).label("customer_count"),
            func.count(func.distinct(Product.product_code)).label("product_count"),
        )
        .select_from(Order)
        .join(Order.customer)
        .join(Order.order_details)
        .join(OrderDetail.product)
    )
    row = db.execute(_apply_filters(statement, filters)).one()
    avg_order_value = _float(row.total_revenue / row.order_count) if row.order_count else 0.0

    return {
        "total_revenue": _float(row.total_revenue),
        "total_quantity": int(row.total_quantity or 0),
        "order_count": int(row.order_count or 0),
        "customer_count": int(row.customer_count or 0),
        "product_count": int(row.product_count or 0),
        "avg_order_value": avg_order_value,
    }


def get_chart_payload(db: Session, filters: SalesFilters) -> dict[str, Any]:
    year_expr = extract("year", Order.order_date).label("year")
    month_expr = extract("month", Order.order_date).label("month")
    customer_statement = (
        select(
            Customer.customer_name.label("label"),
            func.sum(OrderDetail.quantity_ordered * OrderDetail.price_each).label("value"),
        )
        .select_from(Order)
        .join(Order.customer)
        .join(Order.order_details)
        .join(OrderDetail.product)
        .group_by(Customer.customer_name)
        .order_by(func.sum(OrderDetail.quantity_ordered * OrderDetail.price_each).desc())
        .limit(8)
    )
    month_statement = (
        select(
            year_expr,
            month_expr,
            func.sum(OrderDetail.quantity_ordered * OrderDetail.price_each).label("revenue"),
            func.sum(OrderDetail.quantity_ordered).label("quantity"),
        )
        .select_from(Order)
        .join(Order.customer)
        .join(Order.order_details)
        .join(OrderDetail.product)
        .group_by(year_expr, month_expr)
        .order_by(year_expr, month_expr)
    )
    line_statement = (
        select(
            Product.product_line.label("label"),
            func.sum(OrderDetail.quantity_ordered * OrderDetail.price_each).label("value"),
        )
        .select_from(Order)
        .join(Order.customer)
        .join(Order.order_details)
        .join(OrderDetail.product)
        .group_by(Product.product_line)
        .order_by(func.sum(OrderDetail.quantity_ordered * OrderDetail.price_each).desc())
    )

    customer_rows = db.execute(_apply_filters(customer_statement, filters)).all()
    month_rows = db.execute(_apply_filters(month_statement, filters)).all()
    line_rows = db.execute(_apply_filters(line_statement, filters)).all()

    return {
        "customer_sales": [{"label": row.label, "value": _float(row.value)} for row in customer_rows],
        "monthly_sales": [
            {
                "label": f"{int(row.year):04d}-{int(row.month):02d}",
                "revenue": _float(row.revenue),
                "quantity": int(row.quantity or 0),
            }
            for row in month_rows
        ],
        "product_line_sales": [{"label": row.label, "value": _float(row.value)} for row in line_rows],
    }


def get_sales_details(
    db: Session,
    filters: SalesFilters,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    base_statement = _apply_filters(_base_sales_select(), filters)
    total_statement = select(func.count()).select_from(base_statement.subquery())
    detail_statement = (
        base_statement.order_by(Order.order_date.desc(), Order.order_number.desc())
        .offset(max(offset, 0))
        .limit(min(limit, 250))
    )

    total_rows = db.execute(total_statement).scalar_one()
    rows = db.execute(detail_statement).all()

    return {
        "total_rows": int(total_rows),
        "items": [
            {
                "order_number": row.order_number,
                "order_date": row.order_date,
                "customer_name": row.customer_name,
                "country": row.country,
                "product_code": row.product_code,
                "product_name": row.product_name,
                "product_line": row.product_line,
                "status": row.status,
                "quantity": int(row.quantity),
                "unit_price": _float(row.unit_price),
                "revenue": _float(row.revenue),
            }
            for row in rows
        ],
    }


def get_pivot_dataset(db: Session, filters: SalesFilters, limit: int = 1500) -> dict[str, Any]:
    statement = (
        _apply_filters(_base_sales_select(), filters)
        .order_by(Order.order_date.desc(), Customer.customer_name, Product.product_name)
        .limit(min(limit, 5000))
    )
    rows = db.execute(statement).all()
    items = [
        {
            "customer_name": row.customer_name,
            "country": row.country,
            "product_code": row.product_code,
            "product_name": row.product_name,
            "product_line": row.product_line,
            "status": row.status,
            "order_date": row.order_date.isoformat(),
            "order_month": f"{int(row.order_year):04d}-{int(row.order_month):02d}",
            "quantity": int(row.quantity),
            "revenue": _float(row.revenue),
        }
        for row in rows
    ]
    return {"items": items}
