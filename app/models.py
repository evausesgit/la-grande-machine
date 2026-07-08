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


class AssetManager(Base):
    __tablename__ = "asset_managers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(48), unique=True, index=True)
    nom: Mapped[str] = mapped_column(String(120))
    pays: Mapped[str] = mapped_column(String(32), default="")
    # boutique | geant_13f | conviction_13f
    type: Mapped[str] = mapped_column(String(24), index=True)
    blurb: Mapped[str] = mapped_column(String(300), default="")
    site_web: Mapped[str] = mapped_column(String(200), default="")
    cik_sec: Mapped[str] = mapped_column(String(16), default="")

    funds: Mapped[list["Fund"]] = relationship(back_populates="manager")


class Fund(Base):
    __tablename__ = "funds"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    manager_id: Mapped[int] = mapped_column(ForeignKey("asset_managers.id"), index=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    nom: Mapped[str] = mapped_column(String(160))
    isin: Mapped[str] = mapped_column(String(12), default="")
    strategie: Mapped[str] = mapped_column(String(200), default="")
    devise: Mapped[str] = mapped_column(String(8), default="EUR")
    note_source: Mapped[str] = mapped_column(String(300), default="")

    manager: Mapped[AssetManager] = relationship(back_populates="funds")
    snapshots: Mapped[list["FundSnapshot"]] = relationship(back_populates="fund")


class SourceDocument(Base):
    __tablename__ = "source_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    fund_id: Mapped[int] = mapped_column(ForeignKey("funds.id"), index=True)
    # fiche | lettre | 13f | rapport_annuel
    type: Mapped[str] = mapped_column(String(24))
    periode: Mapped[str] = mapped_column(String(10))  # « 2026-03 » ou « 2026-T1 »
    url: Mapped[str] = mapped_column(String(400))
    sha256: Mapped[str] = mapped_column(String(64), default="")
    fetched_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    # en_attente | extrait | erreur — les 13F arrivent déjà structurés : « extrait »
    statut_extraction: Mapped[str] = mapped_column(String(16), default="en_attente")


class FundSnapshot(Base):
    __tablename__ = "fund_snapshots"
    __table_args__ = (UniqueConstraint("fund_id", "date", name="uq_snapshot_fund_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    fund_id: Mapped[int] = mapped_column(ForeignKey("funds.id"), index=True)
    date: Mapped[datetime.date] = mapped_column(Date, index=True)
    source_document_id: Mapped[int | None] = mapped_column(ForeignKey("source_documents.id"), nullable=True)
    encours: Mapped[float | None] = mapped_column(Float, nullable=True)  # dans la devise du fonds
    nb_lignes_publiees: Mapped[int | None] = mapped_column(Integer, nullable=True)

    fund: Mapped[Fund] = relationship(back_populates="snapshots")
    positions: Mapped[list["Position"]] = relationship(back_populates="snapshot")
    document: Mapped[SourceDocument | None] = relationship()


class Security(Base):
    __tablename__ = "securities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nom_canonique: Mapped[str] = mapped_column(String(160), index=True)
    isin: Mapped[str] = mapped_column(String(12), default="", index=True)
    cusip: Mapped[str] = mapped_column(String(9), default="", index=True)
    ticker: Mapped[str] = mapped_column(String(16), default="")
    pays: Mapped[str] = mapped_column(String(32), default="")
    secteur: Mapped[str] = mapped_column(String(64), default="")
    instrument_id: Mapped[int | None] = mapped_column(ForeignKey("instruments.id"), nullable=True)


class SecurityAlias(Base):
    __tablename__ = "security_aliases"
    __table_args__ = (UniqueConstraint("security_id", "libelle_brut", name="uq_alias"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    security_id: Mapped[int] = mapped_column(ForeignKey("securities.id"), index=True)
    libelle_brut: Mapped[str] = mapped_column(String(160))
    source: Mapped[str] = mapped_column(String(32), default="")


class Position(Base):
    __tablename__ = "positions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    snapshot_id: Mapped[int] = mapped_column(ForeignKey("fund_snapshots.id"), index=True)
    security_id: Mapped[int | None] = mapped_column(ForeignKey("securities.id"), nullable=True, index=True)
    libelle_brut: Mapped[str] = mapped_column(String(160))
    poids_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    valeur: Mapped[float | None] = mapped_column(Float, nullable=True)  # 13F : valeur en dollars
    rang: Mapped[int] = mapped_column(Integer)

    snapshot: Mapped[FundSnapshot] = relationship(back_populates="positions")
    security: Mapped[Security | None] = relationship()


class These(Base):
    __tablename__ = "theses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    snapshot_id: Mapped[int] = mapped_column(ForeignKey("fund_snapshots.id"), index=True)
    security_id: Mapped[int | None] = mapped_column(ForeignKey("securities.id"), nullable=True, index=True)
    # achat | renforcement | allegement | vente | commentaire
    action: Mapped[str] = mapped_column(String(16))
    texte_fr: Mapped[str] = mapped_column(Text)
    citation_source: Mapped[str] = mapped_column(Text, default="")
    confiance: Mapped[float | None] = mapped_column(Float, nullable=True)


class Brief(Base):
    __tablename__ = "briefs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[datetime.date] = mapped_column(Date, unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    body_md: Mapped[str] = mapped_column(Text)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
