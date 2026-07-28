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
    # Get web apps
    url = "https://firebase.googleapis.com/v1beta1/projects/hongsheng-temp-523/webApps"
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {token}"}
    )
    context = ssl._create_unverified_context()
    try:
        with urllib.request.urlopen(req, timeout=10, context=context) as response:
            content = response.read().decode("utf-8")
            print("【成功】讀取到 Web Apps：")
            web_apps = json.loads(content)
            print(json.dumps(web_apps, indent=2, ensure_ascii=False))
            
            for app in web_apps.get("apps", []):
                app_id = app.get("appId")
                config_url = f"https://firebase.googleapis.com/v1beta1/projects/hongsheng-temp-523/webApps/{app.get('name').split('/')[-1]}/config"
                req_config = urllib.request.Request(config_url, headers={"Authorization": f"Bearer {token}"})
                with urllib.request.urlopen(req_config, timeout=10, context=context) as res_conf:
                    conf_content = json.loads(res_conf.read().decode("utf-8"))
                    print(f"App {app_id} 配置：")
                    print(json.dumps(conf_content, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"【失敗】讀取 Web Apps 失敗: {e}")
        if hasattr(e, "read"):
            print(e.read().decode("utf-8"))
