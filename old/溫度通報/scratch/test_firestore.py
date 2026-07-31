import urllib.request
import json
import ssl

url = "https://firestore.googleapis.com/v1/projects/hongsheng-temp-523/databases/(default)/documents/history_logs?pageSize=10"
context = ssl._create_unverified_context()

try:
    with urllib.request.urlopen(url, timeout=10, context=context) as response:
        content = response.read().decode("utf-8")
        print("【成功】讀取到 Firestore 歷史紀錄：")
        print(json.dumps(json.loads(content), indent=2, ensure_ascii=False))
except Exception as e:
    print(f"【失敗】讀取 Firestore 歷史紀錄失敗: {e}")
    if hasattr(e, "read"):
        print(e.read().decode("utf-8"))
