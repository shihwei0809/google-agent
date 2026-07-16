import os
import sys
import io
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Reconfigure stdout for Windows console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def list_labels():
    if not os.path.exists('token.json'):
        print("token.json not found")
        return
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    service = build('gmail', 'v1', credentials=creds)
    
    results = service.users().labels().list(userId='me').execute()
    labels = results.get('labels', [])
    
    print("\n=== Gmail 標籤清單 ===")
    for label in sorted(labels, key=lambda x: x['name']):
        print(f"- {label['name']} (ID: {label['id']}, 類型: {label['type']})")

if __name__ == '__main__':
    list_labels()

