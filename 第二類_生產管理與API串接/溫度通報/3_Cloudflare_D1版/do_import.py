import csv
import os

def escape_sql(text):
    if text is None: return ""
    return str(text).replace("'", "''")

base_dir = r"C:\GOOGLE ANGET\第二類_生產管理與API串接\溫度通報"
heartbeat_csv = os.path.join(base_dir, "本地歷史紀錄_心跳明細.csv")
alert_csv = os.path.join(base_dir, "本地歷史紀錄_歷史通報.csv")
sql_file = "clean_import.sql"

with open(sql_file, 'w', encoding='utf-8') as f:
    f.write("DELETE FROM temperature_logs;\n")
    f.write("DELETE FROM alert_logs;\n")
    
    if os.path.exists(heartbeat_csv):
        with open(heartbeat_csv, 'r', encoding='utf-8-sig') as csvfile:
            reader = csv.reader(csvfile)
            next(reader, None)
            for row in reader:
                # row[0]: timestamp, row[1]: threshold, row[2]: temperature, row[3]: obs_time, row[4]: status
                if len(row) >= 5:
                    try:
                        temp = float(row[2])
                        f.write(f"INSERT INTO temperature_logs (timestamp, temperature, obs_time, status) VALUES ('{escape_sql(row[0])}', {temp}, '{escape_sql(row[3])}', '{escape_sql(row[4])}');\n")
                    except:
                        pass

    if os.path.exists(alert_csv):
        with open(alert_csv, 'r', encoding='utf-8-sig') as csvfile:
            reader = csv.reader(csvfile)
            next(reader, None)
            for row in reader:
                # Same columns roughly for alert_logs: 0: timestamp, 1: threshold, 2: temp, 3: obs_time, 4: status, 5: msg
                if len(row) >= 5:
                    try:
                        th = float(row[1])
                        temp = float(row[2])
                        f.write(f"INSERT INTO alert_logs (timestamp, threshold, temperature, obs_time, alert_state, status_text) VALUES ('{escape_sql(row[0])}', {th}, {temp}, '{escape_sql(row[3])}', '{escape_sql(row[4])}', '{escape_sql(row[4])}');\n")
                    except:
                        pass
print("Done writing clean_import.sql")
