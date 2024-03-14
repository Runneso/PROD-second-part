from typing import List
from db import Base, engine
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Text, Integer, Boolean, Float, JSON


class Countries(Base):
    __tablename__ = "countries"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    alpha2: Mapped[str] = mapped_column(Text, nullable=False)
    alpha3: Mapped[str] = mapped_column(Text, nullable=False)
    region: Mapped[str] = mapped_column(Text, nullable=True)


class Users(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    login: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    password: Mapped[str] = mapped_column(Text, nullable=False)
    email: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    countryCode: Mapped[str] = mapped_column(Text, nullable=False)
    isPublic: Mapped[bool] = mapped_column(Boolean, nullable=False)
    phone: Mapped[str] = mapped_column(Text, nullable=True, unique=True)
    image: Mapped[str] = mapped_column(Text, nullable=True)


class Tokens(Base):
    __tablename__ = "tokens"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    login: Mapped[str] = mapped_column(Text, nullable=False)
    token: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    creation_time: Mapped[float] = mapped_column(Float, nullable=False)


class Friends(Base):
    __tablename__ = "friends"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    login: Mapped[str] = mapped_column(Text, nullable=False)
    friend: Mapped[str] = mapped_column(Text, nullable=False)
    addedAt: Mapped[str] = mapped_column(Text, nullable=False)


class Posts(Base):
    __tablename__ = "posts"
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str] = mapped_column(Text, nullable=False)
    tags: Mapped[List[str]] = mapped_column(JSON, nullable=False)
    createdAt: Mapped[str] = mapped_column(Text, nullable=False)
    likesCount: Mapped[int] = mapped_column(Integer, nullable=False)
    dislikesCount: Mapped[int] = mapped_column(Integer, nullable=False)


class Marks(Base):
    __tablename__ = "marks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    post_id: Mapped[str] = mapped_column(Text, nullable=False)
    login: Mapped[str] = mapped_column(Text, nullable=False)
    liked: Mapped[bool] = mapped_column(Boolean, nullable=False)


def create_db() -> None:
    Base.metadata.create_all(engine)
