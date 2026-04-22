from __future__ import annotations

from travel_mind.agents.base import BaseAgent
from travel_mind.agents.discovery_agent import DiscoveryAgent
from travel_mind.agents.marketing_agent import MarketingAgent
from travel_mind.agents.profile_agent import ProfileAgent
from travel_mind.database import get_customer, log_agent_run
from travel_mind.models import AgentResult, TravelerProfile
from travel_mind.tools import ORCHESTRATOR_TOOLS


class Orchestrator(BaseAgent):
    name = "orchestrator"
    tools = ORCHESTRATOR_TOOLS
    system_prompt = """You are the TravelMind Orchestrator. You coordinate specialized sub-agents to deliver a complete, personalized travel intelligence experience.

Your workflow:
1. Analyze the user's request to understand intent (trip planning, proactive scan, campaign generation)
2. Delegate to the Profile Agent to enrich traveler context
3. Delegate to the Discovery Agent for destination recommendations
4. Optionally delegate to the Marketing Agent for campaign creation
5. Synthesize results into a cohesive, actionable plan

You do NOT call external APIs directly — you coordinate sub-agents. Return a clear, structured summary of all agent outputs with next recommended actions."""

    def __init__(self):
        super().__init__()
        self._profile_agent = ProfileAgent()
        self._discovery_agent = DiscoveryAgent()
        self._marketing_agent = MarketingAgent()

    def plan_trip(self, customer_id: int, trip_context: str = "") -> AgentResult:
        profile = get_customer(customer_id)
        if not profile:
            return AgentResult(success=False, data=None, agent=self.name, error=f"Customer {customer_id} not found")

        profile_result = self._profile_agent.analyze(customer_id, profile)
        discovery_result = self._discovery_agent.discover(customer_id, profile, trip_context)

        total_tokens = profile_result.tokens_used + discovery_result.tokens_used

        summary = f"""# TravelMind Trip Plan — {profile.name}

## Profile Analysis
{profile_result.data.get('analysis', '')}

## Top Recommendations
{discovery_result.data.get('recommendations', '')}

---
*Total tokens used: {total_tokens}*"""

        log_agent_run(customer_id, self.name, f"plan_trip: {trip_context[:100]}", summary[:300], total_tokens)

        return AgentResult(
            success=True,
            data={
                "summary": summary,
                "profile": profile_result.data,
                "recommendations": discovery_result.data,
                "customer": profile.to_dict(),
            },
            agent=self.name,
            tokens_used=total_tokens,
        )

    def proactive_scan(self, customer_id: int) -> AgentResult:
        profile = get_customer(customer_id)
        if not profile:
            return AgentResult(success=False, data=None, agent=self.name, error=f"Customer {customer_id} not found")

        profile_result = self._profile_agent.analyze(customer_id, profile)
        discovery_result = self._discovery_agent.discover(customer_id, profile, "Proactive engagement — suggest destinations they haven't considered")
        marketing_result = self._marketing_agent.create_campaign(customer_id, profile, "re_engagement")

        total_tokens = sum(r.tokens_used for r in [profile_result, discovery_result, marketing_result])

        summary = f"""# TravelMind Proactive Scan — {profile.name}

## Profile Insights
{profile_result.data.get('analysis', '')}

## Proactive Recommendations
{discovery_result.data.get('recommendations', '')}

## Proposed Campaign
{marketing_result.data.get('campaign', '')}

---
*Total tokens used: {total_tokens}*"""

        log_agent_run(customer_id, self.name, "proactive_scan", summary[:300], total_tokens)

        return AgentResult(
            success=True,
            data={
                "summary": summary,
                "profile": profile_result.data,
                "recommendations": discovery_result.data,
                "campaign": marketing_result.data,
                "customer": profile.to_dict(),
            },
            agent=self.name,
            tokens_used=total_tokens,
        )

    def generate_campaign_only(self, customer_id: int, campaign_type: str = "destination_spotlight") -> AgentResult:
        profile = get_customer(customer_id)
        if not profile:
            return AgentResult(success=False, data=None, agent=self.name, error=f"Customer {customer_id} not found")

        marketing_result = self._marketing_agent.create_campaign(customer_id, profile, campaign_type)
        log_agent_run(customer_id, self.name, f"campaign_only: {campaign_type}", marketing_result.data.get("campaign", "")[:200], marketing_result.tokens_used)
        return marketing_result
