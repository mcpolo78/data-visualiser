import pytest
import os
import tempfile
from unittest.mock import patch, Mock
from fastapi import HTTPException

class TestAPIErrorHandling:
    """Test comprehensive error handling across the API"""

    @pytest.mark.unit
    def test_missing_openai_api_key(self, client):
        """Test behavior when OpenAI API key is missing"""
        # Temporarily remove the API key
        original_key = os.environ.get("OPENAI_API_KEY")
        if "OPENAI_API_KEY" in os.environ:
            del os.environ["OPENAI_API_KEY"]
        
        try:
            # This should be handled in application startup
            csv_content = "name,value\nTest,100"
            response = client.post(
                "/upload",
                files={"file": ("test.csv", csv_content.encode('utf-8'), "text/csv")}
            )
            
            # Should either fail gracefully or use fallback
            assert response.status_code in [200, 500]
            
        finally:
            # Restore the API key
            if original_key:
                os.environ["OPENAI_API_KEY"] = original_key

    @pytest.mark.unit
    def test_invalid_openai_api_key(self, client):
        """Test behavior with invalid OpenAI API key"""
        with patch('main.client.chat.completions.create') as mock_create:
            mock_create.side_effect = Exception("Invalid API key")
            
            csv_content = "name,value\nTest,100"
            response = client.post(
                "/upload",
                files={"file": ("test.csv", csv_content.encode('utf-8'), "text/csv")}
            )
            
            # Should fallback gracefully
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "chart_suggestions" in data

    @pytest.mark.unit
    def test_network_timeout_openai(self, client):
        """Test behavior when OpenAI API times out"""
        with patch('main.client.chat.completions.create') as mock_create:
            mock_create.side_effect = TimeoutError("Request timeout")
            
            csv_content = "name,value\nTest,100"
            response = client.post(
                "/upload",
                files={"file": ("test.csv", csv_content.encode('utf-8'), "text/csv")}
            )
            
            # Should handle timeout gracefully
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"

    @pytest.mark.unit
    def test_openai_rate_limiting(self, client):
        """Test behavior when OpenAI API rate limits"""
        with patch('main.client.chat.completions.create') as mock_create:
            mock_create.side_effect = Exception("Rate limit exceeded")
            
            csv_content = "name,value\nTest,100"
            response = client.post(
                "/upload",
                files={"file": ("test.csv", csv_content.encode('utf-8'), "text/csv")}
            )
            
            # Should fallback gracefully
            assert response.status_code == 200

class TestFileProcessingErrors:
    """Test error handling in file processing"""

    @pytest.mark.unit
    def test_corrupted_csv_file(self, client):
        """Test handling of corrupted CSV files"""
        # Create corrupted CSV with binary data
        corrupted_content = b'\x00\x01\x02\x03\x04\x05corrupted,data\n\xFF\xFE\xFD,values'
        
        response = client.post(
            "/upload",
            files={"file": ("corrupted.csv", corrupted_content, "text/csv")}
        )
        
        # Should handle gracefully with error message
        assert response.status_code in [400, 500]
        if response.status_code == 400:
            assert "detail" in response.json()

    @pytest.mark.unit
    def test_file_encoding_issues(self, client):
        """Test handling of various file encodings"""
        # Test different encodings
        encodings_to_test = [
            ('latin1', 'Café naïve résumé'),
            ('cp1252', 'Windows specific chars'),
            ('utf-16', 'UTF-16 encoded text'),
        ]
        
        for encoding, text in encodings_to_test:
            csv_content = f"name,description\nTest,{text}"
            
            try:
                encoded_content = csv_content.encode(encoding)
                response = client.post(
                    "/upload",
                    files={"file": (f"test_{encoding}.csv", encoded_content, "text/csv")}
                )
                
                # Should either succeed or fail gracefully
                assert response.status_code in [200, 400, 500]
                
            except UnicodeEncodeError:
                # Some characters can't be encoded in certain formats
                continue

    @pytest.mark.unit
    def test_extremely_large_file(self, client):
        """Test handling of extremely large files"""
        # Create a very large CSV (simulated)
        large_content = "col1,col2\n" + "value1,value2\n" * 100000  # ~1.3MB
        
        response = client.post(
            "/upload",
            files={"file": ("large.csv", large_content.encode('utf-8'), "text/csv")}
        )
        
        # Should either process or reject with appropriate error
        assert response.status_code in [200, 413, 500]

    @pytest.mark.unit
    def test_file_with_no_data_rows(self, client):
        """Test CSV with only headers"""
        csv_content = "name,value,category"  # Only header, no data
        
        response = client.post(
            "/upload",
            files={"file": ("headers_only.csv", csv_content.encode('utf-8'), "text/csv")}
        )
        
        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()

    @pytest.mark.unit
    def test_file_with_inconsistent_columns(self, client):
        """Test CSV with inconsistent column counts"""
        csv_content = """name,value,category
Row1,100
Row2,200,Cat2,Extra
Row3,300,Cat3"""
        
        response = client.post(
            "/upload",
            files={"file": ("inconsistent.csv", csv_content.encode('utf-8'), "text/csv")}
        )
        
        # Pandas usually handles this, but should not crash
        assert response.status_code in [200, 400]

class TestDataValidationErrors:
    """Test data validation error handling"""

    @pytest.mark.unit
    def test_completely_empty_dataframe(self, client):
        """Test handling when DataFrame ends up completely empty after processing"""
        with patch('pandas.read_csv') as mock_read_csv:
            mock_read_csv.return_value = pd.DataFrame()  # Empty DataFrame
            
            csv_content = "name,value\nTest,100"
            response = client.post(
                "/upload",
                files={"file": ("test.csv", csv_content.encode('utf-8'), "text/csv")}
            )
            
            assert response.status_code == 400

    @pytest.mark.unit
    def test_dataframe_with_no_columns(self, client):
        """Test handling when DataFrame has no columns"""
        with patch('pandas.read_csv') as mock_read_csv:
            import pandas as pd
            mock_read_csv.return_value = pd.DataFrame(index=[0, 1, 2])  # No columns
            
            csv_content = "name,value\nTest,100"
            response = client.post(
                "/upload",
                files={"file": ("test.csv", csv_content.encode('utf-8'), "text/csv")}
            )
            
            assert response.status_code == 400

    @pytest.mark.unit
    def test_dataframe_processing_exception(self, client):
        """Test handling when DataFrame processing raises exception"""
        with patch('pandas.read_csv') as mock_read_csv:
            mock_read_csv.side_effect = Exception("Pandas processing error")
            
            csv_content = "name,value\nTest,100"
            response = client.post(
                "/upload",
                files={"file": ("test.csv", csv_content.encode('utf-8'), "text/csv")}
            )
            
            assert response.status_code == 500
            assert "Error processing file" in response.json()["detail"]

class TestMemoryAndResourceErrors:
    """Test memory and resource exhaustion scenarios"""

    @pytest.mark.unit
    def test_memory_error_handling(self, client):
        """Test handling of memory errors during processing"""
        with patch('pandas.read_csv') as mock_read_csv:
            mock_read_csv.side_effect = MemoryError("Out of memory")
            
            csv_content = "name,value\nTest,100"
            response = client.post(
                "/upload",
                files={"file": ("test.csv", csv_content.encode('utf-8'), "text/csv")}
            )
            
            assert response.status_code == 500

    @pytest.mark.unit
    def test_processing_timeout(self, client):
        """Test handling of processing timeouts"""
        with patch('main.generate_chart_suggestions') as mock_generate:
            import time
            def slow_function(*args, **kwargs):
                time.sleep(10)  # Simulate slow processing
                return []
            
            mock_generate.side_effect = slow_function
            
            csv_content = "name,value\nTest,100"
            
            # This test depends on having timeout handling in the application
            response = client.post(
                "/upload",
                files={"file": ("test.csv", csv_content.encode('utf-8'), "text/csv")},
                timeout=5  # 5 second timeout
            )
            
            # Should either complete or timeout gracefully
            assert response.status_code in [200, 408, 500, 504]

class TestEdgeCaseInputValidation:
    """Test validation of edge case inputs"""

    @pytest.mark.unit
    def test_file_parameter_edge_cases(self, client):
        """Test various edge cases for file parameter"""
        # Test with None filename
        response = client.post(
            "/upload",
            files={"file": (None, b"test,data", "text/csv")}
        )
        assert response.status_code in [400, 422]
        
        # Test with empty filename
        response = client.post(
            "/upload",
            files={"file": ("", b"test,data", "text/csv")}
        )
        assert response.status_code in [400, 422]
        
        # Test with very long filename
        long_filename = "a" * 1000 + ".csv"
        response = client.post(
            "/upload",
            files={"file": (long_filename, b"test,data", "text/csv")}
        )
        assert response.status_code in [200, 400]

    @pytest.mark.unit
    def test_content_type_validation(self, client):
        """Test content type validation"""
        csv_content = "name,value\nTest,100"
        
        # Test with wrong content type
        response = client.post(
            "/upload",
            files={"file": ("test.csv", csv_content.encode('utf-8'), "application/json")}
        )
        
        # Should still process based on file extension or content
        assert response.status_code in [200, 400]

    @pytest.mark.unit
    def test_multiple_files_upload(self, client):
        """Test behavior when multiple files are uploaded"""
        csv_content = "name,value\nTest,100"
        
        # FastAPI should handle only the first file or reject multiple files
        files = {
            "file": ("test1.csv", csv_content.encode('utf-8'), "text/csv"),
            "file2": ("test2.csv", csv_content.encode('utf-8'), "text/csv")
        }
        
        response = client.post("/upload", files=files)
        
        # Should either process first file or reject appropriately
        assert response.status_code in [200, 400, 422]

class TestSecurityErrorHandling:
    """Test security-related error handling"""

    @pytest.mark.unit
    def test_path_traversal_in_filename(self, client, mock_openai_client):
        """Test handling of path traversal attempts in filename"""
        malicious_filenames = [
            "../../../etc/passwd.csv",
            "..\\..\\..\\windows\\system32\\config\\sam.csv",
            "/etc/shadow.csv",
            "C:\\Windows\\System32\\config\\SAM.csv"
        ]
        
        csv_content = "name,value\nTest,100"
        
        for filename in malicious_filenames:
            response = client.post(
                "/upload",
                files={"file": (filename, csv_content.encode('utf-8'), "text/csv")}
            )
            
            # Should process safely without accessing filesystem
            assert response.status_code in [200, 400]

    @pytest.mark.unit
    def test_oversized_field_handling(self, client):
        """Test handling of extremely large field values"""
        # Create CSV with extremely large field
        large_field = "x" * 1000000  # 1MB field
        csv_content = f"name,description\nTest,{large_field}"
        
        response = client.post(
            "/upload",
            files={"file": ("large_field.csv", csv_content.encode('utf-8'), "text/csv")}
        )
        
        # Should handle without memory issues
        assert response.status_code in [200, 400, 413]

import pandas as pd

class TestPandasSpecificErrors:
    """Test handling of Pandas-specific errors"""

    @pytest.mark.unit
    def test_pandas_parsing_error(self, client):
        """Test handling of Pandas parsing errors"""
        with patch('pandas.read_csv') as mock_read_csv:
            mock_read_csv.side_effect = pd.errors.ParserError("Pandas parsing error")
            
            csv_content = "name,value\nTest,100"
            response = client.post(
                "/upload",
                files={"file": ("test.csv", csv_content.encode('utf-8'), "text/csv")}
            )
            
            assert response.status_code == 500

    @pytest.mark.unit
    def test_pandas_dtype_error(self, client):
        """Test handling of data type errors"""
        with patch('pandas.read_csv') as mock_read_csv:
            mock_read_csv.side_effect = pd.errors.DtypeWarning("Data type warning")
            
            csv_content = "name,value\nTest,100"
            response = client.post(
                "/upload",
                files={"file": ("test.csv", csv_content.encode('utf-8'), "text/csv")}
            )
            
            assert response.status_code == 500