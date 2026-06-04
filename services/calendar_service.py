"""Task 21: Google Calendar integration with OAuth2 and Fernet token encryption."""
import json
import logging
import sqlite3
from datetime import datetime, timezone
from typing import Optional

from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)

try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import Flow
    from googleapiclient.discovery import build
    _GOOGLE_AVAILABLE = True
except ImportError:
    _GOOGLE_AVAILABLE = False

SCOPES = ["https://www.googleapis.com/auth/calendar"]


class CalendarService:
    def __init__(self, settings):
        self.settings = settings
        self._fernet: Optional[Fernet] = None
        if settings.fernet_key:
            self._fernet = Fernet(settings.fernet_key.encode())
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.settings.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS google_tokens (
                    user_id INTEGER PRIMARY KEY,
                    token_data TEXT
                )
            """)
            conn.commit()

    def _encrypt(self, data: str) -> str:
        if self._fernet:
            return self._fernet.encrypt(data.encode()).decode()
        return data

    def _decrypt(self, data: str) -> str:
        if self._fernet:
            return self._fernet.decrypt(data.encode()).decode()
        return data

    def save_token(self, user_id: int, creds: "Credentials"):
        token_json = creds.to_json()
        encrypted = self._encrypt(token_json)
        with sqlite3.connect(self.settings.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO google_tokens (user_id, token_data) VALUES (?, ?)",
                (user_id, encrypted),
            )
            conn.commit()

    def load_token(self, user_id: int) -> Optional["Credentials"]:
        if not _GOOGLE_AVAILABLE:
            return None
        with sqlite3.connect(self.settings.db_path) as conn:
            row = conn.execute(
                "SELECT token_data FROM google_tokens WHERE user_id = ?", (user_id,)
            ).fetchone()
        if not row:
            return None
        token_json = self._decrypt(row[0])
        return Credentials.from_authorized_user_info(json.loads(token_json), SCOPES)

    def get_auth_url(self, user_id: int) -> Optional[str]:
        if not _GOOGLE_AVAILABLE:
            return None
        try:
            flow = Flow.from_client_secrets_file(
                self.settings.google_credentials_file,
                scopes=SCOPES,
                redirect_uri="urn:ietf:wg:oauth:2.0:oob",
            )
            auth_url, _ = flow.authorization_url(
                access_type="offline",
                include_granted_scopes="true",
                state=str(user_id),
            )
            return auth_url
        except Exception as e:
            logger.error(f"Calendar get_auth_url error: {e}")
            return None

    def exchange_code(self, user_id: int, code: str) -> bool:
        if not _GOOGLE_AVAILABLE:
            return False
        try:
            flow = Flow.from_client_secrets_file(
                self.settings.google_credentials_file,
                scopes=SCOPES,
                redirect_uri="urn:ietf:wg:oauth:2.0:oob",
            )
            flow.fetch_token(code=code)
            self.save_token(user_id, flow.credentials)
            return True
        except Exception as e:
            logger.error(f"Calendar token exchange error: {e}")
            return False

    def create_event(self, user_id: int, summary: str, start_dt: datetime, end_dt: datetime) -> Optional[str]:
        if not _GOOGLE_AVAILABLE:
            return None
        creds = self.load_token(user_id)
        if not creds:
            return None
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            self.save_token(user_id, creds)

        service = build("calendar", "v3", credentials=creds)
        event_body = {
            "summary": summary,
            "start": {"dateTime": start_dt.isoformat(), "timeZone": "Asia/Almaty"},
            "end": {"dateTime": end_dt.isoformat(), "timeZone": "Asia/Almaty"},
        }
        event = service.events().insert(calendarId="primary", body=event_body).execute()
        return event.get("htmlLink")
