#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
部署 QC 檢驗超時自動檢查 Worker 至 Cloudflare
包含：
1. 上傳 worker.js 至 Cloudflare Workers
2. 設定 Cron Trigger 定時排程 (每 5 分鐘一次)
3. 啟用 Workers.dev 子網域方便手動或外部測試
"""

import os
import ssl
import json
import urllib.request
import urllib.error

def load_env(env_path):
    env = {}
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    k, v = line.strip().split('=', 1)
                    env[k] = v
    return env

def find_env_path():
    candidates = [
        r"C:\GOOGLE ANGET\.env",
        os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '.env')),
        os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env')),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    root_env_path = find_env_path()
    
    env = load_env(root_env_path) if root_env_path else {}
    token = env.get('CLOUDFLARE_API_TOKEN')
    account_id = env.get('CLOUDFLARE_ACCOUNT_ID', '7bf430fb55af9ca6c91aba8997fc841d')
    script_name = 'qc-overdue-cron'
    
    if not token:
        print("[ERROR] 找不到 CLOUDFLARE_API_TOKEN，請檢查根目錄 .env 檔案")
        return

    worker_file = os.path.join(base_dir, 'worker.js')
    with open(worker_file, 'r', encoding='utf-8') as f:
        worker_code = f.read()

    ctx = ssl._create_unverified_context()

    print(f"[*] 正在部署 Worker: {script_name}...")
    req = urllib.request.Request(
        f'https://api.cloudflare.com/client/v4/accounts/{account_id}/workers/scripts/{script_name}',
        data=worker_code.encode('utf-8'),
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/javascript'
        },
        method='PUT'
    )
    try:
        with urllib.request.urlopen(req, context=ctx) as r:
            res = json.loads(r.read().decode('utf-8'))
            if res.get('success'):
                print("  [✓] Worker 程式碼上傳成功！")
            else:
                print("  [✗] Worker 上傳失敗:", res)
                return
    except urllib.error.HTTPError as e:
        print(f"  [✗] 上傳失敗 HTTP {e.code}: {e.read().decode('utf-8')}")
        return

    print("[*] 正在設定 Cron Trigger 定時排程 (每 5 分鐘一次: */5 * * * *)...")
    schedule_data = json.dumps([{'cron': '*/5 * * * *'}]).encode('utf-8')
    req2 = urllib.request.Request(
        f'https://api.cloudflare.com/client/v4/accounts/{account_id}/workers/scripts/{script_name}/schedules',
        data=schedule_data,
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        },
        method='PUT'
    )
    try:
        with urllib.request.urlopen(req2, context=ctx) as r2:
            res2 = json.loads(r2.read().decode('utf-8'))
            if res2.get('success'):
                print("  [✓] Cron Trigger 定時排程設定成功！")
    except urllib.error.HTTPError as e:
        print(f"  [✗] 排程設定失敗 HTTP {e.code}: {e.read().decode('utf-8')}")

    print("[*] 正在確保 workers.dev 子網域已啟用...")
    subdomain_data = json.dumps({'enabled': True}).encode('utf-8')
    req3 = urllib.request.Request(
        f'https://api.cloudflare.com/client/v4/accounts/{account_id}/workers/scripts/{script_name}/subdomain',
        data=subdomain_data,
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        },
        method='POST'
    )
    try:
        with urllib.request.urlopen(req3, context=ctx) as r3:
            print("  [✓] workers.dev 路由已啟用！")
    except Exception as e:
        pass

    print("\n==========================================")
    print("部署成功！")
    print(f"Worker 網址: https://{script_name}.shihwei0809.workers.dev")
    print("觸發頻率: 每 5 分鐘自動執行一次 (Cron: */5 * * * *)")
    print("目標 API: https://qc-samples.pages.dev/api?action=checkOverdue")
    print("==========================================")

if __name__ == '__main__':
    main()
