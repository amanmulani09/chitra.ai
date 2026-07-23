# chitra.ai A-Video-Analysis-Agent

AI video analysis has practical applications across industries like healthcare monitoring, security systems, customer service quality assurance, and remote assistance. By combining visual analysis with audio transcription, you can create intelligent systems that understand both what people are saying and what's happening on screen.

## Running locally

```bash
cp .env.example .env          # then fill in your API keys
uv sync                       # install dependencies
uv run uvicorn app.main:app --reload
```

The app runs at http://localhost:8000 (`/health` for a status check, `/docs` for the API).

## Running with Docker

```bash
docker compose up --build
```
