import os
import io
import socket
import zipfile
import urllib.parse
from typing import List
from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from ch_parser import parse_agilent_ch

app = FastAPI(title="Agilent GC/LC Chromatography Data Viewer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for parsed files in current session
PARSED_CACHE = {}

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def find_available_port(start_port: int = 8008, max_attempts: int = 50) -> int:
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("0.0.0.0", port))
                return port
            except OSError:
                continue
    return start_port

@app.get("/api/network-info")
def get_network_info():
    return {
        "local_ip": get_local_ip(),
        "hostname": socket.gethostname()
    }

@app.post("/api/upload")
async def upload_agilent_files(files: List[UploadFile] = File(...)):
    """
    Upload single or multiple Agilent .ch files or a .zip archive of a .D directory.
    """
    results = []

    for file in files:
        file_bytes = await file.read()
        file_name = file.filename
        
        # If user uploaded a ZIP archive
        if file_name.lower().endswith('.zip'):
            try:
                with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
                    for zip_info in z.infolist():
                        if zip_info.filename.lower().endswith(('.ch', '.gcd', '.lcd', '.dat', '.raw', '.csv', '.txt')):
                            ch_data = z.read(zip_info.filename)
                            inner_name = os.path.basename(zip_info.filename)
                            try:
                                parsed = parse_agilent_ch(ch_data, filename=inner_name)
                                parsed['filename'] = f"{file_name} -> {inner_name}"
                                cache_key = f"{file_name}_{inner_name}"
                                PARSED_CACHE[cache_key] = parsed
                                results.append(parsed)
                            except Exception as e:
                                results.append({
                                    "filename": inner_name,
                                    "error": str(e)
                                })
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"解壓縮 ZIP 檔失敗: {str(e)}")
        else:
            # Single .gcd, .ch, .lcd, .raw, .dat, .csv file
            try:
                parsed = parse_agilent_ch(file_bytes, filename=file_name)
                parsed['filename'] = file_name
                PARSED_CACHE[file_name] = parsed
                results.append(parsed)
            except Exception as e:
                results.append({
                    "filename": file_name,
                    "error": str(e)
                })

    if not results:
        raise HTTPException(status_code=400, detail="未上傳任何有效的 Agilent 數據檔案。")

    return {"status": "success", "count": len(results), "data": results}


@app.get("/api/export/csv")
def export_csv(filename: str = Query(...)):
    """
    Exports parsed chromatography signal to CSV format.
    """
    if filename not in PARSED_CACHE:
        raise HTTPException(status_code=404, detail="找不到指定的解析紀錄。")

    data = PARSED_CACHE[filename]
    df = pd.DataFrame({
        "Retention_Time_min": data["retention_times"],
        "Abundance_Signal": data["intensities"]
    })

    stream = io.StringIO()
    # Write metadata header
    stream.write(f"# Agilent GC/LC Data Export\n")
    stream.write(f"# Sample Name: {data['sample_name']}\n")
    stream.write(f"# Operator: {data['operator']}\n")
    stream.write(f"# Date: {data['date_str']}\n")
    stream.write(f"# Signal: {data['signal_name']}\n")
    stream.write(f"# Total Points: {data['total_points']}\n\n")
    
    df.to_csv(stream, index=False)
    
    response = StreamingResponse(iter([stream.getvalue()]), media_type="text/csv")
    safe_filename = urllib.parse.quote(f"{filename}_data.csv")
    response.headers["Content-Disposition"] = f"attachment; filename*=UTF-8''{safe_filename}"
    return response


@app.get("/api/export/excel")
def export_excel(filename: str = Query(...)):
    """
    Exports chromatography data & detected peaks into a multi-tab Excel file.
    """
    if filename not in PARSED_CACHE:
        raise HTTPException(status_code=404, detail="找不到指定的解析紀錄。")

    data = PARSED_CACHE[filename]
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Sheet 1: Metadata & Summary
        summary_df = pd.DataFrame([
            {"項目": "檔案名稱", "內容": filename},
            {"項目": "樣品名稱 (Sample)", "內容": data["sample_name"]},
            {"項目": "操作員 (Operator)", "內容": data["operator"]},
            {"項目": "分析日期", "內容": data["date_str"]},
            {"項目": "訊號類別", "內容": data["signal_name"]},
            {"項目": "總資料點數", "內容": data["total_points"]},
            {"項目": "起始滯留時間 (min)", "內容": data["min_rt"]},
            {"項目": "結束滯留時間 (min)", "內容": data["max_rt"]},
            {"項目": "最高訊號強度", "內容": data["max_abundance"]}
        ])
        summary_df.to_excel(writer, sheet_name="摘要資訊", index=False)

        # Sheet 2: Detected Peaks
        if data.get("peaks"):
            peaks_df = pd.DataFrame(data["peaks"])
            peaks_df.rename(columns={
                "rank": "排名",
                "peak_id": "峰值編號",
                "retention_time": "滯留時間 (RT min)",
                "peak_height": "峰高 (Height)",
                "area": "峰面積 (Peak Area)"
            }, inplace=True)
            peaks_df.to_excel(writer, sheet_name="峰值分析 (Peaks)", index=False)

        # Sheet 3: Raw Signal Points
        signal_df = pd.DataFrame({
            "Retention_Time_min": data["retention_times"],
            "Abundance_Signal": data["intensities"]
        })
        signal_df.to_excel(writer, sheet_name="原始數據點 (Signal)", index=False)

    output.seek(0)
    response = StreamingResponse(output, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    safe_filename = urllib.parse.quote(f"{filename}_report.xlsx")
    response.headers["Content-Disposition"] = f"attachment; filename*=UTF-8''{safe_filename}"
    return response


@app.get("/", response_class=HTMLResponse)
def read_root():
    template_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
    if os.path.exists(template_path):
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Agilent Viewer Service is Running. index.html not found.</h1>"

if __name__ == "__main__":
    import uvicorn
    import webbrowser
    import threading
    
    local_ip = get_local_ip()
    port = find_available_port(8008)
    
    print("=" * 60)
    print(" Agilent GC/LC Chromatography Data Viewer Service")
    print(f" 本機電腦請開 (Local):   http://localhost:{port}")
    print(f" 區網同仁請開 (Network): http://{local_ip}:{port}")
    print(" 注意: 請勿在瀏覽器輸入 0.0.0.0 (瀏覽器會顯示網址無效)")
    print("=" * 60)
    
    # Auto open browser to localhost after 1.5s
    def open_browser():
        webbrowser.open(f"http://localhost:{port}")
        
    threading.Timer(1.5, open_browser).start()
    
    uvicorn.run(app, host="0.0.0.0", port=port)


