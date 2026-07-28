import os
import json
import urllib.request
import ssl
import time

# Use firebase_key.json to sign a JWT or get an access token
# Since we have google-auth package installed (likely, since it's a python environment for GCP work),
# let's try to import it. If not, we'll try another way.
try:
    from google.oauth2 import service_account
    from google.auth.transport.requests import Request
    
    creds = service_account.Credentials.from_service_account_file(
        "firebase_key.json",
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    creds.refresh(Request())
    token = creds.token
    print("【成功】使用 firebase_key.json 獲取 Token 成功！")
except Exception as err:
    print(f"【錯誤】使用 google-auth 失敗: {err}")
    token = None

if token:
    # Query database metadata
    url = "https://firestore.googleapis.com/v1/projects/hongsheng-temp-523/databases"
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {token}"}
    )
    context = ssl._create_unverified_context()
    try:
        with urllib.request.urlopen(req, timeout=10, context=context) as response:
            content = response.read().decode("utf-8")
            print("【成功】讀取到 Firestore 資料庫清單：")
            print(json.dumps(json.loads(content), indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"【失敗】讀取 Firestore 資料庫清單失敗: {e}")
        if hasattr(e, "read"):
            print(e.read().decode("utf-8"))
