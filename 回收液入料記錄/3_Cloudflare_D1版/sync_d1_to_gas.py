import urllib.request
import json
import sys

D1_QUERY_URL = "https://recycle-portal.pages.dev/api/records?action=query"
GAS_URL = "https://script.google.com/macros/s/AKfycbxRnwQm3KmR3eZSGFK4-cm5chGdj5jc8DJiTTvU-OzIkAX9qtFdvPsn_UgTEcuhaRkU/exec"
ORIGIN = "https://recycle-portal.pages.dev"

def sync():
    print("🚀 正在從 Cloudflare D1 讀取最新完整入料數據...")
    req = urllib.request.Request(D1_QUERY_URL, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        print(f"❌ 讀取 D1 失敗: {e}")
        return

    records = data.get("records", [])
    print(f"✅ 成功從 D1 取得 {len(records)} 筆紀錄！")

    # 格式化並補齊絕對網址
    formatted = []
    for r in records:
        t_url = r.get("tBeforeUrl") or ""
        v_url = r.get("vPhotoUrl") or ""
        a_url = r.get("tAfterUrl") or ""

        if t_url and t_url.startswith("/"):
            t_url = ORIGIN + t_url
        if v_url and v_url.startswith("/"):
            v_url = ORIGIN + v_url
        if a_url and a_url.startswith("/"):
            a_url = ORIGIN + a_url

        formatted.append({
            "id": r.get("id"),
            "date": r.get("date"),
            "license_plate": r.get("license_plate"),
            "status": r.get("status", "pending"),
            "before_time": r.get("before_time", ""),
            "after_time": r.get("after_time", ""),
            "duration": r.get("duration"),
            "tBeforeUrl": t_url,
            "vPhotoUrl": v_url,
            "tAfterUrl": a_url
        })

    print("📤 正在將資料全量推送回寫至 Google 試算表 (GAS sync_from_d1)...")
    payload = json.dumps({
        "action": "sync_from_d1",
        "records": formatted
    }).encode("utf-8")

    gas_req = urllib.request.Request(
        GAS_URL,
        data=payload,
        headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(gas_req, timeout=60) as gas_resp:
            result_str = gas_resp.read().decode()
            print("📥 Google 試算表回傳結果:")
            print(result_str)
            try:
                res_obj = json.loads(result_str)
                if res_obj.get("success"):
                    print(f"🎉 回寫成功！新增: {res_obj.get('inserted', 0)} 筆，更新: {res_obj.get('updated', 0)} 筆")
            except Exception:
                pass
    except Exception as e:
        print(f"❌ 呼叫 Google 試算表失敗: {e}")

if __name__ == "__main__":
    sync()
