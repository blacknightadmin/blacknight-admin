from datetime import date

from sqlalchemy import DateTime, func, select
from sqlalchemy.orm import Session

from db import Order, OrderItem, PaymentStatus
from .conf_timeseries import ReportConf
from .time_series_base import TimeSeriesReportBase


class RevenueReport(TimeSeriesReportBase):
    def __init__(self):
        super().__init__(agg_col="revenue")

    def aggregate_table(self, option):
        """
        WITH revenue AS (
            SELECT DATE_TRUNC(field, "order".delivered_at) AS day,
                    SUM(orderitem.price * (orderitem.count - orderitem.quantity_returned)) AS revenue
            FROM "order"
            JOIN orderitem ON order.id = orderitem.order_id
            GROUP BY DATE_TRUNC(field, "order".delivered_at)
            ORDER BY day
        )
        """
        config: ReportConf = self.options[option]
        bucket = func.date_trunc(
            config.date_trunc_field, Order.delivered_at, type_=DateTime
        )
        revenue_table = (
            select(
                bucket.label(option),
                func.sum(
                    OrderItem.price * (OrderItem.count - OrderItem.quantity_returned)
                ).label(self.agg_col),
            )
            .select_from(Order)
            .join(Order.order_items)
            .where(
                Order.delivered_at.is_not(None),
                Order.payment_status == PaymentStatus.Paid,
            )
            .group_by(bucket)
            .order_by(bucket)
            .cte()
        )
        return revenue_table

    def format_report(self, result, option):
        config = self.options[option]

        return [
            (row[0].strftime(config.date_format_string), f"{float(row[1]):.2f}")
            for row in result
        ]


def generate_report(session: Session, option: str):
    return RevenueReport().get_report(session, option)
