import os
import sys
import shutil

# 解決 Windows 控制台 (CP950) UTF-8 表情符號與色彩輸出問題
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='ignore')
        sys.stderr.reconfigure(encoding='utf-8', errors='ignore')
    except Exception:
        pass

import logging
logging.getLogger('werkzeug').setLevel(logging.ERROR)
os.environ['WERKZEUG_RUN_MAIN'] = 'true'

import socket
import datetime
import qrcode
import io
import base64
import subprocess
import threading
import re
import time
import urllib.request
import json
from flask import Flask, render_template, request, jsonify, send_from_directory

try:
    from waitress import serve
    HAS_WAITRESS = True
except ImportError:
    HAS_WAITRESS = False

app = Flask(__name__)

# 基礎配置：預設以 family-file-hub 執行位置為基準，儲存於 ./uploads/
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, 'config.txt')

# 檢查是否有在 config.txt 中自訂儲存路徑
def get_upload_folder():
    default_uploads = os.path.join(BASE_DIR, 'uploads')
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('UPLOAD_FOLDER='):
                    custom_path = line.split('=', 1)[1].strip()
                    if custom_path:
                        os.makedirs(custom_path, exist_ok=True)
                        return custom_path
    os.makedirs(default_uploads, exist_ok=True)
    return default_uploads

UPLOAD_FOLDER = get_upload_folder()
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024 * 1024  # 2 GB 最大上傳限制

# 初始化預設目錄
DEFAULT_FOLDERS = ['一般檔案', '爸爸', '媽媽', '孩子']
for folder in DEFAULT_FOLDERS:
    os.makedirs(os.path.join(UPLOAD_FOLDER, folder), exist_ok=True)

LOCAL_IP = "127.0.0.1"
CURRENT_PORT = 8080
WAN_URL = None
tunnel_process = None

if not os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        f.write('# 自訂固定外網網址與實體儲存路徑設定檔\n# CUSTOM_WAN_URL=https://your-custom-domain.com\n# UPLOAD_FOLDER=D:\\FamilyPhotos\n')

def get_custom_wan_url():
    env_url = os.environ.get('CUSTOM_WAN_URL', '').strip()
    if env_url:
        return env_url
        
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('CUSTOM_WAN_URL='):
                    return line.split('=', 1)[1].strip()
    return None

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def find_available_port(start_port=8080, max_attempts=50):
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("0.0.0.0", port))
                return port
            except OSError:
                continue
    return start_port

def generate_qr_code_base64(url):
    if not url:
        return None
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=8,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#6366f1", back_color="#ffffff")
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buffered.getvalue()).decode()

def get_ngrok_url_from_api():
    try:
        req = urllib.request.urlopen('http://127.0.0.1:4040/api/tunnels', timeout=2)
        data = json.loads(req.read().decode('utf-8'))
        tunnels = data.get('tunnels', [])
        for t in tunnels:
            pub_url = t.get('public_url', '')
            if pub_url.startswith('https://'):
                return pub_url
            elif pub_url.startswith('http://'):
                return pub_url.replace('http://', 'https://')
    except Exception:
        pass
    return None

def find_ngrok_binary():
    which_path = shutil.which('ngrok') or shutil.which('ngrok.exe')
    if which_path and os.path.exists(which_path):
        return which_path

    local_path = os.path.join(BASE_DIR, 'ngrok.exe')
    if os.path.exists(local_path):
        return local_path

    user_home = os.path.expanduser('~')
    program_files = os.environ.get('ProgramFiles', r'C:\Program Files')
    local_app_data = os.environ.get('LOCALAPPDATA', os.path.join(user_home, r'AppData\Local'))

    search_paths = [
        r'C:\ngrok\ngrok.exe',
        r'D:\ngrok\ngrok.exe',
        os.path.join(user_home, 'ngrok.exe'),
        os.path.join(user_home, 'Downloads', 'ngrok.exe'),
        os.path.join(local_app_data, 'Programs', 'ngrok', 'ngrok.exe'),
        os.path.join(local_app_data, 'ngrok', 'ngrok.exe'),
        os.path.join(program_files, 'ngrok', 'ngrok.exe'),
    ]

    for path in search_paths:
        if os.path.exists(path):
            return path

    return None

def start_wan_tunnel(port):
    global WAN_URL, tunnel_process
    
    custom_url = get_custom_wan_url()
    if custom_url:
        WAN_URL = custom_url
        print("-" * 65)
        print(f"✨ 【使用自訂固定外網網址】:")
        print(f"🔗 自訂外網網址: {WAN_URL}")
        print("-" * 65)
        return

    ngrok_bin = find_ngrok_binary()
    if ngrok_bin:
        print(f"🌐 [第一套外網系統] 動態偵測到 Ngrok 執行檔: {ngrok_bin}")
        cmd = [ngrok_bin, 'http', str(port)]
        try:
            ngrok_proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )

            for _ in range(10):
                time.sleep(0.5)
                n_url = get_ngrok_url_from_api()
                if n_url:
                    WAN_URL = n_url
                    print("-" * 65)
                    print(f"✨ 【Ngrok 外網連線成功】手機用 4G/5G/網際網路可直接點擊：")
                    print(f"🔗 Ngrok 安全網址 (HTTPS): {WAN_URL}")
                    print("-" * 65)
                    return
        except Exception as e:
            print(f"💡 Ngrok 訊息: {e}")

    print("🌐 [第二套備援系統] 啟動 SSH 免費極速外網通道...")
    ssh_cmd = ['ssh', '-o', 'StrictHostKeyChecking=no', '-o', 'ServerAliveInterval=30', '-R', f'80:127.0.0.1:{port}', 'nokey@localhost.run']
    
    try:
        ssh_proc = subprocess.Popen(
            ssh_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )

        def monitor_ssh_tunnel():
            global WAN_URL
            for line in iter(ssh_proc.stdout.readline, ''):
                if 'lhr.life' in line or 'https://' in line:
                    match = re.search(r'https://[a-zA-Z0-9-]+\.lhr\.life', line)
                    if match:
                        WAN_URL = match.group(0)
                        print("-" * 65)
                        print(f"✨ 【SSH 備援外網連線成功】手機用 4G/5G/網際網路可直接連線：")
                        print(f"🔗 安全網址 (HTTPS): {WAN_URL}")
                        print("-" * 65)
                        return

        t2 = threading.Thread(target=monitor_ssh_tunnel, daemon=True)
        t2.start()
    except Exception as e:
        print(f"💡 SSH 備援通道訊息: {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/guide')
def guide():
    return send_from_directory(BASE_DIR, '使用說明書.html')

@app.route('/api/info')
def get_info():
    lan_url = f"http://{LOCAL_IP}:{CURRENT_PORT}"
    lan_qr = generate_qr_code_base64(lan_url)
    wan_qr = generate_qr_code_base64(WAN_URL) if WAN_URL else None
    
    total_size = 0
    file_count = 0
    for root, dirs, files in os.walk(UPLOAD_FOLDER):
        for f in files:
            file_count += 1
            total_size += os.path.getsize(os.path.join(root, f))
            
    return jsonify({
        'ip': LOCAL_IP,
        'port': CURRENT_PORT,
        'lan_url': lan_url,
        'lan_qr': lan_qr,
        'wan_url': WAN_URL,
        'wan_qr': wan_qr,
        'file_count': file_count,
        'storage_mb': round(total_size / (1024 * 1024), 2),
        'upload_folder': UPLOAD_FOLDER
    })

@app.route('/api/folders')
def list_folders():
    folders = []
    for item in os.listdir(UPLOAD_FOLDER):
        item_path = os.path.join(UPLOAD_FOLDER, item)
        if os.path.isdir(item_path):
            file_num = len(os.listdir(item_path))
            folders.append({'name': item, 'file_count': file_num})
            
    folders.sort(key=lambda x: (x['name'] != '一般檔案', x['name']))
    return jsonify({'success': True, 'folders': folders})

@app.route('/api/create_folder', methods=['POST'])
def create_folder():
    data = request.json or {}
    folder_name = data.get('folder_name', '').strip()
    if not folder_name:
        return jsonify({'success': False, 'message': '資料夾名稱不能為空'}), 400
        
    folder_name = re.sub(r'[\\/:*?"<>|]', '_', folder_name)
    target_path = os.path.join(UPLOAD_FOLDER, folder_name)
    
    if os.path.exists(target_path):
        return jsonify({'success': True, 'message': '資料夾已存在', 'folder_name': folder_name})
        
    try:
        os.makedirs(target_path, exist_ok=True)
        return jsonify({'success': True, 'message': f'成功建立資料夾 [{folder_name}]', 'folder_name': folder_name})
    except Exception as e:
        return jsonify({'success': False, 'message': f'建立失敗: {str(e)}'}), 500

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'files' not in request.files:
        return jsonify({'success': False, 'message': '未找到上傳檔案'}), 400
        
    uploaded_files = request.files.getlist('files')
    member = request.form.get('member', '一般檔案').strip() or '一般檔案'
    
    member = re.sub(r'[\\/:*?"<>|]', '_', member)
    target_dir = os.path.join(UPLOAD_FOLDER, member)
    os.makedirs(target_dir, exist_ok=True)
    
    saved_list = []
    for file in uploaded_files:
        if file.filename == '':
            continue
            
        filename = os.path.basename(file.filename)
        save_path = os.path.join(target_dir, filename)
        if os.path.exists(save_path):
            name, ext = os.path.splitext(filename)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{name}_{timestamp}{ext}"
            save_path = os.path.join(target_dir, filename)
            
        file.save(save_path)
        saved_list.append(filename)
        
    return jsonify({
        'success': True, 
        'message': f'成功上傳 {len(saved_list)} 個檔案至 [{member}] 資料夾',
        'files': saved_list,
        'folder': member
    })

@app.route('/api/files')
def list_files():
    result = []
    for root, dirs, files in os.walk(UPLOAD_FOLDER):
        for f in files:
            full_path = os.path.join(root, f)
            rel_path = os.path.relpath(full_path, UPLOAD_FOLDER).replace('\\', '/')
            folder_name = rel_path.split('/')[0] if '/' in rel_path else '一般檔案'
            
            stat = os.stat(full_path)
            mod_time = datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            size_mb = round(stat.st_size / (1024 * 1024), 2)
            size_str = f"{round(stat.st_size / 1024, 1)} KB" if size_mb < 0.01 else f"{size_mb} MB"
                
            ext = os.path.splitext(f)[1].lower()
            if ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.heic']:
                file_type = 'image'
            elif ext in ['.mp4', '.mov', '.avi', '.mkv', '.webm']:
                file_type = 'video'
            elif ext in ['.mp3', '.m4a', '.wav', '.flac', '.aac']:
                file_type = 'audio'
            elif ext in ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt']:
                file_type = 'document'
            else:
                file_type = 'other'

            result.append({
                'name': f,
                'rel_path': rel_path,
                'folder': folder_name,
                'size': size_str,
                'bytes': stat.st_size,
                'mtime': mod_time,
                'type': file_type,
                'url': f'/uploads/{rel_path}'
            })
            
    result.sort(key=lambda x: x['mtime'], reverse=True)
    return jsonify({'success': True, 'files': result})

@app.route('/uploads/<path:filename>')
def serve_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/api/delete', methods=['POST'])
def delete_file():
    data = request.json or {}
    rel_path = data.get('rel_path')
    if not rel_path:
        return jsonify({'success': False, 'message': '缺少檔案路徑'}), 400
        
    full_path = os.path.join(UPLOAD_FOLDER, rel_path)
    if os.path.exists(full_path) and os.path.isfile(full_path):
        os.remove(full_path)
        return jsonify({'success': True, 'message': '檔案已成功刪除'})
    return jsonify({'success': False, 'message': '檔案不存在'}), 404

if __name__ == '__main__':
    DEFAULT_PORT = 8080
    CURRENT_PORT = find_available_port(DEFAULT_PORT)
    if CURRENT_PORT != DEFAULT_PORT:
        print(f"💡 [提示] 預設 Port {DEFAULT_PORT} 已被佔用，已自動切換至可用 Port: {CURRENT_PORT}")
        
    LOCAL_IP = get_local_ip()
    
    start_wan_tunnel(CURRENT_PORT)
    
    print("=" * 65)
    print("🚀 家庭手機上傳中心 (Family File Hub) 伺服器已成功啟動！")
    print(f"🏠 區網 (Wi-Fi) 連線網址:  http://{LOCAL_IP}:{CURRENT_PORT}")
    print(f"💻 本機存取網址:         http://localhost:{CURRENT_PORT}")
    print(f"📂 電腦實體儲存目錄:     {UPLOAD_FOLDER}")
    print("=" * 65)
    
    if HAS_WAITRESS:
        serve(app, host='0.0.0.0', port=CURRENT_PORT, _quiet=True)
    else:
        app.run(host='0.0.0.0', port=CURRENT_PORT, debug=False)
