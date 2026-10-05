import pytesseract
from pytesseract import Output
from tkinter import filedialog
from io import BytesIO
from openpyxl.drawing.image import Image as OpenpyxlImage
import tkinter as tk
from tkinter import ttk, messagebox
import openpyxl
from openpyxl.drawing.image import Image as OpenpyxlImage
from openpyxl.drawing.spreadsheet_drawing import AnchorMarker, OneCellAnchor
from openpyxl.drawing.xdr import XDRPositiveSize2D
from openpyxl.utils.units import pixels_to_EMU
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.cell.rich_text import TextBlock, CellRichText
from openpyxl.cell.text import InlineFont
import os
import re
import glob
import json
import csv
import webbrowser
from datetime import datetime, timedelta, date
from openpyxl.utils import get_column_letter
import calendar
import qrcode
from PIL import Image as PILImage, Image
from io import BytesIO
from copy import copy


# ================= OCR 三重引擎：Gemini 2.0 Flash + GCP Vision + Tesseract =================

KEY_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gcp_keys")
GEMINI_KEYS_FILE = os.path.join(KEY_DIR, "gemini_keys.json")
GCP_TRACKER_FILE = os.path.join(KEY_DIR, "usage_tracker.json")


def _load_gemini_keys():
    if not os.path.exists(GEMINI_KEYS_FILE):
        return []
    try:
        with open(GEMINI_KEYS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []


def _save_gemini_keys(keys_data):
    os.makedirs(KEY_DIR, exist_ok=True)
    with open(GEMINI_KEYS_FILE, 'w', encoding='utf-8') as f:
        json.dump(keys_data, f, indent=4, ensure_ascii=False)


def get_gemini_ocr_text(img_pil):
    """優先使用 Gemini 2.0 Flash（最新模型）解析圖片批號，自動輪替 Key"""
    try:
        import google.generativeai as genai
    except ImportError:
        return None

    keys_data = _load_gemini_keys()
    if not keys_data:
        return None

    current_day = datetime.now().strftime("%Y-%m-%d")
    selected = None
    for entry in keys_data:
        if entry.get("day") != current_day:
            entry["day"] = current_day
            entry["count"] = 0
        if entry.get("count", 0) < 1500:
            selected = entry
            break

    if not selected:
        print("⚠️ 所有 Gemini Key 皆已達每日 1500 次上限，退回備援引擎。")
        return None

    try:
        genai.configure(api_key=selected["key"])

        img_byte_arr = BytesIO()
        img_pil.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        import PIL.Image
        pil_img = PIL.Image.open(img_byte_arr)
        
        prompt = (
            "請只回報這張圖片中你看到的所有批號數字（Batch ID），"
            "格式通常是6位以上純數字。多個批號請用逗號分隔。"
            "不要說明、不要解釋，只輸出數字。"
        )

        # 多工自動降級：嘗試最新的模型，失敗則往下一個版本找
        models_to_try = [
            "gemini-3.8-flash",
            "gemini-3.7-flash",
            "gemini-3.6-flash",
            "gemini-3.5-flash",
            "gemini-3.0-flash",
            "gemini-2.5-flash",
            "gemini-2.0-flash"
        ]

        response_text = None
        for model_name in models_to_try:
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content([prompt, pil_img])
                if response.text:
                    response_text = response.text.strip()
                    print(f"✅ 成功使用 {model_name} 解析")
                    break
            except Exception as model_e:
                print(f"⚠️ {model_name} 呼叫失敗，嘗試下一個版本...")
                continue
                
        if response_text is None:
            raise Exception("所有 Gemini 模型版本皆呼叫失敗。")

        selected["count"] = selected.get("count", 0) + 1
        _save_gemini_keys(keys_data)
        return response_text
    except Exception as e:
        print(f"Gemini API 整體發生錯誤: {e}")
        return None


def get_gcp_vision_text(img_pil):
    """使用 GCP Cloud Vision 解析，自動輪替 JSON Key"""
    try:
        from google.oauth2 import service_account
        from google.cloud import vision
    except ImportError:
        return None

    os.makedirs(KEY_DIR, exist_ok=True)
    keys = [f for f in os.listdir(KEY_DIR) if f.endswith('.json')
            and f not in ("usage_tracker.json", "gemini_keys.json", "engine_config.json")]
    if not keys:
        return None

    tracker = {}
    if os.path.exists(GCP_TRACKER_FILE):
        try:
            with open(GCP_TRACKER_FILE, 'r', encoding='utf-8') as f:
                tracker = json.load(f)
        except:
            pass

    current_month = datetime.now().strftime("%Y-%m")
    selected_key = None
    for key in keys:
        data = tracker.get(key, {"month": current_month, "count": 0})
        if data["month"] != current_month:
            data = {"month": current_month, "count": 0}
        if data["count"] < 1000:
            selected_key = key
            tracker[key] = data
            break

    if not selected_key:
        print("⚠️ 所有 GCP Vision Key 皆已達每月 1000 次上限。")
        return None

    try:
        credentials = service_account.Credentials.from_service_account_file(
            os.path.join(KEY_DIR, selected_key))
        client = vision.ImageAnnotatorClient(credentials=credentials)
        img_byte_arr = BytesIO()
        img_pil.save(img_byte_arr, format='PNG')
        image = vision.Image(content=img_byte_arr.getvalue())
        response = client.text_detection(image=image)
        if response.error.message:
            raise Exception(response.error.message)
        tracker[selected_key]["count"] += 1
        with open(GCP_TRACKER_FILE, 'w', encoding='utf-8') as f:
            json.dump(tracker, f, indent=4)
        texts = response.text_annotations
        return texts[0].description if texts else ""
    except Exception as e:
        print(f"GCP Vision 錯誤 ({selected_key}): {e}")
        return None


def _get_engine_mode():
    cfg_path = os.path.join(KEY_DIR, "engine_config.json")
    try:
        with open(cfg_path, 'r', encoding='utf-8') as f:
            return json.load(f).get("engine", "gemini")
    except:
        return "gemini"


def get_ocr_text(img_pil, engine_mode="gemini"):
    """
    統一 OCR 入口（三重保險）：
      gemini    → Gemini 2.0 Flash → GCP Vision → Tesseract
      gcp       → GCP Vision → Tesseract
      tesseract → 直接 Tesseract
    """
    if engine_mode == "gemini":
        text = get_gemini_ocr_text(img_pil)
        if text is None:
            text = get_gcp_vision_text(img_pil)
        return text
    elif engine_mode == "gcp":
        return get_gcp_vision_text(img_pil)
    else:
        return None


# ================= OCR 引擎金鑰管理介面（雙引擎切換）=================
from tkinter import ttk


class OcrKeyManagerDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("🤖 AI OCR 引擎設定")
        self.geometry("600x560")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.key_dir = KEY_DIR
        os.makedirs(self.key_dir, exist_ok=True)

        # ---- 引擎選擇 ----
        engine_frame = tk.LabelFrame(self, text="OCR 引擎優先順序（選好後按儲存）",
                                     font=("Microsoft JhengHei", 9, "bold"), padx=10, pady=5)
        engine_frame.pack(fill="x", padx=15, pady=(10, 5))

        cfg = self._load_engine_config()
        self.engine_var = tk.StringVar(value=cfg.get("engine", "gemini"))
        tk.Radiobutton(engine_frame, text="⚡ Gemini 2.0 Flash（免費、無需信用卡，最推薦）",
                       variable=self.engine_var, value="gemini",
                       font=("Microsoft JhengHei", 9)).pack(anchor="w")
        tk.Radiobutton(engine_frame, text="🔬 GCP Cloud Vision（最高精度 OCR，需 GCP 帳號）",
                       variable=self.engine_var, value="gcp",
                       font=("Microsoft JhengHei", 9)).pack(anchor="w")
        tk.Radiobutton(engine_frame, text="📴 僅 Tesseract 本機（完全離線，精度較低）",
                       variable=self.engine_var, value="tesseract",
                       font=("Microsoft JhengHei", 9)).pack(anchor="w")
        tk.Button(engine_frame, text="💾 儲存引擎選擇", command=self._save_engine,
                  bg="#1565C0", fg="white", font=("Microsoft JhengHei", 9)).pack(anchor="e", pady=(5, 0))

        # ---- Gemini Key 區 ----
        g_frame = tk.LabelFrame(self, text="Gemini API Keys（可加多把，每日 1500 次自動降級輪替）",
                                font=("Microsoft JhengHei", 9, "bold"), padx=10, pady=5)
        g_frame.pack(fill="both", expand=True, padx=15, pady=5)

        self.gemini_tree = ttk.Treeview(g_frame, columns=("Key", "Usage"), show="headings", height=4)
        self.gemini_tree.heading("Key", text="API Key（前20碼）")
        self.gemini_tree.heading("Usage", text="本月次數")
        self.gemini_tree.column("Key", width=380, anchor="w")
        self.gemini_tree.column("Usage", width=120, anchor="center")
        self.gemini_tree.pack(fill="x")
        self._refresh_gemini()

        g_btn = tk.Frame(g_frame)
        g_btn.pack(fill="x", pady=(3, 0))
        tk.Label(g_btn, text="貼上 Gemini API Key：", font=("Microsoft JhengHei", 9)).pack(side="left")
        self.gemini_entry = tk.Entry(g_btn, width=36, font=("Consolas", 9), show="*")
        self.gemini_entry.pack(side="left", padx=5)
        tk.Button(g_btn, text="➕ 新增", bg="#4CAF50", fg="white",
                  font=("Microsoft JhengHei", 9), command=self._add_gemini_key).pack(side="left")
        tk.Button(g_btn, text="🗑️ 刪除", bg="#E53935", fg="white",
                  font=("Microsoft JhengHei", 9), command=self._del_gemini_key).pack(side="left", padx=5)

        # ---- GCP Key 區 ----
        v_frame = tk.LabelFrame(self, text="GCP Cloud Vision Keys（每月 1000 次，貼上 JSON 自動輪替）",
                                font=("Microsoft JhengHei", 9, "bold"), padx=10, pady=5)
        v_frame.pack(fill="both", expand=True, padx=15, pady=5)

        self.gcp_tree = ttk.Treeview(v_frame, columns=("File", "Usage"), show="headings", height=3)
        self.gcp_tree.heading("File", text="金鑰檔名")
        self.gcp_tree.heading("Usage", text="本月次數")
        self.gcp_tree.column("File", width=380, anchor="w")
        self.gcp_tree.column("Usage", width=120, anchor="center")
        self.gcp_tree.pack(fill="x")
        self._refresh_gcp()

        v_btn = tk.Frame(v_frame)
        v_btn.pack(fill="x", pady=(3, 0))
        tk.Button(v_btn, text="📋 貼上 JSON 新增", bg="#4CAF50", fg="white",
                  font=("Microsoft JhengHei", 9), command=self._add_gcp_key_dialog).pack(side="left")
        tk.Button(v_btn, text="🗑️ 刪除", bg="#E53935", fg="white",
                  font=("Microsoft JhengHei", 9), command=self._del_gcp_key).pack(side="left", padx=5)

        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

    def _load_engine_config(self):
        p = os.path.join(KEY_DIR, "engine_config.json")
        try:
            with open(p, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"engine": "gemini"}

    def _save_engine(self):
        p = os.path.join(KEY_DIR, "engine_config.json")
        os.makedirs(KEY_DIR, exist_ok=True)
        with open(p, 'w', encoding='utf-8') as f:
            json.dump({"engine": self.engine_var.get()}, f)
        label = {"gemini": "Gemini 2.0 Flash", "gcp": "GCP Cloud Vision", "tesseract": "本機 Tesseract"}
        messagebox.showinfo("已儲存", f"OCR 引擎已切換為：{label.get(self.engine_var.get())}")

    def _refresh_gemini(self):
        for item in self.gemini_tree.get_children():
            self.gemini_tree.delete(item)
        current_day = datetime.now().strftime("%Y-%m-%d")
        for entry in _load_gemini_keys():
            usage = entry.get("count", 0) if entry.get("day") == current_day else 0
            self.gemini_tree.insert("", "end", values=(entry["key"][:20] + "...", f"{usage} / 1500"))

    def _add_gemini_key(self):
        key = self.gemini_entry.get().strip()
        if not key:
            return
        if not (key.startswith("AIza") or key.startswith("AQ.")):
            if not messagebox.askyesno("格式確認", "這把 Key 看起來不像標準的 Gemini Key (不是 AIza 或 AQ. 開頭)，確定要儲存嗎？"):
                return
        keys_data = _load_gemini_keys()
        if any(e["key"] == key for e in keys_data):
            messagebox.showinfo("重複", "這把 Key 已存在！")
            return
        keys_data.append({"key": key, "day": datetime.now().strftime("%Y-%m-%d"), "count": 0})
        _save_gemini_keys(keys_data)
        self.gemini_entry.delete(0, tk.END)
        self._refresh_gemini()
        messagebox.showinfo("成功", "Gemini API Key 已新增並啟用！")

    def _del_gemini_key(self):
        sel = self.gemini_tree.selection()
        if not sel:
            return
        idx = self.gemini_tree.index(sel[0])
        keys_data = _load_gemini_keys()
        if 0 <= idx < len(keys_data):
            if messagebox.askyesno("確認", "確定要刪除這把 Gemini Key？"):
                keys_data.pop(idx)
                _save_gemini_keys(keys_data)
                self._refresh_gemini()

    def _refresh_gcp(self):
        for item in self.gcp_tree.get_children():
            self.gcp_tree.delete(item)
        tracker = {}
        if os.path.exists(GCP_TRACKER_FILE):
            try:
                with open(GCP_TRACKER_FILE, 'r', encoding='utf-8') as f:
                    tracker = json.load(f)
            except:
                pass
        current_month = datetime.now().strftime("%Y-%m")
        for f_name in os.listdir(self.key_dir):
            if f_name.endswith(".json") and f_name not in ("usage_tracker.json", "gemini_keys.json", "engine_config.json"):
                data = tracker.get(f_name, {"month": current_month, "count": 0})
                usage = data["count"] if data["month"] == current_month else 0
                self.gcp_tree.insert("", "end", values=(f_name, f"{usage} / 1000"))

    def _add_gcp_key_dialog(self):
        dlg = tk.Toplevel(self)
        dlg.title("貼上 GCP JSON 金鑰")
        dlg.geometry("500x340")
        dlg.transient(self)
        dlg.grab_set()
        tk.Label(dlg, text="請貼上 GCP Service Account JSON 內容：",
                 font=("Microsoft JhengHei", 10)).pack(pady=8)
        txt = tk.Text(dlg, height=12, width=58, font=("Consolas", 9))
        txt.pack(padx=10)

        def do_save():
            content = txt.get("1.0", tk.END).strip()
            try:
                d = json.loads(content)
                if "project_id" not in d or "private_key" not in d:
                    raise ValueError("缺少 project_id 或 private_key")
                import uuid
                fname = f"gcp_key_{uuid.uuid4().hex[:6]}.json"
                with open(os.path.join(self.key_dir, fname), "w", encoding="utf-8") as f:
                    f.write(content)
                self._refresh_gcp()
                messagebox.showinfo("成功", f"已儲存並啟用 {fname}")
                dlg.destroy()
            except Exception as e:
                messagebox.showerror("錯誤", f"JSON 格式不正確：{e}")

        tk.Button(dlg, text="💾 儲存並啟用", bg="#4CAF50", fg="white",
                  font=("Microsoft JhengHei", 10, "bold"), command=do_save).pack(pady=10)

    def _del_gcp_key(self):
        sel = self.gcp_tree.selection()
        if not sel:
            return
        f_name = self.gcp_tree.item(sel[0])['values'][0]
        if messagebox.askyesno("確認", f"確定要刪除 {f_name}？"):
            try:
                os.remove(os.path.join(self.key_dir, f_name))
                self._refresh_gcp()
            except Exception as e:
                messagebox.showerror("錯誤", str(e))


class CalendarDialog(tk.Toplevel):
    def __init__(self, parent, target_var):
        super().__init__(parent)
        self.title("選擇日期")
        self.resizable(False, False)
        self.target_var = target_var
        self.transient(parent)
        self.grab_set()

        now = datetime.now()
        self.year = now.year
        self.month = now.month

        val = target_var.get().strip()
        if val:
            for fmt in ("%Y/%m/%d", "%Y-%m-%d", "%Y/%M/%d", "%Y.%m.%d"):
                try:
                    dt = datetime.strptime(val, fmt)
                    self.year = dt.year
                    self.month = dt.month
                    break
                except ValueError:
                    pass

        try:
            x = parent.winfo_pointerx()
            y = parent.winfo_pointery()
            self.geometry(f"+{x}+{y}")
        except Exception:
            pass

        self.setup_ui()
        
    def setup_ui(self):
        header = tk.Frame(self, pady=5, bg="#F5F5F5")
        header.pack(fill="x")
        
        tk.Button(header, text="◄", command=self.prev_month, width=3, relief="groove").pack(side="left", padx=5)
        self.lbl_month = tk.Label(header, text="", font=("Arial", 11, "bold"), bg="#F5F5F5", width=12)
        self.lbl_month.pack(side="left", expand=True)
        tk.Button(header, text="►", command=self.next_month, width=3, relief="groove").pack(side="right", padx=5)

        week_frame = tk.Frame(self, bg="#FFFFFF")
        week_frame.pack(fill="x", padx=5, pady=(5, 0))
        for w in ["一", "二", "三", "四", "五", "六", "日"]:
            fg_col = "#D32F2F" if w in ("六", "日") else "#333333"
            tk.Label(week_frame, text=w, width=4, font=("Arial", 9, "bold"), fg=fg_col, bg="#FFFFFF").pack(side="left")

        self.grid_frame = tk.Frame(self, bg="#FFFFFF", padx=5, pady=5)
        self.grid_frame.pack()
        
        btn_frame = tk.Frame(self, pady=5, bg="#F5F5F5")
        btn_frame.pack(fill="x")
        tk.Button(btn_frame, text="今天", command=self.select_today, bg="#E3F2FD", relief="groove", font=("Arial", 9)).pack(side="left", padx=5)
        tk.Button(btn_frame, text="明天", command=self.select_tomorrow, bg="#E8F5E9", relief="groove", font=("Arial", 9)).pack(side="left", padx=5)
        tk.Button(btn_frame, text="清除", command=self.clear_date, bg="#FFEBEE", relief="groove", font=("Arial", 9)).pack(side="right", padx=5)
        
        self.render_calendar()

    def render_calendar(self):
        for widget in self.grid_frame.winfo_children():
            widget.destroy()
            
        self.lbl_month.config(text=f"{self.year} 年 {self.month} 月")
        cal = calendar.monthcalendar(self.year, self.month)
        
        for r_idx, week in enumerate(cal):
            for c_idx, day in enumerate(week):
                if day == 0:
                    tk.Label(self.grid_frame, text="", width=4, bg="#FFFFFF").grid(row=r_idx, column=c_idx)
                else:
                    date_str = f"{self.year}/{self.month:02d}/{day:02d}"
                    fg_col = "#D32F2F" if c_idx >= 5 else "#000000"
                    btn = tk.Button(
                        self.grid_frame, 
                        text=str(day), 
                        width=4, 
                        bg="#F9F9F9",
                        fg=fg_col,
                        relief="flat",
                        command=lambda d=date_str: self.set_date(d)
                    )
                    btn.grid(row=r_idx, column=c_idx, padx=1, pady=1)

    def prev_month(self):
        if self.month == 1:
            self.month = 12
            self.year -= 1
        else:
            self.month -= 1
        self.render_calendar()

    def next_month(self):
        if self.month == 12:
            self.month = 1
            self.year += 1
        else:
            self.month += 1
        self.render_calendar()

    def select_today(self):
        t = datetime.now()
        self.set_date(f"{t.year}/{t.month:02d}/{t.day:02d}")

    def select_tomorrow(self):
        t = datetime.now() + timedelta(days=1)
        self.set_date(f"{t.year}/{t.month:02d}/{t.day:02d}")

    def clear_date(self):
        self.target_var.set("")
        self.destroy()

    def set_date(self, date_str):
        self.target_var.set(date_str)
        self.destroy()

def split_date_and_time(raw_val):
    """
    將 Excel / 貼上讀取的 datetime 或日期時間字串拆分為 (純日期, 純時間)
    例如:
    - datetime.datetime(2026, 8, 14, 0, 0) -> ("2026-08-14", "")
    - "2026-08-14 00:00:00" -> ("2026-08-14", "")
    - "2026-08-14 08:30:00" -> ("2026-08-14", "08:30")
    """
    if raw_val is None:
        return "", ""
    
    if isinstance(raw_val, datetime):
        d_str = f"{raw_val.year:04d}-{raw_val.month:02d}-{raw_val.day:02d}"
        if raw_val.hour == 0 and raw_val.minute == 0 and raw_val.second == 0:
            t_str = ""
        else:
            t_str = f"{raw_val.hour:02d}:{raw_val.minute:02d}"
        return d_str, t_str

    val_str = str(raw_val).strip()
    if not val_str:
        return "", ""

    parts = val_str.split()
    if len(parts) >= 2:
        d_part = parts[0]
        t_part = parts[1]
        if t_part in ("00:00:00", "00:00", "0:00", "00:00:00.000"):
            return d_part, ""
        else:
            t_sub = t_part.split(':')
            if len(t_sub) >= 2:
                return d_part, f"{t_sub[0]:0>2}:{t_sub[1]:0>2}"
            return d_part, t_part

    return val_str, ""

def normalize_time_str(raw):
    """
    將各種時間格式 (如 09:00, 9:00, 09:00:00, Sat Dec 30 1899 09:00:00, 0.375, 900)
    一律精準轉換為 4 碼時間 (如 '0900', '1400')，絕不夾帶日期或星期文字。
    """
    if raw is None or raw == "":
        return ""
    if hasattr(raw, "hour") and hasattr(raw, "minute"):
        return f"{raw.hour:02d}{raw.minute:02d}"
    s = str(raw).strip()
    if not s:
        return ""
    try:
        f = float(s)
        if 0 < f < 1:
            total_minutes = round(f * 24 * 60)
            h = (total_minutes // 60) % 24
            m = total_minutes % 60
            return f"{h:02d}{m:02d}"
        if 0 <= f < 2400 and len(s) in (3, 4) and s.isdigit():
            return s.zfill(4)
    except ValueError:
        pass
    m = re.search(r'(\d{1,2}):(\d{2})', s)
    if m:
        return f"{int(m.group(1)):02d}{int(m.group(2)):02d}"
    if len(s) == 4 and s.isdigit():
        return s
    if len(s) == 3 and s.isdigit():
        return "0" + s
    return ""

def normalize_date_str(raw):
    if not raw:
        return ""
    if hasattr(raw, "strftime"):
        return raw.strftime("%Y-%m-%d")
    s = str(raw).strip()
    if not s:
        return ""
    try:
        f = float(s)
        if 20000 < f < 60000:
            dt = datetime(1899, 12, 30) + timedelta(days=int(f))
            return dt.strftime("%Y-%m-%d")
    except ValueError:
        pass
    s_part = s.split()[0]
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%Y%m%d", "%m/%d/%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(s_part, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    m = re.match(r"^(\d{2,3})[-/\.](\d{1,2})[-/\.](\d{1,2})", s_part)
    if m and int(m.group(1)) < 1900:
        y = int(m.group(1)) + 1911
        m_val = int(m.group(2))
        d_val = int(m.group(3))
        return f"{y:04d}-{m_val:02d}-{d_val:02d}"
    return s_part

def clean_location_str(loc, mapping_dict=None):
    if not loc:
        return ""
    s = str(loc).strip().upper()
    cleaned = re.sub(r'台積電?|新竹|台中|台南|廠|[-_\s]', '', s)
    if mapping_dict and cleaned in mapping_dict:
        return cleaned
    if mapping_dict and s in mapping_dict:
        return s
    m_ap = re.search(r'(AP\d+[A-Z0-9]*)', s)
    if m_ap:
        return m_ap.group(1)
    m_loc = re.search(r'(\d+[A-Z]\d+[A-Z0-9]*|\d+[A-Z0-9]+)', s)
    if m_loc:
        val = m_loc.group(1)
        if (mapping_dict and val in mapping_dict) or any(x in val for x in ["18P", "15P", "12P", "14P"]):
            return val
    return cleaned or s

class ImportRangeDialog(tk.Toplevel):
    """
    Excel 匯入筆數與範圍選擇對話框 (支援全分頁跨頁統計、今天~後天智慧過濾與倒數擷取)
    """
    def __init__(self, parent, records, filename="", sheet_count=1):
        super().__init__(parent)
        self.parent_app = parent
        self.title("📥 Excel 匯入筆數與範圍選擇 (跨分頁智慧過濾)")
        self.geometry("1080x700")
        self.minsize(920, 560)
        self.grab_set()

        # 視窗居中於父視窗
        try:
            self.update_idletasks()
            pw = parent.winfo_width()
            ph = parent.winfo_height()
            px = parent.winfo_rootx()
            py = parent.winfo_rooty()
            w, h = 1080, 700
            x = max(20, px + (pw - w) // 2)
            y = max(20, py + (ph - h) // 2)
            self.geometry(f"{w}x{h}+{x}+{y}")
        except Exception:
            pass

        self.all_records = records
        self.all_records.sort(key=lambda x: (x.get("date", ""), x.get("time", "")))
        self.sheet_count = max(1, sheet_count)
        self.total_records_count = len(records)
        self.selected_records = None

        # 計算 今天、明天、後天 日期
        today = datetime.now().date()
        self.d0 = today.strftime("%Y-%m-%d")
        self.d1 = (today + timedelta(days=1)).strftime("%Y-%m-%d")
        self.d2 = (today + timedelta(days=2)).strftime("%Y-%m-%d")
        self.d0_d2 = [self.d0, self.d1, self.d2]

        # 預設過濾邏輯：優先過濾「今天~後天 (3天)」
        window_matches = [r for r in self.all_records if r.get("date") in self.d0_d2]
        if window_matches:
            self.current_filtered_records = window_matches
            self.active_mode = "d0_d2"
            self.summary_text = f"已優先過濾「今天~後天 ({self.d0} ~ {self.d2})」共 {len(window_matches)} 筆 (全 {self.sheet_count} 個分頁總計 {self.total_records_count} 筆)"
        else:
            self.current_filtered_records = list(self.all_records)
            self.active_mode = "all"
            self.summary_text = f"全 {self.sheet_count} 個分頁總計 {self.total_records_count} 筆排程 (無今天~後天資料，顯示全部)"

        self.count_var = tk.IntVar(value=len(self.current_filtered_records) if len(self.current_filtered_records) <= 10 else 10)
        self.info_var = tk.StringVar(value=self.summary_text)

        self.date_btns = {}
        self.setup_ui(filename)
        self.update_preview()

    def setup_ui(self, filename):
        # 頂部提示資訊
        info_frame = tk.LabelFrame(self, text="檔案偵測結果", font=("Arial", 10, "bold"), padx=10, pady=8, fg="#002060")
        info_frame.pack(fill="x", pady=(0, 10))

        tk.Label(info_frame, text=f"📄 檔案名稱：{filename}", font=("Arial", 10, "bold")).pack(anchor="w")
        lbl_sum = tk.Label(info_frame, textvariable=self.info_var, fg="#2E7D32", font=("Arial", 10, "bold"), wraplength=1020, justify="left")
        lbl_sum.pack(anchor="w", pady=(2, 0))

        # 篩選控制區
        ctrl_frame = tk.LabelFrame(self, text="🎯 篩選與筆數設定（支援日期過濾與倒數擷取）", font=("Arial", 10, "bold"), padx=10, pady=8, fg="#C00000")
        ctrl_frame.pack(fill="x", pady=(0, 10))

        # 1. 篩選日期按鈕列
        date_bar = tk.Frame(ctrl_frame)
        date_bar.pack(fill="x", pady=(0, 6))

        tk.Label(date_bar, text="篩選日期：", font=("Arial", 10, "bold")).pack(side="left")

        btn_3days = tk.Button(
            date_bar, 
            text="📅 優先抓今天~後天 (3天)", 
            command=lambda: self.filter_by_date_mode("d0_d2"), 
            font=("Arial", 9, "bold"), 
            padx=8, 
            cursor="hand2"
        )
        btn_3days.pack(side="left", padx=3)
        self.date_btns["d0_d2"] = btn_3days

        btn_d0 = tk.Button(
            date_bar, 
            text="今天", 
            command=lambda: self.filter_by_date_mode("d0"), 
            font=("Arial", 9, "bold"), 
            padx=8, 
            cursor="hand2"
        )
        btn_d0.pack(side="left", padx=3)
        self.date_btns["d0"] = btn_d0

        btn_d1 = tk.Button(
            date_bar, 
            text="明天", 
            command=lambda: self.filter_by_date_mode("d1"), 
            font=("Arial", 9, "bold"), 
            padx=8, 
            cursor="hand2"
        )
        btn_d1.pack(side="left", padx=3)
        self.date_btns["d1"] = btn_d1

        btn_d2 = tk.Button(
            date_bar, 
            text="後天", 
            command=lambda: self.filter_by_date_mode("d2"), 
            font=("Arial", 9, "bold"), 
            padx=8, 
            cursor="hand2"
        )
        btn_d2.pack(side="left", padx=3)
        self.date_btns["d2"] = btn_d2

        btn_all_date = tk.Button(
            date_bar, 
            text="全部日期", 
            command=lambda: self.filter_by_date_mode("all"), 
            font=("Arial", 9, "bold"), 
            padx=8, 
            cursor="hand2"
        )
        btn_all_date.pack(side="left", padx=3)
        self.date_btns["all"] = btn_all_date

        self.refresh_date_buttons()

        # 2. 筆數快速按鈕列
        count_bar = tk.Frame(ctrl_frame)
        count_bar.pack(fill="x")

        tk.Label(count_bar, text="選擇筆數：", font=("Arial", 10, "bold")).pack(side="left")

        for num, text in [(5, "5 筆"), (10, "10 筆"), (20, "20 筆"), ("all", "全部")]:
            tk.Button(
                count_bar, 
                text=text, 
                command=lambda n=num: self.set_count(n), 
                font=("Arial", 9, "bold"), 
                bg="#E3F2FD", 
                fg="#0D47A1", 
                padx=6, 
                cursor="hand2"
            ).pack(side="left", padx=3)

        tk.Label(count_bar, text="自訂筆數：", font=("Arial", 9)).pack(side="left", padx=(10, 0))
        self.spin = tk.Spinbox(count_bar, from_=1, to=max(1, len(self.current_filtered_records)), textvariable=self.count_var, width=6, command=self.update_preview, font=("Arial", 10, "bold"))
        self.spin.pack(side="left", padx=5)
        self.spin.bind("<KeyRelease>", lambda e: self.update_preview())
        tk.Label(count_bar, text="筆", font=("Arial", 9)).pack(side="left")

        # 預覽表格區 (採用專業 Treeview 多欄呈現，欄寬自由拖拉，全資料完整展示)
        preview_frame = tk.LabelFrame(self, text="📋 即將匯入資料即時預覽 (欄寬可自由拉動，全欄位完整呈現)", font=("Arial", 10, "bold"), padx=6, pady=6, fg="#002060")
        preview_frame.pack(fill="both", expand=True, pady=(0, 10))

        # 定義 Treeview 欄位
        columns = ("chk", "idx", "sheet", "date", "batch", "loc", "long_code")
        self.tree = ttk.Treeview(preview_frame, columns=columns, show="headings", selectmode="none")

        col_defs = [
            ("chk", "✅選取", 50, "center"),
            ("idx", "項次", 50, "center"),
            ("sheet", "來源分頁", 150, "w"),
            ("date", "出貨日期 📅", 105, "center"),
            ("batch", "批號 (10碼)", 125, "center"),
            ("loc", "指送地點", 95, "center"),
            ("long_code", "地點長代號 (全稱)", 250, "w")
        ]

        for col_id, heading_text, width, anchor in col_defs:
            self.tree.heading(col_id, text=heading_text, anchor=anchor)
            self.tree.column(col_id, width=width, minwidth=40, anchor=anchor, stretch=True)

        scroll_y = ttk.Scrollbar(preview_frame, orient="vertical", command=self.tree.yview)
        scroll_x = ttk.Scrollbar(preview_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")
        self.tree.pack(side="left", fill="both", expand=True)

        # 斑馬紋樣式設定
        self.tree.tag_configure("evenrow", background="#FFFFFF")
        self.tree.tag_configure("oddrow", background="#F2F7FA")
        self.tree.bind("<ButtonRelease-1>", self.on_tree_click)

        # 底部確定按鈕區
        action_frame = tk.Frame(self)
        action_frame.pack(fill="x")

        self.btn_confirm = tk.Button(
            action_frame, 
            text="🚀 確認匯入資料", 
            command=self.confirm_import, 
            bg="#4CAF50", 
            fg="white", 
            font=("Arial", 11, "bold"), 
            pady=7,
            cursor="hand2"
        )
        self.btn_confirm.pack(side="left", fill="x", expand=True, padx=(0, 5))

        tk.Button(
            action_frame, 
            text="❌ 取消", 
            command=self.destroy, 
            bg="#9E9E9E", 
            fg="white", 
            font=("Arial", 10), 
            pady=7,
            width=10,
            cursor="hand2"
        ).pack(side="right", padx=5)

    def refresh_date_buttons(self):
        for mode, btn in self.date_btns.items():
            if mode == self.active_mode:
                if mode == "d0_d2":
                    btn.config(bg="#FF9800", fg="white")
                elif mode == "all":
                    btn.config(bg="#7B1FA2", fg="white")
                else:
                    btn.config(bg="#1976D2", fg="white")
            else:
                btn.config(bg="#EEEEEE", fg="#424242")

    def filter_by_date_mode(self, mode):
        if mode == "d0_d2":
            filtered = [r for r in self.all_records if r.get("date") in self.d0_d2]
            label = f"「今天~後天 ({self.d0} ~ {self.d2})」"
        elif mode == "d0":
            filtered = [r for r in self.all_records if r.get("date") == self.d0]
            label = f"「今天 ({self.d0})」"
        elif mode == "d1":
            filtered = [r for r in self.all_records if r.get("date") == self.d1]
            label = f"「明天 ({self.d1})」"
        elif mode == "d2":
            filtered = [r for r in self.all_records if r.get("date") == self.d2]
            label = f"「後天 ({self.d2})」"
        else:
            filtered = list(self.all_records)
            label = "「全部日期」"
            
        filtered.sort(key=lambda x: (x.get("date", ""), x.get("time", "")))

        if not filtered:
            messagebox.showinfo("無排程資料", f"在所有 {self.sheet_count} 個分頁中，找不到符合 {label} 的出貨排程！")
            return

        self.active_mode = mode
        self.current_filtered_records = filtered
        self.refresh_date_buttons()
        self.info_var.set(f"已篩選 {label} 共 {len(filtered)} 筆 (全 {self.sheet_count} 個分頁總計 {self.total_records_count} 筆)")
        
        self.spin.config(to=max(1, len(filtered)))
        self.count_var.set(len(filtered))
        self.update_preview()

    def set_count(self, num):
        if num == "all":
            self.count_var.set(len(self.current_filtered_records))
        else:
            self.count_var.set(min(int(num), len(self.current_filtered_records)))
        self.update_preview()

    def update_preview(self):
        total = len(self.current_filtered_records)
        try:
            cnt = self.count_var.get()
        except Exception:
            cnt = 1
        cnt = max(1, min(cnt, total))
        self.count_var.set(cnt)

        slice_records = self.current_filtered_records[-cnt:]

        # 清空 Treeview
        for item in self.tree.get_children():
            self.tree.delete(item)

        for idx, rec in enumerate(slice_records):
            sheet_name = rec.get("sheet", "分頁")
            d_str = rec.get("date") or ""
            t_str = rec.get("time") or ""
            b_str = rec.get("batch") or ""
            tank_str = rec.get("tank") or ""
            loc_str = rec.get("loc") or ""
            origin_str = rec.get("origin") or ""
            _md = getattr(self.parent_app, 'mapping_dict', {}).get(loc_str, [])
            _md = _md[0] if isinstance(_md, list) and _md else (_md if isinstance(_md, str) else '')
            long_code_str = rec.get('long_code') or _md

            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            self.tree.insert(
                "",
                "end",
                values=(
                    "☑",
                    f"[{idx+1:02d}]",
                    sheet_name,
                    d_str,
                    b_str,
                    loc_str,
                    long_code_str
                ),
                tags=(tag,)
            )

        self.btn_confirm.config(text=f"🚀 確認由下往上擷取最新的 {cnt} 筆匯入系統")

    def on_tree_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell":
            column = self.tree.identify_column(event.x)
            if column == "#1":
                item_id = self.tree.identify_row(event.y)
                if item_id:
                    vals = list(self.tree.item(item_id, "values"))
                    vals[0] = "☐" if vals[0] == "☑" else "☑"
                    self.tree.item(item_id, values=vals)
                    
                    checked = sum(1 for item in self.tree.get_children() if self.tree.item(item, "values")[0] == "☑")
                    self.btn_confirm.config(text=f"🚀 確認將這 {checked} 筆匯入系統")

    def confirm_import(self):
        cnt = self.count_var.get()
        cnt = max(1, min(cnt, len(self.current_filtered_records)))
        slice_records = self.current_filtered_records[-cnt:]
        
        selected_recs = []
        for idx, item in enumerate(self.tree.get_children()):
            vals = self.tree.item(item, "values")
            if vals[0] == "☑" and idx < len(slice_records):
                selected_recs.append(slice_records[idx])
                
        self.selected_records = selected_recs
        self.destroy()

# ================= 核心邏輯 =================

def get_tank_from_batch(batch):
    batch = batch.strip()
    if not batch:
        return ""
    if len(batch) != 10:
        return "長度錯誤"
    if batch.endswith('J1'):
        return batch[5:8]
    return batch[5:9]

def find_row_by_label(ws, labels):
    for r in range(1, 20):
        val = ws.cell(row=r, column=2).value
        if val and isinstance(val, str):
            for label in labels:
                if label in val:
                    return r
    return None

def generate_transport_notice_file(output_path, items, mat_no=""):
    is_append = os.path.exists(output_path)
    if is_append:
        wb = openpyxl.load_workbook(output_path)
        ws = wb.active
    else:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "運輸通知表"
        ws.views.sheetView[0].showGridLines = True
        
        # 欄寬設定 (Left Card: A~F, Spacer: G, Right Card: H~M)
        col_widths = {
            'A': 8, 'B': 18, 'C': 18, 'D': 16, 'E': 14, 'F': 16,
            'G': 4,
            'H': 8, 'I': 18, 'J': 18, 'K': 16, 'L': 14, 'M': 16
        }
        for col, width in col_widths.items():
            ws.column_dimensions[col].width = width
        
    thin_border = Border(
        left=Side(style='thin', color='000000'),
        right=Side(style='thin', color='000000'),
        top=Side(style='thin', color='000000'),
        bottom=Side(style='thin', color='000000')
    )
    
    fill_yellow = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
    fill_green = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")
    fill_bright_yellow = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")
    
    openpyxl_font_dark_blue = Font(name="Microsoft JhengHei", color="002060", size=11)
    openpyxl_font_dark_blue_b13 = Font(name="Microsoft JhengHei", color="002060", size=13, bold=True)
    openpyxl_font_strike_blue_b13 = Font(name="Microsoft JhengHei", color="002060", size=13, bold=True, strike=True)
    openpyxl_font_red_b13 = Font(name="Microsoft JhengHei", color="C00000", size=13, bold=True)
    openpyxl_font_dark_blue_b14 = Font(name="Microsoft JhengHei", color="002060", size=14, bold=True)
    
    align_center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]

    def render_notice_card(start_r, start_c, is_modified_card, item):
        r1 = start_r
        r2 = start_r + 1
        r3 = start_r + 2
        r4 = start_r + 3
        r5 = start_r + 4
        r6 = start_r + 5
        
        c1 = start_c
        c2 = start_c + 1
        c3 = start_c + 2
        c4 = start_c + 3
        c5 = start_c + 4
        c6 = start_c + 5
        
        for r in range(r1, r6 + 1):
            ws.row_dimensions[r].height = 24 if r >= r3 else 22
            for c in range(c1, c6 + 1):
                cell = ws.cell(row=r, column=c)
                cell.border = thin_border
                cell.font = openpyxl_font_dark_blue
                cell.alignment = align_center

        # --- Title ---
        ws.merge_cells(start_row=r1, start_column=c1, end_row=r2, end_column=c3)
        title_suffix = "出貨排程修正通知" if is_modified_card else "出貨排程通知"
        title_rt = CellRichText([
            TextBlock(InlineFont(color="002060", b=True, sz=12, rFont="Microsoft JhengHei"), "Shiny IPA Lorry\n"),
            TextBlock(InlineFont(color="002060", sz=10, rFont="Microsoft JhengHei"), f"(料號：{mat_no}) {title_suffix}")
        ])
        cell_a1 = ws.cell(row=r1, column=c1)
        cell_a1.value = title_rt
        cell_a1.fill = fill_yellow
        cell_a1.alignment = align_center
        
        cell_d1 = ws.cell(row=r1, column=c4, value="廠區")
        cell_d1.fill = fill_yellow
        cell_d1.font = Font(name="Microsoft JhengHei", color="002060", size=11, bold=True)
        
        cell_e1 = ws.cell(row=r1, column=c5, value="槽號")
        cell_e1.fill = fill_yellow
        cell_e1.font = Font(name="Microsoft JhengHei", color="002060", size=11, bold=True)
        
        date_raw = item.get("date", "").strip()
        formatted_date = ""
        weekday_str = ""
        if date_raw:
            dt = None
            for fmt in ("%Y/%m/%d", "%Y-%m-%d", "%Y/%M/%d", "%Y.%m.%d"):
                try:
                    dt = datetime.strptime(date_raw, fmt)
                    break
                except ValueError:
                    pass
            if dt:
                weekday_str = weekdays[dt.weekday()]
                formatted_date = f"{dt.year}/{dt.month}/{dt.day}"
            else:
                formatted_date = date_raw
        
        cell_f1 = ws.cell(row=r1, column=c6, value=formatted_date)
        cell_f1.fill = fill_green
        cell_f1.font = Font(name="Microsoft JhengHei", color="002060", size=11, bold=True)
        
        cell_f2 = ws.cell(row=r2, column=c6, value=weekday_str)
        cell_f2.fill = fill_green
        cell_f2.font = Font(name="Microsoft JhengHei", color="002060", size=11, bold=True)

        # --- Body ---
        ws.merge_cells(start_row=r3, start_column=c1, end_row=r6, end_column=c1)
        cell_a3 = ws.cell(row=r3, column=c1, value="IPA")
        cell_a3.font = openpyxl_font_dark_blue_b14
        
        time_val = item.get("time", "").strip()
        mod_time_val = item.get("mod_time", "").strip()
        
        ws.merge_cells(start_row=r3, start_column=c2, end_row=r3, end_column=c3)
        ws.cell(row=r3, column=c2, value="預計到廠時間")
        cell_f3 = ws.cell(row=r3, column=c6, value=time_val)
        
        ws.merge_cells(start_row=r4, start_column=c2, end_row=r4, end_column=c3)
        ws.cell(row=r4, column=c2, value="修正到廠時間")
        cell_f4 = ws.cell(row=r4, column=c6)
        
        if is_modified_card:
            cell_f3.font = openpyxl_font_strike_blue_b13
            cell_f4.value = mod_time_val
            cell_f4.font = openpyxl_font_red_b13
        else:
            cell_f3.font = openpyxl_font_dark_blue_b13
            cell_f4.value = ""
        
        ws.merge_cells(start_row=r5, start_column=c2, end_row=r5, end_column=c3)
        ws.cell(row=r5, column=c2, value="充填數量(KG)")
        ws.cell(row=r5, column=c6, value="4300")
        
        ws.merge_cells(start_row=r2, start_column=c4, end_row=r5, end_column=c4)
        full_loc = item.get("loc", "").strip()
        
        d_rt = CellRichText([
            TextBlock(InlineFont(color="002060", b=True, sz=14, rFont="Microsoft JhengHei"), "台積\n"),
            TextBlock(InlineFont(color="C00000", b=True, sz=14, rFont="Microsoft JhengHei"), full_loc)
        ])
        cell_d2 = ws.cell(row=r2, column=c4)
        cell_d2.value = d_rt
        
        ws.merge_cells(start_row=r2, start_column=c5, end_row=r5, end_column=c5)
        cell_e2 = ws.cell(row=r2, column=c5, value=item.get("tank", "").strip())
        cell_e2.font = openpyxl_font_dark_blue_b14
        cell_e2.fill = fill_bright_yellow
        
        ws.merge_cells(start_row=r6, start_column=c2, end_row=r6, end_column=c5)
        cell_b6 = ws.cell(row=r6, column=c2)
        cell_b6.value = CellRichText([
            TextBlock(InlineFont(color="C00000", b=True, sz=11, rFont="Microsoft JhengHei"), "PFA 500ml"),
            TextBlock(InlineFont(color="002060", sz=11, rFont="Microsoft JhengHei"), " 取樣瓶裝原液 8 分滿放置工具箱內")
        ])
        
        cell_f6 = ws.cell(row=r6, column=c6, value="6 支")
        cell_f6.font = Font(name="Microsoft JhengHei", color="002060", size=11, bold=True)

    curr_row = ws.max_row + 2 if is_append and ws.max_row > 1 else 1
    for item in items:
        # 左側：原始出貨排程通知卡片 (Columns A~F)
        render_notice_card(curr_row, 1, False, item)
        
        # 若該筆有輸入「修正到廠時間」，在右側旁 (Columns H~M) 併排產生「出貨排程修正通知」卡片
        if item.get("mod_time", "").strip():
            render_notice_card(curr_row, 8, True, item)
            
        curr_row += 7

    wb.save(output_path)
    wb.close()

def build_single_row_lorry_workbook(src_ws, target_row, max_cols=30):
    new_wb = openpyxl.Workbook()
    new_ws = new_wb.active
    new_ws.title = src_ws.title
    
    # 複製欄寬
    for col_letter, col_dim in src_ws.column_dimensions.items():
        if col_dim.width:
            new_ws.column_dimensions[col_letter].width = col_dim.width
            
    def copy_cell(s_cell, d_cell):
        d_cell.value = s_cell.value
        if s_cell.has_style:
            d_cell.font = copy(s_cell.font)
            d_cell.border = copy(s_cell.border)
            d_cell.fill = copy(s_cell.fill)
            d_cell.number_format = copy(s_cell.number_format)
            d_cell.protection = copy(s_cell.protection)
            d_cell.alignment = copy(s_cell.alignment)

    # 複製列高 (保持第 6 列表頭與資料列原始高度)
    for r in range(1, 8):
        src_r = r if r <= 6 else target_row
        if src_ws.row_dimensions[src_r].height:
            new_ws.row_dimensions[r].height = src_ws.row_dimensions[src_r].height

    # 複製 1~6 列表頭
    for r in range(1, 7):
        for c in range(1, max_cols + 1):
            copy_cell(src_ws.cell(r, c), new_ws.cell(r, c))
            
    # 複製目標資料列至第 7 列
    for c in range(1, max_cols + 1):
        copy_cell(src_ws.cell(target_row, c), new_ws.cell(7, c))
        
    # 自動智慧調整欄寬，確保所有欄位表頭與資料完整顯示不被遮擋
    for col_idx in range(1, max_cols + 1):
        col_letter = get_column_letter(col_idx)
        max_len = 0
        for r in range(1, 8):
            val = new_ws.cell(r, col_idx).value
            if val is not None:
                if isinstance(val, (datetime, date)):
                    s = val.strftime('%Y/%m/%d')
                else:
                    s = str(val).strip()
                lines = s.split('\n')
                for line in lines:
                    line_len = sum(2.0 if ord(ch) > 127 else 1.15 for ch in line)
                    if line_len > max_len:
                        max_len = line_len
        if max_len > 0:
            # 依最長文字加上留白邊界 (+4.0)，至少 13.0
            adjusted_width = max(max_len + 4.0, 13.0)
            orig_w = new_ws.column_dimensions[col_letter].width
            if orig_w and orig_w > adjusted_width:
                adjusted_width = orig_w
            new_ws.column_dimensions[col_letter].width = round(adjusted_width, 1)

    # 確保第 6 列表頭高度 (28.0) 與第 7 列資料列高度 (22.0) 呼吸空間
    new_ws.row_dimensions[6].height = 28.0
    new_ws.row_dimensions[7].height = 22.0

    # 保持正常從第 1 列 (A1) 完整顯示表頭與第 7 列資料 (如圖二)，不捲動遮蔽
    new_ws.freeze_panes = 'A7'
            
    return new_wb

# ================= 介面與操作 =================

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("生產履歷與COA自動產生器")
        self.geometry("1260x820")
        self.minsize(1080, 620)
        self.configure(padx=15, pady=15)
        
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.template_path = None
        self.mapping_path = os.path.join(self.base_dir, "N系料小包-地點代號對照表.xlsx")
        
        self.mapping_dict = {}
        self.imported_lorry_files = []
        self.load_mapping()
        
        self.setup_ui()
        self.entries = []
        self.coa_paths = []
        self._last_dirs = {}  # key: 'excel', 'lorry', 'coa'
        self._dirs_file = os.path.join(self.base_dir, 'last_dirs.json')
        try:
            with open(self._dirs_file, 'r', encoding='utf-8') as f:
                self._last_dirs = json.load(f)
        except Exception:
            pass
        self.add_input_rows(20)

    def _save_last_dir(self, key, filepath):
        self._last_dirs[key] = os.path.dirname(filepath)
        try:
            with open(self._dirs_file, 'w', encoding='utf-8') as f:
                json.dump(self._last_dirs, f, ensure_ascii=False)
        except Exception:
            pass

    def show_loading(self, msg="⏳ 系統處理中，請稍候..."):
        self.config(cursor="wait")
        self.loading_win = tk.Toplevel(self)
        self.loading_win.title("處理中")
        self.loading_win.geometry("300x120")
        self.loading_win.transient(self)
        self.loading_win.grab_set()
        
        self.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - 150
        y = self.winfo_y() + (self.winfo_height() // 2) - 60
        self.loading_win.geometry(f"+{x}+{y}")
        self.loading_win.overrideredirect(True) # Remove window borders
        self.loading_win.configure(bg="white", relief="raised", bd=2)
        
        tk.Label(self.loading_win, text=msg, font=("Microsoft JhengHei", 12, "bold"), fg="#002060", bg="white").pack(expand=True)
        self.update()

    def hide_loading(self):
        self.config(cursor="")
        if hasattr(self, 'loading_win') and self.loading_win:
            self.loading_win.grab_release()
            self.loading_win.destroy()
            self.loading_win = None

    def load_mapping(self):
        self.mapping_dict = {}
        self.part_mapping_dict = {}
        if os.path.exists(self.mapping_path):
            try:
                map_wb = openpyxl.load_workbook(self.mapping_path, data_only=True)
                map_ws = map_wb.active
                rows = list(map_ws.iter_rows(values_only=True))
                if rows:
                    headers = [str(h).strip() if h else "" for h in rows[0]]
                    for row in rows[1:]:
                        if row and len(row) >= 2 and row[0] and row[1]:
                            loc_key = str(row[0]).strip().upper()
                            loc_val = str(row[1]).strip()
                            if any(kw in loc_key for kw in ("到貨", "地點", "SHORT", "LOCATION", "KEY", "HEADER")):
                                continue
                            if loc_key not in self.mapping_dict:
                                self.mapping_dict[loc_key] = []
                            if loc_val not in self.mapping_dict[loc_key]:
                                self.mapping_dict[loc_key].append(loc_val)
                            if loc_key not in self.part_mapping_dict:
                                info = {"default": str(row[2]).strip() if len(row) > 2 and row[2] else "", "origins": {}}
                                for i in range(3, len(headers)):
                                    if i < len(row) and row[i] is not None:
                                        h_name = headers[i]
                                        if h_name: info["origins"][h_name] = str(row[i]).strip()
                                self.part_mapping_dict[loc_key] = info
                map_wb.close()
            except Exception as e:
                pass

        if hasattr(self, "lbl_mapping_status"):
            m_color = "green" if os.path.exists(self.mapping_path) else "red"
            m_text = f"對照表檔案 (N系料小包-地點代號對照表.xlsx): ✅ 已找到 (載入 {len(self.mapping_dict)} 筆代號)" if os.path.exists(self.mapping_path) else "對照表檔案 (N系料小包-地點代號對照表.xlsx): ❌ 未找到"
            self.lbl_mapping_status.config(text=m_text, fg=m_color)

        if hasattr(self, "entries"):
            for entry in self.entries:
                loc_val = entry["loc_var"].get().strip().upper()
                if loc_val:
                    self.on_loc_change(entry["loc_var"], entry["long_code_var"], entry.get("long_code_combo"))

    def update_lorry_status(self):
        if not hasattr(self, "imported_lorry_files"):
            self.imported_lorry_files = []
        if not self.imported_lorry_files:
            defaults = glob.glob(os.path.join(self.base_dir, "Chemical_Lorry*.xlsx"))
            if defaults:
                self.imported_lorry_files = [defaults[0]]
        
        if hasattr(self, "lbl_lorry_status"):
            if self.imported_lorry_files:
                if len(self.imported_lorry_files) > 1:
                    fname = f"已選 {len(self.imported_lorry_files)} 份檔案"
                else:
                    fname = os.path.basename(self.imported_lorry_files[0])
                self.lbl_lorry_status.config(
                    text=f"生產履歷檔案 (Chemical_Lorry*.xlsx): ✅ 已就緒 ({fname})",
                    fg="#2E7D32"
                )
            else:
                self.lbl_lorry_status.config(
                    text="生產履歷檔案 (Chemical_Lorry*.xlsx): ⚠️ 尚未載入 (點擊右側按鈕或下方工具列『📋 載入生產履歷』)",
                    fg="#D32F2F"
                )

    def load_chemical_lorry_file(self):
        filepaths = filedialog.askopenfilenames(
            initialdir=self._last_dirs.get('lorry', self.base_dir),
            title="選擇生產履歷檔案 (Chemical_Lorry, 可多選)",
            filetypes=[("Excel 活頁簿", "*.xlsx *.xls"), ("所有檔案", "*.*")]
        )
        if not filepaths:
            return
        self._save_last_dir('lorry', filepaths[0])
            
        try:
            self.show_loading("⏳ 正在處理生產履歷，請稍候...")
            self.imported_lorry_files = list(filepaths)
            self.update_lorry_status()
            self.gen_lorry_var.set(True)
            
            # 因為這步驟僅是讀取路徑非常快，故意加上 0.5 秒延遲讓畫面顯示給人員看，避免覺得沒反應
            import time
            time.sleep(0.5)
            self.update()
        finally:
            self.hide_loading()
            
        # 比對排程批號 vs 生產履歷批號
        try:
            import openpyxl as _opxl
            lorry_batches = set()
            if hasattr(self, "imported_lorry_files"):
                for l_file in self.imported_lorry_files:
                    try:
                        _wb = _opxl.load_workbook(l_file, data_only=True)
                        _ws = _wb.active
                        _val = str(_ws.cell(row=7, column=1).value or "").strip().upper()
                        if _val:
                            lorry_batches.add(_val)
                        _wb.close()
                    except:
                        pass
            
            table_batches = []
            for row in self.entries:
                b = row["batch_var"].get().strip().upper()
                if b:
                    table_batches.append(b)
            
            missing = []
            found = []
            for b in table_batches:
                is_found = False
                if b in lorry_batches:
                    is_found = True
                else:
                    for l_file in self.imported_lorry_files:
                        if b in os.path.basename(l_file).upper():
                            is_found = True
                            break
                if is_found:
                    found.append(b)
                else:
                    missing.append(b)
            
            fname = f"已選 {len(self.imported_lorry_files)} 份檔案" if len(self.imported_lorry_files) > 1 else os.path.basename(self.imported_lorry_files[0]) if self.imported_lorry_files else ""
            lines = [f"已成功載入生產履歷檔案：\n{fname}\n"]
            if not table_batches:
                lines.append("ℹ️ 排程表格尚未輸入批號，無法比對。")
            else:
                for b in found:
                    lines.append(f"✅ {b} ─ 生產履歷已找到")
                for b in missing:
                    lines.append(f"❌ {b} ─ 生產履歷中找不到！")
                if missing:
                    lines.append("\n請確認是否漏選，或排程表批號輸入有誤。")
            messagebox.showinfo("載入結果", "\n".join(lines))
        except Exception as e:
            messagebox.showerror("錯誤", f"檢查履歷資料夾失敗: {e}")


    def reload_mapping_with_msg(self):
        """點擊『🔄 重新載入對照表』時執行"""
        self.load_mapping()
        messagebox.showinfo("對照表已更新", f"已重新讀取『N系料小包-地點代號對照表.xlsx』！\n目前共載入 {len(self.mapping_dict)} 筆地點對照碼。\n表格中的地點長代號已同步更新！")

    def open_calendar_dialog(self, target_var):
        CalendarDialog(self, target_var)

    def setup_ui(self):
        # 1. 系統檔案狀態區
        status_frame = tk.LabelFrame(self, text="系統狀態", font=("Microsoft JhengHei", 10, "bold"), padx=10, pady=8)
        status_frame.pack(fill="x", pady=(0, 8))
        
        
        
        # 對照表狀態列 + 重新載入按鈕
        map_status_frame = tk.Frame(status_frame)
        map_status_frame.pack(anchor="w", pady=(2, 0))

        m_color = "green" if os.path.exists(self.mapping_path) else "red"
        m_text = f"對照表檔案 (N系料小包-地點代號對照表.xlsx): ✅ 已找到 (載入 {len(self.mapping_dict)} 筆代號)" if os.path.exists(self.mapping_path) else "對照表檔案 (N系料小包-地點代號對照表.xlsx): ❌ 未找到"
        
        self.lbl_mapping_status = tk.Label(map_status_frame, text=m_text, fg=m_color)
        self.lbl_mapping_status.pack(side="left")

        tk.Button(
            map_status_frame, 
            text="🔄 重新載入對照表", 
            command=self.reload_mapping_with_msg, 
            bg="#607D8B", 
            fg="white", 
            font=("Microsoft JhengHei", 8, "bold"), 
            padx=6,
            cursor="hand2"
        ).pack(side="left", padx=10)

        # 生產履歷狀態列 + 選擇檔案按鈕
        lorry_status_frame = tk.Frame(status_frame)
        lorry_status_frame.pack(anchor="w", pady=(2, 0))

        self.lbl_lorry_status = tk.Label(lorry_status_frame, text="", fg="green")
        self.lbl_lorry_status.pack(side="left")

        tk.Button(
            lorry_status_frame, 
            text="📋 選擇生產履歷檔", 
            command=self.load_chemical_lorry_file, 
            bg="#E65100", 
            fg="white", 
            font=("Microsoft JhengHei", 8, "bold"), 
            padx=6,
            cursor="hand2"
        ).pack(side="left", padx=10)
        self.update_lorry_status()

        # 2. 頂部快捷功能與檔案載入工具列
        top_ctrl_frame = tk.Frame(self)
        top_ctrl_frame.pack(fill="x", pady=(0, 6))
        
        # 左側：資料載入與匯入按鈕群組
        left_btn_frame = tk.Frame(top_ctrl_frame)
        left_btn_frame.pack(side="left")
        
        tk.Button(left_btn_frame, text="📥 從 Excel 匯入排程", command=self.import_from_excel, bg="#1976D2", fg="white", font=("Microsoft JhengHei", 9, "bold"), padx=8, pady=2, cursor="hand2").pack(side="left", padx=(0, 4))
        tk.Button(left_btn_frame, text="📋 載入生產履歷 (Chemical_Lorry)", command=self.load_chemical_lorry_file, bg="#E65100", fg="white", font=("Microsoft JhengHei", 9, "bold"), padx=8, pady=2, cursor="hand2").pack(side="left", padx=4)
        tk.Button(left_btn_frame, text="📄 載入 COA 表單", command=self.load_coa_forms, bg="#8E24AA", fg="white", font=("Microsoft JhengHei", 9, "bold"), padx=8, pady=2, cursor="hand2").pack(side="left", padx=4)

        # 右側：表格操作與日期快捷按鈕群組
        right_btn_frame = tk.Frame(top_ctrl_frame)
        right_btn_frame.pack(side="right")
        
        tk.Button(right_btn_frame, text="📅 帶入今天日期", command=self.set_today_all_dates, bg="#546E7A", fg="white", font=("Microsoft JhengHei", 9, "bold"), padx=8, pady=2, cursor="hand2").pack(side="left", padx=4)
        tk.Button(right_btn_frame, text="➕ 新增 10 列", command=lambda: self.add_input_rows(10), bg="#00897B", fg="white", font=("Microsoft JhengHei", 9, "bold"), padx=8, pady=2, cursor="hand2").pack(side="left", padx=4)
        tk.Button(right_btn_frame, text="🗑️ 清除全部資料", command=self.clear_all_rows, bg="#D32F2F", fg="white", font=("Microsoft JhengHei", 9, "bold"), padx=8, pady=2, cursor="hand2").pack(side="left", padx=(4, 0))

        # 預計時間 (遺留變數)
        self.gen_3in1_var = tk.BooleanVar(value=False)
        self.gen_lorry_var = tk.BooleanVar(value=True)

        # 輸出設定區域
        export_opt_frame = tk.LabelFrame(self, text="⚙️ 輸出資料夾模式", font=("Microsoft JhengHei", 9, "bold"), padx=10, pady=5)
        export_opt_frame.pack(fill="x", pady=(0, 6))
        
        self.folder_mode_var = tk.IntVar(value=1)
        tk.Radiobutton(export_opt_frame, text="模式 1：依批號分子資料夾 (出貨日 -> 廠區 -> 批號_廠區 -> 檔案)", variable=self.folder_mode_var, value=1, font=("Microsoft JhengHei", 9)).pack(side="left", padx=(0, 15))
        tk.Radiobutton(export_opt_frame, text="模式 2：集中在廠區資料夾 (出貨日 -> 廠區 -> 檔案)", variable=self.folder_mode_var, value=2, font=("Microsoft JhengHei", 9)).pack(side="left")

        # 5. 表格滾動容器
        table_container = tk.Frame(self)
        table_container.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(table_container, borderwidth=0, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(table_container, orient="vertical", command=self.canvas.yview)
        self.scrollbar_x = ttk.Scrollbar(table_container, orient="horizontal", command=self.canvas.xview)
        
        # 單一 Grid 容器 (scrollable_frame)
        self.scrollable_frame = tk.Frame(self.canvas, padx=5, pady=5)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set, xscrollcommand=self.scrollbar_x.set)

        self.scrollbar.pack(side="right", fill="y")
        self.scrollbar_x.pack(side="bottom", fill="x")
        self.canvas.pack(side="left", fill="both", expand=True)

        # 支援滑鼠滾輪滾動
        self.bind_all("<MouseWheel>", lambda event: self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units"))

        # --- Row 0: 表格標題列 (置於滾動區最上方，共享 100% 同一 Grid 欄位規格) ---
        # col_idx, label_text, min_width(px)
        headers = [
            (0,  "產\n生",                    28),
            (1,  "項\n次",                    28),
            (2,  "批號\n(10碼)",               100),
            (3,  "數量\n(ShipQty)",            70),
            (4,  "地點\n(如15P5)",             65),
            (5,  "長代號\n(自動)",              80),
            (6,  "出貨日期\n📅",               100),
            (7,  "採購單號",                   110),
            (8,  "料號\n(自動)",               80),
            (9,  "品名",                       220),
            (10, "製造日",                     80),
            (11, "保存期限",                   80),
            (12, "剩餘\n天數",                 48),
            (13, "清空\n單列",                 48),
        ]
        
        for col_idx, title, min_w in headers:
            lbl = tk.Label(
                self.scrollable_frame, 
                text=title, 
                font=("Arial", 9, "bold"), 
                bg="#EAEAEA", 
                fg="#333333",
                padx=4,
                pady=3,
                relief="groove",
                justify="center",
                wraplength=0,      # 讓 \n 自然換行
                width=0,
            )
            lbl.grid(row=0, column=col_idx, sticky="ew", padx=1, pady=(0, 4), ipadx=2, ipady=2)
            # 設定最小欄寬
            self.scrollable_frame.columnconfigure(col_idx, minsize=min_w)

        # 產生按鈕
        btn_frame = tk.Frame(self)
        btn_frame.pack(fill="x", pady=10)
        tk.Button(btn_frame, text="🚀 開始批次產生 Excel 報表", command=self.generate_files, bg="#4CAF50", fg="white", font=("Arial", 12, "bold"), pady=8).pack(fill="x")
    def add_input_rows(self, count):
        for i in range(count):
            row_idx = len(self.entries) + 1
            row_grid_idx = row_idx
            
            # Col 0: 勾選
            chk_var = tk.BooleanVar(value=True)
            chk = tk.Checkbutton(self.scrollable_frame, variable=chk_var)
            chk.grid(row=row_grid_idx, column=0, padx=2, pady=2)

            # Col 1: 項次
            lbl_num = tk.Label(self.scrollable_frame, text=str(row_idx), font=("Arial", 10), width=3)
            lbl_num.grid(row=row_grid_idx, column=1, padx=2, pady=2)
            
            # Col 2: 批號
            batch_var = tk.StringVar()
            batch_entry = tk.Entry(self.scrollable_frame, textvariable=batch_var, width=16, font=("Arial", 10))
            batch_entry.grid(row=row_grid_idx, column=2, padx=2, pady=2, sticky="ew")
            
            # Col 3: 槽號
            qty_var = tk.StringVar()
            qty_entry = tk.Entry(self.scrollable_frame, textvariable=qty_var, width=10, font=("Arial", 10), fg="blue")
            qty_entry.grid(row=row_grid_idx, column=3, padx=2, pady=2, sticky="ew")
            
            # Col 4: 地點
            loc_var = tk.StringVar()
            loc_entry = tk.Entry(self.scrollable_frame, textvariable=loc_var, width=12, font=("Arial", 10))
            loc_entry.grid(row=row_grid_idx, column=4, padx=2, pady=2, sticky="ew")
            
            # Col 5: 長代號
            long_code_var = tk.StringVar()
            from tkinter import ttk
            long_code_combo = ttk.Combobox(self.scrollable_frame, textvariable=long_code_var, state="readonly", width=12, font=("Arial", 10))
            long_code_combo.grid(row=row_grid_idx, column=5, padx=2, pady=2, sticky="ew")
            
            # Col 6: 出貨日期 (Entry + 📅 日曆按鈕)
            date_frame = tk.Frame(self.scrollable_frame)
            date_frame.grid(row=row_grid_idx, column=6, padx=2, pady=2, sticky="ew")
            
            date_var = tk.StringVar(value="")
            date_entry = tk.Entry(date_frame, textvariable=date_var, width=11, font=("Arial", 10))
            date_entry.pack(side="left", fill="x", expand=True)
            
            btn_cal = tk.Button(date_frame, text="📅", command=lambda dv=date_var: self.open_calendar_dialog(dv), font=("Arial", 8), cursor="hand2")
            btn_cal.pack(side="right", padx=(2, 0))
            
            # Col 7: 採購單號
            po_var = tk.StringVar(value="")
            po_entry = tk.Entry(self.scrollable_frame, textvariable=po_var, width=18, font=("Arial", 10), fg="#333")
            po_entry.grid(row=row_grid_idx, column=7, padx=2, pady=2, sticky="ew")

            # Col 8: 料號
            part_var = tk.StringVar()
            part_entry = tk.Entry(self.scrollable_frame, textvariable=part_var, width=9, font=("Arial", 10), fg="purple")
            part_entry.grid(row=row_grid_idx, column=8, padx=2, pady=2, sticky="ew")

            # Col 9: 品名
            name_var = tk.StringVar()
            name_entry = tk.Entry(self.scrollable_frame, textvariable=name_var, width=28, font=("Arial", 10), fg="purple")
            name_entry.grid(row=row_grid_idx, column=9, padx=2, pady=2, sticky="ew")

            # Col 10: 製造日
            mfg_var = tk.StringVar()
            mfg_entry = tk.Entry(self.scrollable_frame, textvariable=mfg_var, width=10, font=("Arial", 10), fg="black")
            mfg_entry.grid(row=row_grid_idx, column=10, padx=2, pady=2, sticky="ew")

            # Col 11: 保存期限
            exp_var = tk.StringVar()
            exp_entry = tk.Entry(self.scrollable_frame, textvariable=exp_var, width=10, font=("Arial", 10), fg="black")
            exp_entry.grid(row=row_grid_idx, column=11, padx=2, pady=2, sticky="ew")

            # Col 12: 剩餘天數
            rem_var = tk.StringVar()
            rem_entry = tk.Entry(self.scrollable_frame, textvariable=rem_var, width=6, font=("Arial", 10), fg="red", state="readonly")
            rem_entry.grid(row=row_grid_idx, column=12, padx=2, pady=2, sticky="ew")

            # Col 13: 單列清空按鈕
            btn_clear_row = tk.Button(
                self.scrollable_frame, 
                text="清空", 
                command=lambda r=row_idx-1: self.clear_single_row(r), 
                font=("Microsoft JhengHei", 9, "bold"), 
                bg="#FFEBEE", 
                fg="#C62828", 
                cursor="hand2", 
                width=6,
                pady=1
            )
            btn_clear_row.grid(row=row_grid_idx, column=13, padx=4, pady=2)

            def calc_rem(*args, ev=exp_var, rv=rem_var):
                val = ev.get().strip()
                if not val:
                    rv.set("")
                    return
                for fmt in ("%Y/%m/%d", "%Y-%m-%d", "%Y/%M/%d", "%Y.%m.%d", "%Y%m%d"):
                    try:
                        dt = datetime.strptime(val.split()[0], fmt).date()
                        rem_days = (dt - datetime.now().date()).days
                        rv.set(str(rem_days))
                        return
                    except ValueError:
                        pass
                rv.set("")

            exp_var.trace_add("write", calc_rem)

            # 綁定事件
            batch_var.trace_add("write", lambda name, index, mode, bv=batch_var, tv=qty_var: self.on_batch_change(bv, tv))
            loc_var.trace_add("write", lambda name, index, mode, lv=loc_var, lcv=long_code_var, cb=long_code_combo: self.on_loc_change(lv, lcv, cb))
            loc_var.trace_add("write", lambda name, index, mode, lv=loc_var, pv=part_var: self.update_part_no(lv, pv))
            
            for widget in (batch_entry, loc_entry, date_entry):
                widget.bind("<<Paste>>", lambda e, r=row_idx-1, w=widget: self.on_paste(e, r, w))
                widget.bind("<Control-v>", lambda e, r=row_idx-1, w=widget: self.on_paste(e, r, w))
                widget.bind("<Control-V>", lambda e, r=row_idx-1, w=widget: self.on_paste(e, r, w))
            
            self.entries.append({
                "chk_var": chk_var,
                "batch_var": batch_var,
                "qty_var": qty_var,
                "loc_var": loc_var,
                "long_code_var": long_code_var,
                "date_var": date_var,
                "po_var": po_var,
                "part_var": part_var,
                "name_var": name_var,
                "mfg_var": mfg_var,
                "exp_var": exp_var,
                "rem_var": rem_var,
                
            })

    def clear_all_rows(self):
        """一鍵清除全部輸入欄位 (全清)"""
        if messagebox.askyesno("確認清空", "確定要清空所有已填寫的批號、地點與時間資料嗎？"):
            for entry in self.entries:
                entry["batch_var"].set("")
                entry["loc_var"].set("")
                entry["long_code_var"].set("")
                entry["qty_var"].set("")
                entry["date_var"].set("")
                if "po_var" in entry: entry["po_var"].set("")
                if "part_var" in entry: entry["part_var"].set("")
                if "name_var" in entry: entry["name_var"].set("")
                if "mfg_var" in entry: entry["mfg_var"].set("")
                if "exp_var" in entry: entry["exp_var"].set("")
                if "rem_var" in entry: entry["rem_var"].set("")
                

    def set_today_all_dates(self):
        from datetime import datetime
        today_str = datetime.now().strftime("%Y/%m/%d")
        for entry in self.entries:
            if not entry["date_var"].get().strip():
                entry["date_var"].set(today_str)

    def clear_single_row(self, r_idx):
        """清空單一列的資料 (單個清)"""
        if 0 <= r_idx < len(self.entries):
            entry = self.entries[r_idx]
            entry["batch_var"].set("")
            entry["loc_var"].set("")
            entry["long_code_var"].set("")
            entry["qty_var"].set("")
            entry["date_var"].set("")
            if "po_var" in entry: entry["po_var"].set("")
            if "part_var" in entry: entry["part_var"].set("")
            if "name_var" in entry: entry["name_var"].set("")
            if "mfg_var" in entry: entry["mfg_var"].set("")
            if "exp_var" in entry: entry["exp_var"].set("")
            if "rem_var" in entry: entry["rem_var"].set("")
            

    def on_batch_change(self, batch_var, qty_var):
        batch = batch_var.get().upper().strip()
        tank = ""
        # qty_var.set(tank) # no auto calculation for qty

    def update_part_no(self, loc_var, part_var):
        if not hasattr(self, 'part_mapping_dict'): return
        loc = loc_var.get().strip().upper()
        if loc in self.part_mapping_dict:
            info = self.part_mapping_dict[loc]
            part_no = info["default"]
            # 對照表有此地點，但無設定料號 → 空白
            part_var.set(part_no)
        else:
            # 地點不在對照表 → 空白（不用硬碼兜底）
            part_var.set("")

    def on_loc_change(self, loc_var, long_code_var, long_code_combo=None):
        loc = loc_var.get().strip().upper()
        if not loc:
            long_code_var.set("")
            if long_code_combo: long_code_combo['values'] = []
            return

        if loc in self.mapping_dict:
            vals = self.mapping_dict[loc]
            if long_code_combo: long_code_combo['values'] = vals
            long_code_var.set(vals[0] if isinstance(vals, list) and vals else (vals if isinstance(vals, str) else ""))
        else:
            long_code_var.set("❌ 未知代號")
            if long_code_combo: long_code_combo['values'] = []
    def parse_pasted_row_items(self, parts):
        """
        智慧解析貼上行中的元素，自動辨識：出貨日期、批號、槽號、地點、時間。
        支援 Image 1 範例（到貨 + 批號 + 槽號 + 地點）及各式自訂順序！
        """
        res = {"batch": "", "loc": "", "date": "", "time": "", "mod_time": "", "origin": ""}
        clean_parts = [p.strip() for p in parts if p.strip()]
        if not clean_parts:
            return res

        unassigned = []
        for p in clean_parts:
            p_upper = p.upper()
            
            # 1. 日期 (包含 /, -, ., 或月/日，長度 <= 12)
            if not res["date"] and (any(char in p for char in ("/", "-", ".")) or "月" in p or "日" in p):
                if len(p) <= 12 and not p.isalnum():
                    res["date"] = p
                    continue

            # 2. 批號 (8~12 碼英數混合，例如 26817E3051)
            if not res["batch"] and (8 <= len(p_upper) <= 12 and any(c.isdigit() for c in p_upper) and any(c.isalpha() for c in p_upper)):
                res["batch"] = p_upper
                continue

            # 3. 地點 (在 mapping_dict 內或含 18P, 15P, P, 廠等)
            if not res["loc"] and (p_upper in self.mapping_dict or "18P" in p_upper or "15P" in p_upper or "P" in p_upper or "廠" in p):
                res["loc"] = p_upper
                continue

            # 4. 槽號 (3~5 碼以 E/T/P 開頭，例如 E305) -> 可略過，因為寫入批號時微服務會自動算槽號！
            if len(p_upper) <= 5 and p_upper.startswith(("E", "T", "P")):
                continue

            # 其它填入未指派
            unassigned.append(p)

        # 針對缺額自動後補填入
        for item in unassigned:
            if not res["batch"] and len(item) >= 6:
                res["batch"] = item.upper()
            elif not res["loc"] and len(item) <= 10:
                res["loc"] = item.upper()
            elif not res["date"] and ("/" in item or "-" in item or "." in item):
                res["date"] = item
            elif not res["time"]:
                res["time"] = item
            elif not res["mod_time"]:
                res["mod_time"] = item

        for p in clean_parts:
            p_upper = p.upper()
            if not res.get("origin") and any(k in p_upper for k in ["崙尾", "彰濱", "L1", "L2"]):
                res["origin"] = p
                
        return res

    def on_paste(self, event, start_row_idx, widget=None):
        try:
            clipboard = self.clipboard_get()
            lines = clipboard.split('\n')
            
            valid_lines = [l for l in lines if l.strip()]
            if not valid_lines:
                return "break"
                
            needed_rows = start_row_idx + len(valid_lines)
            if needed_rows > len(self.entries):
                self.add_input_rows(needed_rows - len(self.entries))
            
            curr_row = start_row_idx
            for line in lines:
                if not line.strip(): continue
                parts = line.split('\t')
                if len(parts) == 1:
                    parts = line.split()
                    
                if len(parts) >= 2:
                    # 使用智慧元素剖析器！
                    parsed = self.parse_pasted_row_items(parts)
                    
                    if parsed["batch"]:
                        self.entries[curr_row]["batch_var"].set(parsed["batch"])
                    if parsed["loc"]:
                        self.entries[curr_row]["loc_var"].set(parsed["loc"])
                    if parsed["date"]:
                        self.entries[curr_row]["date_var"].set(parsed["date"])
                    
                    curr_row += 1
                elif len(parts) == 1:
                    val = parts[0].strip()
                    # 單一欄位貼上：依當前焦點與內容自動指派
                    if val:
                        parsed = self.parse_pasted_row_items([val])
                        if parsed["batch"]:
                            self.entries[curr_row]["batch_var"].set(parsed["batch"])
                        elif parsed["loc"]:
                            self.entries[curr_row]["loc_var"].set(parsed["loc"])
                        elif parsed["date"]:
                            self.entries[curr_row]["date_var"].set(parsed["date"])
                        else:
                            self.entries[curr_row]["batch_var"].set(val)
                    curr_row += 1
                    
            return "break"
        except Exception as e:
            messagebox.showerror("貼上失敗", f"解析貼上內容時發生錯誤:\n{e}")
            return "break"




    def _extract_batch_from_coa(self, file_path):
        import csv
        try:
            with open(file_path, 'r', encoding='utf-8-sig', errors='ignore') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 2 and 'RawLotId' in str(row[0]):
                        return str(row[1]).strip()
        except:
            pass
        try:
            with open(file_path, 'r', encoding='cp950', errors='ignore') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 2 and 'RawLotId' in str(row[0]):
                        return str(row[1]).strip()
        except:
            pass
        try:
            import openpyxl
            wb = openpyxl.load_workbook(file_path, data_only=True)
            for sheet in wb.sheetnames:
                ws = wb[sheet]
                for row in ws.iter_rows(min_row=1, max_row=50, min_col=1, max_col=2):
                    if row[0].value and 'RawLotId' in str(row[0].value) and row[1].value:
                        return str(row[1].value).strip()
        except:
            pass
        return None

    def load_coa_forms(self):
        file_paths = filedialog.askopenfilenames(
            initialdir=self._last_dirs.get('coa', self.base_dir),
            title="選擇要載入的 COA 表單 (可多選)",
            filetypes=[("Excel 或 CSV", "*.xlsx *.xls *.csv"), ("所有檔案", "*.*")]
        )
        if not file_paths:
            return
        self._save_last_dir('coa', file_paths[0])

        valid_batches = {}
        for row in self.entries:
            if row["chk_var"].get():
                batch = row["batch_var"].get().strip().upper()
                loc = row["loc_var"].get().strip().upper() if "loc_var" in row else ""
                if batch:
                    vb_key = f"{batch}|{loc}" if loc else batch
                    valid_batches[vb_key] = row

        if not valid_batches:
            messagebox.showwarning("提示", "請先在列表中填寫並勾選包含批號的資料！")
            return
            
        matched_results = []
        unmatched_files = []
        for file_path in file_paths:
            base_name = os.path.basename(file_path)
            fn_upper = base_name.upper()
            
            # 收集所有批號吻合的 key (支援同批號多廠區)
            matched_keys = []
            for b_key, row_entry in valid_batches.items():
                b = b_key.split('|')[0]
                if b in fn_upper:
                    matched_keys.append(b_key)
                    
            if not matched_keys:
                found_batch = self._extract_batch_from_coa(file_path)
                if found_batch:
                    for b_key, row_entry in valid_batches.items():
                        b = b_key.split('|')[0]
                        if b == found_batch or b in found_batch or found_batch in b:
                            matched_keys.append(b_key)
                            
            if matched_keys:
                for mk in matched_keys:
                    matched_results.append((base_name, mk))
            else:
                unmatched_files.append(base_name)

        self.imported_coa_files = list(file_paths)
        
        msg = f"共載入 {len(file_paths)} 份 COA 表單\n\n"
        if matched_results:
            msg += f"✅ 成功對應 {len(matched_results)} 筆批號：\n"
            for fname, b in matched_results:
                msg += f" - {fname} -> {b}\n"
        if unmatched_files:
            msg += f"\n⚠️ 找不到對應批號 {len(unmatched_files)} 份：\n"
            for fname in unmatched_files:
                msg += f" - {fname}\n"
        messagebox.showinfo("COA 表單已載入", msg)

    def upload_coa(self):
        if not os.path.exists(r'C:\Program Files\Tesseract-OCR\tesseract.exe') and not os.path.exists(r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe'):
            ans = messagebox.askyesno(
                "缺少 OCR 引擎", 
                "系統偵測到您尚未安裝『Tesseract OCR 引擎』，無法使用截圖辨識功能！\n\n"
                "是否要立即開啟官方下載網頁？\n\n"
                "(請下載最新的 64 bit 安裝檔，並【一直按下一步】安裝在預設路徑即可)"
            )
            if ans:
                webbrowser.open("https://github.com/UB-Mannheim/tesseract/wiki")
            return
            
        filepaths = filedialog.askopenfilenames(title="選擇 COA 截圖", filetypes=[("Image files", "*.jpg *.jpeg *.png")])
        if filepaths:
            self.coa_paths.extend(filepaths)
            messagebox.showinfo("上傳成功", f"成功上傳 {len(filepaths)} 張截圖！\n目前共 {len(self.coa_paths)} 張待處理。")

    def paste_coa(self):
        try:
            from PIL import ImageGrab
            img = ImageGrab.grabclipboard()
            if img is None:
                messagebox.showwarning("剪貼簿無影像", "剪貼簿中沒有影像，請先使用截圖工具 (例如 Win+Shift+S) 截圖後再點擊貼上！")
                return
            if isinstance(img, list):
                messagebox.showwarning("格式不符", "請直接複製「影像」圖片本身，而不是檔案。")
                return
            
            import tempfile
            import uuid
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, f"coa_paste_{uuid.uuid4().hex[:8]}.png")
            img.save(temp_path, "PNG")
            
            self.coa_paths.append(temp_path)
            messagebox.showinfo("貼上成功", f"成功貼上 1 張截圖！\n目前共 {len(self.coa_paths)} 張待處理。")
        except Exception as e:
            messagebox.showerror("貼上失敗", f"無法讀取剪貼簿內容：{e}")


    def import_from_excel(self):
        filepaths = filedialog.askopenfilenames(
            initialdir=self._last_dirs.get('excel', self.base_dir),
            title="選擇要匯入的 Excel 或 CSV 檔案 (可多選)",
            filetypes=[("Excel & CSV files", "*.xlsx *.xls *.csv")]
        )
        if not filepaths:
            return
        self._save_last_dir('excel', filepaths[0])
            
        if not hasattr(self, "imported_lorry_files"):
            self.imported_lorry_files = []
        for fp in filepaths:
            fn = os.path.basename(fp).lower()
            if fp.lower().endswith(('.xlsx', '.xls')) and ('chemical' in fn or 'lorry' in fn or '勝一' in fn):
                if fp not in self.imported_lorry_files:
                    self.imported_lorry_files.append(fp)
        self.update_lorry_status()

        total_imported = 0
        for filepath in filepaths:
            try:
                records = []
                sheet_count = 1

                if filepath.lower().endswith('.csv'):
                    rows = []
                    try:
                        with open(filepath, 'r', encoding='utf-8-sig') as f:
                            reader = csv.reader(f)
                            rows = list(reader)
                    except UnicodeDecodeError:
                        with open(filepath, 'r', encoding='cp950') as f:
                            reader = csv.reader(f)
                            rows = list(reader)

                    # Check for vertical CSV format (e.g. RawLotId in first column)
                    is_vertical_csv = False
                    for r_idx, row_vals in enumerate(rows[:20]):
                        if len(row_vals) >= 2 and str(row_vals[0]).strip() == "RawLotId":
                            is_vertical_csv = True
                            break

                    if is_vertical_csv:
                        batch_val, date_val, loc_val = "", "", ""
                        for r_idx, row_vals in enumerate(rows[:30]):
                            if len(row_vals) >= 2:
                                key = str(row_vals[0]).strip()
                                val = str(row_vals[1]).strip()
                                if key == "RawLotId": batch_val = val
                                elif key == "DeliverDate": date_val = val
                        fname = os.path.basename(filepath)
                        m = re.search(r'\s([A-Za-z0-9]+)_\d+\.csv$', fname, re.IGNORECASE)
                        if m:
                            loc_val = m.group(1)
                        else:
                            parts = fname.split('_')
                            if len(parts) >= 2:
                                loc_val = parts[-2].split(' ')[-1]
                        po_val = ""
                        if batch_val:
                            norm_d = normalize_date_str(date_val)
                            records.append({
                                "sheet": "CSV",
                                "batch": batch_val,
                                "loc": clean_location_str(loc_val, self.mapping_dict),
                                "date": norm_d,
                                "time": "",
                                "mod_time": "",
                                "tank": get_tank_from_batch(batch_val)
                            })
                    else:
                        # Standard horizontal CSV
                        batch_col, loc_col, date_col, qty_col, time_col, mod_time_col, po_col, origin_col, mfg_col, exp_col = -1, -1, -1, -1, -1, -1, -1, -1, -1, -1
                        name_col = -1
                        start_row = 0
                        for r_idx in range(min(15, len(rows))):
                            row = rows[r_idx]
                            if not row: continue
                            for c_idx, val in enumerate(row):
                                v = str(val or "").strip().upper()
                                if batch_col == -1 and any(k in v for k in ["批號", "BATCH", "LOT"]): batch_col = c_idx
                                if loc_col == -1 and any(k in v for k in ["地點", "指送", "交貨", "到貨地", "送達", "廠區", "LOCATION", "DEST"]): loc_col = c_idx
                                if date_col == -1 and (v in ["出貨", "到貨", "出貨日", "到貨日", "日期", "出車"] or any(k in v for k in ["出貨日", "到貨日", "出車日", "日期", "DATE"])) and "地" not in v and "點" not in v: date_col = c_idx
                                if qty_col == -1 and any(k in v for k in ["數量", "QTY", "QUANTITY", "AMOUNT", "排程量", "需求量", "總重"]): qty_col = c_idx
                                if mfg_col == -1 and any(k in v for k in ["製造", "MFG", "生產日", "製日"]): mfg_col = c_idx
                                if exp_col == -1 and any(k in v for k in ["到期", "保存", "EXP", "期限", "效期", "批號到期"]) and "剩餘" not in v and "天數" not in v: exp_col = c_idx
                                if time_col == -1 and any(k in v for k in ["到貨時間", "預計", "時間", "TIME"]) and "修正" not in v: time_col = c_idx
                                if mod_time_col == -1 and "修正" in v and ("時間" in v or "TIME" in v): mod_time_col = c_idx
                                if po_col == -1 and any(k in v for k in ["採購單號", "採購單", "采购单", "採購"]): po_col = c_idx
                                if origin_col == -1 and any(k in v for k in ["出貨地", "出貨區", "出貨廠", "灌裝"]): origin_col = c_idx
                                if name_col == -1 and any(k in v for k in ["品名", "產品名稱", "PRODUCT", "NAME", "描述", "SPEC"]): name_col = c_idx
                            if batch_col != -1 and (loc_col != -1 or date_col != -1):
                                start_row = r_idx + 1
                                break
                        if batch_col == -1 or loc_col == -1:
                            batch_col, date_col, qty_col, loc_col = 2, 1, 4, 5
                            start_row = 2
                        # 找不到就留空（-1），不死寫固定欄號，以免抓到不相關欄位
                        for r_idx in range(start_row, len(rows)):
                            row = rows[r_idx]
                            if not row: continue
                            def get_c(c): return row[c] if c != -1 and c < len(row) else None
                            b_val = str(get_c(batch_col) or "").strip().upper()
                            l_val = str(get_c(loc_col) or "").strip().upper()
                            d_val = get_c(date_col)
                            qty_val = str(get_c(qty_col) or "").strip()
                            origin_val = str(get_c(origin_col) or "").strip()
                            tm_val = normalize_time_str(get_c(time_col))
                            mt_val = normalize_time_str(get_c(mod_time_col))
                            po_val = str(get_c(po_col) or "").strip()
                            mfg_val = str(get_c(mfg_col) or "").strip()
                            exp_val = str(get_c(exp_col) or "").strip()
                            name_val = str(get_c(name_col) or "").strip() if name_col != -1 else ""
                            if len(b_val) != 10 or not re.search(r'[0-9]', b_val):
                                for cell in row:
                                    cs = str(cell or "").strip().upper()
                                    if len(cs) == 10 and re.search(r'[0-9]', cs) and re.search(r'[A-Z]', cs) and "/" not in cs and "-" not in cs:
                                        b_val = cs
                                        break
                            if len(b_val) == 10 and re.search(r'[0-9]', b_val):
                                tank_final = qty_val
                                clean_l = clean_location_str(l_val, self.mapping_dict)
                                records.append({
                                    "sheet": "CSV",
                                    "batch": b_val,
                                    "tank": tank_final,
                                    "loc": clean_l,
                                    "_vals": self.mapping_dict.get(clean_l, []),
                        "long_code": self.mapping_dict.get(clean_l, [""])[0] if isinstance(self.mapping_dict.get(clean_l), list) and self.mapping_dict.get(clean_l) else (self.mapping_dict.get(clean_l) if isinstance(self.mapping_dict.get(clean_l), str) else ""),
                                    "date": normalize_date_str(d_val),
                                    "time": tm_val,
                                    "mod_time": mt_val,
                                "po": po_val,
                                "origin": origin_val,
                                "name": name_val,
                                "mfg_date": normalize_date_str(mfg_val),
                                "exp_date": normalize_date_str(exp_val)
                            })
                else:
                    # 遍歷 Excel 所有分頁 (跨分頁抓取所有有效排程)
                    wb = openpyxl.load_workbook(filepath, data_only=True)
                    sheet_count = len(wb.worksheets)

                    for ws in wb.worksheets:
                        sheet_name = ws.title
                        rows = list(ws.iter_rows(values_only=True))
                        if not rows or len(rows) == 0:
                            continue

                        # 檢查分頁全域文字是否標記為台積電
                        sheet_has_tsmc = False
                        for r_idx in range(min(5, len(rows))):
                            row_str = " ".join(str(cell or "") for cell in rows[r_idx]).upper()
                            if "TSMC" in row_str or "台積" in row_str:
                                sheet_has_tsmc = True
                                break

                        # 先嘗試從第一列（品名行）或分頁名稱取得品名
                        sheet_product_name = ""
                        if rows:
                            row0_vals = [str(c or "").strip() for c in rows[0] if c is not None and str(c).strip()]
                            if row0_vals:
                                sheet_product_name = row0_vals[0]  # 第一列第一個非空值即品名
                        if not sheet_product_name:
                            sheet_product_name = sheet_name  # fallback 用分頁名稱

                        # 動態掃描前 15 列尋找標題欄位
                        batch_col = -1
                        loc_col = -1
                        date_col = -1
                        qty_col = -1
                        time_col = -1
                        mod_time_col = -1
                        cust_col = -1
                        po_col = -1
                        origin_col = -1
                        mfg_col = -1
                        exp_col = -1
                        name_col = -1
                        start_row = 0

                        for r_idx in range(min(15, len(rows))):
                            row = rows[r_idx]
                            if not row: continue
                            for c_idx, val in enumerate(row):
                                v = str(val or "").strip().upper()
                                if not v: continue
                                if batch_col == -1 and any(k in v for k in ["批號", "BATCH", "LOT"]): batch_col = c_idx
                                if loc_col == -1 and any(k in v for k in ["地點", "指送", "交貨", "到貨地", "送達", "廠區", "LOCATION", "DEST"]): loc_col = c_idx
                                if date_col == -1 and (v in ["出貨", "到貨", "出貨日", "到貨日", "日期", "出車"] or any(k in v for k in ["出貨日", "到貨日", "出車日", "日期", "DATE"])) and "地" not in v and "點" not in v: date_col = c_idx
                                if qty_col == -1 and any(k in v for k in ["數量", "QTY", "QUANTITY", "AMOUNT", "排程量", "需求量", "總重"]): qty_col = c_idx
                                if time_col == -1 and any(k in v for k in ["到貨時間", "預計", "時間", "TIME"]) and "修正" not in v: time_col = c_idx
                                if mod_time_col == -1 and "修正" in v and ("時間" in v or "TIME" in v): mod_time_col = c_idx
                                if po_col == -1 and any(k in v for k in ["採購單號", "採購單", "采购单", "採購"]): po_col = c_idx
                                if origin_col == -1 and any(k in v for k in ["出貨地", "出貨區", "出貨廠", "灌裝"]): origin_col = c_idx
                                if cust_col == -1 and any(k in v for k in ["對象", "客戶", "廠商", "CUSTOMER"]): cust_col = c_idx
                                if origin_col == -1 and any(k in v for k in ["出貨地", "出貨區", "出貨廠", "灌裝"]): origin_col = c_idx
                                if mfg_col == -1 and any(k in v for k in ["製造", "MFG", "生產日", "製日"]): mfg_col = c_idx
                                if exp_col == -1 and any(k in v for k in ["到期", "保存", "EXP", "期限", "效期", "批號到期"]) and "剩餘" not in v and "天數" not in v: exp_col = c_idx
                                if name_col == -1 and any(k in v for k in ["品名", "產品名稱", "PRODUCT", "NAME", "描述", "SPEC"]): name_col = c_idx

                            if batch_col != -1 and (loc_col != -1 or date_col != -1):
                                start_row = r_idx + 1
                                break

                        if batch_col == -1 or loc_col == -1:
                            batch_col = 2
                            date_col = 1
                            qty_col = 4
                            loc_col = 5
                            start_row = 2
                        # 找不到就留空（-1），不死寫固定欄號，以免抓到不相關欄位

                        for r_idx in range(start_row, len(rows)):
                            row = rows[r_idx]
                            if not row or len(row) == 0: continue

                            def get_cell_val(c):
                                return row[c] if c != -1 and c < len(row) else None

                            b_val = str(get_cell_val(batch_col) or "").strip().upper()
                            l_val = str(get_cell_val(loc_col) or "").strip().upper()
                            d_val = get_cell_val(date_col)
                            qty_val = str(get_cell_val(qty_col) or "").strip()
                            time_val = normalize_time_str(get_cell_val(time_col))
                            origin_val = str(get_cell_val(origin_col) or "").strip()
                            mt_val = normalize_time_str(get_cell_val(mod_time_col))
                            po_val = str(get_cell_val(po_col) or "").strip()
                            cust_val = str(get_cell_val(cust_col) or "").strip()
                            mfg_val = str(get_cell_val(mfg_col) or "").strip()
                            exp_val = str(get_cell_val(exp_col) or "").strip()
                            name_val = str(get_cell_val(name_col) or "").strip() if name_col != -1 else ""

                            # 若預設欄位非 10 碼批號，全列搜尋 10 碼英數混合批號
                            if len(b_val) != 10 or not any(c.isdigit() for c in b_val):
                                for cell in row:
                                    cell_str = str(cell or "").strip().upper()
                                    if len(cell_str) == 10 and any(c.isdigit() for c in cell_str) and any(c.isalpha() for c in cell_str) and "/" not in cell_str and "-" not in cell_str:
                                        b_val = cell_str
                                        break

                            if len(b_val) != 10 or not any(c.isdigit() for c in b_val):
                                continue

                            # 排除非台積電客戶 (例如南亞、長春、聯電、日月光)
                            if cust_val and any(non in cust_val for non in ["南亞", "長春", "聯電", "日月光"]) and "台積" not in cust_val:
                                continue

                            clean_loc = clean_location_str(l_val, self.mapping_dict)
                            is_tsmc = sheet_has_tsmc or ("台積" in cust_val if cust_val else False) or \
                                      any(k in l_val for k in ["台積", "18P", "15P", "12P", "14P", "AP", "F"]) or \
                                      (clean_loc in self.mapping_dict)
                            if not is_tsmc and cust_val and "台積" not in cust_val:
                                continue

                            norm_date = normalize_date_str(d_val)
                            
                            # 槽號驗證：槽號為 3~6 碼英數代號（如 E319、E308、E29J），排除誤抓之日期或時間字串
                            # 格式化時間 (統一為 4 碼如 0900)
                            t_final = time_val
                            if isinstance(d_val, datetime) and not t_final:
                                hm = f"{d_val.hour:02d}{d_val.minute:02d}"
                                if hm != "0000": t_final = hm

                            records.append({
                                "sheet": sheet_name,
                                "batch": b_val,
                                "qty": qty_val,
                                "loc": clean_loc,
                                "_vals": self.mapping_dict.get(clean_loc, []),
                                "long_code": self.mapping_dict.get(clean_loc, [""])[0] if isinstance(self.mapping_dict.get(clean_loc), list) and self.mapping_dict.get(clean_loc) else (self.mapping_dict.get(clean_loc) if isinstance(self.mapping_dict.get(clean_loc), str) else ""),
                                "date": norm_date,
                                "time": t_final,
                                "mod_time": mt_val,
                                "po": po_val,
                                "origin": origin_val,
                                "name": name_val if name_val else sheet_product_name,
                                "mfg_date": normalize_date_str(mfg_val),
                                "exp_date": normalize_date_str(exp_val)
                            })
                    wb.close()

                if not records:
                    messagebox.showinfo("匯入提示", f"在檔案 {os.path.basename(filepath)} 的所有 {sheet_count} 個分頁中，找不到任何有效的台積電排程資料！")
                    continue

                dialog = ImportRangeDialog(self, records, os.path.basename(filepath), sheet_count=sheet_count)
                self.wait_window(dialog)

                if not dialog.selected_records:
                    continue

                target_records = dialog.selected_records

                start_idx = 0
                for idx, entry in enumerate(self.entries):
                    if not entry["batch_var"].get().strip():
                        start_idx = idx
                        break
                else:
                    start_idx = len(self.entries)
                    
                needed_rows = start_idx + len(target_records)
                if needed_rows > len(self.entries):
                    self.add_input_rows(needed_rows - len(self.entries))
                    
                for i, rec in enumerate(target_records):
                    row_e = self.entries[start_idx + i]
                    row_e["batch_var"].set(rec.get("batch", ""))
                    if "qty_var" in row_e and rec.get("qty"):
                        row_e["qty_var"].set(rec["qty"])
                    row_e["loc_var"].set(rec.get("loc", ""))
                    if rec.get("date"): row_e["date_var"].set(rec["date"])
                    if rec.get("po"): row_e.get("po_var", tk.StringVar()).set(rec["po"])
                    if rec.get("name") and "name_var" in row_e: row_e["name_var"].set(rec["name"])
                    if rec.get("mfg_date") and "mfg_var" in row_e: row_e["mfg_var"].set(rec["mfg_date"])
                    if rec.get("exp_date") and "exp_var" in row_e: row_e["exp_var"].set(rec["exp_date"])
                    
                total_imported += len(target_records)
                
            except Exception as e:
                messagebox.showerror("匯入錯誤", f"解析檔案 {os.path.basename(filepath)} 時發生錯誤:\n{e}")
                
        if total_imported > 0:
            messagebox.showinfo("匯入成功", f"成功從所選檔案匯入 {total_imported} 筆！")


    def generate_files(self):
        if not os.path.exists(self.mapping_path):
            messagebox.showerror("錯誤", f"找不到對照表檔案:\n{self.mapping_path}")
            return
            
        do_3in1 = False # Disable 3-in-1 generation
        do_transport = False
        


        valid_data = []
        for idx, row in enumerate(self.entries):
            if not row["chk_var"].get():
                continue
                
            batch = row["batch_var"].get().strip().upper()
            loc = row["loc_var"].get().strip().upper()
            qty = row["qty_var"].get().strip()
            date_str = row["date_var"].get().strip()
            time_str = ""
            mod_time_str = ""
            
            if not batch and not loc:
                continue
            if not batch or not loc:
                messagebox.showerror("錯誤", f"第 {idx+1} 項資料不齊全！")
                return
            if len(batch) != 10:
                messagebox.showerror("錯誤", f"第 {idx+1} 項的批號長度錯誤！\n批號必須剛好 10 碼，目前輸入: {batch} (長度 {len(batch)})")
                return
                
            part_no_str = row.get("part_var", tk.StringVar()).get().strip() if "part_var" in row else ""
            po_str = row.get("po_var", tk.StringVar()).get().strip() if "po_var" in row else ""
            mfg_date_str = row.get("mfg_var", tk.StringVar()).get().strip() if "mfg_var" in row else ""
            exp_date_str = row.get("exp_var", tk.StringVar()).get().strip() if "exp_var" in row else ""
            valid_data.append({
                "batch": batch,
                "qty": qty,
                "loc": loc,
                "long_code": row.get("long_code_var", type("X", (), {"get": lambda: ""})()).get().strip().upper() if "long_code_var" in row else "",
                "date": date_str,
                "time": time_str,
                "mod_time": mod_time_str,
                "origin": "",
                "part_no": "4" + part_no_str if part_no_str and not part_no_str.startswith("4") else part_no_str,
                "po": po_str,
                "mfg_date": mfg_date_str,
                "exp_date": exp_date_str
            })
            
        if not valid_data:
            messagebox.showinfo("提示", "請至少勾選並輸入一筆有效資料！")
            return

        missing_locs = [data["loc"] for data in valid_data if data["loc"] not in self.mapping_dict]
        if missing_locs:
            missing_str = ", ".join(set(missing_locs))
            messagebox.showerror("錯誤", f"地點代號對照表中找不到以下地點：\n{missing_str}\n\n請先更新對照表後再試！")
            return

        self.show_loading("⏳ 正在產生所有報表，請稍候...")
        
        # 按出貨日分群，每個日期產生獨立資料夾
        groups = {}
        for data in valid_data:
            d_raw = data.get("date", "").strip()
            g_date_str = datetime.now().strftime('%Y%m%d')
            if d_raw:
                d_part = d_raw.split()[0]
                for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%Y%m%d", "%m/%d/%Y", "%d/%m/%Y"):
                    try:
                        dt_found = datetime.strptime(d_part, fmt)
                        g_date_str = dt_found.strftime('%Y%m%d')
                        break
                    except ValueError:
                        pass
            groups.setdefault(g_date_str, []).append(data)

        all_output_dirs = []
        total_success_3in1 = 0
        total_success_transport = False
        total_success_lorry = 0
        total_error_msgs = []
        mat_no = ""

        for _g_date_str, _g_data in groups.items():
            valid_data = _g_data
            output_dir = os.path.join(self.base_dir, f"N系小包報表輸出_{_g_date_str}")
            os.makedirs(output_dir, exist_ok=True)
            all_output_dirs.append(output_dir)
            success_3in1 = 0
            error_msgs = []
            success_transport = False
            success_lorry = 0

            if do_3in1:

                coa_crops = {}
                if os.path.exists(r'C:\Program Files\Tesseract-OCR\tesseract.exe'):
                    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
                else:
                    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe' 
                if self.coa_paths:
                    for img_path in self.coa_paths:
                        try:
                            orig_img = PILImage.open(img_path)
                            img_rgb = orig_img.convert('RGB')
                            w, h = orig_img.size
                        
                            # 移植伺服版的精確定位演算法
                            def parse_tsmc_query_table_accurate(coa_raw):
                                w, h = coa_raw.size
                                img_rgb = coa_raw.convert('RGB')
                                query_result_y = None
                                for y in range(int(h * 0.3), int(h * 0.9)):
                                    sample = [img_rgb.getpixel((x, y)) for x in range(int(w * 0.1), int(w * 0.9), max(1, int(w * 0.05)))]
                                    if sum(1 for p in sample if p[0] < 100 and p[1] < 160 and p[2] > 200) > len(sample) * 0.7:
                                        query_result_y = y
                                        break
                                start_y = query_result_y if query_result_y else int(h * 0.5)
                                btn_y_list = []
                                for y in range(start_y + 20, h):
                                    sample = [img_rgb.getpixel((x, y)) for x in range(15, 65, 2)]
                                    blue_cnt = sum(1 for p in sample if p[0] < 60 and p[2] > 180)
                                    if blue_cnt >= 8:
                                        btn_y_list.append(y)
                                btn_clusters = []
                                for y in btn_y_list:
                                    if not btn_clusters or y > btn_clusters[-1][-1] + 5:
                                        btn_clusters.append([y])
                                    else:
                                        btn_clusters[-1].append(y)
                                def find_border_line(start_y, direction, max_search=40):
                                    for step in range(max_search):
                                        curr_y = start_y + step * direction
                                        if curr_y <= 0 or curr_y >= h:
                                            break
                                        sample_xs = range(int(w * 0.2), int(w * 0.8), max(1, int(w * 0.05)))
                                        pixels = [img_rgb.getpixel((x, curr_y)) for x in sample_xs]
                                        if all(abs(p[0] - p[1]) < 8 and abs(p[1] - p[2]) < 8 and 150 < p[0] < 235 for p in pixels):
                                            if step > 1:
                                                return curr_y
                                    return None
                                if not btn_clusters:
                                    return None, []
                                first_btn_top = btn_clusters[0][0]
                                header_bottom = find_border_line(first_btn_top, -1, max_search=50) or (first_btn_top - 6)
                                data_rows = []
                                for cluster in btn_clusters:
                                    mid_y = int(sum(cluster) / len(cluster))
                                    row_t = find_border_line(mid_y, -1, max_search=30) or (cluster[0] - 6)
                                    row_b = find_border_line(mid_y, +1, max_search=30) or (cluster[-1] + 8)
                                    data_rows.append((max(0, row_t), min(h, row_b + 1)))
                                return header_bottom, data_rows

                            hb_struct, rows_struct = parse_tsmc_query_table_accurate(orig_img)
                            if hb_struct and rows_struct:
                                img_top = orig_img.crop((0, 0, w, hb_struct))
                            
                                if not hasattr(self, 'fallback_coa'):
                                    self.fallback_coa = []
                            
                                for row in rows_struct:
                                    img_row = orig_img.crop((0, row[0], w, row[1]))
                                    new_img = PILImage.new('RGB', (w, img_top.height + img_row.height), 'white')
                                    new_img.paste(img_top, (0, 0))
                                    new_img.paste(img_row, (0, img_top.height))
                                
                                    new_img = new_img.resize((new_img.width * 4, new_img.height * 4), PILImage.Resampling.LANCZOS)
                                
                                    self.fallback_coa.append(new_img)
                                
                                    # OCR 尋找此行的批號：優先使用 GCP Vision，失敗或超過額度則退回 Tesseract
                                    row_scaled = img_row.resize((img_row.width * 2, img_row.height * 2), PILImage.Resampling.LANCZOS)
                                    gcp_text = get_gcp_vision_text(row_scaled)
                                
                                    if gcp_text is not None:
                                        # GCP API 成功
                                        words = gcp_text.replace('\n', ' ').split()
                                        for text in words:
                                            digits = ''.join(c for c in text.strip() if c.isdigit())
                                            if len(digits) >= 6:
                                                coa_crops[digits] = new_img
                                    else:
                                        # Tesseract 備用方案
                                        d = pytesseract.image_to_data(row_scaled, output_type=Output.DICT)
                                        for i in range(len(d['text'])):
                                            text = d['text'][i].strip()
                                            digits = ''.join(c for c in text if c.isdigit())
                                            if len(digits) >= 6:
                                                coa_crops[digits] = new_img
                            else:
                                # 找不到結構，整張圖備用
                                if not hasattr(self, 'fallback_coa'):
                                    self.fallback_coa = []
                                orig_img_hr = orig_img.resize((orig_img.width * 2, orig_img.height * 2), PILImage.Resampling.LANCZOS)
                                self.fallback_coa.append(orig_img_hr)
                        except Exception as e:
                            print("OCR error:", e)

                for data in valid_data:
                    batch_no = data["batch"]
                    tank_no = data["tank"]
                    loc = data["loc"]
                    loc_code = data.get("long_code", "")
                
                    try:
                        wb = openpyxl.load_workbook(self.template_path)
                        ws = wb.worksheets[0]
                    
                        tank_row = find_row_by_label(ws, ['槽號']) or 5
                        batch_row = find_row_by_label(ws, ['批號']) or 7
                        loc_row = find_row_by_label(ws, ['送達地點', '地點']) or 11
                        mat_row = find_row_by_label(ws, ['料號']) or 3
                        sup_row = find_row_by_label(ws, ['供應商']) or 9
                        if data.get("part_no"):
                            ws.cell(row=mat_row, column=3).value = data["part_no"]
                    
                        raw_mat = str(ws.cell(row=mat_row, column=3).value or "").strip()
                        if raw_mat.startswith("4"):
                            mat_no = raw_mat[1:]
                        elif raw_mat:
                            mat_no = raw_mat
                        else:
                            mat_no = ""
                    
                        final_tank_no = "5" + tank_no
                        final_batch_no = "6" + batch_no
                    
                        ws.cell(row=tank_row, column=3).value = final_tank_no
                        ws.cell(row=batch_row, column=3).value = final_batch_no
                        ws.cell(row=loc_row, column=3).value = loc_code
                    
                        images_to_keep = []
                        for img in ws._images:
                            if img.height < 150 and img.width > 200:
                                images_to_keep.append(img)
                        ws._images = images_to_keep
                    
                        c3_val = ws.cell(row=mat_row, column=3).value or ""
                        c6_val = ws.cell(row=sup_row, column=3).value or ""
                        qr_str = f"||{c3_val}||{final_tank_no}||{final_batch_no}||{c6_val}||{loc_code}"
                    
                        qr = qrcode.QRCode(box_size=4, border=2)
                        qr.add_data(qr_str)
                        qr.make(fit=True)
                        raw_img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
                    
                        offset_x = 35
                        offset_y = 45
                        new_width = raw_img.width + offset_x
                        new_height = raw_img.height + offset_y
                        img_qr = Image.new('RGBA', (new_width, new_height), (255,255,255,0))
                        img_qr.paste(raw_img, (offset_x, offset_y))
                    
                        img_byte_arr = BytesIO()
                        img_qr.save(img_byte_arr, format='PNG')
                        img_byte_arr.seek(0)
                    
                        new_qr = OpenpyxlImage(img_byte_arr)
                        new_qr.anchor = 'F2'
                        ws.add_image(new_qr)
                    
                        safe_loc = "".join(c for c in loc if c.isalnum() or c in (' ', '_', '-')).rstrip()
                        if not safe_loc:
                            safe_loc = "未命名地點"
                    
                        # 產生檔名規格：[出貨日期]. [地點]台積電槽車barcode三合一單.xlsx (例如: 2026.8.18. 18P3B台積電槽車barcode三合一單.xlsx)
                        date_raw = data.get("date", "").strip()
                        dt_file = None
                        if date_raw:
                            date_part = date_raw.split()[0]
                            for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%Y%m%d", "%m/%d/%Y", "%d/%m/%Y"):
                                try:
                                    dt_file = datetime.strptime(date_part, fmt)
                                    break
                                except ValueError:
                                    pass
                        if not dt_file:
                            dt_file = datetime.now()
                        

                        # Insert COA Crop
                        found_coa = False
                        user_digits = ''.join(c for c in batch_no if c.isdigit())
                        for k_batch, crop_img in coa_crops.items():
                            if user_digits in k_batch or k_batch in user_digits:
                                img_byte_arr2 = BytesIO()
                                crop_img.save(img_byte_arr2, format='PNG', dpi=(600, 600))
                                img_byte_arr2.seek(0)
                                xl_img = OpenpyxlImage(img_byte_arr2)
                                xl_img.width = int(round(24.1 * 96 / 2.54))   # 24.1 公分
                                xl_img.height = int(round(11.51 * 96 / 2.54)) # 11.51 公分
                            
                                col_off = pixels_to_EMU(15) # 向右微調
                                row_off = 0
                                _from = AnchorMarker(col=5, colOff=col_off, row=4, rowOff=row_off)
                                size = XDRPositiveSize2D(pixels_to_EMU(xl_img.width), pixels_to_EMU(xl_img.height))
                                xl_img.anchor = OneCellAnchor(_from=_from, ext=size)
                                ws.add_image(xl_img)
                                found_coa = True
                                break
                    

                        if not found_coa and self.coa_paths:
                            error_msgs.append(f"⚠️ 警告: 批號 {batch_no} OCR未找到完全吻合的截圖，已留白處理，請人工確認！")

                        date_prefix = f"{dt_file.year}.{dt_file.month}.{dt_file.day}. "
                        tank_part = f"{tank_no} " if tank_no else ""
                        base_filename = f"{date_prefix}{tank_part}{safe_loc}台積電槽車barcode三合一單.xlsx"
                    
                        # 修正產出資料夾結構為 [出貨日] [廠區] [槽號]
                        date_MMDD = f"{dt_file.month:02d}{dt_file.day:02d}"
                        safe_tank = str(tank_no).strip() if tank_no else ""
                        loc_sub_dir = f"{date_MMDD} {safe_loc} {safe_tank}".strip()
                        
                        if self.folder_mode_var.get() == 2:
                            loc_folder = os.path.join(output_dir, safe_loc)
                        else:
                            loc_folder = os.path.join(output_dir, safe_loc, loc_sub_dir)
                    
                        if not os.path.exists(loc_folder):
                            os.makedirs(loc_folder)
                        output_path = os.path.join(loc_folder, base_filename)
                        
                        output_filename = base_filename
                        wb.save(output_path)
                        wb.close()
                        success_3in1 += 1
                    except Exception as e:
                        error_msgs.append(f"處理三合一單 {loc}_{batch_no} 失敗: {e}")

                if do_transport:
                    try:
                        transport_path = os.path.join(output_dir, "運輸通知表.xlsx")
                        generate_transport_notice_file(transport_path, valid_data, mat_no=mat_no)
                        success_transport = True
                    except Exception as e:
                        error_msgs.append(f"產生運輸通知表失敗: {e}")

            if True:

                lorry_sources = list(getattr(self, "imported_lorry_files", []))
                if not lorry_sources:
                    lorry_sources = glob.glob(os.path.join(self.base_dir, "Chemical_Lorry*.xlsx"))
                    if not lorry_sources:
                        error_msgs.append("⚠️ 找不到任何 Chemical_Lorry 檔案作為來源！")

                lorry_generated_batches = set()
                
                for l_path in lorry_sources:
                    with open(os.path.join(os.path.expanduser('~'), 'Desktop', 'debug_lorry.txt'), 'a', encoding='utf-8') as dfile:
                        dfile.write(f"\n--- Processing {l_path} ---\n")
                        dfile.write(f"valid_data has {len(valid_data)} items\n")

                    orig_filename = os.path.splitext(os.path.basename(l_path))[0]
                    orig_ext = os.path.splitext(l_path)[1]
                    base_lorry_name = orig_filename.rsplit('-', 1)[0] if '-' in orig_filename else orig_filename

                    try:
                        wb_data = openpyxl.load_workbook(l_path, data_only=True)
                        ws_data = wb_data.active
                        l_batch = str(ws_data.cell(row=7, column=1).value or "").strip().upper()
                        wb_data.close()
                        
                        fn_upper = orig_filename.upper()
                        
                        # 找出所有批號吻合的項目 (同批號多廠區)
                        matched_items = []
                        for item in valid_data:
                            b_no = str(item.get("batch", "")).strip().upper()
                            # 批號必須吻合 (不強制檔名有廠區，因為原始檔名通常沒有廠區)
                            if b_no and (b_no in l_batch or b_no in fn_upper):
                                matched_items.append((item, b_no))
                                
                        for item, l_batch_found in matched_items:
                            # 每次寫入都重新載入原始檔，避免多廠區時資料互相覆蓋
                            wb_l = openpyxl.load_workbook(l_path, data_only=False)
                            ws_l = wb_l.active
                            
                            l_loc = item.get("loc", "")
                            d_str = item.get("date", "")
                            
                            # Convert d_str to YYYY/MM/DD format
                            try:
                                for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%Y%m%d", "%m/%d/%Y", "%d/%m/%Y"):
                                    try:
                                        _dt = datetime.strptime(d_str.split()[0], fmt)
                                        d_str_fmt = f"{_dt.year}/{_dt.month:02d}/{_dt.day:02d}"
                                        break
                                    except ValueError:
                                        pass
                                else:
                                    d_str_fmt = d_str
                            except:
                                d_str_fmt = d_str

                            # Convert mfg_date to YYYY/MM/DD format
                            try:
                                mfg_str = item.get('mfg_date', '')
                                for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%Y%m%d", "%m/%d/%Y", "%d/%m/%Y"):
                                    try:
                                        _mdt = datetime.strptime(str(mfg_str).split()[0], fmt)
                                        mfg_str_fmt = f"{_mdt.year}/{_mdt.month:02d}/{_mdt.day:02d}"
                                        break
                                    except ValueError:
                                        pass
                                else:
                                    mfg_str_fmt = str(mfg_str)
                            except:
                                mfg_str_fmt = str(item.get('mfg_date', ''))

                            long_code_val = item.get('long_code', '')
                            # 用文字搜尋表頭的位置後再寫入，寫入位置為「表頭的正下方一格」
                            lorry_field_map = {
                                "fabphase": (long_code_val, 7, 7), # 預設 G7
                                "tsmcfab": (long_code_val, 7, 2),  # 預設 B7
                                "deliverydate": (d_str_fmt, 7, 3), # 預設 C7
                                "deliverdate": (d_str_fmt, 7, 3),  # 預防拼寫差異
                                "manufacturedate": (mfg_str_fmt, 7, 6), # 預設 F7
                                "manufacturingdate": (mfg_str_fmt, 7, 6),
                            }
                            
                            lorry_found_keys = set()
                            # 掃描前 15 列、前 20 欄尋找表頭
                            for r_idx in range(1, min(ws_l.max_row + 5, 16)):
                                for c_idx in range(1, min(ws_l.max_column + 5, 22)):
                                    cell_val = ws_l.cell(row=r_idx, column=c_idx).value
                                    if cell_val and isinstance(cell_val, str):
                                        ck = cell_val.lower().replace(" ", "")
                                        for sk, (sv, fb_row, fb_col) in lorry_field_map.items():
                                            if sv and sk in ck and sk not in lorry_found_keys:
                                                # 表頭的正下方一格 (r_idx + 1)
                                                ws_l.cell(row=r_idx + 1, column=c_idx).value = sv
                                                lorry_found_keys.add(sk)
                                                
                            # 沒找到的 fallback 到固定格子
                            for sk, (sv, fb_row, fb_col) in lorry_field_map.items():
                                if sv and sk not in lorry_found_keys:
                                    ws_l.cell(row=fb_row, column=fb_col).value = sv

                            mmdd = "0000"
                            if d_str:
                                for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%Y%m%d", "%m/%d/%Y", "%d/%m/%Y"):
                                    try:
                                        dt_l = datetime.strptime(d_str.split()[0], fmt)
                                        mmdd = f"{dt_l.month:02d}{dt_l.day:02d}"
                                        break
                                    except ValueError:
                                        pass
                            if mmdd == "0000":
                                now_l = datetime.now()
                                mmdd = f"{now_l.month:02d}{now_l.day:02d}"
                            
                            safe_loc = "".join(c for c in l_loc if c.isalnum() or c in (' ', '_', '-')).rstrip()
                            loc_sub_dir = f"{mmdd} {safe_loc} {l_batch_found}".strip()
                            
                            if self.folder_mode_var.get() == 2:
                                current_loc_folder = os.path.join(output_dir, safe_loc)
                            else:
                                current_loc_folder = os.path.join(output_dir, safe_loc, loc_sub_dir)
                                
                            os.makedirs(current_loc_folder, exist_ok=True)

                            lorry_out_name = f"{base_lorry_name}-{l_batch_found} {mmdd} {l_loc}{orig_ext}"
                            out_l_path = os.path.join(current_loc_folder, lorry_out_name)
                            wb_l.save(out_l_path)
                            wb_l.close()
                            
                            success_lorry += 1
                            lorry_generated_batches.add(l_batch_found)
                    except PermissionError as le:
                        import os as _os2
                        locked_file = _os2.path.basename(str(le).split("'")[-2]) if "'" in str(le) else "Chemical_Lorry 檔案"
                        error_msgs.append(
                            f"🔒 {locked_file} 正在被 Excel 開啟中，無法寫入！\n"
                            f"   → 請先關閉 Excel 後，重新執行產生，即可解決此問題。"
                        )

                    except Exception as le:
                        error_msgs.append(f"產生 Chemical_Lorry 失敗: {le}")

                # After checking all Lorry files, see which ones missed
                for item in valid_data:
                    b_no = str(item.get("batch", "")).strip().upper()
                    if b_no not in lorry_generated_batches:
                        # if it failed because of factory, it's already in error_msgs, but it's fine to just add a general missing one if not in there
                        if not any(b_no in e for e in error_msgs):
                            error_msgs.append(f"⚠️ 批號 {b_no}：在來源 Lorry 檔案中找不到，無法產出該筆履歷。")


            # 快取 session
            try:
                for target_path in [os.path.join(self.base_dir, "last_generated_session.json")]:
                    with open(target_path, "w", encoding="utf-8") as f:
                        json.dump(valid_data, f, ensure_ascii=False, indent=2)
            except Exception:
                pass

            # 累計至全域
            total_success_3in1 += success_3in1
            total_success_lorry += success_lorry
            if success_transport:
                total_success_transport = True
            total_error_msgs.extend(error_msgs)

        # 全部日期群組跑完後，處理 COA 表單
        success_coa = 0
        if getattr(self, "imported_coa_files", None):
            self.show_loading("⏳ 正在產生 COA 表單，請稍候...")
            
            # prepare valid_batches - key = "BATCH|LOC" to support same batch going to multiple fabs
            valid_batches = {}
            for row in self.entries:
                if row["chk_var"].get():
                    b_val = row["batch_var"].get().strip().upper()
                    l_val = row["loc_var"].get().strip().upper() if "loc_var" in row else ""
                    if b_val:
                        # key 用 批號|廠區 確保同批號不同廠區各自獨立
                        vb_key = f"{b_val}|{l_val}" if l_val else b_val
                        valid_batches[vb_key] = row
            
            lorry_data_map = {}
            if hasattr(self, "imported_lorry_files") and self.imported_lorry_files:
                try:
                    for l_file in self.imported_lorry_files:
                        try:
                            src_wb_l = openpyxl.load_workbook(l_file, data_only=True)
                            src_ws_l = src_wb_l.active
                            for r in range(7, src_ws_l.max_row + 1):
                                val = str(src_ws_l.cell(row=r, column=1).value or "").strip().upper()
                                if val and val not in lorry_data_map:
                                    col_b = str(src_ws_l.cell(row=r, column=2).value or "").strip()
                                    raw_c = src_ws_l.cell(row=r, column=3).value
                                    if isinstance(raw_c, datetime):
                                        col_c = f"{raw_c.year}/{raw_c.month}/{raw_c.day}"
                                    else:
                                        col_c = str(raw_c or "").strip().split()[0] if raw_c else ""
                                    col_g = str(src_ws_l.cell(row=r, column=7).value or "").strip()
                                    lorry_data_map[val] = {"b": col_b, "c": col_c, "g": col_g}
                            src_wb_l.close()
                        except Exception:
                            pass
                except Exception:
                    pass

            for file_path in self.imported_coa_files:
                try:
                    base_name, ext = os.path.splitext(os.path.basename(file_path))
                    fn_upper = base_name.upper()

                    # 收集所有批號吻合的 vb_key（同批號不同廠會有多個）
                    matched_keys = []
                    for vb_key, vb_row in valid_batches.items():
                        b_part = vb_key.split("|")[0]
                        if b_part in fn_upper:
                            matched_keys.append(vb_key)
                    if not matched_keys:
                        found_batch = self._extract_batch_from_coa(file_path)
                        if found_batch:
                            for vb_key, vb_row in valid_batches.items():
                                b_part = vb_key.split("|")[0]
                                if b_part == found_batch or b_part in found_batch or found_batch in b_part:
                                    matched_keys.append(vb_key)
                    if not matched_keys:
                        total_error_msgs.append(f"COA: 找不到對應批號: {os.path.basename(file_path)}")
                        continue

                    for matched_key in matched_keys:
                        try:
                            matched_batch = matched_key.split("|")[0]

                            row = valid_batches[matched_key]
                            loc_str = row["loc_var"].get().strip()
                            import re
                            fc_match = re.search(r'[A-Za-z0-9]+', loc_str)
                            factory_code = fc_match.group(0) if fc_match else loc_str
                            date_str = row["date_var"].get().strip()
                            formatted_date = date_str.replace("/", "").replace("-", "")

                            import os as _os
                            import re
                            
                            # base_name 已經在前面去過副檔名了，直接處理
                            # 移除 TSMC字樣 (不分大小寫)
                            clean_base = re.sub(r'(?i)\s*TSMC\s*', ' ', base_name)
                            
                            # 移除原有批號，避免後續重複加上
                            for b_candidate in list(valid_batches.keys()):
                                b_only = b_candidate.split('|')[0]
                                clean_base = clean_base.replace(b_only, " ")
                            clean_base = clean_base.rstrip("-_ ").strip()

                            date_MMDD = formatted_date[4:8] if len(formatted_date) >= 8 else formatted_date
                            new_base = f"{clean_base} {matched_batch} {date_MMDD} {factory_code}"
                            # 合併多餘空白
                            new_base = re.sub(r'\s+', ' ', new_base).strip()
                            output_dir = os.path.join(self.base_dir, f"N系小包報表輸出_{formatted_date}")
                            if output_dir not in all_output_dirs:
                                all_output_dirs.append(output_dir)

                            qty_str = row["qty_var"].get().strip()
                            safe_loc = "".join(c for c in loc_str if c.isalnum() or c in (' ', '_', '-')).rstrip()
                            if not safe_loc: safe_loc = "未命名地點"
                            loc_sub_dir = f"{date_MMDD} {safe_loc} {matched_batch}".strip()

                            if self.folder_mode_var.get() == 2:
                                loc_folder = os.path.join(output_dir, safe_loc)
                            else:
                                loc_folder = os.path.join(output_dir, safe_loc, loc_sub_dir)
                                
                            os.makedirs(loc_folder, exist_ok=True)
                            new_file_path = os.path.join(loc_folder, new_base + ext)

                            col_b, col_g, col_c = "", "", ""
                            if matched_batch in lorry_data_map:
                                l_info = lorry_data_map[matched_batch]
                                col_b = l_info.get("b", "")
                                col_c = l_info.get("c", "")
                                col_g = l_info.get("g", "")

                            po_no = ""
                            matched_row = row
                            if matched_row:
                                if "po_var" in matched_row:
                                    full_po = matched_row["po_var"].get().strip()
                                    po_no = full_po[:10] if len(full_po) >= 10 else full_po
                                if "mfg_var" in matched_row:
                                    col_c = matched_row["mfg_var"].get().strip() or col_c
                                
                                long_code = matched_row.get("long_code_var", type("X", (), {"get": lambda: ""})()).get().strip()
                                loc_str_tmp = matched_row.get("loc_var", type("X", (), {"get": lambda: ""})()).get().strip()
                                if long_code or loc_str_tmp:
                                    col_g = long_code or loc_str_tmp

                            # Date formatting
                            date_str_fmt = date_str
                            for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%Y%m%d"):
                                try:
                                    _dt = datetime.strptime(date_str.split()[0], fmt)
                                    date_str_fmt = f"{_dt.year}/{_dt.month:02d}/{_dt.day:02d}"
                                    break
                                except:
                                    pass
                                    
                            col_c_fmt = col_c
                            for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%Y%m%d"):
                                try:
                                    _dt = datetime.strptime(str(col_c).split()[0], fmt)
                                    col_c_fmt = f"{_dt.year}/{_dt.month:02d}/{_dt.day:02d}"
                                    break
                                except:
                                    pass
                                    
                            long_code_val = row.get("long_code_var", type("X", (), {"get": lambda: ""})()).get().strip()

                            if ext.lower() in ['.xlsx', '.xls']:
                                wb = openpyxl.load_workbook(file_path)
                                ws = wb.active
                                
                                field_map = {
                                    "tsmcfab": (long_code_val, 6),
                                    "fabphase": (col_g, 7),
                                    "shipqty": (qty_str, 8),
                                    "manufacturingdate": (col_c_fmt, 11),
                                    "deliverdate": (date_str_fmt, 12),
                                    "pono": (po_no, 14),
                                }
                                found_keys = set()
                                for r_idx in range(1, ws.max_row + 20):
                                    cell_val = ws.cell(row=r_idx, column=1).value
                                    if cell_val and isinstance(cell_val, str):
                                        cell_key = cell_val.lower().replace(" ", "")
                                        for search_key, (set_val, fallback_row) in field_map.items():
                                            if set_val and search_key in cell_key:
                                                ws.cell(row=r_idx, column=2).value = set_val
                                                found_keys.add(search_key)
                                
                                for search_key, (set_val, fallback_row) in field_map.items():
                                    if set_val and search_key not in found_keys:
                                        ws.cell(row=fallback_row, column=2).value = set_val

                                if matched_row:
                                    rem_days = matched_row.get('rem_var', tk.StringVar()).get().strip()
                                    if rem_days:
                                        found = False
                                        for r_idx in range(1, ws.max_row + 20):
                                            cell_val = ws.cell(row=r_idx, column=1).value
                                            if cell_val and isinstance(cell_val, str) and "remainlifetime" in cell_val.lower().replace(" ", ""):
                                                ws.cell(row=r_idx, column=7).value = rem_days
                                                found = True
                                                break

                                wb.save(new_file_path)
                                try:
                                    wb.close()
                                except:
                                    pass
                            elif ext.lower() == '.csv':
                                import csv
                                try:
                                    with open(file_path, 'r', encoding='big5') as f:
                                        reader = list(csv.reader(f))
                                except UnicodeDecodeError:
                                    with open(file_path, 'r', encoding='utf-8-sig', errors='ignore') as f:
                                        reader = list(csv.reader(f))
                                        
                                field_map_csv = {
                                    "tsmcfab": (long_code_val, 5),
                                    "fabphase": (col_g, 6),
                                    "shipqty": (qty_str, 7),
                                    "manufacturingdate": (col_c_fmt, 10),
                                    "deliverdate": (date_str_fmt, 11),
                                    "pono": (po_no, 13),
                                }
                                found_keys_csv = set()
                                for row_data in reader:
                                    if row_data and len(row_data) > 0:
                                        cell_key = str(row_data[0]).lower().replace(" ", "")
                                        for search_key, (set_val, fallback_idx) in field_map_csv.items():
                                            if set_val and search_key in cell_key:
                                                while len(row_data) <= 1:
                                                    row_data.append("")
                                                row_data[1] = set_val
                                                found_keys_csv.add(search_key)
                                
                                for search_key, (set_val, fallback_idx) in field_map_csv.items():
                                    if set_val and search_key not in found_keys_csv:
                                        while len(reader) <= fallback_idx:
                                            reader.append([''] * 8)
                                        while len(reader[fallback_idx]) <= 1:
                                            reader[fallback_idx].append("")
                                        reader[fallback_idx][1] = set_val
                                    
                                if matched_row:
                                    rem_days = matched_row.get('rem_var', tk.StringVar()).get().strip()
                                    if rem_days:
                                        found = False
                                        for row_data in reader:
                                            if row_data and len(row_data) > 0 and "remainlifetime" in str(row_data[0]).lower().replace(" ", ""):
                                                while len(row_data) <= 6:
                                                    row_data.append("")
                                                row_data[6] = rem_days
                                                found = True
                                                break

                                with open(new_file_path, 'w', encoding='big5', errors='ignore', newline='') as f:
                                    writer = csv.writer(f)
                                    writer.writerows(reader)
                            success_coa += 1
                        except PermissionError as e:
                            import os as _os2
                            locked_file = _os2.path.basename(new_file_path)
                            total_error_msgs.append(f"🔒 COA 檔案被佔用: {locked_file} 正在被開啟中，無法寫入！")
                        except Exception as e:
                            total_error_msgs.append(f"處理 COA {os.path.basename(file_path)} 失敗: {str(e)}")
                except Exception as e:
                    total_error_msgs.append(f"處理 COA {os.path.basename(file_path)} 失敗: {str(e)}")

        # 全部日期群組跑完後，顯示訊息
        self.hide_loading()
        msg_parts = []
        if do_3in1:
            msg_parts.append(f"• 三合一單：成功產生 {total_success_3in1} 份")
        if do_transport:
            status_str = "成功" if total_success_transport else "失敗"
            total_count = sum(len(g) for g in groups.values())
            msg_parts.append(f"• 運輸通知表：{status_str} (共 {total_count} 筆排程卡片)")

        if True:
            msg_parts.append(f"• 單列 Chemical_Lorry：成功產生 {total_success_lorry} 份")
        if getattr(self, "imported_coa_files", None) and success_coa > 0:
            msg_parts.append(f"• COA 表單：成功產生 {success_coa} 份")

        dirs_str = "\n".join(all_output_dirs) if all_output_dirs else "(無產出資料夾)"
        msg = "\n".join(msg_parts) + f"\n\n檔案已儲存於資料夾：\n{dirs_str}"

        if total_error_msgs:
            msg += "\n\n部分錯誤 / 警告:\n" + "\n".join(set(total_error_msgs)) # deduplicate errors just in case

            messagebox.showwarning("完成 (但有部分錯誤)", msg)
        else:
            messagebox.showinfo("成功", msg)

        for d in all_output_dirs:
            os.startfile(d)

if __name__ == "__main__":
    app = App()
    app.mainloop()
