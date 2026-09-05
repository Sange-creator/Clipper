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
        original_data = res.json()
        assert "ai_provider" in original_data
        assert "gemini_api_key_configured" in original_data
        assert "groq_api_key_configured" in original_data

        try:
            # 2. Update settings (change provider to gemini and save key)
            update_res = await client.post(
                "/api/settings",
                json={
                    "ai_provider": "gemini",
                    "gemini_api_key": "AIzaSyRealValidFormatKeyForTesting99",
                },
            )
            assert update_res.status_code == 200
            updated = update_res.json()
            assert updated["ai_provider"] == "gemini"
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
        finally:
            # Restore clean state
            await client.post(
                "/api/settings",
                json={
                    "ai_provider": "gemini",
                    "gemini_api_key": "",
                    "groq_api_key": "",
                },
            )
