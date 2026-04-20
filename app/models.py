from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import Date, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Office(Base):
    __tablename__ = "offices"

    office_code: Mapped[str] = mapped_column("officeCode", String(10), primary_key=True)
    city: Mapped[str] = mapped_column(String(50))
    phone: Mapped[str] = mapped_column(String(50))
    address_line1: Mapped[str] = mapped_column("addressLine1", String(50))
    address_line2: Mapped[Optional[str]] = mapped_column("addressLine2", String(50))
    state: Mapped[Optional[str]] = mapped_column(String(50))
    country: Mapped[str] = mapped_column(String(50))
    postal_code: Mapped[str] = mapped_column("postalCode", String(15))
    territory: Mapped[str] = mapped_column(String(10))

    employees: Mapped[list["Employee"]] = relationship(back_populates="office")


class Employee(Base):
    __tablename__ = "employees"

    employee_number: Mapped[int] = mapped_column("employeeNumber", Integer, primary_key=True)
    last_name: Mapped[str] = mapped_column("lastName", String(50))
    first_name: Mapped[str] = mapped_column("firstName", String(50))
    extension: Mapped[str] = mapped_column(String(10))
    email: Mapped[str] = mapped_column(String(100))
    office_code: Mapped[str] = mapped_column(
        "officeCode",
        String(10),
        ForeignKey("offices.officeCode"),
    )
    reports_to: Mapped[Optional[int]] = mapped_column(
        "reportsTo",
        Integer,
        ForeignKey("employees.employeeNumber"),
    )
    job_title: Mapped[str] = mapped_column("jobTitle", String(50))

    office: Mapped[Office] = relationship(back_populates="employees")
    manager: Mapped[Optional["Employee"]] = relationship(remote_side=[employee_number])
    customers: Mapped[list["Customer"]] = relationship(back_populates="sales_rep")


class Customer(Base):
    __tablename__ = "customers"

    customer_number: Mapped[int] = mapped_column("customerNumber", Integer, primary_key=True)
    customer_name: Mapped[str] = mapped_column("customerName", String(50))
    contact_last_name: Mapped[str] = mapped_column("contactLastName", String(50))
    contact_first_name: Mapped[str] = mapped_column("contactFirstName", String(50))
    phone: Mapped[str] = mapped_column(String(50))
    address_line1: Mapped[str] = mapped_column("addressLine1", String(50))
    address_line2: Mapped[Optional[str]] = mapped_column("addressLine2", String(50))
    city: Mapped[str] = mapped_column(String(50))
    state: Mapped[Optional[str]] = mapped_column(String(50))
    postal_code: Mapped[Optional[str]] = mapped_column("postalCode", String(15))
    country: Mapped[str] = mapped_column(String(50))
    sales_rep_employee_number: Mapped[Optional[int]] = mapped_column(
        "salesRepEmployeeNumber",
        Integer,
        ForeignKey("employees.employeeNumber"),
    )
    credit_limit: Mapped[Optional[Decimal]] = mapped_column("creditLimit", Numeric(10, 2))

    sales_rep: Mapped[Optional[Employee]] = relationship(back_populates="customers")
    orders: Mapped[list["Order"]] = relationship(back_populates="customer")
    payments: Mapped[list["Payment"]] = relationship(back_populates="customer")


class Payment(Base):
    __tablename__ = "payments"

    customer_number: Mapped[int] = mapped_column(
        "customerNumber",
        Integer,
        ForeignKey("customers.customerNumber"),
        primary_key=True,
    )
    check_number: Mapped[str] = mapped_column("checkNumber", String(50), primary_key=True)
    payment_date: Mapped[date] = mapped_column("paymentDate", Date)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    customer: Mapped[Customer] = relationship(back_populates="payments")


class Product(Base):
    __tablename__ = "products"

    product_code: Mapped[str] = mapped_column("productCode", String(15), primary_key=True)
    product_name: Mapped[str] = mapped_column("productName", String(70))
    product_line: Mapped[str] = mapped_column("productLine", String(50))
    product_scale: Mapped[str] = mapped_column("productScale", String(10))
    product_vendor: Mapped[str] = mapped_column("productVendor", String(50))
    product_description: Mapped[str] = mapped_column("productDescription", Text)
    quantity_in_stock: Mapped[int] = mapped_column("quantityInStock", Integer)
    buy_price: Mapped[Decimal] = mapped_column("buyPrice", Numeric(10, 2))
    msrp: Mapped[Decimal] = mapped_column("MSRP", Numeric(10, 2))

    order_details: Mapped[list["OrderDetail"]] = relationship(back_populates="product")


class Order(Base):
    __tablename__ = "orders"

    order_number: Mapped[int] = mapped_column("orderNumber", Integer, primary_key=True)
    order_date: Mapped[date] = mapped_column("orderDate", Date)
    required_date: Mapped[date] = mapped_column("requiredDate", Date)
    shipped_date: Mapped[Optional[date]] = mapped_column("shippedDate", Date)
    status: Mapped[str] = mapped_column(String(15))
    comments: Mapped[Optional[str]] = mapped_column(Text)
    customer_number: Mapped[int] = mapped_column(
        "customerNumber",
        Integer,
        ForeignKey("customers.customerNumber"),
    )

    customer: Mapped[Customer] = relationship(back_populates="orders")
    order_details: Mapped[list["OrderDetail"]] = relationship(back_populates="order")


class OrderDetail(Base):
    __tablename__ = "orderdetails"

    order_number: Mapped[int] = mapped_column(
        "orderNumber",
        Integer,
        ForeignKey("orders.orderNumber"),
        primary_key=True,
    )
    product_code: Mapped[str] = mapped_column(
        "productCode",
        String(15),
        ForeignKey("products.productCode"),
        primary_key=True,
    )
    quantity_ordered: Mapped[int] = mapped_column("quantityOrdered", Integer)
    price_each: Mapped[Decimal] = mapped_column("priceEach", Numeric(10, 2))
    order_line_number: Mapped[int] = mapped_column("orderLineNumber", Integer)

    order: Mapped[Order] = relationship(back_populates="order_details")
    product: Mapped[Product] = relationship(back_populates="order_details")
