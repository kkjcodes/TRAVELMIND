"""Pytest fixtures for TravelMind tests."""
import os
import tempfile

import pytest

# Use a temp database for all tests
@pytest.fixture(autouse=True)
def test_db(tmp_path, monkeypatch):
    db_path = str(tmp_path / "test_travelmind.db")
    monkeypatch.setenv("TRAVELMIND_DB", db_path)
    # Patch the config so imports pick up the new path
    import travel_mind.config as cfg
    monkeypatch.setattr(cfg, "DB_PATH", db_path)
    import travel_mind.database as db_module
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    db_module.init_db(seed=True)
    yield db_path
