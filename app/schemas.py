from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel


class CustomerSearchItem(BaseModel):
    customer_number: int
    customer_name: str
    contact_name: str
    city: str
    country: str
    phone: str
    sales_rep: Optional[str] = None


class ProductSearchItem(BaseModel):
    product_code: str
    product_name: str
    product_line: str
    product_vendor: str
    quantity_in_stock: int
    buy_price: float
    msrp: float


class SalesDetailItem(BaseModel):
    order_number: int
    order_date: date
    customer_name: str
    country: str
    product_code: str
    product_name: str
    product_line: str
    status: str
    quantity: int
    unit_price: float
    revenue: float


class ChartPoint(BaseModel):
    label: str
    value: float


class MonthlyPoint(BaseModel):
    label: str
    revenue: float
    quantity: int
