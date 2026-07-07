import datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class Instrument(Base):
    __tablename__ = "instruments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    family: Mapped[str] = mapped_column(String(32), index=True)
    source: Mapped[str] = mapped_column(String(16))
    symbol: Mapped[str] = mapped_column(String(32))
    unit: Mapped[str] = mapped_column(String(16), default="")
    decimals: Mapped[int] = mapped_column(Integer, default=2)

    prices: Mapped[list["PriceDaily"]] = relationship(back_populates="instrument")


class PriceDaily(Base):
    __tablename__ = "prices_daily"
    __table_args__ = (UniqueConstraint("instrument_id", "date", name="uq_price_day"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    instrument_id: Mapped[int] = mapped_column(ForeignKey("instruments.id"), index=True)
    date: Mapped[datetime.date] = mapped_column(Date, index=True)
    close: Mapped[float] = mapped_column(Float)

    instrument: Mapped[Instrument] = relationship(back_populates="prices")


class Brief(Base):
    __tablename__ = "briefs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[datetime.date] = mapped_column(Date, unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    body_md: Mapped[str] = mapped_column(Text)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
