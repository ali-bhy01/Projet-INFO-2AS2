# tests/test_api_client.py
from src.service.collector.session_manager import SessionManager
from src.service.collector.api_client import CapitalClient
from dotenv import load_dotenv
import os, json

load_dotenv()

sm = SessionManager(
    api_key=os.getenv("CAPITAL_API_KEY"),
    identifier=os.getenv("CAPITAL_IDENTIFIER"),
    password=os.getenv("CAPITAL_PASSWORD")
)

client = CapitalClient(sm)

result = client.get_instrument("UK 100")
print(json.dumps(result, indent=2))