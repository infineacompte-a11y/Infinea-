"""Smoke test — verify test infrastructure works."""

import pytest


@pytest.mark.asyncio
async def test_mock_db_works(mock_db):
    """Verify mongomock-motor is functional."""
    await mock_db.test_collection.insert_one({"key": "value"})
    doc = await mock_db.test_collection.find_one({"key": "value"})
    assert doc is not None
    assert doc["key"] == "value"


@pytest.mark.asyncio
async def test_fixtures_loaded(sample_action, sample_objective, sample_session):
    """Verify all sample data fixtures are accessible."""
    assert sample_action["action_id"] == "action_test_001"
    assert sample_objective["objective_id"] == "obj_test_001"
    assert sample_session["session_id"] == "sess_test_001"
