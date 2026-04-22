from __future__ import annotations

from travel_mind.agents.base import BaseAgent
from travel_mind.config import HITL_ACTION_TYPES, HITL_VALUE_THRESHOLD
from travel_mind.models import AgentResult, TravelerProfile
from travel_mind.tools import MARKETING_AGENT_TOOLS


class MarketingAgent(BaseAgent):
    name = "marketing"
    tools = MARKETING_AGENT_TOOLS
    system_prompt = f"""You are the TravelMind Marketing Agent. Your role is to generate highly personalized, conversion-optimized marketing campaigns for travelers.

Use the available tools to:
1. Generate a targeted email campaign based on the traveler's segment and history
2. Score the likelihood that the traveler will convert
3. Submit high-value or high-risk actions for human approval

IMPORTANT — Human-in-the-Loop (HITL) rules:
- ALWAYS use submit_for_approval when estimated_value > {HITL_VALUE_THRESHOLD} OR action_type is in {HITL_ACTION_TYPES}
- For bulk sends affecting many customers, ALWAYS use submit_for_approval with action_type "bulk_marketing_send"
- For booking confirmations, ALWAYS use submit_for_approval with action_type "booking_confirmation"
- For lower-value single emails, you may proceed without approval

Return a campaign summary including: subject line, body preview, conversion likelihood, estimated value, and whether it was submitted for approval."""

    def create_campaign(self, customer_id: int, profile: TravelerProfile, campaign_type: str = "destination_spotlight") -> AgentResult:
        from travel_mind.database import log_agent_run

        top_destination = profile.preferred_destinations[0] if profile.preferred_destinations else "a top destination"
        offer_value = round((profile.budget_range[0] + profile.budget_range[1]) * 0.05, 2)

        prompt = f"""Create a personalized marketing campaign for:
- Customer: {profile.name} (ID: {customer_id})
- Segment: {profile.segment.value}
- Loyalty tier: {profile.loyalty_tier}
- Top destination affinity: {top_destination}
- Campaign type: {campaign_type}
- Suggested offer value: ${offer_value}
- Budget range: ${profile.budget_range[0]:,.0f} - ${profile.budget_range[1]:,.0f}

Generate the campaign using generate_email_campaign, score it with score_campaign_likelihood, then apply HITL rules before returning a summary."""

        text, tokens = self.run(prompt, customer_profile=profile)
        log_agent_run(customer_id, self.name, f"campaign for customer {customer_id}", text[:200], tokens)
        return AgentResult(success=True, data={"campaign": text}, agent=self.name, tokens_used=tokens)
