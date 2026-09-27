from dotenv import load_dotenv
from sqlalchemy import create_engine, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
import os

load_dotenv()
engine = create_engine(os.environ["DATABASE_URL"], echo=True)
LocalSession = sessionmaker(engine)

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__="users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(32))
    hash_password: Mapped[str]
    # email: Mapped[str] = mapped_column(nullable=True)

    def __repr__(self):
        return f"User(id={self.id}, username={self.usernamename})"

if __name__=="__main__":
    Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)