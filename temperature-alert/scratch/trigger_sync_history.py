import urllib.request
import json
import ssl
import sys

# The actual deployed Web App URL
url = "https://script.google.com/macros/s/AKfycbxDLlhTQEP0GoccYAJWk2x2ua6UAk2Cuka6dhrf2x1sZJdURi0/exec"
context = ssl._create_unverified_context()

payload = {
    "action": "syncHistory"
}

data = json.dumps(payload).encode("utf-8")
req = urllib.request.Request(
    url,
    data=data,
    headers={"Content-Type": "application/json"},
    method="POST"
)

print("正在向 Google Apps Script 發送自動補登請求...")

try:
    with urllib.request.urlopen(req, timeout=30, context=context) as response:
        content = response.read().decode("utf-8")
        res_json = json.loads(content)
        if res_json.get("status") == "success":
            print(f"【成功】已成功補登 {res_json.get('synced_logs')} 筆歷史紀錄至 Firebase！")
        else:
            print(f"【失敗】補登失敗，原因: {res_json.get('message')}")
except Exception as e:
    print(f"【錯誤】請求發送失敗: {e}")
