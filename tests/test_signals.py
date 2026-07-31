from app.services.signals.engine import SignalEngine


def test_score_below_review_is_rejected(monkeypatch):
    engine = SignalEngine()
    monkeypatch.setattr(engine.settings, "signal_review_threshold", 65.0)
    monkeypatch.setattr(engine.settings, "signal_actionable_threshold", 80.0)
    result = engine.classify(54.0, risk_approved=True)
    assert result.status == "rejected"
    assert result.actionable is False


def test_review_band_requires_human_review(monkeypatch):
    engine = SignalEngine()
    monkeypatch.setattr(engine.settings, "signal_review_threshold", 65.0)
    monkeypatch.setattr(engine.settings, "signal_actionable_threshold", 80.0)
    result = engine.classify(72.0, risk_approved=True)
    assert result.status == "review"
    assert result.actionable is False


def test_actionable_requires_score_and_risk(monkeypatch):
    engine = SignalEngine()
    monkeypatch.setattr(engine.settings, "signal_review_threshold", 65.0)
    monkeypatch.setattr(engine.settings, "signal_actionable_threshold", 80.0)
    assert engine.classify(85.0, risk_approved=True).status == "actionable"
    assert engine.classify(85.0, risk_approved=False).status == "rejected"


def test_consensus_score_uses_real_technical_score():
    engine = SignalEngine()
    score, components = engine.score({"confidence": 0.8}, technical_score=100)
    assert score == 85.0
    assert components["technical"] == 100.0
