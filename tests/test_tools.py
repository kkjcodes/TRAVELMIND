"""Tests for tool executor functions."""
import pytest

from travel_mind.database import get_customer
from travel_mind.tools import execute_tool


class TestSearchDestinations:
    def test_luxury_destinations_returned(self):
        result = execute_tool("search_destinations", {"segment": "luxury"})
        assert "destinations" in result
        assert len(result["destinations"]) > 0

    def test_adventure_destinations_returned(self):
        result = execute_tool("search_destinations", {"segment": "adventure"})
        assert any("Patagonia" in d["name"] or "Iceland" in d["name"] or "Nepal" in d["name"]
                   for d in result["destinations"])

    def test_returns_at_most_three(self):
        result = execute_tool("search_destinations", {"segment": "family"})
        assert len(result["destinations"]) <= 3

    def test_total_found_in_result(self):
        result = execute_tool("search_destinations", {"segment": "business"})
        assert "total_found" in result


class TestGetHotelRecommendations:
    def test_five_star_hotels(self):
        result = execute_tool("get_hotel_recommendations", {"destination": "Maldives", "stars": 5})
        assert len(result["hotels"]) > 0
        assert all(h["stars"] == 5 for h in result["hotels"])

    def test_destination_in_result(self):
        result = execute_tool("get_hotel_recommendations", {"destination": "Paris"})
        assert all(h["destination"] == "Paris" for h in result["hotels"])

    def test_three_star_hotels(self):
        result = execute_tool("get_hotel_recommendations", {"destination": "Rome", "stars": 3})
        assert len(result["hotels"]) > 0


class TestEstimateTripCost:
    def test_returns_estimated_total(self):
        result = execute_tool("estimate_trip_cost", {"destination": "Maldives", "duration_days": 7})
        assert "estimated_total" in result
        assert result["estimated_total"] > 0

    def test_breakdown_has_three_keys(self):
        result = execute_tool("estimate_trip_cost", {"destination": "Paris", "duration_days": 5})
        assert set(result["breakdown"].keys()) == {"flights", "hotel", "activities"}

    def test_longer_trips_cost_more(self):
        r7 = execute_tool("estimate_trip_cost", {"destination": "Iceland", "duration_days": 7})
        r14 = execute_tool("estimate_trip_cost", {"destination": "Iceland", "duration_days": 14})
        assert r14["estimated_total"] > r7["estimated_total"]

    def test_luxury_profile_costs_more_than_occasional(self):
        luxury = get_customer(1)
        occasional = get_customer(5)
        r_luxury = execute_tool("estimate_trip_cost", {"destination": "Paris", "duration_days": 7}, luxury)
        r_occasional = execute_tool("estimate_trip_cost", {"destination": "Paris", "duration_days": 7}, occasional)
        assert r_luxury["estimated_total"] > r_occasional["estimated_total"]


class TestComputeSegmentScore:
    def test_platinum_high_score(self):
        result = execute_tool("compute_segment_score", {"customer_id": 1})
        assert result["score"] >= 0.7
        assert result["tier"] == "Platinum"

    def test_standard_low_score(self):
        result = execute_tool("compute_segment_score", {"customer_id": 5})
        assert result["score"] < 0.7

    def test_score_between_zero_and_one(self):
        for cid in range(1, 6):
            result = execute_tool("compute_segment_score", {"customer_id": cid})
            assert 0.0 <= result["score"] <= 1.0


class TestGetTravelerProfile:
    def test_existing_customer(self):
        result = execute_tool("get_traveler_profile", {"customer_id": 1})
        assert result["name"] == "Alexandra Chen"

    def test_missing_customer(self):
        result = execute_tool("get_traveler_profile", {"customer_id": 9999})
        assert "error" in result


class TestSubmitForApproval:
    def test_creates_hitl_request(self):
        result = execute_tool("submit_for_approval", {
            "action_type": "booking_confirmation",
            "customer_id": 1,
            "customer_name": "Alexandra Chen",
            "payload": {"destination": "Maldives"},
            "estimated_value": 12000.0,
            "rationale": "High-value booking requires approval",
        })
        assert result["status"] == "pending"
        assert "approval_id" in result

    def test_approval_id_is_string(self):
        result = execute_tool("submit_for_approval", {
            "action_type": "bulk_marketing_send",
            "customer_id": 2,
            "customer_name": "Marcus Williams",
            "payload": {"campaign": "summer2025"},
            "estimated_value": 1.0,
            "rationale": "Bulk send requires approval",
        })
        assert isinstance(result["approval_id"], str)
        assert len(result["approval_id"]) > 0


class TestGenerateEmailCampaign:
    def test_returns_subject_and_body(self):
        result = execute_tool("generate_email_campaign", {
            "customer_id": 1,
            "campaign_type": "destination_spotlight",
            "featured_destination": "Santorini",
            "offer_value": 500.0,
        })
        assert "subject" in result
        assert "body" in result
        assert "Santorini" in result["subject"] or "Santorini" in result["body"]

    def test_customer_name_in_body(self):
        result = execute_tool("generate_email_campaign", {
            "customer_id": 1,
            "campaign_type": "loyalty_reward",
        })
        assert "Alexandra" in result["body"]


class TestUnknownTool:
    def test_unknown_tool_returns_error(self):
        result = execute_tool("nonexistent_tool", {})
        assert "error" in result
