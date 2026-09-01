"""Tests for FastAPI endpoints using AsyncClient."""

import pytest
from httpx import ASGITransport, AsyncClient
from app.core.database import init_db
from app.main import app


@pytest.mark.asyncio
async def test_health_check():
    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "ai_provider_configured" in data
        assert "ffmpeg_available" in data
