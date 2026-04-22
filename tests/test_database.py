"""Tests for database layer."""
import uuid

import pytest

from travel_mind.database import (
    get_all_customers,
    get_customer,
    get_hitl_request,
    get_pending_hitl_requests,
    resolve_hitl_request,
    save_hitl_request,
)
from travel_mind.models import ApprovalStatus, HITLRequest, TravelerSegment


class TestCustomerQueries:
    def test_seed_creates_five_customers(self):
        customers = get_all_customers()
        assert len(customers) == 5

    def test_get_customer_by_id(self):
        c = get_customer(1)
        assert c is not None
        assert c.name == "Alexandra Chen"
        assert c.segment == TravelerSegment.LUXURY

    def test_get_customer_segments(self):
        segments = {c.segment for c in get_all_customers()}
        expected = {TravelerSegment(s) for s in ["luxury", "business", "family", "adventure", "occasional"]}
        assert segments == expected

    def test_get_customer_not_found(self):
        assert get_customer(9999) is None

    def test_customer_budget_range_is_tuple(self):
        c = get_customer(1)
        assert isinstance(c.budget_range, tuple)
        assert len(c.budget_range) == 2

    def test_customer_preferred_destinations_is_list(self):
        c = get_customer(1)
        assert isinstance(c.preferred_destinations, list)
        assert len(c.preferred_destinations) > 0

    def test_customer_travel_history_is_list(self):
        c = get_customer(1)
        assert isinstance(c.travel_history, list)

    def test_customer_preferences_is_dict(self):
        c = get_customer(1)
        assert isinstance(c.preferences, dict)

    def test_all_customers_have_loyalty_tier(self):
        for c in get_all_customers():
            assert c.loyalty_tier in {"Platinum", "Gold", "Silver", "Standard"}

    def test_luxury_customer_budget_above_5000(self):
        c = get_customer(1)
        assert c.budget_range[0] >= 5000


class TestHITLDatabase:
    def _make_req(self, **kwargs) -> HITLRequest:
        defaults = dict(
            id=str(uuid.uuid4()),
            action_type="marketing_email",
            customer_id=1,
            customer_name="Test Customer",
            payload={"subject": "Test"},
            estimated_value=100.0,
            rationale="Test rationale",
        )
        defaults.update(kwargs)
        return HITLRequest(**defaults)

    def test_save_and_retrieve(self):
        req = self._make_req()
        save_hitl_request(req)
        fetched = get_hitl_request(req.id)
        assert fetched is not None
        assert fetched.customer_name == "Test Customer"

    def test_pending_queue_includes_saved(self):
        req = self._make_req()
        save_hitl_request(req)
        pending = get_pending_hitl_requests()
        ids = [r.id for r in pending]
        assert req.id in ids

    def test_resolve_approve(self):
        req = self._make_req()
        save_hitl_request(req)
        resolve_hitl_request(req.id, ApprovalStatus.APPROVED, "looks good")
        updated = get_hitl_request(req.id)
        assert updated.status == ApprovalStatus.APPROVED
        assert updated.resolver_note == "looks good"

    def test_resolve_reject(self):
        req = self._make_req()
        save_hitl_request(req)
        resolve_hitl_request(req.id, ApprovalStatus.REJECTED)
        updated = get_hitl_request(req.id)
        assert updated.status == ApprovalStatus.REJECTED

    def test_resolved_not_in_pending(self):
        req = self._make_req()
        save_hitl_request(req)
        resolve_hitl_request(req.id, ApprovalStatus.APPROVED)
        pending_ids = [r.id for r in get_pending_hitl_requests()]
        assert req.id not in pending_ids

    def test_resolve_nonexistent_returns_false(self):
        result = resolve_hitl_request("nonexistent-id", ApprovalStatus.APPROVED)
        assert result is False

    def test_get_nonexistent_hitl_request(self):
        assert get_hitl_request("nonexistent") is None

    def test_booking_confirmation_payload_stored(self):
        req = self._make_req(action_type="booking_confirmation", payload={"destination": "Maldives", "total": 12000})
        save_hitl_request(req)
        fetched = get_hitl_request(req.id)
        assert fetched.payload["destination"] == "Maldives"
        assert fetched.estimated_value == 100.0
