"""TravelMind — Agentic Travel Intelligence Platform (Streamlit UI)."""
from __future__ import annotations

import streamlit as st

from travel_mind.database import (
    get_all_customers,
    get_hitl_request,
    get_pending_hitl_requests,
    init_db,
    resolve_hitl_request,
)
from travel_mind.config import ANTHROPIC_API_KEY
from travel_mind.models import ApprovalStatus

st.set_page_config(page_title="TravelMind", page_icon="✈️", layout="wide")

# ── Bootstrap DB ─────────────────────────────────────────────────────────────
@st.cache_resource
def setup():
    print(f"ANTHROPIC_API_KEY: {ANTHROPIC_API_KEY}")
    init_db(seed=True)
    return True

setup()


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("TravelMind")
    st.caption("Agentic Travel Intelligence Platform")
    st.markdown("---")
    st.markdown("""
**Architecture**
- Orchestrator Agent
- Profile Agent
- Discovery Agent
- Marketing Agent
- HITL Approval Gate

**Model:** `claude-sonnet-4-6`
**Tools:** Prompt caching + tool use
""")


# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["Trip Planner", "Proactive Scan", "Approval Queue", "Marketing Studio"])


# ── Tab 1: Trip Planner ───────────────────────────────────────────────────────
with tab1:
    st.header("Trip Planner")
    st.caption("Select a traveler and get personalized destination recommendations via multi-agent analysis.")

    customers = get_all_customers()
    customer_map = {f"{c.name} ({c.segment.value}, {c.loyalty_tier})": c for c in customers}
    selected_label = st.selectbox("Select Traveler", list(customer_map.keys()), key="planner_customer")
    selected_customer = customer_map[selected_label]

    trip_context = st.text_input("Trip context (optional)", placeholder="e.g., 10-day honeymoon in May, budget-flexible")

    col1, col2 = st.columns([1, 3])
    with col1:
        run_btn = st.button("Plan Trip", type="primary", key="plan_trip_btn")

    if run_btn:
        with st.spinner("Running multi-agent trip planner..."):
            from travel_mind.agents.orchestrator import Orchestrator
            orch = Orchestrator()
            result = orch.plan_trip(selected_customer.id, trip_context)

        if result.success:
            st.success(f"Plan generated — {result.tokens_used:,} tokens used")
            st.markdown(result.data["summary"])

            with st.expander("Raw agent outputs"):
                st.json(result.data)
        else:
            st.error(f"Error: {result.error}")


# ── Tab 2: Proactive Scan ─────────────────────────────────────────────────────
with tab2:
    st.header("Proactive Engagement Scan")
    st.caption("Run a full scan: profile analysis + recommendations + campaign generation with HITL gate.")

    customers2 = get_all_customers()
    customer_map2 = {f"{c.name} ({c.segment.value})": c for c in customers2}
    selected_label2 = st.selectbox("Select Traveler", list(customer_map2.keys()), key="scan_customer")
    selected_customer2 = customer_map2[selected_label2]

    col1b, _ = st.columns([1, 3])
    with col1b:
        scan_btn = st.button("Run Proactive Scan", type="primary", key="scan_btn")

    if scan_btn:
        with st.spinner("Running proactive scan across all agents..."):
            from travel_mind.agents.orchestrator import Orchestrator
            orch2 = Orchestrator()
            result2 = orch2.proactive_scan(selected_customer2.id)

        if result2.success:
            st.success(f"Scan complete — {result2.tokens_used:,} tokens used")
            st.markdown(result2.data["summary"])

            pending = get_pending_hitl_requests()
            if pending:
                st.warning(f"{len(pending)} item(s) pending human approval — check the Approval Queue tab.")

            with st.expander("Raw agent outputs"):
                st.json(result2.data)
        else:
            st.error(f"Error: {result2.error}")


# ── Tab 3: Approval Queue ─────────────────────────────────────────────────────
with tab3:
    st.header("Human-in-the-Loop Approval Queue")
    st.caption("Review and approve/reject high-value or high-risk actions flagged by agents.")

    if st.button("Refresh Queue", key="refresh_queue"):
        st.rerun()

    pending_requests = get_pending_hitl_requests()

    if not pending_requests:
        st.info("No pending approvals. Queue is clear.")
    else:
        st.metric("Pending Items", len(pending_requests))
        for req in pending_requests:
            with st.expander(f"[{req.action_type}] {req.customer_name} — ${req.estimated_value:,.2f}"):
                col_l, col_r = st.columns(2)
                with col_l:
                    st.markdown(f"**Customer:** {req.customer_name} (ID: {req.customer_id})")
                    st.markdown(f"**Action:** `{req.action_type}`")
                    st.markdown(f"**Estimated Value:** ${req.estimated_value:,.2f}")
                    st.markdown(f"**Created:** {req.created_at}")
                with col_r:
                    st.markdown(f"**Rationale:**\n{req.rationale}")
                    st.json(req.payload)

                note = st.text_input("Resolution note (optional)", key=f"note_{req.id}")
                col_approve, col_reject = st.columns(2)
                with col_approve:
                    if st.button("Approve", key=f"approve_{req.id}", type="primary"):
                        resolve_hitl_request(req.id, ApprovalStatus.APPROVED, note)
                        st.success("Approved")
                        st.rerun()
                with col_reject:
                    if st.button("Reject", key=f"reject_{req.id}"):
                        resolve_hitl_request(req.id, ApprovalStatus.REJECTED, note)
                        st.error("Rejected")
                        st.rerun()


# ── Tab 4: Marketing Studio ───────────────────────────────────────────────────
with tab4:
    st.header("Marketing Studio")
    st.caption("Generate personalized campaigns for individual travelers or run a bulk campaign.")

    customers4 = get_all_customers()
    customer_map4 = {f"{c.name} ({c.segment.value})": c for c in customers4}

    mode = st.radio("Mode", ["Single Customer", "All Customers (Bulk)"], horizontal=True)

    campaign_type = st.selectbox(
        "Campaign Type",
        ["destination_spotlight", "seasonal_offer", "loyalty_reward", "re_engagement"],
    )

    if mode == "Single Customer":
        selected_label4 = st.selectbox("Select Traveler", list(customer_map4.keys()), key="mktg_customer")
        selected_customer4 = customer_map4[selected_label4]

        if st.button("Generate Campaign", type="primary", key="mktg_btn"):
            with st.spinner("Marketing Agent generating campaign..."):
                from travel_mind.agents.orchestrator import Orchestrator
                orch4 = Orchestrator()
                result4 = orch4.generate_campaign_only(selected_customer4.id, campaign_type)

            if result4.success:
                st.success(f"Campaign generated — {result4.tokens_used:,} tokens used")
                st.markdown(result4.data.get("campaign", ""))
            else:
                st.error(result4.error)

    else:
        st.warning("Bulk send will be routed to the HITL approval queue automatically.")
        if st.button("Generate Bulk Campaign", type="primary", key="bulk_btn"):
            from travel_mind.agents.orchestrator import Orchestrator
            results = []
            prog = st.progress(0)
            for i, customer in enumerate(customers4):
                with st.spinner(f"Generating for {customer.name}..."):
                    orch = Orchestrator()
                    r = orch.generate_campaign_only(customer.id, campaign_type)
                    results.append((customer.name, r))
                prog.progress((i + 1) / len(customers4))

            st.success(f"Processed {len(results)} customers")
            pending_after = get_pending_hitl_requests()
            if pending_after:
                st.info(f"{len(pending_after)} items sent to approval queue.")

            for name, r in results:
                with st.expander(name):
                    if r.success:
                        st.markdown(r.data.get("campaign", ""))
                    else:
                        st.error(r.error)
