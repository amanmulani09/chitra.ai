"""Shared configuration: environment variables, logging, and API clients."""

import logging
import os
import sys

import openai
from dotenv import load_dotenv
from fastapi.templating import Jinja2Templates

load_dotenv()

# Logging (to stdout so Docker/log collectors pick it up)
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("chitra")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")
FROM_EMAIL = os.getenv("FROM_EMAIL")

# Allowed CORS origins, comma-separated (default: all).
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]

# Jinja2 templates (shared so API routes can render without re-instantiating).
templates = Jinja2Templates(directory="templates")

# Shared async client. Timeout + retries stop a slow OpenAI call from tying up
# a worker under load.
openai_client = openai.AsyncOpenAI(
    api_key=OPENAI_API_KEY,
    timeout=30.0,
    max_retries=2,
)
