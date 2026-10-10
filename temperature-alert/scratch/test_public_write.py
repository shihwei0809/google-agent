import urllib.request
import json
import ssl

url = "https://firestore.googleapis.com/v1/projects/hongsheng-temp-523/databases/(default)/documents/realtime_data/status"
context = ssl._create_unverified_context()

payload = {
    "fields": {
        "current_temp": {"doubleValue": 25.5},
        "threshold": {"doubleValue": 28.0},
        "obs_time": {"stringValue": "2026-06-11 20:00:00"},
        "alert_state": {"stringValue": "正常 (未超標)"},
        "status_text": {"stringValue": "測試寫入"},
        "last_heartbeat": {"integerValue": "1781178208813"},
        "start_hour": {"integerValue": "8"},
        "end_hour": {"integerValue": "24"},
        "frequency": {"integerValue": "60"},
        "password": {"stringValue": "admin888"},
        "web_app_url": {"stringValue": "https://script.google.com/macros/s/AKfycbytest/exec"}
    }
}

data = json.dumps(payload).encode("utf-8")
req = urllib.request.Request(
    url,
    data=data,
    headers={"Content-Type": "application/json"},
    method="PATCH" # PATCH creates or updates the document
)

try:
    with urllib.request.urlopen(req, timeout=10, context=context) as response:
        content = response.read().decode("utf-8")
        print("【成功】公用 REST API 寫入成功！")
        print(json.dumps(json.loads(content), indent=2, ensure_ascii=False))
except Exception as e:
    print(f"【失敗】公用 REST API 寫入失敗: {e}")
    if hasattr(e, "read"):
        print(e.read().decode("utf-8"))
