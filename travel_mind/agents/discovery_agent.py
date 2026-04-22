from __future__ import annotations
import json

from travel_mind.agents.base import BaseAgent
from travel_mind.models import AgentResult, TravelerProfile
from travel_mind.tools import DISCOVERY_AGENT_TOOLS


class DiscoveryAgent(BaseAgent):
    name = "discovery"
    tools = DISCOVERY_AGENT_TOOLS
    system_prompt = """You are the TravelMind Discovery Agent. Your role is to find the best travel destinations, hotels, and experiences for a specific traveler based on their profile.

Use the available tools to:
1. Search destinations matching their segment and interests
2. Get hotel recommendations aligned with their star preference and budget
3. Estimate total trip costs for top candidates
4. Rank options by fit score considering budget, preferences, and season

Return your top 3 recommendations as a structured list. Each recommendation must include:
- Destination name
- Recommended hotel
- Estimated total cost
- Why it fits this traveler (2-3 sentences)
- Top 3 highlights

Be specific and data-driven. Prioritize destinations the traveler hasn't visited yet when possible."""

    def discover(self, customer_id: int, profile: TravelerProfile, trip_context: str = "") -> AgentResult:
        from travel_mind.database import log_agent_run

        visited = [h["destination"] for h in profile.travel_history]
        prompt = f"""Find the best travel recommendations for:
- Customer: {profile.name} (ID: {customer_id})
- Segment: {profile.segment.value}
- Budget: ${profile.budget_range[0]:,.0f} - ${profile.budget_range[1]:,.0f}
- Preferred hotel stars: {profile.preferences.get('hotel_stars', 4)}
- Interests: {profile.preferences.get('activities', [])}
- Previously visited: {visited}
- Trip context: {trip_context or 'General vacation planning'}

Use search_destinations, get_hotel_recommendations, and estimate_trip_cost tools to build 3 ranked recommendations."""

        text, tokens = self.run(prompt, customer_profile=profile)
        log_agent_run(customer_id, self.name, f"discover for customer {customer_id}", text[:200], tokens)
        return AgentResult(success=True, data={"recommendations": text}, agent=self.name, tokens_used=tokens)
