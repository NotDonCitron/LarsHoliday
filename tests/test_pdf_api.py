import pytest
from fastapi.testclient import TestClient
from api import app
import os

client = TestClient(app)

def test_pdf_export_endpoint():
    # Mock data
    payload = {
        "deals": [
            {"name": "Hotel 1", "price_per_night": 100, "location": "Amsterdam", "source": "test"},
            {"name": "Hotel 2", "price_per_night": 120, "location": "Amsterdam", "source": "test"}
        ],
        "search_params": {
            "cities": ["Amsterdam"],
            "checkin": "2026-03-08",
            "checkout": "2026-03-15",
            "nights": 7,
            "group_size": 2,
            "pets": 1,
            "budget_range": "0-250"
        }
    }
    
    response = client.post("/export-pdf", json=payload)
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    # Ensure file was generated and has content
    assert len(response.content) > 1000
