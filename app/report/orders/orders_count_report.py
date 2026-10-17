from datetime import date

from sqlalchemy import DateTime, func, select
from sqlalchemy.orm import Session

from db import Order
from .conf_timeseries import ReportConf
from .time_series_base import TimeSeriesReportBase


class OrderCountReport(TimeSeriesReportBase):
    def __init__(self):
        super().__init__(agg_col="count")

    def aggregate_table(self, option):
        """
        WITH order_count_table AS (
            SELECT DATE_TRUNC(field, "order".created_at) AS option,
                    COUNT("order".id) AS count
            FROM "order"
            GROUP BY DATE_TRUNC(field, "order".created_at)
            ORDER BY option
        )
        """
        config: ReportConf = self.options[option]
        bucket = func.date_trunc(
            config.date_trunc_field, Order.created_at, type_=DateTime
        )
        stmt = (
            select(bucket.label(option), func.count(Order.id).label(self.agg_col))
            .group_by(bucket)
            .order_by(bucket)
            .cte()
        )
        return stmt


def generate_report(session: Session, option: str):
    return OrderCountReport().get_report(session, option)
