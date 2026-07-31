import asyncio
import json
from datetime import datetime, timedelta, timezone

import structlog
from redis.asyncio import Redis

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import SessionLocal, engine
from app.models.entities import RiskDecisionRecord, TradeSignal
from app.schemas.events import TradingViewWebhook
from app.services.brokers.factory import get_broker
from app.services.llm.claude import ClaudeNewsAnalyzer
from app.services.options.engine import OptionsEngine
from app.services.risk.engine import RiskEngine
from app.services.signals.engine import SignalEngine
from app.services.technical.engine import TechnicalScoringEngine


async def persist_result(result: dict, candidate: dict, decision) -> TradeSignal:
    settings = get_settings()
    strategy = str(candidate.get("strategy", "no_trade"))
    details = {
        "candidate": candidate,
        "risk_reasons": decision.reasons,
        "classification_reason": result["classification_reason"],
        "source_event_id": result["source_event_id"],
        "actionable": result["actionable"],
        "score_components": result["score_components"],
        "technical_analysis": result["technical_analysis"],
    }
    signal = TradeSignal(
        symbol=result["symbol"],
        direction=result["direction"],
        strategy=strategy,
        score=result["score"],
        status=result["status"],
        details=details,
        risk_approved=decision.approved,
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=settings.signal_ttl_seconds),
    )
    async with SessionLocal() as session:
        async with session.begin():
            session.add(signal)
            await session.flush()
            session.add(
                RiskDecisionRecord(
                    trade_signal_id=signal.id,
                    approved=decision.approved,
                    reasons=decision.reasons,
                    policy_snapshot={
                        "max_risk_per_trade_pct": settings.max_risk_per_trade_pct,
                        "max_open_positions": settings.max_open_positions,
                        "review_threshold": settings.signal_review_threshold,
                        "actionable_threshold": settings.signal_actionable_threshold,
                    },
                )
            )
        await session.refresh(signal)
    return signal


async def run() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    log = structlog.get_logger()
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    broker = get_broker()
    claude = ClaudeNewsAnalyzer()
    options = OptionsEngine()
    risk = RiskEngine()
    signals = SignalEngine()
    technicals = TechnicalScoringEngine()
    last_id = "0-0"
    log.info(
        "signal_worker_started",
        mode=settings.market_data_mode,
        review_threshold=settings.signal_review_threshold,
        actionable_threshold=settings.signal_actionable_threshold,
    )
    try:
        while True:
            streams = await redis.xread({"technical-signals": last_id}, count=10, block=5000)
            for _, messages in streams:
                for event_id, fields in messages:
                    last_id = event_id
                    try:
                        tv = TradingViewWebhook.model_validate_json(fields["payload"])
                        direction = (
                            "bullish"
                            if "bull" in tv.signal.lower()
                            else "bearish"
                            if "bear" in tv.signal.lower()
                            else "neutral"
                        )
                        news = await claude.analyze(
                            tv.symbol,
                            f"Technical event: {tv.signal}",
                            None,
                        )
                        if news["direction"] == "neutral":
                            news["direction"] = direction
                        chain = await broker.option_chain(tv.symbol)
                        candidate = options.choose_defined_risk(news["direction"], chain)
                        decision = risk.evaluate(candidate)
                        technical_result = technicals.score(tv.model_dump(), news["direction"])
                        score, score_components = signals.score(news, technical_result.score)
                        classification = signals.classify(score, decision.approved)
                        result = {
                            "symbol": tv.symbol,
                            "direction": news["direction"],
                            "score": score,
                            "status": classification.status,
                            "actionable": classification.actionable,
                            "classification_reason": classification.reason,
                            "candidate": candidate,
                            "score_components": score_components,
                            "technical_analysis": technical_result.model_dump(),
                            "risk_approved": decision.approved,
                            "risk_reasons": decision.reasons,
                            "source_event_id": event_id,
                        }
                        persisted = await persist_result(result, candidate, decision)
                        result["signal_id"] = str(persisted.id)
                        await redis.xadd("trade-signals", {"payload": json.dumps(result)})
                        log.info("signal_evaluated", **result)
                    except Exception:
                        log.exception("signal_processing_failed", source_event_id=event_id)
    finally:
        await redis.aclose()
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(run())
