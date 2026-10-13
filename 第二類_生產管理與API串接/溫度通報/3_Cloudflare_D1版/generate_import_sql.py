import csv
import os

def escape_sql(text):
    if text is None:
        return ""
    return str(text).replace("'", "''")

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    heartbeat_csv = os.path.join(base_dir, "本地歷史紀錄_心跳明細.csv")
    alert_csv = os.path.join(base_dir, "本地歷史紀錄_歷史通報.csv")
    sql_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "import_history.sql")

    with open(sql_file, 'w', encoding='utf-8') as f:
        f.write("-- 自動生成的歷史資料匯入 SQL\n\n")

        # 1. 處理 24 小時心跳明細 (temperature_logs)
        if os.path.exists(heartbeat_csv):
            f.write("BEGIN TRANSACTION;\n")
            with open(heartbeat_csv, 'r', encoding='utf-8-sig') as csvfile:
                reader = csv.reader(csvfile)
                next(reader, None)  # 略過標題列
                batch_size = 500
                count = 0
                for row in reader:
                    if len(row) >= 6:
                        timestamp = escape_sql(row[0])
                        temp = row[2]
                        obs_time = escape_sql(row[3])
                        status = escape_sql(row[5])
                        
                        try:
                            float(temp) # 確保是數字
                            f.write(f"INSERT INTO temperature_logs (timestamp, temperature, obs_time, status) VALUES ('{timestamp}', {temp}, '{obs_time}', '{status}');\n")
                            count += 1
                            if count % batch_size == 0:
                                f.write("COMMIT;\nBEGIN TRANSACTION;\n")
                        except ValueError:
                            pass
            f.write("COMMIT;\n\n")

        # 2. 處理警報歷史紀錄 (alert_logs)
        if os.path.exists(alert_csv):
            f.write("BEGIN TRANSACTION;\n")
            with open(alert_csv, 'r', encoding='utf-8-sig') as csvfile:
                reader = csv.reader(csvfile)
                next(reader, None)  # 略過標題列
                batch_size = 500
                count = 0
                for row in reader:
                    if len(row) >= 6:
                        timestamp = escape_sql(row[0])
                        threshold = row[1]
                        temp = row[2]
                        obs_time = escape_sql(row[3])
                        alert_state = escape_sql(row[4])
                        status_text = escape_sql(row[5])
                        
                        try:
                            float(temp)
                            float(threshold)
                            f.write(f"INSERT INTO alert_logs (timestamp, threshold, temperature, obs_time, alert_state, status_text) VALUES ('{timestamp}', {threshold}, {temp}, '{obs_time}', '{alert_state}', '{status_text}');\n")
                            count += 1
                            if count % batch_size == 0:
                                f.write("COMMIT;\nBEGIN TRANSACTION;\n")
                        except ValueError:
                            pass
            f.write("COMMIT;\n")

    print(f"✅ 成功生成匯入用 SQL 檔：{sql_file}")
    print("請使用以下指令匯入至 Cloudflare D1：")
    print("wrangler d1 execute weather-monitor-db --file=import_history.sql --remote")

if __name__ == "__main__":
    main()
