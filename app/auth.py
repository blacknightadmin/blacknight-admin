from passlib.hash import bcrypt
from sqladmin.authentication import AuthenticationBackend
from sqlalchemy import select
from starlette.requests import Request
from starlette.responses import RedirectResponse

import db


def get_user_by_username(username):
    SessionLocal = db.get_session_factory()
    with SessionLocal() as session:
        return session.execute(
            select(db.User).filter_by(username=username)
        ).scalar_one_or_none()


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool | RedirectResponse:
        form = await request.form()
        username, password = form["username"], form["password"]

        user = get_user_by_username(username)
        if user and bcrypt.verify(password, user.hash_password):
            request.session.update({"user_id": user.id})
            return True
        return False

    async def authenticate(self, request: Request) -> bool:
        return request.session.get("user_id") is not None

    async def logout(self, request: Request) -> bool | RedirectResponse:
        request.session.clear()
