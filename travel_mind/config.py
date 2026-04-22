import os
from pathlib import Path

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
MODEL = "claude-sonnet-4-6"
DB_PATH = os.getenv("TRAVELMIND_DB", str(Path(__file__).parent.parent / "travelmind.db"))

HITL_VALUE_THRESHOLD = 500.0
HITL_ACTION_TYPES = {"booking_confirmation", "bulk_marketing_send"}

MAX_TOKENS = 4096
