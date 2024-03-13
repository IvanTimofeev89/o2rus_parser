
import os

import sqlalchemy as sa
import sqlalchemy.orm as so
from dotenv import load_dotenv
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()

POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")


DSN = f'postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@postgresdb:5432/{POSTGRES_DB}'
engine = sa.create_engine(url=DSN, echo=False)
Session = sessionmaker(bind=engine)
session = Session()


class Base(DeclarativeBase):
    pass


class O2Rus(Base):
    __tablename__ = "SAE J1939-71"

    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    can_id: so.Mapped[str] = so.mapped_column(sa.String(4), nullable=False)
    data_length: so.Mapped[str] = so.mapped_column(sa.String(10), nullable=False)
    length: so.Mapped[str] = so.mapped_column(sa.String(60), nullable=False)
    name: so.Mapped[str] = so.mapped_column(sa.String(255), nullable=False)
    rusname: so.Mapped[str] = so.mapped_column(sa.String(255), nullable=True)
    scaling: so.Mapped[str] = so.mapped_column(sa.String(100), nullable=False)
    range: so.Mapped[str] = so.mapped_column(sa.String(100), nullable=False)
    spn: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False)


def create_tables(engine):
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    create_tables(engine)
