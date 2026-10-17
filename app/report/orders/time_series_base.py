from datetime import date
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .conf_timeseries import ReportConf, REPORT_OPTIONS


class TimeSeriesReportBase:
    def __init__(self, agg_col: str):
        self.agg_col = agg_col
        self.options = REPORT_OPTIONS

    def time_series_table(self, option: str):
        """
        WITH trunc_time_series AS (
            SELECT DATE_TRUNC(field, series) AS period
            FROM generate_series(
                CURRENT_DATE - INTERVAL '14 days',
                CURRENT_DATE,
                INTERVAL '1 day'
            ) AS series
        )
        """
        config: ReportConf = self.options[option]
        time_series = (
            func.generate_series(
                config.time_series_start(), date.today(), config.time_series_step
            )
            .table_valued(option)
            .render_derived()
        )
        trunc_time_series = select(
            func.date_trunc(config.date_trunc_field, time_series.c[option]).label(
                option
            )
        ).cte()

        return trunc_time_series

    def aggregate_table(self, option: str):
        """
        WITH aggregate_table AS (
            SELECT DATE_TRUNC(field, table.datetime_col) option,
                AGG_FUNC("order".id)
            FROM table
            GROUP BY DATE_TRUNC(field, table.datetime_col)
            ORDER BY option
        )
        """
        raise NotImplementedError

    def report_query(self, option: str):
        """
        SELECT time_series_table.option, aggregate_table.agg_col
        FROM time_series_table
        LEFT JOIN order_count ON time_series_table.option = aggregate_table.option;
        """
        time_series_table = self.time_series_table(option)
        aggregate_table = self.aggregate_table(option)

        stmt = (
            select(
                time_series_table.c[option],
                func.coalesce(aggregate_table.c[self.agg_col], 0),
            )
            .select_from(time_series_table)
            .join(
                aggregate_table,
                time_series_table.c[option] == aggregate_table.c[option],
                isouter=True,
            )
        )
        return stmt

    def get_report(self, session: Session, option: str):
        stmt = self.report_query(option)
        result = session.execute(stmt).all()
        formatted = self.format_report(result, option)
        return formatted

    def format_report(self, result, option):
        config = self.options[option]

        return [(row[0].strftime(config.date_format_string), row[1]) for row in result]
