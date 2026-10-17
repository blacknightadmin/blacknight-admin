from collections import namedtuple
from datetime import date, timedelta

from sqlalchemy import literal_column

ReportConf = namedtuple(
    "ReportConf",
    ["date_trunc_field", "time_series_start", "time_series_step", "date_format_string"],
)

REPORT_OPTIONS = {
    "daily": ReportConf(
        "day",
        lambda: date.today() - timedelta(days=14),
        literal_column("INTERVAL '1 day'"),
        "%b-%d-%Y",
    ),
    "weekly": ReportConf(
        "week",
        lambda: date.today() - timedelta(weeks=4),
        literal_column("INTERVAL '1 week'"),
        "%Y-%b-%d",
    ),
    "monthly": ReportConf(
        "month",
        lambda: date.today() - timedelta(weeks=12),
        literal_column("INTERVAL '4 weeks'"),
        "%b-%Y",
    ),
}
