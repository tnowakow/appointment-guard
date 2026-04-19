"""
ZenticPro Platform - Twilio Service Layer
Reusable Twilio SMS/Voice integration for all industry modules.
"""

import os
import logging
from typing import Optional, Dict, Any
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class TwilioConfig(BaseModel):
    """Twilio configuration model."""
    account_sid: str
    auth_token: str
    from_number: str
    
    @classmethod
    def from_env(cls) -> "TwilioConfig":
        """Load config from environment variables."""
        return cls(
            account_sid=os.getenv("TWILIO_ACCOUNT_SID"),
            auth_token=os.getenv("TWILIO_AUTH_TOKEN"),
            from_number=os.getenv("TWILIO_PHONE_NUMBER")
        )


class TwilioService:
    """
    Unified Twilio service for SMS and Voice operations.
    
    Usage:
        service = TwilioService()
        success = await service.send_sms(to="+1234567890", body="Hello!")
    """
    
    def __init__(self, config: Optional[TwilioConfig] = None):
        """Initialize Twilio service with optional config (defaults to env vars)."""
        self.config = config or TwilioConfig.from_env()
        self._client = None
        from .utils import RateLimiter, retry_on_failure
        self.rate_limiter = RateLimiter(max_tokens=60, refill_rate=1.0)
        self.retry = retry_on_failure
    
    @property
    def client(self):
        """Lazy-load Twilio client."""
        if self._client is None:
            from twilio.rest import Client as TwilioClient
            self._client = TwilioClient(
                self.config.account_sid,
                self.config.auth_token
            )
        return self._client
    
    async def send_sms(
        self,
        to: str,
        body: str,
        media_url: Optional[str] = None
    ) -> bool:
        """
        Send an SMS message.
        
        Args:
            to: Recipient phone number (E.164 format)
            body: Message text
            media_url: Optional image/media URL
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not all([self.config.account_sid, self.config.auth_token, self.config.from_number]):
            logger.warning("Twilio credentials not configured. Skipping SMS.")
            return False
        
        # Apply rate limiting
        await self.rate_limiter.acquire(to)
        
        # Add retry logic
        @self.retry(max_attempts=3, base_delay=1.0, max_delay=10.0)
        async def _send_sms_internal():
            try:
                import asyncio
                loop = asyncio.get_event_loop()
                
                def send_sms_sync():
                    message = self.client.messages.create(
                        body=body,
                        from_=self.config.from_number,
                        to=to,
                        media_url=[media_url] if media_url else None
                    )
                    return message.sid
                
                # Run in executor to avoid blocking
                message_sid = await loop.run_in_executor(None, send_sms_sync)
                
                logger.info(f"SMS sent to {to}: {body[:50]}... (SID: {message_sid})")
                return True
                
            except Exception as e:
                logger.error(f"Error sending SMS to {to}: {e}")
                raise  # Re-raise to trigger retry
        
        try:
            return await _send_sms_internal()
        except Exception as e:
            logger.error(f"Failed to send SMS to {to} after retries: {e}")
            return False
    
    async def send_voice_call(
        self,
        to: str,
        url: str,  # TwiML URL or media URL
        fallback_url: Optional[str] = None
    ) -> bool:
        """
        Initiate a voice call.
        
        Args:
            to: Recipient phone number (E.164 format)
            url: TwiML URL or media URL for the call
            fallback_url: Fallback URL if primary fails
            
        Returns:
            True if call initiated successfully, False otherwise
        """
        if not all([self.config.account_sid, self.config.auth_token]):
            logger.warning("Twilio credentials not configured. Skipping voice call.")
            return False
        
        # Add retry logic for voice calls as well
        @self.retry(max_attempts=3, base_delay=1.0, max_delay=10.0)
        async def _send_voice_call_internal():
            try:
                import asyncio
                loop = asyncio.get_event_loop()
                
                def make_call_sync():
                    call = self.client.calls.create(
                        to=to,
                        from_=self.config.from_number,
                        url=url,
                        fallback_url=fallback_url
                    )
                    return call.sid
                
                # Run in executor to avoid blocking
                call_sid = await loop.run_in_executor(None, make_call_sync)
                
                logger.info(f"Voice call initiated to {to} (SID: {call_sid})")
                return True
                
            except Exception as e:
                logger.error(f"Error initiating voice call to {to}: {e}")
                raise  # Re-raise to trigger retry
        
        try:
            return await _send_voice_call_internal()
        except Exception as e:
            logger.error(f"Failed to initiate voice call to {to} after retries: {e}")
            return False
    
    def verify_phone_number(self, to: str) -> bool:
        """
        Verify a phone number is valid (E.164 format check).
        
        Args:
            to: Phone number to validate
            
        Returns:
            True if valid E.164 format, False otherwise
        """
        import re
        # Basic E.164 validation: + followed by 1-15 digits
        pattern = r'^\+?[1-9]\d{1,14}$'
        return bool(re.match(pattern, to.replace(' ', '').replace('-', '')))