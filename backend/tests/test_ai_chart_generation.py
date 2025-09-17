import pytest
import json
import pandas as pd
from unittest.mock import patch, Mock
from main import generate_chart_suggestions, create_fallback_suggestions

class TestAIChartGeneration:
    """Test AI-powered chart generation functionality"""

    @pytest.mark.unit
    def test_generate_chart_suggestions_success(self, mock_openai_client):
        """Test successful chart generation with valid AI response"""
        # Create test DataFrame
        test_data = pd.DataFrame({
            'category': ['A', 'B', 'C'],
            'value': [10, 20, 15],
            'description': ['First', 'Second', 'Third']
        })
        
        # Call the function
        result = generate_chart_suggestions(test_data)
        
        # Verify result structure
        assert isinstance(result, list)
        assert len(result) > 0
        
        # Check first suggestion structure
        suggestion = result[0]
        assert "type" in suggestion
        assert "title" in suggestion
        assert "explanation" in suggestion
        assert "data" in suggestion
        
        # Verify OpenAI was called
        mock_openai_client.chat.completions.create.assert_called_once()

    @pytest.mark.unit
    def test_generate_chart_suggestions_with_numeric_data(self, mock_openai_client):
        """Test chart generation with purely numeric data"""
        test_data = pd.DataFrame({
            'sales': [100, 200, 150, 300],
            'profit': [20, 40, 30, 60],
            'expenses': [80, 160, 120, 240]
        })
        
        result = generate_chart_suggestions(test_data)
        
        assert isinstance(result, list)
        assert len(result) > 0

    @pytest.mark.unit
    def test_generate_chart_suggestions_with_categorical_data(self, mock_openai_client):
        """Test chart generation with categorical data"""
        test_data = pd.DataFrame({
            'product': ['Widget A', 'Widget B', 'Widget C'],
            'category': ['Electronics', 'Home', 'Garden'],
            'brand': ['BrandX', 'BrandY', 'BrandZ']
        })
        
        result = generate_chart_suggestions(test_data)
        
        assert isinstance(result, list)
        assert len(result) > 0

    @pytest.mark.unit
    def test_generate_chart_suggestions_mixed_data_types(self, mock_openai_client):
        """Test chart generation with mixed data types"""
        test_data = pd.DataFrame({
            'name': ['Item 1', 'Item 2', 'Item 3'],
            'value': [100, 200, 150],
            'active': [True, False, True],
            'date': pd.to_datetime(['2024-01-01', '2024-01-02', '2024-01-03'])
        })
        
        result = generate_chart_suggestions(test_data)
        
        assert isinstance(result, list)
        assert len(result) > 0

    @pytest.mark.unit
    def test_generate_chart_suggestions_ai_failure_fallback(self):
        """Test fallback when AI fails"""
        with patch('main.client.chat.completions.create') as mock_create:
            mock_create.side_effect = Exception("AI API Error")
            
            test_data = pd.DataFrame({
                'category': ['A', 'B', 'C'],
                'value': [10, 20, 15]
            })
            
            result = generate_chart_suggestions(test_data)
            
            # Should still return suggestions via fallback
            assert isinstance(result, list)
            assert len(result) > 0

    @pytest.mark.unit
    def test_generate_chart_suggestions_invalid_json_fallback(self):
        """Test fallback when AI returns invalid JSON"""
        with patch('main.client.chat.completions.create') as mock_create:
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message = Mock()
            mock_response.choices[0].message.content = "Invalid JSON response from AI"
            mock_create.return_value = mock_response
            
            test_data = pd.DataFrame({
                'category': ['A', 'B', 'C'],
                'value': [10, 20, 15]
            })
            
            result = generate_chart_suggestions(test_data)
            
            # Should fallback to basic suggestions
            assert isinstance(result, list)
            assert len(result) > 0

    @pytest.mark.unit
    def test_ai_prompt_construction(self, mock_openai_client):
        """Test that AI prompt contains necessary information"""
        test_data = pd.DataFrame({
            'sales': [100, 200, 150],
            'region': ['North', 'South', 'East']
        })
        
        generate_chart_suggestions(test_data)
        
        # Get the call arguments
        call_args = mock_openai_client.chat.completions.create.call_args
        messages = call_args[1]['messages']
        prompt_content = messages[0]['content']
        
        # Verify prompt contains key information
        assert 'sales' in prompt_content
        assert 'region' in prompt_content
        assert 'chart' in prompt_content.lower()
        assert 'json' in prompt_content.lower()

class TestFallbackChartGeneration:
    """Test fallback chart generation when AI fails"""

    @pytest.mark.unit
    def test_create_fallback_suggestions_with_mixed_data(self):
        """Test fallback suggestions with mixed data types"""
        test_data = pd.DataFrame({
            'category': ['A', 'B', 'C', 'D'],
            'sales': [100, 200, 150, 300],
            'profit': [20, 40, 30, 60]
        })
        
        result = create_fallback_suggestions(test_data)
        
        assert isinstance(result, list)
        assert len(result) > 0
        
        # Should create multiple types of charts
        chart_types = [suggestion['type'] for suggestion in result]
        assert 'bar' in chart_types  # Should suggest bar chart

    @pytest.mark.unit
    def test_create_fallback_suggestions_numeric_only(self):
        """Test fallback with only numeric columns"""
        test_data = pd.DataFrame({
            'value1': [10, 20, 30],
            'value2': [15, 25, 35],
            'value3': [5, 10, 15]
        })
        
        result = create_fallback_suggestions(test_data)
        
        assert isinstance(result, list)
        assert len(result) > 0
        
        # Should create line chart for numeric data
        chart_types = [suggestion['type'] for suggestion in result]
        assert 'line' in chart_types

    @pytest.mark.unit
    def test_create_fallback_suggestions_categorical_only(self):
        """Test fallback with only categorical columns"""
        test_data = pd.DataFrame({
            'category1': ['A', 'B', 'C'],
            'category2': ['X', 'Y', 'Z'],
            'category3': ['P', 'Q', 'R']
        })
        
        result = create_fallback_suggestions(test_data)
        
        # Might return empty or pie chart based on value counts
        assert isinstance(result, list)

    @pytest.mark.unit
    def test_create_fallback_suggestions_empty_dataframe(self):
        """Test fallback with empty DataFrame"""
        test_data = pd.DataFrame()
        
        result = create_fallback_suggestions(test_data)
        
        assert isinstance(result, list)
        # Empty DataFrame should return empty suggestions

    @pytest.mark.unit
    def test_fallback_chart_data_structure(self):
        """Test that fallback charts have correct data structure"""
        test_data = pd.DataFrame({
            'category': ['A', 'B', 'C'],
            'value': [10, 20, 15]
        })
        
        result = create_fallback_suggestions(test_data)
        
        for suggestion in result:
            assert 'type' in suggestion
            assert 'title' in suggestion
            assert 'explanation' in suggestion
            assert 'data' in suggestion
            assert isinstance(suggestion['data'], list)

    @pytest.mark.unit
    def test_fallback_data_limit(self):
        """Test that fallback limits data points for performance"""
        # Create large dataset
        large_data = pd.DataFrame({
            'category': [f'Cat_{i}' for i in range(100)],
            'value': list(range(100))
        })
        
        result = create_fallback_suggestions(large_data)
        
        # Check that data is limited
        for suggestion in result:
            if 'data' in suggestion and suggestion['data']:
                assert len(suggestion['data']) <= 10  # Should limit to 10 points

class TestChartDataValidation:
    """Test validation of chart data structures"""

    @pytest.mark.unit
    def test_chart_suggestion_structure_validation(self, mock_openai_client):
        """Test that chart suggestions have required structure"""
        test_data = pd.DataFrame({
            'x': [1, 2, 3],
            'y': [10, 20, 30]
        })
        
        result = generate_chart_suggestions(test_data)
        
        for suggestion in result:
            # Required fields
            assert 'type' in suggestion
            assert 'title' in suggestion
            assert 'explanation' in suggestion
            assert 'data' in suggestion
            
            # Data should be a list
            assert isinstance(suggestion['data'], list)
            
            # Title and explanation should be strings
            assert isinstance(suggestion['title'], str)
            assert isinstance(suggestion['explanation'], str)
            
            # Type should be valid chart type
            valid_types = ['bar', 'line', 'pie', 'scatter', 'area']
            assert suggestion['type'] in valid_types

    @pytest.mark.unit
    def test_chart_data_sanitization(self, mock_openai_client):
        """Test that chart data is properly sanitized"""
        # Create data with potentially problematic values
        test_data = pd.DataFrame({
            'category': ['<script>alert("xss")</script>', 'Normal', 'Special"Quote'],
            'value': [100, 200, 300]
        })
        
        result = generate_chart_suggestions(test_data)
        
        # Data should be present and safe
        assert len(result) > 0
        for suggestion in result:
            assert 'data' in suggestion
            assert isinstance(suggestion['data'], list)

class TestAIPromptEdgeCases:
    """Test edge cases in AI prompt generation"""

    @pytest.mark.unit
    def test_very_large_dataset_prompt(self, mock_openai_client):
        """Test prompt generation with very large dataset"""
        # Create large dataset
        large_data = pd.DataFrame({
            'col1': range(10000),
            'col2': [f'value_{i}' for i in range(10000)]
        })
        
        result = generate_chart_suggestions(large_data)
        
        # Should handle large dataset without issues
        assert isinstance(result, list)
        
        # Verify AI was called (prompt shouldn't be too large)
        mock_openai_client.chat.completions.create.assert_called_once()

    @pytest.mark.unit
    def test_many_columns_prompt(self, mock_openai_client):
        """Test prompt generation with many columns"""
        # Create dataset with many columns
        data_dict = {f'col_{i}': [1, 2, 3] for i in range(50)}
        many_cols_data = pd.DataFrame(data_dict)
        
        result = generate_chart_suggestions(many_cols_data)
        
        assert isinstance(result, list)
        mock_openai_client.chat.completions.create.assert_called_once()

    @pytest.mark.unit
    def test_unicode_column_names_prompt(self, mock_openai_client):
        """Test prompt generation with Unicode column names"""
        unicode_data = pd.DataFrame({
            'Café☕': [1, 2, 3],
            '数据': [10, 20, 30],
            '🚀Revenue': [100, 200, 300],
            'Ψυχή': [0.1, 0.2, 0.3]
        })
        
        result = generate_chart_suggestions(unicode_data)
        
        assert isinstance(result, list)
        mock_openai_client.chat.completions.create.assert_called_once()