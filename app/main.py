import os
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv
from app.directline import DirectLineAPI
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables from .env file
load_dotenv()

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fastapi_app")

# Initialize FastAPI app
app = FastAPI(
    title="FastAPI Microservice with Direct Line Integration",
    description="A microservice that communicates with a Copilot Studio agent via Direct Line API.",
    version="1.0.0",
    contact={"name": "Support Team", "email": "support@example.com"},
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins. Replace with specific domains for security.
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods
    allow_headers=["*"],  # Allows all headers
)

# Configuration
DIRECT_LINE_SECRET = os.getenv("DIRECT_LINE_SECRET")
BOT_ENDPOINT = os.getenv("BOT_ENDPOINT")
if not DIRECT_LINE_SECRET or not BOT_ENDPOINT:
    raise RuntimeError("Missing Direct Line secret or bot endpoint in environment variables.")

# Direct Line API instance
direct_line_api = None


@app.on_event("startup")
def startup_event():
    global direct_line_api
    direct_line_api = DirectLineAPI(secret=DIRECT_LINE_SECRET, bot_endpoint=BOT_ENDPOINT)
    logger.info("Direct Line API initialized.")


# Request and response models
class SendRequest(BaseModel):
    name: Optional[str] = None
    message: str

class SendResponse(BaseModel):
    bot_response: str
    citations : Optional[dict] = None
    conversationId : str
    name : Optional[str] = None


# Root endpoint
@app.get("/", summary="Root endpoint", tags=["General"])
async def root():
    return {"message": "Welcome to the FastAPI microservice!"}


# Send message endpoint
@app.post(
    "/send",
    response_model=SendResponse,
    summary="Send a message to the bot",
    description="Send a user message to the bot and get the bot's response.",
    tags=["Messaging"],
)
async def send_message(request: SendRequest):
    try:
        # Send user message to the bot
        logger.info(f"Sending message to bot: {request.message}")
        direct_line_api.send_activity(request.message)

        # Get bot's response
        bot_responses, conversationId, citations = direct_line_api.get_activity_response()
        if bot_responses:
            return {"bot_response": bot_responses, "name" : request.name, "conversationId" : conversationId, "citations" : citations}  # Return the latest bot response
        else:
            return {"bot_response": "No response from the bot.", "name" : request.name, "conversationId" : conversationId, "citations" : "No citations"}
    except Exception as e:
        logger.error(f"Error in /send endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Health check endpoint
@app.get("/checkHealth", summary="Check service health", tags=["Health"])
async def check_health():
    return {"status": "healthy"}


# API Info endpoint
@app.get("/api-info", summary="API Information", tags=["General"])
async def api_info():
    return {
        "title": app.title,
        "description": app.description,
        "version": app.version,
        "contact": app.contact,
    }


# Index of routes
@app.get("/index", summary="List all routes", tags=["General"])
async def index():
    routes = [
        {"path": route.path, "name": route.name, "methods": list(route.methods)}
        for route in app.routes
    ]
    return {"routes": routes}
