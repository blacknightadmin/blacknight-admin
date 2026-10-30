from datetime import datetime, timezone, timedelta
from sqlalchemy import cast, select, String

from db import Order, OrderItem, Product, Supplier
import db


def _exec(stmt, scalar=False, scalars_all=False):
    SessionLocal = db.get_session_factory()
    with SessionLocal() as session:
        result = session.execute(stmt)
        if scalar:
            return result.scalar_one_or_none()
        if scalars_all:
            return result.scalars().all()
        else:
            return result.all()


def get_supplier_choices():
    stmt = select(Supplier.id, Supplier.name).order_by(Supplier.name)
    return [tuple(row) for row in _exec(stmt)]


def get_product_choices():
    stmt = select(Product.id, Product.name).where(Product.stock_count > 0)
    return [tuple(row) for row in _exec(stmt)]


def get_orderitem_by_id(id):
    return _exec(select(OrderItem).filter_by(id=id), scalar=True)


def get_orderitems_by_order_id(order_id):
    return _exec(select(OrderItem).filter_by(order_id=order_id))


def get_returnable_items():
    cutoff = lambda: datetime.now(timezone.utc) - timedelta(days=14)
    stmt = (
        select(OrderItem)
        .join(OrderItem.order)
        .where(
            Order.delivered_at >= cutoff(),
        )
        .order_by(OrderItem.quantity_returned.desc(), Order.created_at.desc())
    )
    return _exec(stmt, scalars_all=True)


def can_return_item(order_item: OrderItem):
    cutoff = datetime.now(timezone.utc) - timedelta(days=14)
    within_cutoff = order_item.order.delivered_at >= cutoff
    return within_cutoff


def get_order_choices():
    stmt = select(Order.id, "Order #" + cast(Order.id, String)).order_by(
        Order.created_at.desc()
    )
    return [tuple(row) for row in _exec(stmt)]


def get_product_count(prod_id: int):
    return _exec(select(Product.stock_count).filter_by(id=prod_id), scalar=True)


def get_order_status_by_id(order_id: int):
    return _exec(select(Order.status).filter_by(id=order_id), scalar=True)


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
    SessionLocal = db.get_session_factory()
    with SessionLocal() as session:
        order = session.scalar(select(Order).filter_by(id=order_id))
        for order_item in order.order_items:
            if order_item.product.stock_count < order_item.count:
                return False
        return True


def return_order_item(item_id: int, quantity_returned: int):
    SessionLocal = db.get_session_factory()
    with SessionLocal() as session:
        with session.begin():
            order_item = session.scalar(select(OrderItem).filter_by(id=item_id))
            prev_quantity_returned = order_item.quantity_returned
            order_item.product.stock_count += quantity_returned - prev_quantity_returned
            order_item.quantity_returned = quantity_returned
