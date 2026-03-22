"""
Google Calendar API client for InFinea.
Handles OAuth flow, token management, and calendar operations.
"""
import os
import httpx
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleRequest
from googleapiclient.discovery import build
import logging

from .encryption import encrypt_token, decrypt_token

logger = logging.getLogger(__name__)

# Google OAuth Configuration
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
GOOGLE_SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
GOOGLE_TOKEN_URI = 'https://oauth2.googleapis.com/token'
GOOGLE_AUTH_URI = 'https://accounts.google.com/o/oauth2/auth'


def get_redirect_uri(request_base_url: str) -> str:
    """Generate OAuth redirect URI based on request."""
    base = str(request_base_url).rstrip('/')
    return f"{base}/api/integrations/google/callback"


def generate_auth_url(redirect_uri: str, state: str) -> str:
    """Generate Google OAuth authorization URL."""
    params = {
        'client_id': GOOGLE_CLIENT_ID,
        'redirect_uri': redirect_uri,
        'scope': ' '.join(GOOGLE_SCOPES),
        'response_type': 'code',
        'access_type': 'offline',
        'prompt': 'consent',
        'state': state
    }
    query = '&'.join(f"{k}={v}" for k, v in params.items())
    return f"{GOOGLE_AUTH_URI}?{query}"


async def exchange_code_for_tokens(code: str, redirect_uri: str) -> Dict[str, Any]:
    """Exchange authorization code for access and refresh tokens."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            GOOGLE_TOKEN_URI,
            data={
                'code': code,
                'client_id': GOOGLE_CLIENT_ID,
                'client_secret': GOOGLE_CLIENT_SECRET,
                'redirect_uri': redirect_uri,
                'grant_type': 'authorization_code'
            }
        )
        
        if response.status_code != 200:
            logger.error(f"Token exchange failed: {response.text}")
            raise Exception(f"Failed to exchange code: {response.text}")
        
        return response.json()


async def refresh_access_token(refresh_token: str) -> Dict[str, Any]:
    """Refresh an expired access token."""
    decrypted_refresh = decrypt_token(refresh_token)
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            GOOGLE_TOKEN_URI,
            data={
                'refresh_token': decrypted_refresh,
                'client_id': GOOGLE_CLIENT_ID,
                'client_secret': GOOGLE_CLIENT_SECRET,
                'grant_type': 'refresh_token'
            }
        )
        
        if response.status_code != 200:
            logger.error(f"Token refresh failed: {response.text}")
            raise Exception("Failed to refresh token")
        
        return response.json()


def get_calendar_service(access_token: str):
    """Create Google Calendar service instance."""
    decrypted_token = decrypt_token(access_token)
    
    creds = Credentials(
        token=decrypted_token,
        token_uri=GOOGLE_TOKEN_URI,
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET
    )
    
    return build('calendar', 'v3', credentials=creds)


async def get_calendar_events(
    access_token: str,
    time_min: datetime,
    time_max: datetime,
    calendar_id: str = 'primary'
) -> List[Dict[str, Any]]:
    """Fetch calendar events within a time range."""
    try:
        service = get_calendar_service(access_token)
        
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min.isoformat(),
            timeMax=time_max.isoformat(),
            singleEvents=True,
            orderBy='startTime',
            maxResults=100
        ).execute()
        
        return events_result.get('items', [])
    except Exception as e:
        logger.error(f"Failed to fetch calendar events: {e}")
        raise


async def get_user_calendars(access_token: str) -> List[Dict[str, Any]]:
    """Get list of user's calendars."""
    try:
        service = get_calendar_service(access_token)
        
        calendars_result = service.calendarList().list().execute()
        
        return calendars_result.get('items', [])
    except Exception as e:
        logger.error(f"Failed to fetch calendars: {e}")
        raise


def encrypt_tokens(tokens: Dict[str, Any]) -> Dict[str, Any]:
    """Encrypt sensitive token data for storage."""
    encrypted = {
        'access_token': encrypt_token(tokens.get('access_token', '')),
        'token_type': tokens.get('token_type', 'Bearer'),
        'expires_in': tokens.get('expires_in', 3600),
        'scope': tokens.get('scope', ''),
    }
    
    if 'refresh_token' in tokens:
        encrypted['refresh_token'] = encrypt_token(tokens['refresh_token'])
    
    return encrypted
