"""Tool definitions for Claude API tool use."""
from __future__ import annotations

import json
from typing import Any

PROFILE_AGENT_TOOLS = [
    {
        "name": "get_traveler_profile",
        "description": "Retrieve the complete profile for a traveler including segment, preferences, budget, and travel history.",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "integer", "description": "The customer's unique ID"},
            },
            "required": ["customer_id"],
        },
    },
    {
        "name": "update_traveler_preferences",
        "description": "Update the traveler's preferences in the database.",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "integer"},
                "preferences": {"type": "object", "description": "Key-value preferences to merge"},
            },
            "required": ["customer_id", "preferences"],
        },
    },
    {
        "name": "compute_segment_score",
        "description": "Compute a personalization score for a traveler based on their history and preferences.",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "integer"},
            },
            "required": ["customer_id"],
        },
    },
]

DISCOVERY_AGENT_TOOLS = [
    {
        "name": "search_destinations",
        "description": "Search for travel destinations matching criteria. Returns a list of matching destinations with details.",
        "input_schema": {
            "type": "object",
            "properties": {
                "segment": {"type": "string", "enum": ["luxury", "business", "family", "adventure", "occasional"]},
                "budget_max": {"type": "number", "description": "Maximum budget in USD"},
                "season": {"type": "string", "description": "Travel season or month"},
                "interests": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["segment"],
        },
    },
    {
        "name": "get_hotel_recommendations",
        "description": "Get hotel recommendations for a destination filtered by star rating and budget.",
        "input_schema": {
            "type": "object",
            "properties": {
                "destination": {"type": "string"},
                "stars": {"type": "integer", "minimum": 1, "maximum": 5},
                "budget_per_night": {"type": "number"},
            },
            "required": ["destination"],
        },
    },
    {
        "name": "estimate_trip_cost",
        "description": "Estimate total trip cost for a destination including flights, hotel, and activities.",
        "input_schema": {
            "type": "object",
            "properties": {
                "destination": {"type": "string"},
                "duration_days": {"type": "integer"},
                "party_size": {"type": "integer", "default": 2},
                "hotel_stars": {"type": "integer"},
            },
            "required": ["destination", "duration_days"],
        },
    },
]

MARKETING_AGENT_TOOLS = [
    {
        "name": "generate_email_campaign",
        "description": "Generate a personalized marketing email campaign for a customer.",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "integer"},
                "campaign_type": {"type": "string", "enum": ["seasonal_offer", "loyalty_reward", "re_engagement", "destination_spotlight"]},
                "featured_destination": {"type": "string"},
                "offer_value": {"type": "number", "description": "Discount or reward value in USD"},
            },
            "required": ["customer_id", "campaign_type"],
        },
    },
    {
        "name": "score_campaign_likelihood",
        "description": "Score the likelihood (0-1) that a customer will convert on a campaign.",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "integer"},
                "campaign_type": {"type": "string"},
                "estimated_value": {"type": "number"},
            },
            "required": ["customer_id", "campaign_type", "estimated_value"],
        },
    },
    {
        "name": "submit_for_approval",
        "description": "Submit an action for human-in-the-loop approval when it exceeds value thresholds or is a high-risk action type.",
        "input_schema": {
            "type": "object",
            "properties": {
                "action_type": {"type": "string"},
                "customer_id": {"type": "integer"},
                "customer_name": {"type": "string"},
                "payload": {"type": "object"},
                "estimated_value": {"type": "number"},
                "rationale": {"type": "string"},
            },
            "required": ["action_type", "customer_id", "customer_name", "payload", "estimated_value", "rationale"],
        },
    },
]

ORCHESTRATOR_TOOLS = [
    {
        "name": "delegate_to_profile_agent",
        "description": "Delegate profile enrichment and analysis to the Profile Agent.",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "integer"},
                "task": {"type": "string", "description": "Specific task for the profile agent"},
            },
            "required": ["customer_id", "task"],
        },
    },
    {
        "name": "delegate_to_discovery_agent",
        "description": "Delegate destination and hotel discovery to the Discovery Agent.",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "integer"},
                "task": {"type": "string"},
                "context": {"type": "object", "description": "Profile context to guide discovery"},
            },
            "required": ["customer_id", "task"],
        },
    },
    {
        "name": "delegate_to_marketing_agent",
        "description": "Delegate campaign generation to the Marketing Agent.",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "integer"},
                "task": {"type": "string"},
                "context": {"type": "object"},
            },
            "required": ["customer_id", "task"],
        },
    },
    {
        "name": "finalize_trip_plan",
        "description": "Compile final trip recommendations into a structured plan.",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "integer"},
                "recommendations": {"type": "array", "items": {"type": "object"}},
                "total_estimated_cost": {"type": "number"},
            },
            "required": ["customer_id", "recommendations"],
        },
    },
]


# ── Simulated tool executors ──────────────────────────────────────────────────

DESTINATION_CATALOG = {
    "luxury": [
        {"name": "Maldives", "season": "year-round", "highlight": "overwater bungalows, crystal lagoons"},
        {"name": "Amalfi Coast", "season": "May-October", "highlight": "cliffside villages, Italian cuisine"},
        {"name": "Kyoto", "season": "March-May, October-November", "highlight": "temples, kaiseki dining, onsen"},
        {"name": "St. Barts", "season": "December-April", "highlight": "celebrity scene, pristine beaches"},
    ],
    "business": [
        {"name": "Singapore", "season": "year-round", "highlight": "financial hub, Changi airport, Marina Bay"},
        {"name": "Dubai", "season": "October-April", "highlight": "DIFC, luxury transit hub, tax-free shopping"},
        {"name": "Tokyo", "season": "year-round", "highlight": "Shinjuku, rail network, precision"},
        {"name": "New York", "season": "year-round", "highlight": "Midtown, JFK, diverse cuisine"},
    ],
    "family": [
        {"name": "Orlando", "season": "year-round", "highlight": "Walt Disney World, Universal, SeaWorld"},
        {"name": "Barcelona", "season": "April-June, September", "highlight": "Gaudí, beaches, family-friendly restaurants"},
        {"name": "Hawaii", "season": "year-round", "highlight": "volcanic parks, snorkeling, luau"},
        {"name": "Costa Rica", "season": "December-April", "highlight": "zip-lining, wildlife, eco-lodges"},
    ],
    "adventure": [
        {"name": "Patagonia", "season": "November-March", "highlight": "Torres del Paine, glaciers, hiking"},
        {"name": "Nepal", "season": "March-May, October-November", "highlight": "Everest Base Camp, Annapurna Circuit"},
        {"name": "Iceland", "season": "June-August (midnight sun), December-February (aurora)", "highlight": "glaciers, volcanoes, Northern Lights"},
        {"name": "New Zealand", "season": "November-April", "highlight": "Milford Sound, bungee jumping, Hobbiton"},
    ],
    "occasional": [
        {"name": "Paris", "season": "April-June, September", "highlight": "Eiffel Tower, Louvre, café culture"},
        {"name": "Rome", "season": "April-June, September-October", "highlight": "Colosseum, Vatican, pasta"},
        {"name": "Amsterdam", "season": "April-May, September", "highlight": "canals, Van Gogh Museum, cycling"},
        {"name": "Lisbon", "season": "March-May, September-October", "highlight": "Alfama, trams, pastéis de nata"},
    ],
}

HOTEL_CATALOG = {
    5: ["Four Seasons", "Aman Resort", "Ritz-Carlton", "Park Hyatt"],
    4: ["Marriott", "Hilton", "Westin", "Hyatt Regency"],
    3: ["Courtyard by Marriott", "Holiday Inn", "Ibis", "Novotel"],
}

COST_ESTIMATES = {
    "luxury": {"flight": 3500, "hotel_per_night": 800, "activities_per_day": 300},
    "business": {"flight": 2500, "hotel_per_night": 400, "activities_per_day": 150},
    "family": {"flight": 1800, "hotel_per_night": 350, "activities_per_day": 200},
    "adventure": {"flight": 2000, "hotel_per_night": 200, "activities_per_day": 150},
    "occasional": {"flight": 1200, "hotel_per_night": 180, "activities_per_day": 80},
}


def execute_tool(tool_name: str, tool_input: dict[str, Any], customer_profile: TravelerProfile | None = None) -> Any:
    """Execute a simulated tool and return the result."""
    from travel_mind.models import TravelerProfile

    if tool_name == "get_traveler_profile":
        from travel_mind.database import get_customer
        profile = get_customer(tool_input["customer_id"])
        if profile:
            return profile.to_dict()
        return {"error": "Customer not found"}

    elif tool_name == "update_traveler_preferences":
        return {"success": True, "updated": tool_input.get("preferences", {})}

    elif tool_name == "compute_segment_score":
        profile = customer_profile
        if not profile:
            from travel_mind.database import get_customer
            profile = get_customer(tool_input["customer_id"])
        if not profile:
            return {"score": 0.5}
        history_count = len(profile.travel_history)
        tier_scores = {"Platinum": 1.0, "Gold": 0.8, "Silver": 0.6, "Standard": 0.4}
        tier_score = tier_scores.get(profile.loyalty_tier, 0.4)
        recency = min(history_count / 5.0, 1.0)
        return {"score": round((tier_score * 0.6 + recency * 0.4), 2), "tier": profile.loyalty_tier}

    elif tool_name == "search_destinations":
        segment = tool_input.get("segment", "occasional")
        destinations = DESTINATION_CATALOG.get(segment, DESTINATION_CATALOG["occasional"])
        return {"destinations": destinations[:3], "total_found": len(destinations)}

    elif tool_name == "get_hotel_recommendations":
        stars = tool_input.get("stars", 4)
        stars = max(3, min(5, stars))
        hotels = HOTEL_CATALOG.get(stars, HOTEL_CATALOG[4])
        destination = tool_input.get("destination", "")
        return {
            "hotels": [{"name": h, "destination": destination, "stars": stars} for h in hotels[:3]],
            "budget_per_night": tool_input.get("budget_per_night", 300),
        }

    elif tool_name == "estimate_trip_cost":
        segment = "occasional"
        if customer_profile:
            segment = customer_profile.segment.value
        rates = COST_ESTIMATES.get(segment, COST_ESTIMATES["occasional"])
        days = tool_input.get("duration_days", 7)
        party = tool_input.get("party_size", 2)
        stars = tool_input.get("hotel_stars", 4)
        hotel_multiplier = {5: 2.0, 4: 1.0, 3: 0.6}.get(stars, 1.0)
        total = (
            rates["flight"] * party
            + rates["hotel_per_night"] * days * hotel_multiplier
            + rates["activities_per_day"] * days * party
        )
        return {
            "destination": tool_input.get("destination"),
            "duration_days": days,
            "party_size": party,
            "estimated_total": round(total, 2),
            "breakdown": {
                "flights": rates["flight"] * party,
                "hotel": rates["hotel_per_night"] * days * hotel_multiplier,
                "activities": rates["activities_per_day"] * days * party,
            },
        }

    elif tool_name == "generate_email_campaign":
        from travel_mind.database import get_customer
        cid = tool_input["customer_id"]
        profile = get_customer(cid)
        name = profile.name if profile else f"Customer {cid}"
        dest = tool_input.get("featured_destination", "your next adventure")
        offer = tool_input.get("offer_value", 200)
        campaign_type = tool_input.get("campaign_type", "destination_spotlight")
        return {
            "customer_id": cid,
            "customer_name": name,
            "subject": f"Exclusive {campaign_type.replace('_', ' ').title()} — {dest} awaits, {name.split()[0]}",
            "body": f"Dear {name.split()[0]},\n\nWe have a personalized travel offer for you: discover {dest} with ${offer} in savings. Based on your travel profile, we think this is the perfect next destination for you.\n\nBook now to secure your spot.\n\nBest,\nTravelMind Team",
            "estimated_value": offer,
            "action_type": "marketing_email",
        }

    elif tool_name == "score_campaign_likelihood":
        tier_multipliers = {"Platinum": 0.85, "Gold": 0.70, "Silver": 0.55, "Standard": 0.40}
        if customer_profile:
            base = tier_multipliers.get(customer_profile.loyalty_tier, 0.5)
        else:
            base = 0.55
        return {"likelihood": round(base, 2), "confidence": "medium"}

    elif tool_name == "submit_for_approval":
        from travel_mind.database import save_hitl_request
        import uuid
        from datetime import datetime
        req = HITLRequest(
            id=str(uuid.uuid4()),
            action_type=tool_input["action_type"],
            customer_id=tool_input["customer_id"],
            customer_name=tool_input["customer_name"],
            payload=tool_input["payload"],
            estimated_value=tool_input["estimated_value"],
            rationale=tool_input["rationale"],
        )
        save_hitl_request(req)
        return {"approval_id": req.id, "status": "pending", "message": "Submitted for human review"}

    elif tool_name == "delegate_to_profile_agent":
        return {"delegated": True, "agent": "profile", "customer_id": tool_input["customer_id"]}

    elif tool_name == "delegate_to_discovery_agent":
        return {"delegated": True, "agent": "discovery", "customer_id": tool_input["customer_id"]}

    elif tool_name == "delegate_to_marketing_agent":
        return {"delegated": True, "agent": "marketing", "customer_id": tool_input["customer_id"]}

    elif tool_name == "finalize_trip_plan":
        return {
            "plan_id": f"PLAN-{tool_input['customer_id']}-001",
            "recommendations": tool_input.get("recommendations", []),
            "total_estimated_cost": tool_input.get("total_estimated_cost", 0),
            "status": "ready",
        }

    return {"error": f"Unknown tool: {tool_name}"}


# Import here to avoid circular at module load
from travel_mind.models import HITLRequest  # noqa: E402
