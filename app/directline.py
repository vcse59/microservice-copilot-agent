import requests
import logging
from fastapi import HTTPException
from datetime import datetime, timedelta
import time

logger = logging.getLogger("directline_api")


class DirectLineAPI:
    def __init__(self, secret: str, bot_endpoint: str):
        self.secret = secret
        self.bot_endpoint = bot_endpoint
        self.token_endpoint = "https://directline.botframework.com/v3/directline/tokens/generate"
        self.token = None
        self.token_expiry = None
        self.conversation_id = None
        self.recent_activity = 0
        self.generate_token()

    def generate_token(self):

        """Generate a Direct Line token using the secret."""
        headers = {"Authorization": f"Bearer {self.secret}"}
        response = requests.post(self.token_endpoint, headers=headers)

        if response.status_code == 200:
            token_data = response.json()
            self.token = token_data["token"]
            self.token_expiry = datetime.utcnow() + timedelta(seconds=3600)  # Tokens expire after 1 hour
            logger.info("Successfully generated Direct Line token.")
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to generate token: {response.text}",
            )

    def ensure_token_valid(self):
        """Ensure the token is valid, refreshing it if necessary."""
        if not self.token or datetime.utcnow() >= self.token_expiry:
            logger.info("Token expired or missing. Generating a new token...")
            self.generate_token()

    def start_conversation(self):
        """Start a new conversation with the bot."""
        self.ensure_token_valid()
        self.recent_activity = 0
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.post(self.bot_endpoint, headers=headers)

        if response.status_code == 201:
            self.conversation_id = response.json()["conversationId"]
            logger.info(f"Started new conversation: {self.conversation_id}")
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail="Failed to start conversation with the bot.",
            )

    def send_activity(self, message: str, user_id: str = "user1"):
        """Send a message activity to the bot."""
        self.ensure_token_valid()

        if not self.conversation_id:
            self.start_conversation()

        url = f"{self.bot_endpoint}/{self.conversation_id}/activities"
        headers = {"Authorization": f"Bearer {self.token}"}
        payload = {
            "type": "message",
            "from": {"id": user_id},
            "text": message,
        }
        response = requests.post(url, headers=headers, json=payload)

        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to send activity: {response.text}",
            )

    def get_activity_response(self):
        """Retrieve bot's response from the conversation."""
        self.ensure_token_valid()

        if not self.conversation_id:
            raise HTTPException(
                status_code=400, detail="No active conversation to retrieve activities."
            )
        url = f"{self.bot_endpoint}/{self.conversation_id}/activities"
        headers = {"Authorization": f"Bearer {self.token}"}

        while True :
            time.sleep(1)
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                activities = response.json().get("activities", [])
                for activity in activities:
                    id = activity["id"]
                    id = int(id.split('|')[1])
                    if activity["type"] == "message"  and activity["from"]["id"] != "user1" and id > self.recent_activity:
                        self.recent_activity = id
                        citation = None
                        # Look for the citation in the entities field
                        if "entities" in activity:
                            for entity in activity["entities"]:
                                if entity.get("type") == "https://schema.org/Message" and "citation" in entity:
                                    citation = entity["citation"][0] if isinstance(entity["citation"], list) else entity["citation"]
                                    break
                                if citation:
                                    break
                        return activity["text"], self.conversation_id, citation
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Failed to retrieve activities from the bot.",
                )
