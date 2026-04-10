# tests/test_session.py
from src.service.collector.session_manager import SessionManager
from dotenv import load_dotenv
import os

load_dotenv()

sm = SessionManager(
    api_key=os.getenv("CAPITAL_API_KEY"),
    identifier=os.getenv("CAPITAL_IDENTIFIER"),
    password=os.getenv("CAPITAL_PASSWORD")
)

print("CST:", sm.cst)
print("Token:", sm.security_token)