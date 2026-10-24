"""L1 Contract: what goes into the service and what comes out.

Your tasks (about 12 minutes). Run `bash grade.sh l1` to check.
1. Complete `Complaint`: id (1-20 chars), text (1-4000 chars), channel (email/chat/branch/phone, default email).
2. Complete `TriageResult`: category (Category), priority (int 1-4), team (Team),
   summary (at most 200 chars), needs_human (bool, default False). Reject unknown fields.
3. Complete `parse_triage`: validate the model's raw text; if it's invalid, return
   `human_review(...)` instead of crashing.

Hints: `Field(min_length=..., max_length=..., ge=..., le=...)`, `ConfigDict(extra="forbid")`,
`TriageResult.model_validate_json(raw)`, `except ValidationError`.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal  # noqa: F401  (you'll need it for `channel`)

from pydantic import BaseModel, ConfigDict, Field, ValidationError  # noqa: F401


class Category(str, Enum):
    CARD_DISPUTE = "card_dispute"
    FRAUD = "fraud"
    ACCOUNT_ACCESS = "account_access"
    CHARGES = "charges"
    OTHER = "other"


class Team(str, Enum):
    DISPUTES = "disputes"
    FRAUD_OPS = "fraud_ops"
    DIGITAL_SUPPORT = "digital_support"
    BRANCH_SERVICES = "branch_services"
    HUMAN_REVIEW = "human_review"


class Complaint(BaseModel):
    """What the contact-centre system sends us."""
    id: str = Field(min_length=1, max_length=20)
    text: str = Field(min_length=1, max_length=4000)
    channel: Literal["email", "chat", "branch", "phone"] = "email"


class TriageResult(BaseModel):
    """What we send back. Code downstream routes on this, so it must be exact."""
    
    # (L1.2): model_config that rejects unknown fields
    model_config = ConfigDict(extra="forbid")
    # (L1.2): category, priority, team, summary, needs_human
    category: Category
    needs_human: bool = False
    priority: int = Field(ge=1, le=4)
    team: Team
    summary: str = Field(max_length=200)


def human_review(reason: str) -> TriageResult:
    """The safe answer when we can't trust the model's output. (Works once TriageResult is done.)"""
    return TriageResult(
        category=Category.OTHER, priority=2, team=Team.HUMAN_REVIEW, summary=reason[:200], needs_human=True
    )


def parse_triage(raw: str) -> TriageResult:
    """Validate the model's raw text. Never crash, never guess: bad output goes to a human."""
    try:
        return TriageResult.model_validate_json(raw)
    except ValidationError as e:
        return human_review(f"invalid model output ({e.error_count()} error(s))")