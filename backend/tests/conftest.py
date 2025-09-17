import pytest
import os
import tempfile
import pandas as pd
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from main import app

# Test environment setup
@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """Setup test environment variables"""
    os.environ["OPENAI_API_KEY"] = "test-api-key"
    yield
    if "OPENAI_API_KEY" in os.environ:
        del os.environ["OPENAI_API_KEY"]

@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)

@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing"""
    with patch('main.client') as mock:
        # Mock the chat completion response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = '''[
            {
                "type": "bar",
                "title": "Sample Bar Chart",
                "x_axis": "category",
                "y_axis": "value",
                "explanation": "This is a test bar chart",
                "data": [
                    {"category": "A", "value": 10},
                    {"category": "B", "value": 20},
                    {"category": "C", "value": 15}
                ]
            }
        ]'''
        
        mock.chat.completions.create.return_value = mock_response
        yield mock

@pytest.fixture
def sample_csv_file():
    """Create a temporary CSV file for testing"""
    data = {
        'category': ['A', 'B', 'C', 'D'],
        'value': [10, 20, 15, 25],
        'description': ['First', 'Second', 'Third', 'Fourth']
    }
    df = pd.DataFrame(data)
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        df.to_csv(f.name, index=False)
        yield f.name
    
    os.unlink(f.name)

@pytest.fixture
def sample_excel_file():
    """Create a temporary Excel file for testing"""
    data = {
        'product': ['Widget A', 'Widget B', 'Widget C'],
        'sales': [100, 150, 200],
        'profit': [20, 30, 40]
    }
    df = pd.DataFrame(data)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as f:
        df.to_excel(f.name, index=False)
        yield f.name
    
    os.unlink(f.name)

@pytest.fixture
def empty_csv_file():
    """Create an empty CSV file for testing"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        f.write("")
        yield f.name
    
    os.unlink(f.name)

@pytest.fixture
def invalid_csv_file():
    """Create an invalid CSV file for testing"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        f.write("invalid,csv,content\nwith,malformed\ndata")
        yield f.name
    
    os.unlink(f.name)

@pytest.fixture
def large_csv_file():
    """Create a large CSV file for testing"""
    data = {
        'id': range(1000),
        'name': [f'Item {i}' for i in range(1000)],
        'value': [i * 2 for i in range(1000)],
        'category': [f'Cat {i % 10}' for i in range(1000)]
    }
    df = pd.DataFrame(data)
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        df.to_csv(f.name, index=False)
        yield f.name
    
    os.unlink(f.name)