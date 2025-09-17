# Data Visualization Web Application

A full-stack web application that allows users to upload CSV/Excel files and get AI-powered chart suggestions using GPT-4o-mini.

## Architecture
- **Frontend**: Next.js + TypeScript + Tailwind CSS
- **Backend**: FastAPI + Python
- **Deployment**: Vercel (frontend) + Heroku (backend)

## Features
- Drag-and-drop file upload for CSV/Excel files
- AI-powered chart suggestions using OpenAI GPT-4o-mini
- Interactive data visualizations using Recharts
- Responsive design with Tailwind CSS

## Development

### Prerequisites
- Node.js 18+
- Python 3.9+
- OpenAI API key

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Environment Variables
Create `.env` in backend directory:
```
OPENAI_API_KEY=your_openai_api_key
```

Create `.env.local` in frontend directory:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Usage
1. Start both frontend (port 3000) and backend (port 8000) servers
2. Upload a CSV/Excel file using the drag-and-drop interface
3. View AI-generated chart suggestions
4. Interact with the visualizations

## Deployment
- Frontend: Deploy to Vercel
- Backend: Deploy to Heroku with provided configuration files