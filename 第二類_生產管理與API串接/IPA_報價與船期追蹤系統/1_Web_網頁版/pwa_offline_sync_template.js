/**
 * ============================================================================
 * PWA 離線優先與自動重連補傳通用模組 (pwa_offline_sync_template.js)
 * ============================================================================
 * 說明：
 * 本模組提供開箱即用的「離線暫存、斷網不阻擋、連網秒補傳」機制。
 * 凡是表單送出、檢驗打卡、出入庫登錄等操作，皆可無縫套用此模組：
 * 
 * 核心特色：
 * 1. 斷網攔截：斷網 (navigator.onLine === false) 或 API 請求失敗時，自動將資料寫入 localStorage 離線佇列。
 * 2. 狀態徽章：可綁定 HTML 徽章元素，自動顯示「🟢 雲端已同步」或「🟡 離線暫存 (X筆待同步)」。
 * 3. 自動補傳：監聽 window 'online' 事件，並搭配 30 秒定時巡檢，連網時自動 FIFO 消化佇列並送出。
 * 4. 輕量通知：內建簡約浮動 Toast 提示，補傳完成時主動提示使用者，強化操作信心。
 * 5. 即插即用：支援直接引用 <script src="pwa_offline_sync_template.js"> 或模組化引用。
 * 
 * 快速使用範例 (Quick Start)：
 * ----------------------------------------------------------------------------
 * 1. 引入本檔：
 *    <script src="pwa_offline_sync_template.js"></script>
 * 
 * 2. 初始化：
 *    const syncMgr = new OfflineSyncManager({
 *        storageKey: 'qc_offline_queue',
 *        badgeElementId: 'syncBadge', // HTML 中放入 <span id="syncBadge"></span>
 *        syncHandler: async (item) => {
 *            // 真正向後端 (Cloudflare D1 / GAS) 補傳資料的邏輯
 *            const res = await fetch(item.url, {
 *                method: item.method,
 *                headers: item.headers,
 *                body: typeof item.body === 'string' ? item.body : JSON.stringify(item.body)
 *            });
 *            if (!res.ok) throw new Error(`HTTP ${res.status}`);
 *            return await res.json();
 *        }
 *    });
 * 
 * 3. 呼叫方式 (二選一)：
 *    // 方法 A：直接用 syncMgr.request 包裝原生的 fetch
 *    const result = await syncMgr.request('/api/qc/submit', {
 *        method: 'POST',
 *        body: { barcode: 'SN12345', status: 'PASS' }
 *    });
 *    if (result.offline) {
 *        alert('目前無網路，資料已離線暫存，連網後將自動補傳！');
 *    }
 * 
 *    // 方法 B：手動加入佇列
 *    syncMgr.enqueue({
 *        url: 'https://api.example.com/checkin',
 *        method: 'POST',
 *        body: { id: 1, action: 'IN' },
 *        title: '入庫掃描'
 *    });
 * ============================================================================
 */

(function (global) {
    'use strict';

    class OfflineSyncManager {
        /**
         * @param {Object} options 設定選項
         * @param {string} [options.storageKey='pwa_offline_sync_queue'] 儲存於 localStorage 的 Key
         * @param {string|HTMLElement} [options.badgeElementId=null] 顯示狀態的徽章元素或 ID
         * @param {Function} [options.syncHandler=null] 自訂補傳處理函式 async (item) => boolean|Object
         * @param {number} [options.checkIntervalMs=30000] 定時巡檢查離線佇列的時間間隔 (毫秒，預設 30 秒)
         * @param {boolean} [options.enableToast=true] 是否在自動同步時顯示浮動提示
         * @param {Function} [options.onQueueChange=null] 佇列長度變更時的回呼函式 (count) => {}
         * @param {Function} [options.onSyncSuccess=null] 單筆補傳成功回呼 (item, res) => {}
         * @param {Function} [options.onSyncError=null] 單筆補傳失敗回呼 (item, err) => {}
         */
        constructor(options = {}) {
            this.storageKey = options.storageKey || 'pwa_offline_sync_queue';
            this.badgeElementId = options.badgeElementId || null;
            this.syncHandler = options.syncHandler || this._defaultSyncHandler.bind(this);
            this.checkIntervalMs = options.checkIntervalMs || 30000;
            this.enableToast = options.enableToast !== false;
            this.onQueueChange = options.onQueueChange || null;
            this.onSyncSuccess = options.onSyncSuccess || null;
            this.onSyncError = options.onSyncError || null;

            this.isSyncing = false;
            this.timer = null;

            this._init();
        }

        /**
         * 初始化事件監聽與定時器
         */
        _init() {
            // 監聽連網恢復事件
            window.addEventListener('online', () => {
                console.log('[OfflineSync] 偵測到網路已連線，準備啟動佇列補傳...');
                this.updateBadge();
                this.flushQueue();
            });

            // 監聽斷網事件
            window.addEventListener('offline', () => {
                console.warn('[OfflineSync] 偵測到網路中斷，已切換至離線暫存模式。');
                this.updateBadge();
                if (this.enableToast) {
                    this.showToast('網路已中斷，系統已切換至離線暫存模式', 'warning');
                }
            });

            // 定期背景巡檢補傳 (即使 missed online event 也能自動補救)
            if (this.checkIntervalMs > 0) {
                this.timer = setInterval(() => {
                    if (navigator.onLine && this.getQueue().length > 0 && !this.isSyncing) {
                        this.flushQueue();
                    }
                }, this.checkIntervalMs);
            }

            // 初始化時立即更新徽章狀態
            this.updateBadge();

            // 若啟動時已有網路且佇列有待處理資料，立刻嘗試消化
            if (navigator.onLine && this.getQueue().length > 0) {
                setTimeout(() => this.flushQueue(), 1500);
            }
        }

        /**
         * 取得目前離線佇列陣列
         * @returns {Array<Object>}
         */
        getQueue() {
            try {
                const raw = localStorage.getItem(this.storageKey);
                return raw ? JSON.parse(raw) : [];
            } catch (err) {
                console.error('[OfflineSync] 讀取離線佇列失敗:', err);
                return [];
            }
        }

        /**
         * 覆寫儲存佇列陣列
         * @param {Array<Object>} queue 
         */
        _saveQueue(queue) {
            try {
                localStorage.setItem(this.storageKey, JSON.stringify(queue));
                this.updateBadge();
                if (typeof this.onQueueChange === 'function') {
                    this.onQueueChange(queue.length);
                }
            } catch (err) {
                console.error('[OfflineSync] 儲存離線佇列失敗:', err);
            }
        }

        /**
         * 將一筆操作存入離線佇列
         * @param {Object} item 
         * @param {string} item.url API 請求網址
         * @param {string} [item.method='POST'] HTTP 方法
         * @param {Object} [item.headers] HTTP 標頭
         * @param {any} item.body 請求內容 (物件或字串)
         * @param {string} [item.title] 業務標題（例如：檢驗單號 #12345）
         * @returns {Object} 佇列項目實體
         */
        enqueue(item) {
            const queue = this.getQueue();
            const record = {
                id: 'sync_' + Date.now() + '_' + Math.random().toString(36).substring(2, 8),
                url: item.url || '',
                method: (item.method || 'POST').toUpperCase(),
                headers: item.headers || { 'Content-Type': 'application/json' },
                body: item.body || null,
                title: item.title || '離線資料',
                timestamp: Date.now(),
                retryCount: 0
            };

            queue.push(record);
            this._saveQueue(queue);

            console.log(`[OfflineSync] 資料已寫入離線佇列 (${record.id})，目前待同步筆數: ${queue.length}`);
            if (this.enableToast) {
                this.showToast(`🟡 已離線暫存 (${record.title})，連網後將自動補傳`, 'warning');
            }
            return record;
        }

        /**
         * 智慧請求包裝函式 (Drop-in Fetch)
         * 若在線則發送網路請求；若連線失敗或離線，自動寫入離線佇列
         * @param {string} url 請求 URL
         * @param {Object} options fetch 選項
         * @returns {Promise<Object>} 回傳 { offline: boolean, queued: boolean, data?: any, error?: any }
         */
        async request(url, options = {}) {
            const method = (options.method || 'GET').toUpperCase();
            const isMutation = ['POST', 'PUT', 'PATCH', 'DELETE'].includes(method);

            // 若非網路修改操作 (例如 GET)，或者明確知道已斷網且不是修改操作，直接拋錯
            if (!navigator.onLine && !isMutation) {
                throw new Error('目前處於離線狀態，無法取得最新網路資料');
            }

            // 若目前處於斷網狀態，且是資料變更類請求，直接存入佇列
            if (!navigator.onLine && isMutation) {
                const record = this.enqueue({
                    url: url,
                    method: method,
                    headers: options.headers || { 'Content-Type': 'application/json' },
                    body: options.body || null,
                    title: options.title || '離線請求'
                });
                return { offline: true, queued: true, item: record };
            }

            // 嘗試在線發送
            try {
                const response = await fetch(url, options);
                if (!response.ok) {
                    throw new Error(`HTTP 狀態碼異常: ${response.status} ${response.statusText}`);
                }
                let data = null;
                const contentType = response.headers.get('content-type') || '';
                if (contentType.includes('application/json')) {
                    data = await response.json();
                } else {
                    data = await response.text();
                }
                return { offline: false, queued: false, data: data };
            } catch (err) {
                // 網路連線錯誤 (TypeError: Failed to fetch / 網路中斷)
                if (isMutation) {
                    console.warn('[OfflineSync] 網路連線請求失敗，自動轉為離線暫存:', err.message);
                    const record = this.enqueue({
                        url: url,
                        method: method,
                        headers: options.headers || { 'Content-Type': 'application/json' },
                        body: options.body || null,
                        title: options.title || '連線中斷暫存'
                    });
                    return { offline: true, queued: true, item: record, error: err };
                }
                // GET 失敗直接丟出例外
                throw err;
            }
        }

        /**
         * 預設補傳執行邏輯 (若未傳入 syncHandler 時使用)
         * @param {Object} item 
         */
        async _defaultSyncHandler(item) {
            const body = typeof item.body === 'object' && item.body !== null
                ? JSON.stringify(item.body)
                : item.body;

            const res = await fetch(item.url, {
                method: item.method,
                headers: item.headers,
                body: body
            });

            if (!res.ok) {
                throw new Error(`HTTP ${res.status}: ${res.statusText}`);
            }

            const cType = res.headers.get('content-type') || '';
            if (cType.includes('application/json')) {
                return await res.json();
            }
            return await res.text();
        }

        /**
         * 消化並批次補傳離線佇列 (FIFO 順序)
         */
        async flushQueue() {
            if (this.isSyncing) return;
            const queue = this.getQueue();
            if (queue.length === 0) {
                this.updateBadge();
                return;
            }

            if (!navigator.onLine) {
                console.log('[OfflineSync] 仍處於離線狀態，暫緩補傳。');
                return;
            }

            this.isSyncing = true;
            console.log(`[OfflineSync] 開始消化補傳離線佇列，共 ${queue.length} 筆...`);
            this.updateBadge();

            let successCount = 0;
            let failCount = 0;
            const remainingQueue = [];

            for (let i = 0; i < queue.length; i++) {
                const item = queue[i];
                try {
                    console.log(`[OfflineSync] 正在補傳 [${i + 1}/${queue.length}] ${item.title} (${item.id})...`);
                    const result = await this.syncHandler(item);
                    successCount++;
                    if (typeof this.onSyncSuccess === 'function') {
                        this.onSyncSuccess(item, result);
                    }
                } catch (err) {
                    console.error(`[OfflineSync] 補傳失敗 (${item.id}):`, err);
                    failCount++;
                    item.retryCount = (item.retryCount || 0) + 1;
                    item.lastError = err.message || String(err);
                    remainingQueue.push(item);
                    if (typeof this.onSyncError === 'function') {
                        this.onSyncError(item, err);
                    }
                    // 若是因網路再度中斷，中斷後續補傳避免浪費請求
                    if (!navigator.onLine) {
                        for (let j = i + 1; j < queue.length; j++) {
                            remainingQueue.push(queue[j]);
                        }
                        break;
                    }
                }
            }

            this._saveQueue(remainingQueue);
            this.isSyncing = false;
            this.updateBadge();

            if (successCount > 0) {
                const msg = `🎉 離線補傳完成！已成功同步 ${successCount} 筆資料至雲端`;
                console.log(`[OfflineSync] ${msg}`);
                if (this.enableToast) {
                    this.showToast(msg, 'success');
                }
            }

            if (failCount > 0 && remainingQueue.length > 0) {
                console.warn(`[OfflineSync] 尚有 ${remainingQueue.length} 筆資料補傳失敗，將在下次連線時自動重試。`);
            }
        }

        /**
         * 清空離線佇列
         */
        clearQueue() {
            this._saveQueue([]);
            console.log('[OfflineSync] 離線佇列已完全清空。');
        }

        /**
         * 更新 UI 徽章顯示
         * 徽章支援顯示三種狀態：
         * 1. 🟡 離線暫存 (X 筆待同步)
         * 2. 🔄 正在同步中 (X 筆)...
         * 3. 🟢 雲端已同步 / 在線就緒
         */
        updateBadge() {
            if (!this.badgeElementId) return;

            let el = null;
            if (typeof this.badgeElementId === 'string') {
                el = document.getElementById(this.badgeElementId);
            } else if (this.badgeElementId instanceof HTMLElement) {
                el = this.badgeElementId;
            }

            if (!el) return;

            const queue = this.getQueue();
            const count = queue.length;

            if (this.isSyncing) {
                el.innerHTML = `🔄 正在同步中 (${count}筆)...`;
                el.className = 'sync-badge syncing';
                el.style.backgroundColor = '#e0f2fe';
                el.style.color = '#0369a1';
                el.style.borderColor = '#7dd3fc';
            } else if (count > 0) {
                el.innerHTML = `🟡 離線暫存 (${count}筆待同步)`;
                el.className = 'sync-badge pending';
                el.style.backgroundColor = '#fef3c7';
                el.style.color = '#92400e';
                el.style.borderColor = '#fcd34d';
            } else {
                if (navigator.onLine) {
                    el.innerHTML = `🟢 雲端已同步`;
                    el.className = 'sync-badge synced';
                    el.style.backgroundColor = '#dcfce7';
                    el.style.color = '#15803d';
                    el.style.borderColor = '#86efac';
                } else {
                    el.innerHTML = `⚪ 離線模式 (無待同步)`;
                    el.className = 'sync-badge offline';
                    el.style.backgroundColor = '#f3f4f6';
                    el.style.color = '#4b5563';
                    el.style.borderColor = '#d1d5db';
                }
            }

            // 確保基本樣式美觀
            el.style.display = 'inline-flex';
            el.style.alignItems = 'center';
            el.style.gap = '4px';
            el.style.padding = '4px 10px';
            el.style.borderRadius = '9999px';
            el.style.fontSize = '12px';
            el.style.fontWeight = '600';
            el.style.border = '1px solid';
            el.style.cursor = count > 0 ? 'pointer' : 'default';
            el.title = count > 0 ? '點擊立即嘗試補傳' : (navigator.onLine ? '網路正常，資料已同步' : '離線狀態');

            // 點擊待同步徽章時可主動觸發一次補傳
            if (count > 0 && !el._syncClickBound) {
                el.addEventListener('click', () => {
                    if (navigator.onLine) {
                        this.flushQueue();
                    } else {
                        this.showToast('目前設備仍無網路連線，無法補傳', 'warning');
                    }
                });
                el._syncClickBound = true;
            }
        }

        /**
         * 顯示浮動 Toast 提示
         * @param {string} message 提示訊息內容
         * @param {'success'|'warning'|'error'|'info'} [type='info'] 樣式類別
         */
        showToast(message, type = 'info') {
            if (typeof document === 'undefined') return;

            let toastContainer = document.getElementById('offline-sync-toast-container');
            if (!toastContainer) {
                toastContainer = document.createElement('div');
                toastContainer.id = 'offline-sync-toast-container';
                Object.assign(toastContainer.style, {
                    position: 'fixed',
                    bottom: '24px',
                    right: '24px',
                    zIndex: '99999',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '10px',
                    pointerEvents: 'none'
                });
                document.body.appendChild(toastContainer);
            }

            const toast = document.createElement('div');
            Object.assign(toast.style, {
                minWidth: '240px',
                maxWidth: '420px',
                padding: '12px 18px',
                borderRadius: '8px',
                fontSize: '14px',
                fontWeight: '500',
                lineHeight: '1.4',
                boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1)',
                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                opacity: '0',
                transform: 'translateY(16px)',
                pointerEvents: 'auto',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
            });

            // 依類型指定配色
            if (type === 'success') {
                toast.style.backgroundColor = '#10b981';
                toast.style.color = '#ffffff';
            } else if (type === 'warning') {
                toast.style.backgroundColor = '#f59e0b';
                toast.style.color = '#ffffff';
            } else if (type === 'error') {
                toast.style.backgroundColor = '#ef4444';
                toast.style.color = '#ffffff';
            } else {
                toast.style.backgroundColor = '#1f2937';
                toast.style.color = '#ffffff';
            }

            toast.textContent = message;
            toastContainer.appendChild(toast);

            // 動態進場
            requestAnimationFrame(() => {
                toast.style.opacity = '1';
                toast.style.transform = 'translateY(0)';
            });

            // 3.5 秒後淡出並移除
            setTimeout(() => {
                toast.style.opacity = '0';
                toast.style.transform = 'translateY(16px)';
                setTimeout(() => {
                    if (toast.parentNode) {
                        toast.parentNode.removeChild(toast);
                    }
                }, 300);
            }, 3500);
        }
    }

    // 匯出至全域環境 (或 ES 模組)
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = OfflineSyncManager;
    } else {
        global.OfflineSyncManager = OfflineSyncManager;
    }

})(typeof window !== 'undefined' ? window : this);
