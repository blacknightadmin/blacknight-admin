import enum
import os
from datetime import datetime
from decimal import Decimal
from typing import Optional

from dotenv import load_dotenv
from sqlalchemy import (DECIMAL, DateTime, Enum, ForeignKey, String,
                        create_engine)
from sqlalchemy.orm import (DeclarativeBase, Mapped, mapped_column,
                            relationship, sessionmaker)

load_dotenv()
engine = create_engine(os.environ["DATABASE_URL"], echo=True)
LocalSession = sessionmaker(engine)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(32))
    hash_password: Mapped[str]

    def __repr__(self):
        return "User(" + format_row_attrs(self, "id", "username") + ")"


class Platform(enum.Enum):
    Alibaba = "alibaba"
    Amazon = "amazon"
    eBay = "eBay"
    Local = "local"


class Supplier(Base):
    __tablename__ = "supplier"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    platform: Mapped[enum.Enum] = mapped_column(Enum(Platform))
    contact_info: Mapped[Optional[str]]

    def __repr__(self):
        return f"Supplier({format_row_attrs(self, 'id', 'name', 'platform')})"

    def __str__(self):
        return self.name


class Product(Base):
    __tablename__ = "product"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    # 9,999,999 ~ N 10million
    price: Mapped[Decimal] = mapped_column(DECIMAL(7, 2))
    stock_count: Mapped[int]

    supplier_id: Mapped[int] = mapped_column(ForeignKey(Supplier.id))
    supplier: Mapped[Supplier] = relationship()

    def __repr__(self):
        return "Product(" + format_row_attrs(self, "name", "price", "stock_count") + ")"


def format_row_attrs(model: Base, *attrs):
    """
    Returns: name=model.name, age=mode.age, ...
    """
    return ", ".join(f"{attr}={model.__getattribute__(attr)}" for attr in attrs)


if __name__ == "__main__":
    Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)
