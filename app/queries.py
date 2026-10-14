from datetime import datetime, timezone, timedelta
from sqlalchemy import cast, select, String

from db import LocalSession, Order, OrderItem, Product, Supplier


def get_supplier_choices():
    with LocalSession() as session:
        stmt = select(Supplier.id, Supplier.name).order_by(Supplier.name)
        return [tuple(row) for row in session.execute(stmt).all()]


def get_product_choices():
    with LocalSession() as session:
        stmt = select(Product.id, Product.name).where(Product.stock_count > 0)
        result = session.execute(stmt).all()
        return [tuple(row) for row in result]


def get_orderitem_by_id(id):
    with LocalSession() as session:
        return session.execute(select(OrderItem).filter_by(id=id)).scalar_one_or_none()


def get_orderitems_by_order_id(order_id):
    with LocalSession() as session:
        return session.scalars(select(OrderItem).filter_by(order_id=order_id)).all()


def get_returnable_items():
    with LocalSession() as session:
        cutoff = lambda: datetime.now(timezone.utc) - timedelta(days=14)
        stmt = (
            select(OrderItem)
            .join(OrderItem.order)
            .where(
                Order.delivered_at >= cutoff(),
                OrderItem.quantity_returned <= OrderItem.count,
            )
        )
        return session.scalars(stmt).all()


def get_order_choices():
    with LocalSession() as session:
        stmt = select(Order.id, "Order #" + cast(Order.id, String)).order_by(
            Order.created_at.desc()
        )
        result = session.execute(stmt).all()
        return [tuple(row) for row in result]


def get_product_count(prod_id: int):
    with LocalSession() as session:
        return session.execute(
            select(Product.stock_count).filter_by(id=prod_id)
        ).scalar_one()


def get_order_status_by_id(order_id: int):
    with LocalSession() as session:
        return session.scalar(select(Order.status).filter_by(id=order_id))


# order management
def decrement_products_in_order(order):
    for order_item in order.order_items:
        order_item.product.stock_count -= order_item.count


def increment_products_in_order(order):
    for order_item in order.order_items:
        order_item.product.stock_count += order_item.count


def set_delivered_at(order: Order):
    order.delivered_at = datetime.now(timezone.utc)


def check_stock_count(order_id: int):
    with LocalSession() as session:
        order = session.scalar(select(Order).filter_by(id=order_id))
        for order_item in order.order_items:
            if order_item.product.stock_count < order_item.count:
                return False
        return True


# Order.order_items.any(OrderItem.count > Product.stock_count).where(Product.id==OrderItem.product_id)
def return_order_item(item_id: int, quantity_returned: int):
    with LocalSession() as session:
        with session.begin():
            order_item = session.scalar(select(OrderItem).filter_by(id=item_id))
            order_item.quantity_returned = quantity_returned
            order_item.product.stock_count += quantity_returned
