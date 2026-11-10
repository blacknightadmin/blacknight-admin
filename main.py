import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded
from sqladmin import Admin
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request

from app.admin import (
    InventoryReport,
    OrderAdmin,
    OrderItemAdmin,
    OrderReport,
    ProductAdmin,
    SupplierAdmin,
    UserAdmin,
    ReturnOrderItemAdin,
)
from app.auth import AdminAuth
from login_rate_limit import configure_rate_limited_login_route
import db

load_dotenv()


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    context = {"error": f"Rate limit exceeded: {exc.detail}"}
    response = await admin.templates.TemplateResponse(
        request, "sqladmin/login.html", context=context, status_code=429
    )

    request.app.state.limiter._inject_asgi_headers(
        response.headers, request.state.view_rate_limit
    )
    return response


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
app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ["SECRET_KEY"],
    max_age=int(os.environ["SESSION_COOKIE_AGE"]),
)

auth_backend = AdminAuth(os.environ["SECRET_KEY"])

admin = CustomAdmin(
    app,
    db.get_engine(),
    authentication_backend=auth_backend,
    session_maker=db.get_session_factory(),
    title="Blacknight Admin",
    templates_dir="app/templates",
)
admin.admin.mount(
    "/custom-statics",
    StaticFiles(directory="app/templates/sqladmin/static"),
    name="custom-statics",
)


limit_value = os.environ.get("RATE_LIMIT_VALUE", "5/minute")
REDIS_URL = os.environ["REDIS_URL"]

configure_rate_limited_login_route(
    admin.admin, admin.login, rate_limit_exceeded_handler, limit_value, REDIS_URL
)

admin.add_view(UserAdmin)
admin.add_view(SupplierAdmin)
admin.add_view(ProductAdmin)
admin.add_view(OrderAdmin)
admin.add_view(OrderItemAdmin)
admin.add_view(ReturnOrderItemAdin)
admin.add_view(OrderReport)
admin.add_view(InventoryReport)


@app.get("/")
def home():
    return RedirectResponse("/admin/")
