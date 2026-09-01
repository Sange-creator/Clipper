"""Integration tests for project API endpoints, project deletion, and batch management."""

import pytest
from httpx import ASGITransport, AsyncClient
from app.core.database import init_db
from app.main import app


@pytest.mark.asyncio
async def test_project_crud_lifecycle():
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Create project
        create_res = await client.post(
            "/api/projects",
            json={
                "name": "Podcast Masterclass Project",
                "description": "20 long form interview episodes",
                "mode": "podcast",
            },
        )
        assert create_res.status_code == 201
        data = create_res.json()
        project_id = data["id"]
        assert data["name"] == "Podcast Masterclass Project"

        # 2. List projects
        list_res = await client.get("/api/projects")
        assert list_res.status_code == 200
        projects = list_res.json()
        assert any(p["id"] == project_id for p in projects)

        # 3. Get project details
        detail_res = await client.get(f"/api/projects/{project_id}")
        assert detail_res.status_code == 200
        detail = detail_res.json()
        assert detail["id"] == project_id
        assert detail["total_videos"] == 0
        assert detail["total_clips"] == 0

        # 4. Delete project
        del_res = await client.delete(f"/api/projects/{project_id}")
        assert del_res.status_code == 200

        # Verify not found
        get_again = await client.get(f"/api/projects/{project_id}")
        assert get_again.status_code == 404


@pytest.mark.asyncio
async def test_project_bulk_delete():
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create 2 projects
        p1 = (await client.post("/api/projects", json={"name": "Bulk P1", "mode": "podcast"})).json()["id"]
        p2 = (await client.post("/api/projects", json={"name": "Bulk P2", "mode": "viral_moments"})).json()["id"]

        # Bulk delete
        bulk_res = await client.post("/api/projects/bulk-delete", json={"project_ids": [p1, p2]})
        assert bulk_res.status_code == 200
        assert bulk_res.json()["deleted_count"] == 2

        # Verify both deleted
        assert (await client.get(f"/api/projects/{p1}")).status_code == 404
        assert (await client.get(f"/api/projects/{p2}")).status_code == 404


@pytest.mark.asyncio
async def test_admin_metrics_endpoint():
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/admin/metrics")
        assert res.status_code == 200
        metrics = res.json()
        assert "total_projects" in metrics
        assert "total_videos" in metrics
        assert "total_clips_generated" in metrics
        assert "acceptance_rate_pct" in metrics
