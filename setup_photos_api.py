import os
import sys
import json
import requests
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# Scopes required to read Google Photos
SCOPES = ['https://www.googleapis.com/auth/photoslibrary.readonly']

CREDENTIALS_FILE = 'C:/GOOGLE ANGET/credentials.json'
TOKEN_FILE = 'C:/GOOGLE ANGET/token.json'
OUTPUT_DIR = 'C:/GOOGLE ANGET/trip_photos'

def authenticate():
    """Authenticates the user and returns the credentials."""
    creds = None
    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        except Exception as e:
            print(f"[INFO] Read token.json failed, will re-auth: {e}")
            
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("[INFO] Refreshing Access Token...")
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"[INFO] Refresh failed, starting full auth: {e}")
                creds = None
                
        if not creds:
            if not os.path.exists(CREDENTIALS_FILE):
                print(f"[ERROR] Cannot find credentials file: {CREDENTIALS_FILE}")
                print("Please download credentials.json from Google Cloud Console and save it to C:/GOOGLE ANGET/")
                sys.exit(1)
            
            print("[INFO] Starting local browser for Google Account authentication...")
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0, prompt='consent')
            
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
            
    return creds

def download_photos(creds, start_date, end_date):
    """Downloads photos within the date range from Google Photos."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    headers = {
        'Authorization': f'Bearer {creds.token}',
        'Content-Type': 'application/json'
    }
    
    # Parse dates
    start_y, start_m, start_d = map(int, start_date.split('-'))
    end_y, end_m, end_d = map(int, end_date.split('-'))
    
    payload = {
        "filters": {
            "dateFilter": {
                "ranges": [
                    {
                        "startDate": {
                            "year": start_y,
                            "month": start_m,
                            "day": start_d
                        },
                        "endDate": {
                            "year": end_y,
                            "month": end_m,
                            "day": end_d
                        }
                    }
                ]
            }
        },
        "pageSize": 100
    }
    
    print(f"[SEARCH] Searching Google Photos from {start_date} to {end_date}...")
    
    url = "https://photoslibrary.googleapis.com/v1/mediaItems:search"
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code != 200:
        print(f"[ERROR] Search failed. Status: {response.status_code}")
        print(response.text)
        return
        
    result = response.json()
    items = result.get('mediaItems', [])
    
    if not items:
        print("[INFO] No photos or videos found in the specified range.")
        return
        
    print(f"[OK] Found {len(items)} items! Starting download...")
    
    success_count = 0
    for idx, item in enumerate(items):
        filename = item.get('filename')
        base_url = item.get('baseUrl')
        mime_type = item.get('mimeType', '')
        
        # We only download images
        if not mime_type.startswith('image/'):
            print(f"[SKIP] Skipping non-image item [{idx+1}/{len(items)}]: {filename}")
            continue
            
        # Download at original size
        download_url = f"{base_url}=d"
        save_path = os.path.join(OUTPUT_DIR, filename)
        
        print(f"[DOWNLOAD] Downloading [{idx+1}/{len(items)}]: {filename}...")
        try:
            img_data = requests.get(download_url).content
            with open(save_path, 'wb') as f:
                f.write(img_data)
            success_count += 1
        except Exception as e:
            print(f"[ERROR] Failed downloading {filename}: {e}")
            
    print(f"\n[SUCCESS] Completed download! Successfully downloaded {success_count} photos to {OUTPUT_DIR}")

if __name__ == "__main__":
    creds = authenticate()
    # Download photos for the date range
    download_photos(creds, '2025-08-21', '2025-08-24')
