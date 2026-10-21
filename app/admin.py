from sqlalchemy import func, select, update
from sqladmin import BaseView, ModelView, expose, Flash
from starlette import status
from starlette.exceptions import HTTPException
from starlette.responses import RedirectResponse

from db import Order, OrderItem, Product, Supplier, User
from .filters import (
    FilterOrderItemsByOrder,
    FilterProductBySupplier,
    FilterSupplierByPlatform,
    PaymentStatusFilter,
    OrderStatusFilter,
)
from .forms import CustomOrderItemForm, ReturnOrderItemForm
from .queries import (
    get_orderitem_by_id,
    get_orderitems_by_order_id,
    get_product_choices,
    get_order_choices,
    get_order_status_by_id,
    get_returnable_items,
    return_order_item,
    can_return_item,
)
from .order_state_machine import ORDER_STATE_MACHINE, do_check, do_action
from .report.orders import report as order_report
import db

DATE_FORMAT_STRING = "%Y-%m-%d %H:%M:%S"


def date_formatter(model, attr, request):
    date = getattr(model, attr)
    if date:
        return date.strftime(DATE_FORMAT_STRING)
    return ""


class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.username]
    can_create = False
    can_edit = False
    can_delete = False


class SupplierAdmin(ModelView, model=Supplier):
    column_list = [Supplier.id, Supplier.name, Supplier.platform, Supplier.contact_info]
    column_details_list = [
        Supplier.name,
        Supplier.platform,
        Supplier.contact_info,
        Supplier.products,
    ]
    form_excluded_columns = [Supplier.products]
    category = "inventory"
    category_icon = "fa-regular fa-rectangle-list"

    column_filters = [FilterSupplierByPlatform()]
    column_searchable_list = [Supplier.name]


class ProductAdmin(ModelView, model=Product):
    column_list = [
        Product.id,
        Product.name,
        Product.price,
        Product.stock_count,
        Product.supplier,
    ]
    category = "inventory"
    category_icon = "fa-regular fa-rectangle-list"

    column_filters = [FilterProductBySupplier()]
    column_searchable_list = [Product.name]


class OrderAdmin(ModelView, model=Order):
    details_template = "sqladmin/custom_order_details.html"
    edit_template = "sqladmin/custom_order_edit.html"
    create_template = "sqladmin/custom_order_create.html"
    # can_delete = False
    column_list = ["id", "status", "payment_status", "created_at"]
    column_details_exclude_list = [Order.order_items]

    column_formatters = {
        Order.id: lambda m, a: f"Order #{m.id}",
        Order.created_at: date_formatter,
    }
    column_formatters_detail = {
        Order.created_at: date_formatter,
        Order.delivered_at: date_formatter,
    }

    form_excluded_columns = [Order.order_items, Order.created_at, Order.delivered_at]

    column_filters = [PaymentStatusFilter(), OrderStatusFilter()]

    category = "orders"
    category_icon = "fa-solid fa-cart-shopping"

    def list_query(self, request):
        base_stmt = super().list_query(request)
        return base_stmt.order_by(Order.created_at.desc())

    async def details_context(self, request):
        pk = request.path_params["pk"]
        order_items = get_orderitems_by_order_id(pk)
        return {"order_items": order_items}

    async def get_custom_create_form(self, request):
        Form = await self.scaffold_form(self._form_create_rules)
        Form.status.kwargs["choices"] = [("Pending", "Pending")]
        return Form()

    async def create_context(self, request):
        context = await super().create_context(request)
        return {**context, "_form": await self.get_custom_create_form(request)}

    async def get_custom_edit_form(self, request):
        pk = request.path_params["pk"]

        order_status = get_order_status_by_id(pk).name
        valid_status_choices = [(order_status, order_status)] + [
            (status, status) for status in ORDER_STATE_MACHINE[order_status]
        ]

        Form = await self.scaffold_form(self.form_edit_rules)
        model = await self.get_object_for_edit(request)
        initial_data = await self.get_form_data_for_edit(model)
        Form.status.kwargs["choices"] = valid_status_choices

        return Form(data=initial_data)

    async def edit_context(self, request):
        context = await super().edit_context(request)
        return {**context, "_form": await self.get_custom_edit_form(request)}

    async def update_model(self, request, pk, data):
        SessionLocal = db.get_session_factory()
        with SessionLocal() as session:
            with session.begin():
                model = session.execute(
                    select(Order).filter_by(id=pk)
                ).scalar_one_or_none()
                if model is None:
                    raise HTTPException(status.HTTP_404_NOT_FOUND)

                from_status = model.status.name
                to_status = data["status"]
                status_change = from_status != to_status

                # status_change allowed ?
                if status_change and not do_check(from_status, to_status, pk):
                    err_msg = f"Can't move {model} from {from_status} to {to_status}, possibly due to products with low stock count."
                    raise Exception(err_msg)

                session.execute(update(Order).values(data).where(Order.id == pk))

                # do status change action
                if status_change:
                    do_action(from_status, to_status, model)
                return model

    async def on_model_change(self, data, model, is_created, request):
        if is_created and data["status"] != "Pending":
            raise Exception("Newly created orders must have Pending status")
        return await super().on_model_change(data, model, is_created, request)

    async def on_model_delete(self, model, request):
        if model.status.name != "Pending" or len(model.order_items) > 0:
            raise Exception("Only pending orders with no items can be deleted!")


class OrderItemAdmin(ModelView, model=OrderItem):
    create_template = "sqladmin/custom_order_item_create.html"
    column_list = [
        OrderItem.product,
        OrderItem.order_id,
        OrderItem.count,
        OrderItem.order,
    ]

    column_filters = [FilterOrderItemsByOrder()]
    column_searchable_list = [OrderItem.product]

    category = "orders"
    category_icon = "fa-solid fa-cart-shopping"

    def list_query(self, request):
        base_stmt = super().list_query(request)
        return base_stmt.join(OrderItem.order).order_by(
            Order.created_at.desc(), OrderItem.count.desc()
        )

    async def scaffold_form(self, rules=None):
        form_class = CustomOrderItemForm
        form_class.product_id.kwargs["choices"] = get_product_choices()
        form_class.order_id.kwargs["choices"] = get_order_choices()
        return form_class

    async def on_model_change(self, data, model, is_created, request):
        if model.order:
            order_status = model.order.status.name
            msg = f"Only items from pending orders can be modified"
        else:
            order_status = get_order_status_by_id(data["order_id"]).name
            msg = "Items can only be added to pending orders"
        if order_status != "Pending":
            raise Exception(msg)

        return await super().on_model_change(data, model, is_created, request)

    async def on_model_delete(self, model, request):
        if model.order.status.name != "Pending":
            raise Exception("Only items in pending orders can be deleted!")

    def search_query(self, stmt, term):
        return stmt.join(OrderItem.product).filter(Product.name.like(f"%{term}%"))


class ReturnOrderItemAdin(BaseView):
    name = "Return Items"
    category = "orders"
    category_icon = "fa-solid fa-cart-shopping"

    @expose("/return-item/", methods=["GET"])
    async def list_returnable_items(self, request):
        context = {"order_items": get_returnable_items()}
        return await self.templates.TemplateResponse(
            request, "sqladmin/returnable_items_list.html", context=context
        )

    @expose("/return-item/{pk:int}/", methods=["GET", "POST"])
    async def edit_returnable_items(self, request):
        pk = request.path_params["pk"]
        model = get_orderitem_by_id(pk)

        if model is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND)
        elif not can_return_item(model):
            Flash.error(request, "Selected item cannot be returned")
            return RedirectResponse("/return-item/", status.HTTP_400_BAD_REQUEST)

        if request.method == "GET":
            return await self.templates.TemplateResponse(
                request,
                "sqladmin/return_item_form.html",
                {
                    "form": ReturnOrderItemForm(
                        data={"quantity_returned": model.quantity_returned}
                    ),
                    "model": model,
                    "form_opts": None,
                },
            )

        form_data = await request.form()
        form = ReturnOrderItemForm(form_data)
        context = {
            "form": form,
            "model": model,
            "form_opts": None,
        }

        form_validated = form.validate()
        quantity_okay = form.data["quantity_returned"] <= model.count
        if not quantity_okay:
            form.quantity_returned.errors.append(
                f"Quantity returned for this item cannot be greater than {model.count}"
            )

        if not (form_validated and quantity_okay):
            return await self.templates.TemplateResponse(
                request,
                "sqladmin/return_item_form.html",
                context,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        return_order_item(pk, form.data["quantity_returned"])

        return RedirectResponse("/admin/return-item/", status.HTTP_302_FOUND)


class OrderReport(BaseView):
    name = "Order Report"
    category = "reports"
    category_icon = "fa fa-line-chart"

    @expose("/reports/order/", methods=["GET"])
    async def reports(self, request):
        return await self.templates.TemplateResponse(
            request,
            "sqladmin/order_report.html",
            context=order_report.get_report_context(request),
        )
