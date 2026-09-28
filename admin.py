from sqladmin import ModelView

from db import Product, Supplier, User


class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.username]
    can_create = False
    can_edit = False
    can_delete = False


class SupplierAdmin(ModelView, model=Supplier):
    column_list = [Supplier.name, Supplier.platform, Supplier.contact_info]


class ProductAdmin(ModelView, model=Product):
    column_list = [Product.name, Product.price, Product.stock_count, Product.supplier]
