from fastapi import FastAPI, Request, WebSocket,HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import json 
import os 

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from datetime import datetime
from dotenv import load_dotenv, find_dotenv
import openai
import logging


# setup logging 
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Chitra.ai AI video analysis app", version="0.0.1")

templates = Jinja2Templates(directory=".")

# Configuration
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")
FROM_EMAIL = os.getenv("FROM_EMAIL")


# Initialize services
openai_client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)