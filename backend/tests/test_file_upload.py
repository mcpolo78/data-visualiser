import pytest
import os
import json
from unittest.mock import patch, Mock

class TestFileUpload:
    """Test file upload functionality"""

    @pytest.mark.integration
    def test_upload_valid_csv_file(self, client, sample_csv_file, mock_openai_client):
        """Test uploading a valid CSV file"""
        with open(sample_csv_file, 'rb') as f:
            response = client.post(
                "/upload",
                files={"file": ("test.csv", f, "text/csv")}
            )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "success"
        assert "data_info" in data
        assert "chart_suggestions" in data
        
        # Check data info structure
        data_info = data["data_info"]
        assert "columns" in data_info
        assert "row_count" in data_info
        assert "column_count" in data_info
        assert "sample_data" in data_info
        assert "column_types" in data_info
        
        # Verify expected columns
        assert "category" in data_info["columns"]
        assert "value" in data_info["columns"]
        assert data_info["row_count"] == 4
        assert data_info["column_count"] == 3

    @pytest.mark.integration
    def test_upload_valid_excel_file(self, client, sample_excel_file, mock_openai_client):
        """Test uploading a valid Excel file"""
        with open(sample_excel_file, 'rb') as f:
            response = client.post(
                "/upload",
                files={"file": ("test.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
            )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "success"
        assert "data_info" in data
        assert "chart_suggestions" in data
        
        # Check data structure
        data_info = data["data_info"]
        assert "product" in data_info["columns"]
        assert "sales" in data_info["columns"]
        assert "profit" in data_info["columns"]

    @pytest.mark.unit
    def test_upload_unsupported_file_type(self, client):
        """Test uploading an unsupported file type"""
        # Create a fake text file
        file_content = b"This is not a CSV or Excel file"
        
        response = client.post(
            "/upload",
            files={"file": ("test.txt", file_content, "text/plain")}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "Only CSV and Excel files are supported" in data["detail"]

    @pytest.mark.unit
    def test_upload_empty_csv_file(self, client, empty_csv_file):
        """Test uploading an empty CSV file"""
        with open(empty_csv_file, 'rb') as f:
            response = client.post(
                "/upload",
                files={"file": ("empty.csv", f, "text/csv")}
            )
        
        assert response.status_code == 400
        data = response.json()
        assert "empty" in data["detail"].lower()

    @pytest.mark.unit
    def test_upload_no_file(self, client):
        """Test upload endpoint without providing a file"""
        response = client.post("/upload")
        
        assert response.status_code == 422  # Unprocessable Entity

    @pytest.mark.unit
    def test_upload_invalid_csv_format(self, client, invalid_csv_file):
        """Test uploading a malformed CSV file"""
        with open(invalid_csv_file, 'rb') as f:
            response = client.post(
                "/upload",
                files={"file": ("invalid.csv", f, "text/csv")}
            )
        
        # Should handle gracefully and return error
        assert response.status_code in [400, 500]

    @pytest.mark.integration
    def test_upload_large_file(self, client, large_csv_file, mock_openai_client):
        """Test uploading a large CSV file"""
        with open(large_csv_file, 'rb') as f:
            response = client.post(
                "/upload",
                files={"file": ("large.csv", f, "text/csv")}
            )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "success"
        assert data["data_info"]["row_count"] == 1000
        assert data["data_info"]["column_count"] == 4

    @pytest.mark.unit
    def test_upload_file_with_special_characters(self, client, mock_openai_client):
        """Test uploading a file with special characters in data"""
        csv_content = "name,value,description\n"
        csv_content += "Test Item,100,Description with àccénts\n"
        csv_content += "Another Item,200,Description with émojis 🚀\n"
        csv_content += "Special Chars,300,Quotes \"test\" and commas, here\n"
        
        response = client.post(
            "/upload",
            files={"file": ("special.csv", csv_content.encode('utf-8'), "text/csv")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    @pytest.mark.unit
    def test_upload_file_with_numeric_data(self, client, mock_openai_client):
        """Test uploading a file with various numeric data types"""
        csv_content = "integer,float,negative,zero\n"
        csv_content += "1,1.5,-10,0\n"
        csv_content += "2,2.7,-20,0\n"
        csv_content += "3,3.14,-30,0\n"
        
        response = client.post(
            "/upload",
            files={"file": ("numeric.csv", csv_content.encode('utf-8'), "text/csv")}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check that numeric columns are identified
        column_types = data["data_info"]["column_types"]
        assert "int" in column_types["integer"] or "float" in column_types["integer"]
        assert "float" in column_types["float"]

    @pytest.mark.unit
    def test_upload_file_with_missing_values(self, client, mock_openai_client):
        """Test uploading a file with missing/null values"""
        csv_content = "name,value,category\n"
        csv_content += "Item 1,100,A\n"
        csv_content += "Item 2,,B\n"  # Missing value
        csv_content += "Item 3,300,\n"  # Missing category
        csv_content += ",400,C\n"  # Missing name
        
        response = client.post(
            "/upload",
            files={"file": ("missing.csv", csv_content.encode('utf-8'), "text/csv")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

class TestFileProcessing:
    """Test file processing and data extraction"""

    @pytest.mark.unit
    def test_csv_parsing_accuracy(self, client, mock_openai_client):
        """Test that CSV data is parsed accurately"""
        csv_content = "product,price,quantity\n"
        csv_content += "Widget A,19.99,10\n"
        csv_content += "Widget B,29.99,5\n"
        
        response = client.post(
            "/upload",
            files={"file": ("test.csv", csv_content.encode('utf-8'), "text/csv")}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check sample data accuracy
        sample_data = data["data_info"]["sample_data"]
        assert len(sample_data) == 2
        assert sample_data[0]["product"] == "Widget A"
        assert sample_data[0]["price"] == 19.99
        assert sample_data[0]["quantity"] == 10

    @pytest.mark.unit
    def test_data_type_detection(self, client, mock_openai_client):
        """Test that data types are correctly detected"""
        csv_content = "text_col,int_col,float_col,bool_col\n"
        csv_content += "hello,1,1.5,true\n"
        csv_content += "world,2,2.7,false\n"
        
        response = client.post(
            "/upload",
            files={"file": ("types.csv", csv_content.encode('utf-8'), "text/csv")}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        column_types = data["data_info"]["column_types"]
        assert "object" in column_types["text_col"]  # String data
        assert any(t in column_types["int_col"] for t in ["int", "Int"])  # Integer data
        assert "float" in column_types["float_col"]  # Float data

    @pytest.mark.integration
    def test_sample_data_limitation(self, client, large_csv_file, mock_openai_client):
        """Test that sample data is limited to prevent huge responses"""
        with open(large_csv_file, 'rb') as f:
            response = client.post(
                "/upload",
                files={"file": ("large.csv", f, "text/csv")}
            )
        
        assert response.status_code == 200
        data = response.json()
        
        # Sample data should be limited (typically to 5 rows)
        sample_data = data["data_info"]["sample_data"]
        assert len(sample_data) <= 5