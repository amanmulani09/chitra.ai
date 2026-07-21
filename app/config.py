"""Shared configuration: environment variables, logging, and API clients.

Centralising these here means the app and the agents import them from one
place instead of each module re-reading the environment.
"""

import logging
import os

import openai
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("chitra")

# Load environment variables from .env
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")
FROM_EMAIL = os.getenv("FROM_EMAIL")

# Initialize services
openai_client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)
