from __future__ import annotations

from travel_mind.agents.base import BaseAgent
from travel_mind.models import AgentResult, TravelerProfile
from travel_mind.tools import PROFILE_AGENT_TOOLS


class ProfileAgent(BaseAgent):
    name = "profile"
    tools = PROFILE_AGENT_TOOLS
    system_prompt = """You are the TravelMind Profile Agent. Your role is to deeply analyze a traveler's profile, preferences, and history to build rich personalization context.

Use the available tools to:
1. Retrieve the traveler's complete profile
2. Compute their personalization score
3. Identify patterns in their travel history
4. Surface key insights about their preferences, budget range, and loyalty status

Return a concise profile summary with: segment classification, top 3 destination affinities, budget tier, loyalty status, and 2-3 personalization insights that downstream agents can use for recommendations and marketing."""

    def analyze(self, customer_id: int, profile: TravelerProfile) -> AgentResult:
        from travel_mind.database import log_agent_run

        prompt = f"""Analyze traveler profile for customer ID {customer_id}.

Profile summary:
- Name: {profile.name}
- Segment: {profile.segment.value}
- Loyalty tier: {profile.loyalty_tier}
- Budget range: ${profile.budget_range[0]:,.0f} - ${profile.budget_range[1]:,.0f}
- Preferred destinations: {', '.join(profile.preferred_destinations)}
- Travel history: {len(profile.travel_history)} trips
- Preferences: {profile.preferences}

Use your tools to compute a personalization score and return a profile analysis with key insights."""

        text, tokens = self.run(prompt, customer_profile=profile)
        log_agent_run(customer_id, self.name, f"analyze customer {customer_id}", text[:200], tokens)
        return AgentResult(success=True, data={"analysis": text, "profile": profile.to_dict()}, agent=self.name, tokens_used=tokens)
