"""Tests for Pydantic/dataclass models."""
import pytest
from travel_mind.models import (
    AgentResult,
    ApprovalStatus,
    HITLRequest,
    TravelerProfile,
    TravelerSegment,
)


class TestTravelerProfile:
    def _make_profile(self, **kwargs):
        defaults = dict(
            id=1, name="Test User", email="test@example.com",
            segment=TravelerSegment.LUXURY,
            preferred_destinations=["Maldives", "Paris"],
            budget_range=(5000.0, 20000.0),
            loyalty_tier="Platinum",
            travel_history=[{"destination": "Maldives", "year": 2024, "spend": 12000}],
            preferences={"hotel_stars": 5, "class": "business"},
        )
        defaults.update(kwargs)
        return TravelerProfile(**defaults)

    def test_to_dict_keys(self):
        p = self._make_profile()
        d = p.to_dict()
        assert set(d.keys()) == {"id", "name", "email", "segment", "preferred_destinations",
                                  "budget_range", "loyalty_tier", "travel_history", "preferences"}

    def test_segment_serialized_as_string(self):
        p = self._make_profile(segment=TravelerSegment.ADVENTURE)
        assert p.to_dict()["segment"] == "adventure"

    def test_budget_range_serialized_as_list(self):
        p = self._make_profile(budget_range=(1000.0, 5000.0))
        assert p.to_dict()["budget_range"] == [1000.0, 5000.0]


class TestHITLRequest:
    def _make_req(self, **kwargs):
        defaults = dict(
            id="test-id-1",
            action_type="marketing_email",
            customer_id=1,
            customer_name="Alice",
            payload={"subject": "Hi"},
            estimated_value=100.0,
            rationale="Test",
            status=ApprovalStatus.PENDING,
        )
        defaults.update(kwargs)
        return HITLRequest(**defaults)

    def test_low_value_email_no_approval(self):
        req = self._make_req(estimated_value=100.0, action_type="marketing_email")
        assert req.requires_approval() is False

    def test_high_value_requires_approval(self):
        req = self._make_req(estimated_value=501.0, action_type="marketing_email")
        assert req.requires_approval() is True

    def test_exactly_at_threshold_no_approval(self):
        req = self._make_req(estimated_value=500.0, action_type="marketing_email")
        assert req.requires_approval() is False

    def test_booking_confirmation_always_requires_approval(self):
        req = self._make_req(estimated_value=1.0, action_type="booking_confirmation")
        assert req.requires_approval() is True

    def test_bulk_marketing_send_always_requires_approval(self):
        req = self._make_req(estimated_value=1.0, action_type="bulk_marketing_send")
        assert req.requires_approval() is True

    def test_default_status_is_pending(self):
        req = self._make_req()
        assert req.status == ApprovalStatus.PENDING

    def test_created_at_populated(self):
        req = self._make_req()
        assert req.created_at is not None and len(req.created_at) > 0


class TestAgentResult:
    def test_success_result(self):
        r = AgentResult(success=True, data={"key": "val"}, agent="profile")
        assert r.success is True
        assert r.error == ""

    def test_failure_result(self):
        r = AgentResult(success=False, data=None, agent="discovery", error="not found")
        assert r.success is False
        assert "not found" in r.error
