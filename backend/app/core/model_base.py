"""Shared SQLAlchemy 2 declarative base; model registration lives in app.models."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
