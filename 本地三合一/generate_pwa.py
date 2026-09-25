import os
import re

pwa_dir = r'c:\GOOGLE ANGET\本地三合一\2_PWA_App版'
icons_dir = os.path.join(pwa_dir, 'icons')
os.makedirs(icons_dir, exist_ok=True)

# 1. Generate manifest.json
manifest_content = '''{
  "name": "台積三合一單與COA 雙重核對系統",
  "short_name": "三合一核對",
  "start_url": "./index.html",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#3b82f6",
  "icons": [
    {
      "src": "icons/icon-192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "icons/icon-512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}'''
with open(os.path.join(pwa_dir, 'manifest.json'), 'w', encoding='utf-8') as f:
    f.write(manifest_content)

# 2. Generate sw.js
sw_content = '''
const CACHE_NAME = 'pwa-cache-v1';
const urlsToCache = [
  './index.html',
  './manifest.json'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', event => {
  // 只攔截 GET 請求進行快取，POST (打 GAS API) 直接放行
  if (event.request.method !== 'GET') return;
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        return response || fetch(event.request);
      })
  );
});
'''
with open(os.path.join(pwa_dir, 'sw.js'), 'w', encoding='utf-8') as f:
    f.write(sw_content)

# 3. Generate run_server.py
server_content = '''import http.server
import socketserver
import socket

PORT = 8000
Handler = http.server.SimpleHTTPRequestHandler

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

while True:
    try:
        with socketserver.TCPServer(('', PORT), Handler) as httpd:
            ip = get_ip()
            print(f"\\n[✅] 伺服器已啟動！")
            print(f"👉 電腦本機請訪問: http://localhost:{PORT}")
            print(f"👉 手機測試請訪問: http://{ip}:{PORT}")
            print(f"\\n請確保手機與電腦連線至同一個 Wi-Fi 網路。")
            httpd.serve_forever()
    except OSError:
        PORT += 1
'''
with open(os.path.join(pwa_dir, 'run_server.py'), 'w', encoding='utf-8') as f:
    f.write(server_content)

# 4. Generate .bat
bat_content = '''@echo off
chcp 65001 >nul
echo =========================================
echo      啟動 PWA 雙軌系統本機測試伺服器
echo =========================================
python run_server.py
pause
'''
with open(os.path.join(pwa_dir, '啟動PWA本機測試.bat'), 'w', encoding='utf-8') as f:
    f.write(bat_content)

# 5. Read original HTML and transform
source_html = r'c:\GOOGLE ANGET\本地三合一\Index_Backup.html'
with open(source_html, 'r', encoding='utf-8') as f:
    html_content = f.read()

# Add manifest and sw.js registration in <head>
head_injection = '''
    <!-- PWA Setup -->
    <link rel="manifest" href="manifest.json">
    <meta name="theme-color" content="#3b82f6">
    <script>
      if ('serviceWorker' in navigator) {
        window.addEventListener('load', () => {
          navigator.serviceWorker.register('sw.js').then(reg => {
            console.log('SW registered!', reg);
          }).catch(err => console.log('SW registration failed', err));
        });
      }
    </script>
'''
html_content = html_content.replace('</head>', head_injection + '</head>')

# Add PWA Install Banner UI below body
body_injection = '''
    <div id="pwa-install-banner" class="hidden" style="background-color: #3b82f6; color: white; padding: 10px; text-align: center; position: sticky; top: 0; z-index: 9999; display: flex; justify-content: space-between; align-items: center;">
        <span>📲 將此系統安裝為 App，體驗更好！</span>
        <button id="pwa-install-btn" style="background: white; color: #3b82f6; border: none; padding: 5px 15px; border-radius: 5px; font-weight: bold;">立即安裝</button>
    </div>
'''
# Using regex to inject just inside <body>
html_content = re.sub(r'<body[^>]*>', lambda m: m.group(0) + body_injection, html_content, count=1)

# Add Mock google.script.run
mock_gas = '''
    <script>
      let deferredPrompt;
      window.addEventListener('beforeinstallprompt', (e) => {
        e.preventDefault();
        deferredPrompt = e;
        document.getElementById('pwa-install-banner').classList.remove('hidden');
      });
      document.getElementById('pwa-install-btn').addEventListener('click', async () => {
        if (deferredPrompt) {
          deferredPrompt.prompt();
          const { outcome } = await deferredPrompt.userChoice;
          if (outcome === 'accepted') {
            document.getElementById('pwa-install-banner').classList.add('hidden');
          }
          deferredPrompt = null;
        }
      });

      const GAS_API_URL = "https://script.google.com/macros/s/AKfycbyJNqo25ny2IiwajeltMlSi1M8PnVonczlLA2UoEoxZYGSE72tiWTEJ61Y_wQhPU0H5/exec";

      // Mock google.script.run for PWA backend decoupling
      const google = {
        script: {
          run: {
            withSuccessHandler: function(onSuccess) { this._onSuccess = onSuccess; return this; },
            withFailureHandler: function(onFailure) { this._onFailure = onFailure; return this; },
            _callBackend: function(action, ...args) {
              const successCb = this._onSuccess; const failureCb = this._onFailure;
              this._onSuccess = null; this._onFailure = null;
              
              let payload = { action: action };
              if (action === "analyzeLabelPhoto") payload.base64Data = args[0];
              else if (action === "processFormAndVerify") payload.formObject = args[0];
              else if (action === "getLogData") { payload.page = args[0]; payload.searchText = args[1]; payload.startDate = args[2]; payload.endDate = args[3]; }
              else if (action === "getExportData") { payload.searchText = args[0]; payload.startDate = args[1]; payload.endDate = args[2]; }

              fetch(GAS_API_URL, {
                method: "POST",
                headers: { "Content-Type": "text/plain;charset=utf-8" },
                body: JSON.stringify(payload)
              })
              .then(res => res.json())
              .then(data => { if(successCb) successCb(data); })
              .catch(err => { if(failureCb) failureCb(err); });
            },
            analyzeLabelPhoto: function(base64Data) { this._callBackend("analyzeLabelPhoto", base64Data); },
            processFormAndVerify_V10: function(formObject) { this._callBackend("processFormAndVerify", formObject); },
            getLogData: function(page, search, start, end) { this._callBackend("getLogData", page, search, start, end); },
            getExportData: function(search, start, end) { this._callBackend("getExportData", search, start, end); }
          }
        }
      };
    </script>
'''
html_content = html_content.replace('</body>', mock_gas + '</body>')

with open(os.path.join(pwa_dir, 'index.html'), 'w', encoding='utf-8') as f:
    f.write(html_content)

print("PWA generated successfully!")
