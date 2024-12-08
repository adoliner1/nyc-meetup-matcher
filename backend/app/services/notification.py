from typing import List
from twilio.rest import Client
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from ..config import settings

class NotificationService:
    def __init__(self):
        self.twilio_client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        self.sendgrid_client = SendGridAPIClient(settings.SENDGRID_API_KEY)
    
    async def send_group_proposal(self, users: List[dict], proposed_location: str, proposed_time: str):
        """Send proposal to potential group members"""
        message = f"You've been matched with a potential meetup group! Proposed meetup at {proposed_location} on {proposed_time}. Reply YES to confirm."
        
        for user in users:
            await self._send_sms(user["phone_number"], message)
            await self._send_email(
                user["email"],
                "New Meetup Group Proposal",
                message
            )
    
    async def send_group_confirmation(self, users: List[dict], location: str, time: str, group_chat_id: str):
        """Send confirmation and group chat details to confirmed members"""
        message = f"Your meetup is confirmed! Meeting at {location} on {time}. Join the group chat: {group_chat_id}"
        
        for user in users:
            await self._send_sms(user["phone_number"], message)
            await self._send_email(
                user["email"],
                "Meetup Confirmed!",
                message
            )
    
    async def create_group_chat(self, users: List[dict]) -> str:
        """Create a group chat using Twilio and return the chat ID"""
        # Create a group chat using Twilio's Conversations API
        conversation = self.twilio_client.conversations.conversations.create(
            friendly_name="NYC Meetup Group"
        )
        
        # Add participants to the conversation
        for user in users:
            self.twilio_client.conversations.conversations(conversation.sid).participants.create(
                identity=user["phone_number"]
            )
        
        return conversation.sid
    
    async def _send_sms(self, phone_number: str, message: str):
        """Send SMS using Twilio"""
        self.twilio_client.messages.create(
            body=message,
            to=phone_number,
            from_=settings.TWILIO_PHONE_NUMBER
        )
    
    async def _send_email(self, email: str, subject: str, content: str):
        """Send email using SendGrid"""
        message = Mail(
            from_email=settings.FROM_EMAIL,
            to_emails=email,
            subject=subject,
            plain_text_content=content
        )
        self.sendgrid_client.send(message)