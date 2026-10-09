from db import Order, OrderStatus, PaymentStatus
from queries import get_order_choices

class OrderStatusFilter:
    title = "Status"
    parameter_name = "status"
    template = "sqladmin/filters/lookup_filter.html"

    async def lookups(self, request, model, run_query):
        return [(s.name, s.name) for s in OrderStatus]

    async def get_filtered_query(self, query, value, model):
        return query.filter(Order.status==OrderStatus[value])

class PaymentStatusFilter:
    title = "Payment Status"
    parameter_name = "payment_status"
    template = "sqladmin/filters/lookup_filter.html"

    async def lookups(self, request, model, run_query):
        return [(s.name, s.name) for s in PaymentStatus]

    async def get_filtered_query(self, query, value, model):
        return query.filter(Order.payment_status==PaymentStatus[value])

class FilterOrderItemsByOrder:
    title = "Order"
    parameter_name = "order"
    template = "sqladmin/filters/lookup_filter.html"

    async def lookups(self, request, model, run_query):
        return [(str(value), label) for value, label in get_order_choices()]

    async def get_filtered_query(self, query, value, model):
        return query.join(model.order).filter(Order.id==int(value))   
    