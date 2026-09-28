import os

from dotenv import load_dotenv
from fastapi import FastAPI
from sqladmin import Admin, ModelView

from admin import ProductAdmin, SupplierAdmin, UserAdmin
from auth import AdminAuth
from db import engine

load_dotenv()

app = FastAPI()
auth_backend = AdminAuth(os.environ["SECRET_KEY"])
admin = Admin(app, engine, authentication_backend=auth_backend)

admin.add_view(UserAdmin)
admin.add_view(SupplierAdmin)
admin.add_view(ProductAdmin)
