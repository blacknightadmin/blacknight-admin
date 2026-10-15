from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import Engine
from sqlalchemy.orm import Session

from db import Base, Supplier, Product, Order, OrderItem
from db import Platform, PaymentStatus, OrderStatus


def create_baseline(engine: Engine):
    with Session(engine, expire_on_commit=False) as session:
        with session.begin():
            hp_envy = Product(name="HP Envy 360", price=Decimal(1200000), stock_count=3)
            toners = Product(name="Toner", price=Decimal(15000), stock_count=4)
            power_banks = Product(
                name="Itel 3600mAh PowerBank", price=Decimal(30000), stock_count=2
            )

            supplier1 = Supplier(
                name="HP Inc.", platform=Platform.eBay, products=[hp_envy]
            )
            supplier2 = Supplier(
                name="Lekzyd Ventures.",
                platform=Platform.Local,
                contact_info="+234 804 5687 693",
                products=[toners, power_banks],
            )

            item1 = OrderItem(product=power_banks, count=1, price=Decimal(37000))
            item2 = OrderItem(product=toners, count=2, price=Decimal(18000))
            order1 = Order(
                status=OrderStatus.Pending,
                payment_status=PaymentStatus.Unpaid,
                order_items=[item1, item2],
            )

            order2 = Order(
                status=OrderStatus.Cancelled,
                payment_status=PaymentStatus.Unpaid,
                order_items=[OrderItem(product=toners, count=1, price=Decimal(15000))],
            )

            order3 = Order(
                status=OrderStatus.Shipped,
                payment_status=PaymentStatus.Unpaid,
                order_items=[
                    OrderItem(product=hp_envy, count=1, price=Decimal(1800000))
                ],
            )

            now = datetime.now(timezone.utc)
            created = now - timedelta(days=20)
            delivered = now - timedelta(days=18)

            order4 = Order(
                status=OrderStatus.Delivered,
                payment_status=PaymentStatus.Paid,
                created_at=created,
                delivered_at=delivered,
                order_items=[
                    OrderItem(
                        product=toners,
                        count=5,
                        price=Decimal(165000),
                    )
                ],
            )

            session.add_all([supplier1, supplier2, order1, order2, order3, order4])
