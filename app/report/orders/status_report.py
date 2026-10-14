from collections import namedtuple
from sqlalchemy import values, column, String, select, func
from sqlalchemy.orm import Session

from db import Order, OrderStatus, PaymentStatus

ReportConf = namedtuple("ReportConf", ["status_enum", "status_column"])

REPORT_OPTIONS = {
    "order_status": ReportConf(OrderStatus, Order.status),
    "payment_status": ReportConf(PaymentStatus, Order.payment_status),
}


def generate_report(session: Session, option: str):
    """
    WITH status_cte(status) AS (
        VALUES ('Pending'),
                ('Shipped'),
                ('Delivered'),
                ('Cancelled')
    )

    WITH order_status_count AS (
        SELECT CAST(status AS CHAR) status,
            COUNT(status) count
        FROM "order"
        GROUP BY CAST(status AS CHAR)
        ORDER BY status
    )

    SELECT status_cte.status,
            order_status_count.count
    FROM status_cte
    LEFT JOIN order_status_count USING status
    """
    assert option in REPORT_OPTIONS

    config = REPORT_OPTIONS[option]
    status_cte = (
        values(column("status", String)).data(
            [(status.name,) for status in config.status_enum]
        )
    ).cte()

    order_status_count = (
        select(
            func.cast(config.status_column, String).label("status"),
            func.count(config.status_column).label("count"),
        )
        .group_by(config.status_column)
        .order_by(config.status_column)
    ).cte()

    stmt = (
        select(
            status_cte.c.status,
            func.coalesce(order_status_count.c.count, 0),
        )
        .select_from(status_cte)
        .join(
            order_status_count,
            order_status_count.c.status == status_cte.c.status,
            isouter=True,
        )
    )

    return [tuple(row) for row in session.execute(stmt).all()]
