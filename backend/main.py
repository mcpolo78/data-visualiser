from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import json
import io
from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(title="Data Visualization API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.get("/")
async def health_check():
    return {"status": "healthy", "message": "Data Visualization API is running"}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        # Check file type
        if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="Only CSV and Excel files are supported")
        
        # Read file content
        content = await file.read()
        
        # Parse file based on extension
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(content))
        else:
            df = pd.read_excel(io.BytesIO(content))
        
        # Basic data validation
        if df.empty:
            raise HTTPException(status_code=400, detail="The uploaded file is empty")
        
        if len(df.columns) == 0:
            raise HTTPException(status_code=400, detail="No columns found in the file")
        
        # Get basic info about the dataset
        data_info = {
            "columns": list(df.columns),
            "row_count": len(df),
            "column_count": len(df.columns),
            "sample_data": df.head(5).to_dict('records'),
            "column_types": {col: str(df[col].dtype) for col in df.columns}
        }
        
        # Generate AI suggestions for charts
        chart_suggestions = await generate_chart_suggestions(df)
        
        return {
            "status": "success",
            "data_info": data_info,
            "chart_suggestions": chart_suggestions
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

async def generate_chart_suggestions(df: pd.DataFrame):
    try:
        # Prepare data summary for AI
        data_summary = {
            "columns": list(df.columns),
            "row_count": len(df),
            "column_types": {col: str(df[col].dtype) for col in df.columns},
            "sample_data": df.head(3).to_dict('records'),
            "numeric_columns": list(df.select_dtypes(include=['number']).columns),
            "categorical_columns": list(df.select_dtypes(include=['object']).columns)
        }
        
        prompt = f"""
        Based on the following dataset information, suggest the 3 most appropriate chart types and provide the data structure needed for each chart.
        
        Dataset Info:
        - Columns: {data_summary['columns']}
        - Row count: {data_summary['row_count']}
        - Column types: {data_summary['column_types']}
        - Numeric columns: {data_summary['numeric_columns']}
        - Categorical columns: {data_summary['categorical_columns']}
        - Sample data: {data_summary['sample_data']}
        
        For each chart suggestion, provide:
        1. Chart type (bar, line, pie, scatter, area)
        2. Title
        3. X-axis column
        4. Y-axis column (if applicable)
        5. Brief explanation of why this chart is suitable
        6. The actual data in the format needed for the chart (limit to 10 data points for performance)
        
        Respond in valid JSON format with an array of chart suggestions.
        """
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2000
        )
        
        # Parse AI response
        suggestions_text = response.choices[0].message.content
        
        # Try to extract JSON from the response
        try:
            suggestions = json.loads(suggestions_text)
            return suggestions
        except json.JSONDecodeError:
            # Fallback: create basic suggestions if AI response is not valid JSON
            return create_fallback_suggestions(df)
            
    except Exception as e:
        # Fallback suggestions if AI fails
        return create_fallback_suggestions(df)

def create_fallback_suggestions(df: pd.DataFrame):
    """Create basic chart suggestions if AI fails"""
    suggestions = []
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
    
    # Bar chart suggestion
    if len(categorical_cols) > 0 and len(numeric_cols) > 0:
        suggestions.append({
            "type": "bar",
            "title": f"{numeric_cols[0]} by {categorical_cols[0]}",
            "x_axis": categorical_cols[0],
            "y_axis": numeric_cols[0],
            "explanation": f"Bar chart showing {numeric_cols[0]} values across different {categorical_cols[0]} categories",
            "data": df.groupby(categorical_cols[0])[numeric_cols[0]].sum().head(10).reset_index().to_dict('records')
        })
    
    # Line chart suggestion
    if len(numeric_cols) >= 2:
        suggestions.append({
            "type": "line",
            "title": f"{numeric_cols[0]} vs {numeric_cols[1]}",
            "x_axis": numeric_cols[1],
            "y_axis": numeric_cols[0],
            "explanation": f"Line chart showing the relationship between {numeric_cols[0]} and {numeric_cols[1]}",
            "data": df[[numeric_cols[1], numeric_cols[0]]].head(10).to_dict('records')
        })
    
    # Pie chart suggestion
    if len(categorical_cols) > 0:
        value_counts = df[categorical_cols[0]].value_counts().head(5)
        suggestions.append({
            "type": "pie",
            "title": f"Distribution of {categorical_cols[0]}",
            "explanation": f"Pie chart showing the distribution of different {categorical_cols[0]} categories",
            "data": [{"name": str(k), "value": int(v)} for k, v in value_counts.items()]
        })
    
    return suggestions

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)