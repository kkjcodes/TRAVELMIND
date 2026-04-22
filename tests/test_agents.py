"""Tests for agents using mocked Claude API."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from travel_mind.agents.base import BaseAgent
from travel_mind.agents.discovery_agent import DiscoveryAgent
from travel_mind.agents.marketing_agent import MarketingAgent
from travel_mind.agents.orchestrator import Orchestrator
from travel_mind.agents.profile_agent import ProfileAgent
from travel_mind.database import get_customer


def _make_mock_end_turn_response(text: str = "Test agent output"):
    """Build a mock anthropic response that triggers end_turn."""
    block = MagicMock()
    block.type = "text"
    block.text = text

    response = MagicMock()
    response.stop_reason = "end_turn"
    response.content = [block]
    response.usage.input_tokens = 100
    response.usage.output_tokens = 50
    return response


def _make_mock_tool_then_end(tool_name: str, tool_input: dict, final_text: str = "Done"):
    """Build two responses: first tool_use, then end_turn."""
    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.id = "test-tool-id"
    tool_block.name = tool_name
    tool_block.input = tool_input

    tool_response = MagicMock()
    tool_response.stop_reason = "tool_use"
    tool_response.content = [tool_block]
    tool_response.usage.input_tokens = 150
    tool_response.usage.output_tokens = 30

    end_block = MagicMock()
    end_block.type = "text"
    end_block.text = final_text

    end_response = MagicMock()
    end_response.stop_reason = "end_turn"
    end_response.content = [end_block]
    end_response.usage.input_tokens = 200
    end_response.usage.output_tokens = 80

    return [tool_response, end_response]


class TestBaseAgent:
    def test_extract_text_from_content(self):
        block = MagicMock()
        block.type = "text"
        block.text = "Hello world"
        result = BaseAgent._extract_text([block])
        assert result == "Hello world"

    def test_extract_text_ignores_non_text(self):
        b1 = MagicMock()
        b1.type = "tool_use"
        b1.text = "ignored"
        b2 = MagicMock()
        b2.type = "text"
        b2.text = "kept"
        result = BaseAgent._extract_text([b1, b2])
        assert result == "kept"

    def test_run_end_turn_returns_text(self):
        agent = BaseAgent()
        mock_response = _make_mock_end_turn_response("Profile analysis complete")
        with patch.object(agent._client.messages, "create", return_value=mock_response):
            text, tokens = agent.run("Test message")
        assert text == "Profile analysis complete"
        assert tokens == 150  # 100 input + 50 output

    def test_run_tool_use_loop(self):
        agent = BaseAgent()
        responses = _make_mock_tool_then_end("get_traveler_profile", {"customer_id": 1}, "Analysis done")
        with patch.object(agent._client.messages, "create", side_effect=responses):
            text, tokens = agent.run("Analyze customer 1")
        assert text == "Analysis done"
        assert tokens == 180 + 280  # 150+30 + 200+80

    def test_run_accumulates_tokens(self):
        agent = BaseAgent()
        responses = _make_mock_tool_then_end("compute_segment_score", {"customer_id": 2}, "Score computed")
        with patch.object(agent._client.messages, "create", side_effect=responses):
            _, tokens = agent.run("Score customer 2")
        assert tokens > 0


class TestProfileAgent:
    def test_analyze_returns_agent_result(self):
        agent = ProfileAgent()
        profile = get_customer(1)
        mock_resp = _make_mock_end_turn_response("Profile: Luxury traveler, Platinum tier")
        with patch.object(agent._client.messages, "create", return_value=mock_resp):
            result = agent.analyze(1, profile)
        assert result.success is True
        assert result.agent == "profile"
        assert "analysis" in result.data

    def test_analyze_includes_profile_in_data(self):
        agent = ProfileAgent()
        profile = get_customer(1)
        mock_resp = _make_mock_end_turn_response("Analysis text")
        with patch.object(agent._client.messages, "create", return_value=mock_resp):
            result = agent.analyze(1, profile)
        assert "profile" in result.data
        assert result.data["profile"]["name"] == "Alexandra Chen"


class TestDiscoveryAgent:
    def test_discover_returns_agent_result(self):
        agent = DiscoveryAgent()
        profile = get_customer(2)
        mock_resp = _make_mock_end_turn_response("1. Singapore 2. Dubai 3. Tokyo")
        with patch.object(agent._client.messages, "create", return_value=mock_resp):
            result = agent.discover(2, profile)
        assert result.success is True
        assert result.agent == "discovery"
        assert "recommendations" in result.data

    def test_discover_with_context(self):
        agent = DiscoveryAgent()
        profile = get_customer(4)
        mock_resp = _make_mock_end_turn_response("Adventure recommendations")
        with patch.object(agent._client.messages, "create", return_value=mock_resp):
            result = agent.discover(4, profile, "10-day trekking adventure")
        assert result.success is True


class TestMarketingAgent:
    def test_create_campaign_returns_result(self):
        agent = MarketingAgent()
        profile = get_customer(3)
        mock_resp = _make_mock_end_turn_response("Campaign: Family fun in Orlando")
        with patch.object(agent._client.messages, "create", return_value=mock_resp):
            result = agent.create_campaign(3, profile)
        assert result.success is True
        assert result.agent == "marketing"
        assert "campaign" in result.data

    def test_campaign_tokens_tracked(self):
        agent = MarketingAgent()
        profile = get_customer(1)
        mock_resp = _make_mock_end_turn_response("Luxury campaign")
        with patch.object(agent._client.messages, "create", return_value=mock_resp):
            result = agent.create_campaign(1, profile, "loyalty_reward")
        assert result.tokens_used == 150


class TestOrchestrator:
    def test_plan_trip_unknown_customer(self):
        orch = Orchestrator()
        result = orch.plan_trip(9999)
        assert result.success is False
        assert "not found" in result.error

    def test_plan_trip_success(self):
        orch = Orchestrator()
        mock_resp = _make_mock_end_turn_response("Trip plan output")
        with patch.object(orch._profile_agent._client.messages, "create", return_value=mock_resp), \
             patch.object(orch._discovery_agent._client.messages, "create", return_value=mock_resp):
            result = orch.plan_trip(1, "honeymoon trip")
        assert result.success is True
        assert "summary" in result.data
        assert "customer" in result.data

    def test_plan_trip_summary_contains_customer_name(self):
        orch = Orchestrator()
        mock_resp = _make_mock_end_turn_response("Recommendation output")
        with patch.object(orch._profile_agent._client.messages, "create", return_value=mock_resp), \
             patch.object(orch._discovery_agent._client.messages, "create", return_value=mock_resp):
            result = orch.plan_trip(1)
        assert "Alexandra Chen" in result.data["summary"]

    def test_proactive_scan_unknown_customer(self):
        orch = Orchestrator()
        result = orch.proactive_scan(9999)
        assert result.success is False

    def test_proactive_scan_success(self):
        orch = Orchestrator()
        mock_resp = _make_mock_end_turn_response("Agent output")
        with patch.object(orch._profile_agent._client.messages, "create", return_value=mock_resp), \
             patch.object(orch._discovery_agent._client.messages, "create", return_value=mock_resp), \
             patch.object(orch._marketing_agent._client.messages, "create", return_value=mock_resp):
            result = orch.proactive_scan(2)
        assert result.success is True
        assert "campaign" in result.data

    def test_generate_campaign_only(self):
        orch = Orchestrator()
        mock_resp = _make_mock_end_turn_response("Campaign: Business traveler offer")
        with patch.object(orch._marketing_agent._client.messages, "create", return_value=mock_resp):
            result = orch.generate_campaign_only(2, "seasonal_offer")
        assert result.success is True

    def test_generate_campaign_unknown_customer(self):
        orch = Orchestrator()
        result = orch.generate_campaign_only(9999)
        assert result.success is False

    def test_total_tokens_sum_of_agents(self):
        orch = Orchestrator()
        mock_resp = _make_mock_end_turn_response("Output")
        with patch.object(orch._profile_agent._client.messages, "create", return_value=mock_resp), \
             patch.object(orch._discovery_agent._client.messages, "create", return_value=mock_resp):
            result = orch.plan_trip(3)
        assert result.tokens_used == 150 * 2  # each agent uses 150 (100+50)
