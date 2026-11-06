from datetime import datetime, timezone, timedelta

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session
from starlette.requests import Request

from db import Order, OrderItem, OrderStatus, Product
import db

LOW_STOCK_THRESHOLD = 5
TOP_SELLING_WINDOW = timedelta(weeks=4)


def low_stock_products(session: Session):
    stmt = select(Product).where(Product.stock_count < LOW_STOCK_THRESHOLD)
    return session.scalars(stmt).all()


def out_of_stock_products(session: Session):
    stmt = select(Product).filter_by(stock_count=0)
    return session.scalars(stmt).all()


def top_selling_products(session: Session):
    delivered_item_cte = (
        select(
            OrderItem.product_id,
            OrderItem.count,
            OrderItem.quantity_returned,
            Order.delivered_at,
        )
        .select_from(OrderItem)
        .join(OrderItem.order)
        .where(Order.status == OrderStatus.Delivered)
    ).cte()

    cutoff = datetime.now(timezone.utc) - TOP_SELLING_WINDOW
    top_selling = (
        select(
            Product,
            func.sum(
                delivered_item_cte.c.count - delivered_item_cte.c.quantity_returned
            ).label("freq"),
        )
        .join(delivered_item_cte, Product.id == delivered_item_cte.c.product_id)
        .where(delivered_item_cte.c.delivered_at >= cutoff)
        .group_by(Product)
        .order_by(desc("freq"), Product.name)
    )
    return [tuple(row) for row in session.execute(top_selling).all()]


def stock_value(session: Session):
    stmt = select(func.sum(Product.price * Product.stock_count))
    return session.scalar(stmt)


def get_report_context(request: Request):
    sessionmaker = db.get_session_factory()
    with sessionmaker() as session:
        context = {
            "low_stock": low_stock_products(session),
            "out_of_stock": out_of_stock_products(session),
            "top_selling": top_selling_products(session),
            "stock_value": stock_value(session),
        }

        return context
