import json
import sqlite3
import uuid
from contextlib import contextmanager
from pathlib import Path

from travel_mind.config import DB_PATH
from travel_mind.models import (
    ApprovalStatus,
    HITLRequest,
    TravelerProfile,
    TravelerSegment,
)

SEED_CUSTOMERS = [
    {
        "id": 1,
        "name": "Alexandra Chen",
        "email": "alexandra.chen@example.com",
        "segment": "luxury",
        "preferred_destinations": ["Maldives", "Santorini", "Bali", "Amalfi Coast"],
        "budget_range": [5000.0, 20000.0],
        "loyalty_tier": "Platinum",
        "travel_history": [
            {"destination": "Maldives", "year": 2024, "spend": 12000},
            {"destination": "Santorini", "year": 2023, "spend": 8500},
        ],
        "preferences": {"class": "business", "hotel_stars": 5, "activities": ["spa", "fine dining", "yacht"]},
    },
    {
        "id": 2,
        "name": "Marcus Williams",
        "email": "marcus.williams@example.com",
        "segment": "business",
        "preferred_destinations": ["New York", "London", "Tokyo", "Singapore"],
        "budget_range": [2000.0, 8000.0],
        "loyalty_tier": "Gold",
        "travel_history": [
            {"destination": "New York", "year": 2024, "spend": 3200},
            {"destination": "London", "year": 2024, "spend": 4100},
        ],
        "preferences": {"class": "business", "hotel_stars": 4, "activities": ["business center", "airport lounge", "express checkout"]},
    },
    {
        "id": 3,
        "name": "The Rodriguez Family",
        "email": "rodriguez.family@example.com",
        "segment": "family",
        "preferred_destinations": ["Orlando", "Cancun", "Barcelona", "Hawaii"],
        "budget_range": [3000.0, 10000.0],
        "loyalty_tier": "Silver",
        "travel_history": [
            {"destination": "Orlando", "year": 2024, "spend": 5500},
            {"destination": "Cancun", "year": 2023, "spend": 4200},
        ],
        "preferences": {"class": "economy", "hotel_stars": 4, "activities": ["theme parks", "beach", "kid-friendly dining"], "party_size": 4},
    },
    {
        "id": 4,
        "name": "Jordan Kim",
        "email": "jordan.kim@example.com",
        "segment": "adventure",
        "preferred_destinations": ["Patagonia", "Nepal", "Iceland", "New Zealand"],
        "budget_range": [2500.0, 7000.0],
        "loyalty_tier": "Silver",
        "travel_history": [
            {"destination": "Iceland", "year": 2024, "spend": 3800},
            {"destination": "Nepal", "year": 2023, "spend": 4500},
        ],
        "preferences": {"class": "economy", "hotel_stars": 3, "activities": ["hiking", "camping", "extreme sports", "local cuisine"]},
    },
    {
        "id": 5,
        "name": "Patricia Moore",
        "email": "patricia.moore@example.com",
        "segment": "occasional",
        "preferred_destinations": ["Paris", "Rome", "Amsterdam"],
        "budget_range": [1500.0, 4000.0],
        "loyalty_tier": "Standard",
        "travel_history": [
            {"destination": "Paris", "year": 2022, "spend": 2800},
        ],
        "preferences": {"class": "economy", "hotel_stars": 3, "activities": ["museums", "sightseeing", "local food tours"]},
    },
]


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(seed: bool = True) -> None:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                segment TEXT NOT NULL,
                preferred_destinations TEXT NOT NULL,
                budget_range TEXT NOT NULL,
                loyalty_tier TEXT NOT NULL,
                travel_history TEXT NOT NULL,
                preferences TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS hitl_requests (
                id TEXT PRIMARY KEY,
                action_type TEXT NOT NULL,
                customer_id INTEGER NOT NULL,
                customer_name TEXT NOT NULL,
                payload TEXT NOT NULL,
                estimated_value REAL NOT NULL,
                rationale TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL,
                resolved_at TEXT,
                resolver_note TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS agent_runs (
                id TEXT PRIMARY KEY,
                customer_id INTEGER,
                agent TEXT NOT NULL,
                input_summary TEXT NOT NULL,
                output_summary TEXT NOT NULL,
                tokens_used INTEGER DEFAULT 0,
                created_at TEXT NOT NULL
            );
        """)

    if seed:
        _seed_customers()


def _seed_customers() -> None:
    with get_conn() as conn:
        for c in SEED_CUSTOMERS:
            conn.execute(
                """INSERT OR IGNORE INTO customers
                   (id, name, email, segment, preferred_destinations, budget_range, loyalty_tier, travel_history, preferences)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    c["id"], c["name"], c["email"], c["segment"],
                    json.dumps(c["preferred_destinations"]),
                    json.dumps(c["budget_range"]),
                    c["loyalty_tier"],
                    json.dumps(c["travel_history"]),
                    json.dumps(c["preferences"]),
                ),
            )


def get_customer(customer_id: int) -> TravelerProfile | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM customers WHERE id = ?", (customer_id,)).fetchone()
    if not row:
        return None
    return _row_to_profile(row)


def get_all_customers() -> list[TravelerProfile]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM customers ORDER BY id").fetchall()
    return [_row_to_profile(r) for r in rows]


def _row_to_profile(row: sqlite3.Row) -> TravelerProfile:
    return TravelerProfile(
        id=row["id"],
        name=row["name"],
        email=row["email"],
        segment=TravelerSegment(row["segment"]),
        preferred_destinations=json.loads(row["preferred_destinations"]),
        budget_range=tuple(json.loads(row["budget_range"])),
        loyalty_tier=row["loyalty_tier"],
        travel_history=json.loads(row["travel_history"]),
        preferences=json.loads(row["preferences"]),
    )


def save_hitl_request(req: HITLRequest) -> None:
    with get_conn() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO hitl_requests
               (id, action_type, customer_id, customer_name, payload, estimated_value,
                rationale, status, created_at, resolved_at, resolver_note)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                req.id, req.action_type, req.customer_id, req.customer_name,
                json.dumps(req.payload), req.estimated_value, req.rationale,
                req.status.value, req.created_at, req.resolved_at, req.resolver_note,
            ),
        )


def get_pending_hitl_requests() -> list[HITLRequest]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM hitl_requests WHERE status = 'pending' ORDER BY created_at DESC"
        ).fetchall()
    return [_row_to_hitl(r) for r in rows]


def get_hitl_request(req_id: str) -> HITLRequest | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM hitl_requests WHERE id = ?", (req_id,)).fetchone()
    return _row_to_hitl(row) if row else None


def resolve_hitl_request(req_id: str, status: ApprovalStatus, note: str = "") -> bool:
    from datetime import datetime
    with get_conn() as conn:
        cursor = conn.execute(
            "UPDATE hitl_requests SET status = ?, resolved_at = ?, resolver_note = ? WHERE id = ?",
            (status.value, datetime.utcnow().isoformat(), note, req_id),
        )
    return cursor.rowcount > 0


def _row_to_hitl(row: sqlite3.Row) -> HITLRequest:
    return HITLRequest(
        id=row["id"],
        action_type=row["action_type"],
        customer_id=row["customer_id"],
        customer_name=row["customer_name"],
        payload=json.loads(row["payload"]),
        estimated_value=row["estimated_value"],
        rationale=row["rationale"],
        status=ApprovalStatus(row["status"]),
        created_at=row["created_at"],
        resolved_at=row["resolved_at"],
        resolver_note=row["resolver_note"] or "",
    )


def log_agent_run(customer_id: int | None, agent: str, input_summary: str, output_summary: str, tokens_used: int = 0) -> None:
    from datetime import datetime
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO agent_runs (id, customer_id, agent, input_summary, output_summary, tokens_used, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), customer_id, agent, input_summary, output_summary, tokens_used, datetime.utcnow().isoformat()),
        )
