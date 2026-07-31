from dataclasses import dataclass
from datetime import datetime
from typing import Literal

SweepCandidateType = Literal["WORKFLOW", "EXECUTION", "POSITION"]


@dataclass(frozen=True)
class SweepCandidate:
    candidate_id: str
    candidate_type: SweepCandidateType
    status: str
    account_id: str | None
    updated_at: datetime | None
