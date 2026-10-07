import os

from dotenv import load_dotenv
from fastapi import FastAPI
from sqladmin import Admin

from admin import (
    OrderAdmin,
    OrderItemAdmin,
    ProductAdmin,
    SupplierAdmin,
    UserAdmin,
    ReturnOrderItemAdin,
)
from auth import AdminAuth
from db import engine, LocalSession

load_dotenv()


class CustomAdmin(Admin):
    @staticmethod
    def get_save_redirect_url(request, form, model_view, obj):
        identity = request.path_params["identity"]
        if identity == "order":
            return request.url_for(
                "admin:details", identity=request.path_params["identity"], pk=obj.id
            )
        else:
            return Admin.get_save_redirect_url(request, form, model_view, obj)


app = FastAPI()
auth_backend = AdminAuth(os.environ["SECRET_KEY"])
admin = CustomAdmin(
    app, engine, authentication_backend=auth_backend, session_maker=LocalSession
)

admin.add_view(UserAdmin)
admin.add_view(SupplierAdmin)
admin.add_view(ProductAdmin)
admin.add_view(OrderAdmin)
admin.add_view(OrderItemAdmin)
admin.add_view(ReturnOrderItemAdin)
