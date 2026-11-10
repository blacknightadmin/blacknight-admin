from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.applications import Starlette
from starlette.routing import Route


def configure_rate_limited_login_route(
    app: Starlette, login_endpoint, limit_exceeded_handler, limit_value, storage_uri
):
    limiter = Limiter(key_func=get_remote_address, storage_uri=storage_uri)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, limit_exceeded_handler)

    rate_limited_login_route = get_rate_limited_login_route(
        limiter, login_endpoint, limit_value
    )
    app.router.routes.insert(0, rate_limited_login_route)


def get_rate_limited_login_route(limiter: Limiter, login_endpoint, limit_value):
    limit_decorator = limiter.limit(limit_value)
    rate_limited_login = limit_decorator(login_endpoint)
    return Route(
        "/login", endpoint=rate_limited_login, name="login", methods=["GET", "POST"]
    )
