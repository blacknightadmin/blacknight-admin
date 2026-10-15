from datetime import date

from sqlalchemy import DateTime, func, select
from sqlalchemy.orm import Session

from db import Order, OrderItem, PaymentStatus
from .timebased_report_conf import ReportConf, REPORT_OPTIONS


def generate_report(session: Session, option: str):
    """
    WITH revenue AS (
        SELECT DATE_TRUNC(field, "order".delivered_at) AS day,
                SUM(orderitem.price * (orderitem.count - orderitem.quantity_returned)) AS revenue
        FROM "order"
        JOIN orderitem ON order.id = orderitem.order_id
        GROUP BY DATE_TRUNC(field, "order".delivered_at)
        ORDER BY day
    )

    WITH trunc_time_series AS (
        SELECT DATE_TRUNC(field, series) AS day
        FROM generate_series(
            CURRENT_DATE - INTERVAL '14 days',
            CURRENT_DATE,
            INTERVAL '1 day'
        ) AS series
    )

    SELECT trunc_time_series.day, revenue.revenue
    FROM trunc_time_series
    LEFT JOIN order_count ON trunc_time_series.day = revenue.day;
    """
    assert option in REPORT_OPTIONS

    config: ReportConf = REPORT_OPTIONS[option]

    bucket = func.date_trunc(
        config.date_trunc_field, Order.delivered_at, type_=DateTime
    )
    revenue = (
        select(
            bucket.label(option),
            func.sum(
                OrderItem.price * (OrderItem.count - OrderItem.quantity_returned)
            ).label("revenue"),
        )
        .select_from(Order)
        .join(Order.order_items)
        .where(
            Order.delivered_at.is_not(None),
            Order.payment_status == PaymentStatus.Paid,
        )
        .group_by(bucket)
        .order_by(bucket)
    ).cte()

    time_series = (
        func.generate_series(
            config.time_series_start(), date.today(), config.time_series_step
        )
        .table_valued(option)
        .render_derived()
    )
    trunc_time_series = select(
        func.date_trunc(config.date_trunc_field, time_series.c[option]).label(option)
    ).cte()

    stmt = (
        select(
            func.to_char(trunc_time_series.c[option], config.date_format_string),
            func.round(func.coalesce(revenue.c.revenue, 0), 2),
        )
        .select_from(trunc_time_series)
        .join(revenue, trunc_time_series.c[option] == revenue.c[option], isouter=True)
    )

    return [(row[0], float(row[1])) for row in session.execute(stmt).all()]
