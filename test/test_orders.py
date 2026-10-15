import os
import pytest

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqladmin import Admin
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker, Session

from app.admin import OrderAdmin, OrderItemAdmin
from db import Base, Product, Order, OrderItem

from .baseline import create_baseline

load_dotenv()
DATABASE_URL = os.environ["TEST_DATABASE_URL"]


@pytest.fixture(scope="session")
def engine():
    engine = create_engine(DATABASE_URL)
    yield engine
    engine.dispose()


@pytest.fixture(scope="session", autouse=True)
def baseline(engine):
    Base.metadata.create_all(engine)
    try:
        create_baseline(engine)
        yield
    finally:
        Base.metadata.drop_all(engine)


@pytest.fixture(scope="session", autouse=True)
def verified_baseline(baseline, engine):
    with Session(engine) as session:
        products_exist = select(1).where(select(Product.id).exists())
        orders_exist = select(1).where(select(Order.id).exists())
        orderitems_exist = select(1).where(select(OrderItem.id).exists())

        if any(
            session.execute(stmt).scalar_one_or_none() is None
            for stmt in [products_exist, orders_exist, orderitems_exist]
        ):
            pytest.exit(
                "Test cannot proceed with empty product, order or orderitem table in the test database.",
                returncode=1,
            )


@pytest.fixture
def session_factory(engine):
    connection = engine.connect()
    transaction = connection.begin()
    SessionLocal = sessionmaker(
        bind=connection,
        join_transaction_mode="create_savepoint",
        expire_on_commit=False,
    )
    try:
        yield SessionLocal
    finally:
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(session_factory, engine, monkeypatch):
    import db

    monkeypatch.setattr(db, "get_session_factory", lambda: session_factory)

    app = FastAPI()
    admin = Admin(
        app, engine=engine, session_maker=session_factory, templates_dir="app/templates"
    )
    admin.add_view(OrderAdmin)
    admin.add_view(OrderItemAdmin)

    return TestClient(app)