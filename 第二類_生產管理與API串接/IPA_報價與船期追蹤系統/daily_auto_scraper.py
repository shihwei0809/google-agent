# -*- coding: utf-8 -*-
"""
IPA (異丙醇) 每日定時背景爬蟲與價差分析腳本 (daily_auto_scraper.py)
用途：供 Windows 工作排程器每天早上 08:00 自動執行，抓取最新匯率與行情，
      自動換算為 【美金/公噸 (USD/MT)】 與 【台幣/公斤 (TWD/KG)】，
      寫入 SQLite 歷史資料庫並輸出最新 CSV 報表。
"""

import csv
import os
import sys
from datetime import date, datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PWA_DIR = os.path.join(BASE_DIR, "2_PWA_App版")
sys.path.insert(0, PWA_DIR)

from run_server import (
    build_dashboard_payload,
    convert_price,
    fetch_exchange_rates,
    get_db,
    init_db,
)


def run_daily_job():
    init_db()
    fx = fetch_exchange_rates()
    today_str = date.today().isoformat()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO fx_rates VALUES (?, ?, ?, ?, ?)",
        (today_str, fx["USD_TWD"], fx["USD_CNY"], fx["CNY_TWD"], fx["updated_at"]),
    )

    cur.execute("SELECT DISTINCT chem_key FROM chemical_quotes")
    keys = [r["chem_key"] for r in cur.fetchall()]
    for k in keys:
        cur.execute(
            "SELECT * FROM chemical_quotes WHERE chem_key=? ORDER BY record_date DESC LIMIT 1",
            (k,),
        )
        last_row = cur.fetchone()
        if last_row:
            conv = convert_price(last_row["raw_price"], last_row["raw_unit"], fx)
            cur.execute(
                """INSERT OR REPLACE INTO chemical_quotes
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    today_str,
                    last_row["chem_key"],
                    last_row["chem_name"],
                    last_row["category"],
                    last_row["raw_price"],
                    last_row["raw_unit"],
                    conv["usd_mt"],
                    conv["twd_kg"],
                    fx["USD_TWD"],
                    last_row["note"],
                    now_str,
                ),
            )
    conn.commit()
    conn.close()

    payload = build_dashboard_payload()
    report_path = os.path.join(BASE_DIR, f"IPA每日報價與船期日報_{today_str}.csv")
    with open(report_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["【IPA 異丙醇與上游原料每日雙單位報價日報】", f"產出時間: {now_str}"])
        writer.writerow(["即時匯率", f"1 USD = {fx['USD_TWD']} TWD", f"1 RMB = {fx['CNY_TWD']} TWD"])
        writer.writerow([])
        writer.writerow(["日期", "化學品名稱", "類別", "原始報價", "原始單位", "台幣/公斤 (TWD/KG)", "美金/公噸 (USD/MT)", "日漲跌(USD)", "7日漲跌幅(%)"])
        for c in payload.get("cards", []):
            writer.writerow([
                c["record_date"], c["chem_name"], c["category"],
                c["raw_price"], c["raw_unit"], c["twd_kg"], c["usd_mt"],
                c["diff_usd_1d"], f"{c['pct_7d']}%"
            ])
        writer.writerow([])
        sp = payload.get("spread_analysis", {})
        writer.writerow(["【上游丙酮 -> IPA 價差預警】", f"美金價差: +${sp.get('spread_usd_mt', 0)} USD/MT", f"台幣價差: +NT${sp.get('spread_twd_kg', 0)} TWD/KG", sp.get("advice", "")])
        writer.writerow([])
        writer.writerow(["【出貨單櫃號與船名自動追蹤清單】"])
        writer.writerow(["採購單號", "櫃號", "自動識別船公司/箱主", "櫃型", "船名", "起運港", "目的港", "台幣成本(TWD/KG)", "美金成本(USD/MT)", "預計到港(ETA)", "倒數天數", "狀態"])
        for s in payload.get("shipments", []):
            writer.writerow([
                s["order_no"], s["container_no"], s["carrier"], s["box_type"],
                s["vessel_name"], s["pol"], s["pod"], s["buy_price_twd_kg"],
                s["buy_price_usd_mt"], s["eta"], f"{s['days_left']}天", s["status"]
            ])

    print("=" * 72)
    print(f"✅ [{now_str}] IPA 每日報價與船期自動爬蟲執行完成！")
    print(f"💱 今日匯率: 1 USD = {fx['USD_TWD']} TWD | 1 RMB = {fx['CNY_TWD']} TWD")
    for c in payload.get("cards", []):
        print(f"   - {c['chem_name']}: NT$ {c['twd_kg']:.2f} /KG  ($ {c['usd_mt']:.2f} USD/MT)")
    print(f"📄 日報已輸出至: {report_path}")
    print("=" * 72)


if __name__ == "__main__":
    run_daily_job()
