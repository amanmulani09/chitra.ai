from fastapi import FastAPI
from fastapi.templating import Jinja2Templates

from app.agents.data_capture import DataCaptureAgent
from app.config import logger

app = FastAPI(title="Chitra.ai AI video analysis app", version="0.0.1")

templates = Jinja2Templates(directory="templates")

# Agents
data_capture_agent = DataCaptureAgent()

logger.info("Chitra.ai app initialized")


@app.get("/health")
async def health():
    return {"status": "ok"}
