"""Unit and integration tests for Settings and API Key management."""

import pytest
from httpx import ASGITransport, AsyncClient
from app.core.database import init_db
from app.main import app


@pytest.mark.asyncio
async def test_get_and_update_settings():
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Get settings
        res = await client.get("/api/settings")
        assert res.status_code == 200
        data = res.json()
        assert "ai_provider" in data
        assert "gemini_api_key_configured" in data
        assert "groq_api_key_configured" in data

        # 2. Update settings (change provider to mock and save fake gemini key)
        update_res = await client.post(
            "/api/settings",
            json={
                "ai_provider": "mock",
                "gemini_api_key": "AIzaSyTest1234567890abcdef",
                "groq_api_key": "gsk_test1234567890abcdef",
            },
        )
        assert update_res.status_code == 200
        updated = update_res.json()
        assert updated["ai_provider"] == "mock"
        assert updated["gemini_api_key_configured"] is True
        assert updated["gemini_api_key_masked"].startswith("AIzaSy...")

        # 3. Test API key validation ping with empty/invalid key
        test_res = await client.post(
            "/api/settings/test",
            json={
                "provider": "gemini",
                "api_key": "",
            },
        )
        assert test_res.status_code == 200
        test_data = test_res.json()
        assert test_data["valid"] is False
