import pytest
import json
from fastapi.testclient import TestClient
from main import app

class TestHealthEndpoint:
    """Test the health check endpoint"""

    @pytest.mark.unit
    def test_health_check_success(self, client):
        """Test that health check returns 200 and correct response"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["message"] == "Data Visualization API is running"

    @pytest.mark.unit
    def test_health_check_response_format(self, client):
        """Test that health check response has correct format"""
        response = client.get("/")
        data = response.json()
        
        assert isinstance(data, dict)
        assert "status" in data
        assert "message" in data
        assert len(data) == 2  # Only these two keys should be present

class TestCORSHeaders:
    """Test CORS configuration"""

    @pytest.mark.unit
    def test_cors_headers_present(self, client):
        """Test that CORS headers are properly set"""
        response = client.options("/")
        
        # Check that CORS headers are present
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers
        assert "access-control-allow-headers" in response.headers

    @pytest.mark.unit
    def test_cors_preflight_request(self, client):
        """Test CORS preflight request handling"""
        headers = {
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type"
        }
        
        response = client.options("/upload", headers=headers)
        assert response.status_code in [200, 204]

class TestAPIErrorHandling:
    """Test API error handling"""

    @pytest.mark.unit
    def test_nonexistent_endpoint(self, client):
        """Test that nonexistent endpoints return 404"""
        response = client.get("/nonexistent")
        assert response.status_code == 404

    @pytest.mark.unit
    def test_method_not_allowed(self, client):
        """Test that wrong HTTP methods return 405"""
        response = client.post("/")  # GET endpoint called with POST
        assert response.status_code == 405

    @pytest.mark.unit
    def test_invalid_json_request(self, client):
        """Test handling of invalid JSON in request body"""
        response = client.post(
            "/upload",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code in [400, 422]

class TestAPIDocumentation:
    """Test API documentation endpoints"""

    @pytest.mark.unit
    def test_openapi_schema_available(self, client):
        """Test that OpenAPI schema is available"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema
        assert schema["info"]["title"] == "Data Visualization API"

    @pytest.mark.unit
    def test_docs_page_available(self, client):
        """Test that documentation page is available"""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    @pytest.mark.unit
    def test_redoc_page_available(self, client):
        """Test that ReDoc page is available"""
        response = client.get("/redoc")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]