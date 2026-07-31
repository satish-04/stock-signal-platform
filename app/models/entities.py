from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4
from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, Index, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class NewsEvent(Base):
    __tablename__ = "news_events"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    symbol: Mapped[str] = mapped_column(String(16), index=True)
    headline: Mapped[str] = mapped_column(Text)
    body: Mapped[str | None] = mapped_column(Text)
    provider: Mapped[str] = mapped_column(String(64), default="unknown")
    source_id: Mapped[str] = mapped_column(String(256), unique=True)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    raw: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class TechnicalSignal(Base):
    __tablename__ = "technical_signals"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    symbol: Mapped[str] = mapped_column(String(16), index=True)
    timeframe: Mapped[str] = mapped_column(String(16))
    signal: Mapped[str] = mapped_column(String(64))
    close: Mapped[Decimal] = mapped_column(Numeric(18, 6))
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    event_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class Analysis(Base):
    __tablename__ = "analyses"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    news_event_id: Mapped[UUID] = mapped_column(ForeignKey("news_events.id"), index=True)
    symbol: Mapped[str] = mapped_column(String(16), index=True)
    direction: Mapped[str] = mapped_column(String(16))
    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 4))
    impact: Mapped[str] = mapped_column(String(16))
    result: Mapped[dict] = mapped_column(JSON)
    model: Mapped[str] = mapped_column(String(64))
    prompt_version: Mapped[str] = mapped_column(String(32), default="v1")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class TradeSignal(Base):
    __tablename__ = "trade_signals"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    symbol: Mapped[str] = mapped_column(String(16), index=True)
    direction: Mapped[str] = mapped_column(String(16))
    strategy: Mapped[str] = mapped_column(String(64))
    score: Mapped[Decimal] = mapped_column(Numeric(6, 2))
    status: Mapped[str] = mapped_column(String(24), default="candidate", index=True)
    details: Mapped[dict] = mapped_column(JSON)
    risk_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

Index("ix_news_symbol_published", NewsEvent.symbol, NewsEvent.published_at)
Index("ix_technical_symbol_event", TechnicalSignal.symbol, TechnicalSignal.event_time)

class RiskDecisionRecord(Base):
    __tablename__ = "risk_decisions"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    trade_signal_id: Mapped[UUID] = mapped_column(
        ForeignKey("trade_signals.id", ondelete="CASCADE"), index=True
    )
    approved: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    reasons: Mapped[list] = mapped_column(JSON, default=list)
    policy_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
