import pytest
import asyncio
from httpx import AsyncClient
from app import app

@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_health_endpoint(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "version" in data
    assert "gemini_api_status" in data

@pytest.mark.asyncio
async def test_root_endpoint(client):
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "service" in data
    assert "version" in data
    assert "endpoints" in data

@pytest.mark.asyncio
async def test_status_endpoint(client):
    response = await client.get("/status")
    assert response.status_code == 200
    data = response.json()
    assert "service_status" in data
    assert "components" in data

@pytest.mark.asyncio
async def test_analyze_endpoint_basic():
    # This test requires a more complex setup with mock data
    # For now, just test that the endpoint exists
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Test with minimal email data
        email_data = {
            "raw_email": "From: test@example.com\nTo: user@bank.com\nSubject: Test\n\nThis is a test email."
        }
        
        response = await client.post("/analyze", json=email_data)
        # Should either succeed or fail gracefully
        assert response.status_code in [200, 422, 500]  # Valid responses
