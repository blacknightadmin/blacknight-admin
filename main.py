from dotenv import load_dotenv
from fastapi import FastAPI
from sqladmin import Admin, ModelView
import os

from auth import AdminAuth
from db import engine, User

load_dotenv()

app = FastAPI()
auth_backend = AdminAuth(os.environ["SECRET_KEY"])
admin = Admin(app, engine, authentication_backend=auth_backend)

class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.username]
    can_create = False
    can_edit = False
    can_delete = False

admin.add_view(UserAdmin)