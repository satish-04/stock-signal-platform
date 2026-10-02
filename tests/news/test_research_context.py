from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.events import ResearchArtifactInput
from app.services.news.context import recent_research_context


def test_research_artifact_normalizes_symbol_and_requires_known_source():
    artifact = ResearchArtifactInput(
        symbol=" aapl ",
        provider="grok-x-research",
        headline="Reviewed research",
        body="Research notes",
        source_id="grok-run-1",
        reviewed_by="analyst",
    )
    assert artifact.symbol == "AAPL"
    with pytest.raises(ValidationError):
        ResearchArtifactInput(
            symbol="AAPL",
            provider="other",
            headline="Unknown source",
            body="Notes",
            source_id="other-1",
            reviewed_by="analyst",
        )


class FakeScalars:
    def __init__(self, rows):
        self.rows = rows

    def all(self):
        return self.rows


class FakeSession:
    def __init__(self, rows):
        self.rows = rows

    async def scalars(self, _query):
        return FakeScalars(self.rows)


@pytest.mark.asyncio
async def test_recent_research_context_includes_sources_for_signal_audit():
    event_id = uuid4()
    event = type(
        "ResearchEvent",
        (),
        {
            "id": event_id,
            "provider": "grok-x-research",
            "source_id": "grok-run-1",
            "headline": "Reviewed report",
            "published_at": datetime.now(timezone.utc),
            "body": "Balanced source material",
            "raw": {"reviewed_by": "analyst", "human_reviewed": True},
        },
    )()

    context, references = await recent_research_context(FakeSession([event]), "AAPL")

    assert context is not None and "Balanced source material" in context
    assert references == [
        {
            "id": str(event_id),
            "provider": "grok-x-research",
            "source_id": "grok-run-1",
            "headline": "Reviewed report",
            "published_at": event.published_at.isoformat(),
            "reviewed_by": "analyst",
        }
    ]