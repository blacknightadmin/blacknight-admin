from datetime import date

from sqlalchemy import DateTime, func, select
from sqlalchemy.orm import Session

from db import Order
from .timebased_report_conf import ReportConf, REPORT_OPTIONS


def generate_report(session: Session, option: str):
    """
    WITH order_count AS (
        SELECT DATE_TRUNC(field, "order".created_at) AS day,
                COUNT("order".id) AS count
        FROM "order"
        GROUP BY DATE_TRUNC(field, "order".created_at)
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

    SELECT trunc_time_series.day, order_count.count
    FROM trunc_time_series
    LEFT JOIN order_count ON trunc_time_series.day = order_count.day;
    """
    assert option in REPORT_OPTIONS

    config: ReportConf = REPORT_OPTIONS[option]

    bucket = func.date_trunc(config.date_trunc_field, Order.created_at, type_=DateTime)
    order_count = (
        select(bucket.label(option), func.count(Order.id).label("count"))
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
            func.coalesce(order_count.c.count, 0),
        )
        .select_from(trunc_time_series)
        .join(
            order_count,
            trunc_time_series.c[option] == order_count.c[option],
            isouter=True,
        )
    )

    return [tuple(row) for row in session.execute(stmt).all()]
