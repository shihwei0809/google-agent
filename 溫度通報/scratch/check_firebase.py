import os
import sys
import json
import urllib.request
import ssl
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Working directory might be one level up, let's look for firebase_key.json
key_path = os.path.join(SCRIPT_DIR, "..", "firebase_key.json")
if not os.path.exists(key_path):
    key_path = os.path.join(SCRIPT_DIR, "firebase_key.json")

print("Key path:", os.path.abspath(key_path))

from google.oauth2 import service_account
from google.auth.transport.requests import Request as GRequest

creds = service_account.Credentials.from_service_account_file(
    key_path,
    scopes=["https://www.googleapis.com/auth/datastore"]
)
creds.refresh(GRequest())
with open(key_path) as f:
    project_id = json.load(f)["project_id"]

url = f"https://firestore.googleapis.com/v1/projects/{project_id}/databases/(default)/documents/realtime_data/status"
req = urllib.request.Request(
    url,
    headers={"Authorization": f"Bearer {creds.token}"}
)
context = ssl._create_unverified_context()
try:
    with urllib.request.urlopen(req, timeout=10, context=context) as response:
        doc = json.loads(response.read().decode("utf-8"))
        print(json.dumps(doc, indent=2, ensure_ascii=False))
except Exception as e:
    print("Error:", e)
