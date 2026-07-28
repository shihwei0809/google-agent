import os
import json
import urllib.request
import ssl

try:
    from google.oauth2 import service_account
    from google.auth.transport.requests import Request
    
    creds = service_account.Credentials.from_service_account_file(
        "firebase_key.json",
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    creds.refresh(Request())
    token = creds.token
except Exception as err:
    print(f"【錯誤】使用 google-auth 失敗: {err}")
    token = None

if token:
    # Get releases
    url = "https://firebaserules.googleapis.com/v1/projects/hongsheng-temp-523/releases"
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {token}"}
    )
    context = ssl._create_unverified_context()
    try:
        with urllib.request.urlopen(req, timeout=10, context=context) as response:
            content = response.read().decode("utf-8")
            print("【成功】讀取到 Firebase Releases：")
            releases = json.loads(content)
            print(json.dumps(releases, indent=2, ensure_ascii=False))
            
            # For each release, get ruleset
            for release in releases.get("releases", []):
                ruleset_name = release.get("rulesetName")
                ruleset_url = f"https://firebaserules.googleapis.com/v1/{ruleset_name}"
                req_ruleset = urllib.request.Request(ruleset_url, headers={"Authorization": f"Bearer {token}"})
                with urllib.request.urlopen(req_ruleset, timeout=10, context=context) as res_set:
                    ruleset_content = json.loads(res_set.read().decode("utf-8"))
                    print(f"規則集 {ruleset_name} 內容：")
                    print(json.dumps(ruleset_content, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"【失敗】讀取 Rules 失敗: {e}")
        if hasattr(e, "read"):
            print(e.read().decode("utf-8"))
