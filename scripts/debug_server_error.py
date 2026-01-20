
from fastapi.testclient import TestClient
from api.main import app
import logging
import sys

# Configure logging to show everything
logging.basicConfig(level=logging.DEBUG)

client = TestClient(app)

print("--- Requesting /api/sources/congress ---")
try:
    response = client.get("/api/sources/congress")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print("Caught Exception during request:")
    import traceback
    traceback.print_exc()

print("\n--- Requesting /api/sources/news ---")
try:
    response = client.get("/api/sources/news")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print("Caught Exception during request:")
    import traceback
    traceback.print_exc()
