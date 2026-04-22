from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class TravelerSegment(str, Enum):
    LUXURY = "luxury"
    BUSINESS = "business"
    FAMILY = "family"
    ADVENTURE = "adventure"
    OCCASIONAL = "occasional"


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass
class TravelerProfile:
    id: int
    name: str
    email: str
    segment: TravelerSegment
    preferred_destinations: list[str]
    budget_range: tuple[float, float]
    loyalty_tier: str
    travel_history: list[dict]
    preferences: dict[str, Any]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "segment": self.segment.value,
            "preferred_destinations": self.preferred_destinations,
            "budget_range": list(self.budget_range),
            "loyalty_tier": self.loyalty_tier,
            "travel_history": self.travel_history,
            "preferences": self.preferences,
        }


@dataclass
class TripRecommendation:
    destination: str
    hotel: str
    estimated_cost: float
    rationale: str
    highlights: list[str]
    booking_url: str = ""


@dataclass
class MarketingCampaign:
    customer_id: int
    customer_name: str
    subject: str
    body: str
    estimated_value: float
    action_type: str = "marketing_email"


@dataclass
class HITLRequest:
    id: str
    action_type: str
    customer_id: int
    customer_name: str
    payload: dict
    estimated_value: float
    rationale: str
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    resolved_at: str | None = None
    resolver_note: str = ""

    def requires_approval(self) -> bool:
        from travel_mind.config import HITL_VALUE_THRESHOLD, HITL_ACTION_TYPES
        return (
            self.estimated_value > HITL_VALUE_THRESHOLD
            or self.action_type in HITL_ACTION_TYPES
        )


@dataclass
class AgentResult:
    success: bool
    data: Any
    agent: str
    tokens_used: int = 0
    error: str = ""
