import pytest
import os
from httpx import AsyncClient, ASGITransport
from app.api.main import app
from app.api.dependencies import get_db

# Fake async connection to bypass real database for fast API tests
class FakeCursor:
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
        
    async def execute(self, query):
        pass
        
    async def fetchall(self):
        # Return fake schema rows if it's the schema query, else fake data rows
        return [{"table_name": "users", "column_name": "id", "data_type": "integer"}]

class FakeConnection:
    def cursor(self):
        return FakeCursor()
        
    def transaction(self):
        return FakeCursor() # Reuse FakeCursor as a dummy transaction context manager
        
    async def execute(self, query):
        pass

async def override_get_db():
    yield FakeConnection()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture
def anyio_backend():
    return "asyncio"

@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "OK"}

@pytest.mark.asyncio
async def test_schema_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/schema")
    assert response.status_code == 200
    assert "schema" in response.json()

@pytest.mark.asyncio
async def test_ask_endpoint():
    # Force use of FakeLLMClient
    os.environ["USE_FAKE_LLM"] = "1"
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/ask", json={"question": "Show the top customers by revenue"})
    
    assert response.status_code == 200
    data = response.json()
    assert "sql" in data
    assert "rows" in data
    assert "summary" in data
    
    os.environ.pop("USE_FAKE_LLM", None)
