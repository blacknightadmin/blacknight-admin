from collections import namedtuple

from .queries import (
    decrement_products_in_order,
    increment_products_in_order,
    check_stock_count,
    set_delivered_at,
)

Actions = namedtuple("Actions", ["check", "action"])

ORDER_STATE_MACHINE = {
    "Pending": {
        "Cancelled": Actions(None, None),
        "Shipped": Actions(check_stock_count, decrement_products_in_order),
        "Delivered": Actions(check_stock_count, decrement_products_in_order),
    },
    "Shipped": {
        "Cancelled": Actions(None, increment_products_in_order),
        "Delivered": Actions(None, set_delivered_at),
    },
    "Delivered": {},
    "Cancelled": {},
}


def do_check(from_status, to_status, param):
    check_func = ORDER_STATE_MACHINE[from_status][to_status].check
    if check_func is not None:
        return check_func(param)


def do_action(from_status, to_status, param):
    action = ORDER_STATE_MACHINE[from_status][to_status].action
    if action is not None:
        action(param)
