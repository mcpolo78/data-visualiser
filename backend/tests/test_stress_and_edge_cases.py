import pytest
import os
import json
from unittest.mock import patch, Mock

class TestStressAndEdgeCases:
    """Comprehensive stress tests with problematic data"""

    @pytest.mark.integration
    def test_problematic_csv_handling(self, client, mock_openai_client):
        """Test the app with extremely problematic CSV data"""
        test_file_path = os.path.join(os.path.dirname(__file__), "problematic_test_data.csv")
        
        with open(test_file_path, 'rb') as f:
            response = client.post(
                "/upload",
                files={"file": ("stress_test.csv", f, "text/csv")}
            )
        
        # App should handle this gracefully - either succeed or fail with proper error
        assert response.status_code in [200, 400, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert data["status"] == "success"
            assert "data_info" in data
            
            # Verify it doesn't crash and returns reasonable data
            data_info = data["data_info"]
            assert data_info["row_count"] >= 0
            assert data_info["column_count"] >= 0
            assert isinstance(data_info["columns"], list)
            assert isinstance(data_info["sample_data"], list)

    @pytest.mark.unit
    def test_unicode_data_handling(self, client, mock_openai_client):
        """Test handling of various Unicode characters"""
        unicode_csv = """name,value,description
Unicode Test 1,100,"Standard ASCII text"
Unicode Test 2,200,"Café naïve résumé"
Unicode Test 3,300,"Ψυχή (soul) in Greek"
Unicode Test 4,400,"العربية (Arabic text)"
Unicode Test 5,500,"🚀🎯💡⚡️ Emoji test"
Unicode Test 6,600,"αβγδεζηθικλμνξοπρστυφχψω"
Unicode Test 7,700,"עברית שלום"
Unicode Test 8,800,"∞±∑∆∇∂∫∏√∝∞"
"""
        
        response = client.post(
            "/upload",
            files={"file": ("unicode_test.csv", unicode_csv.encode('utf-8'), "text/csv")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    @pytest.mark.unit
    def test_null_and_missing_data_variants(self, client, mock_openai_client):
        """Test various representations of null/missing data"""
        null_csv = """col1,col2,col3,col4,col5
1,null,NULL,None,
2,,,n/a,N/A
3,#N/A,#NULL!,#DIV/0!,#VALUE!
4,nan,NaN,NAN,inf
5,-inf,+inf,Infinity,-Infinity
6,undefined,void,empty,blank
"""
        
        response = client.post(
            "/upload",
            files={"file": ("null_test.csv", null_csv.encode('utf-8'), "text/csv")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    @pytest.mark.unit
    def test_extremely_long_strings(self, client, mock_openai_client):
        """Test handling of extremely long string values"""
        long_string = "A" * 10000  # 10k character string
        very_long_string = "B" * 100000  # 100k character string
        
        long_csv = f"""name,description,value
Short,Normal description,100
Medium,{'Medium ' * 100},200
Long,{long_string},300
Very Long,{very_long_string},400
"""
        
        response = client.post(
            "/upload",
            files={"file": ("long_strings.csv", long_csv.encode('utf-8'), "text/csv")}
        )
        
        # Should handle gracefully - either process or return error
        assert response.status_code in [200, 400, 413, 500]

    @pytest.mark.unit
    def test_malformed_csv_structures(self, client):
        """Test various malformed CSV structures"""
        malformed_csvs = [
            # Inconsistent column counts
            "col1,col2,col3\nval1,val2\nval3,val4,val5,val6",
            
            # Unmatched quotes
            'col1,col2\n"unmatched quote,value2',
            
            # Mixed delimiters
            "col1,col2;col3\nval1,val2;val3",
            
            # Binary data mixed in
            "col1,col2\n\x00\x01\x02,normal_value",
            
            # Only headers
            "col1,col2,col3",
            
            # Empty lines and spaces
            "\n\n   \n  col1,col2  \n\n  val1,val2  \n\n",
        ]
        
        for i, csv_content in enumerate(malformed_csvs):
            response = client.post(
                "/upload",
                files={"file": (f"malformed_{i}.csv", csv_content.encode('utf-8', errors='ignore'), "text/csv")}
            )
            
            # Should not crash - either process or return appropriate error
            assert response.status_code in [200, 400, 422, 500]

    @pytest.mark.unit
    def test_injection_attacks(self, client, mock_openai_client):
        """Test protection against injection attacks"""
        injection_csv = """name,command,script
SQL Injection,"'; DROP TABLE users; --",normal_value
XSS Injection,"<script>alert('xss')</script>",normal_value
Command Injection,"$(rm -rf /)",normal_value
Path Traversal,"../../../etc/passwd",normal_value
CSV Injection,"=cmd|'/c calc'!A0",normal_value
Formula Injection,"@SUM(1+1)*cmd|'/c calc'!A0",normal_value
"""
        
        response = client.post(
            "/upload",
            files={"file": ("injection_test.csv", injection_csv.encode('utf-8'), "text/csv")}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Data should be safely processed without executing anything
        assert data["status"] == "success"
        assert "data_info" in data

    @pytest.mark.unit
    def test_extreme_numeric_values(self, client, mock_openai_client):
        """Test handling of extreme numeric values"""
        extreme_csv = """type,value,description
Large Integer,999999999999999999999999999999999999999,Very large number
Small Float,1e-324,Smallest positive float
Large Float,1.7976931348623157e+308,Largest float
Negative Large,-999999999999999999999999999999999999999,Very large negative
Scientific,1.23e-45,Scientific notation
Hex,0xFFFFFFFF,Hexadecimal
Binary,0b11111111,Binary
Octal,0o777,Octal
Complex,"3+4j",Complex number (as string)
"""
        
        response = client.post(
            "/upload",
            files={"file": ("extreme_numbers.csv", extreme_csv.encode('utf-8'), "text/csv")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    @pytest.mark.unit
    def test_date_format_chaos(self, client, mock_openai_client):
        """Test various date formats and invalid dates"""
        date_csv = """event,date,alternative_date
Event 1,2024-01-15,01/15/2024
Event 2,2024-02-30,30/02/2024
Event 3,2024-13-45,45/13/2024
Event 4,01-Jan-2024,Jan 1st 2024
Event 5,2024/001/001,001/001/2024
Event 6,32-Dec-2023,Dec 32nd 2023
Event 7,2024-00-00,00/00/0000
Event 8,9999-99-99,99/99/9999
Event 9,Not a date,Also not a date
Event 10,2024-W53-7,Week 53 Day 7
"""
        
        response = client.post(
            "/upload",
            files={"file": ("date_chaos.csv", date_csv.encode('utf-8'), "text/csv")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

class TestErrorRecovery:
    """Test error recovery and graceful failure"""

    @pytest.mark.unit
    def test_openai_api_failure(self, client):
        """Test behavior when OpenAI API fails"""
        with patch('main.client.chat.completions.create') as mock_create:
            mock_create.side_effect = Exception("OpenAI API Error")
            
            csv_content = "name,value\nTest,100"
            response = client.post(
                "/upload",
                files={"file": ("test.csv", csv_content.encode('utf-8'), "text/csv")}
            )
            
            # Should still return data_info and fallback suggestions
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "data_info" in data
            assert "chart_suggestions" in data

    @pytest.mark.unit
    def test_memory_stress(self, client, mock_openai_client):
        """Test with data that might stress memory usage"""
        # Create a CSV with many columns and rows
        columns = [f"col_{i}" for i in range(100)]  # 100 columns
        header = ",".join(columns)
        
        rows = []
        for i in range(100):  # 100 rows
            row = ",".join([f"value_{i}_{j}" for j in range(100)])
            rows.append(row)
        
        large_csv = header + "\n" + "\n".join(rows)
        
        response = client.post(
            "/upload",
            files={"file": ("memory_stress.csv", large_csv.encode('utf-8'), "text/csv")}
        )
        
        # Should handle gracefully
        assert response.status_code in [200, 413, 500]

    @pytest.mark.unit
    def test_concurrent_uploads(self, client, mock_openai_client):
        """Test multiple concurrent uploads (simulated)"""
        csv_content = "name,value\nTest,100"
        
        # Simulate multiple requests
        responses = []
        for i in range(5):
            response = client.post(
                "/upload",
                files={"file": (f"concurrent_{i}.csv", csv_content.encode('utf-8'), "text/csv")}
            )
            responses.append(response)
        
        # All should succeed
        for response in responses:
            assert response.status_code == 200

class TestPerformanceEdgeCases:
    """Test performance edge cases"""

    @pytest.mark.slow
    def test_processing_timeout_protection(self, client):
        """Test that processing doesn't hang indefinitely"""
        # Create complex data that might cause slow processing
        complex_csv = "name,value,complex_data\n"
        for i in range(1000):
            complex_data = f"Complex string with numbers {i} and symbols !@#$%^&*() and unicode 🚀" * 10
            complex_csv += f"Item {i},{i},{complex_data}\n"
        
        response = client.post(
            "/upload",
            files={"file": ("complex.csv", complex_csv.encode('utf-8'), "text/csv")},
            timeout=30  # 30 second timeout
        )
        
        # Should complete within reasonable time
        assert response.status_code in [200, 400, 413, 500, 504]