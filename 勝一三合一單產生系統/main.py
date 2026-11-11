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

# ================= 產品品名與固定充填重量、料號對照表 =================
PRODUCT_WEIGHT_MAP = {
    "CPNE4R": "6000",
    "SEP73E4": "6000",
    "SEP73E5": "6000",
    "PMAHQ": "6000",
    "PMAHQ(R)": "6000",
    "PMAHQR": "6000",
    "IPA": "4300",
    "IPA HQ": "4300",
    "IPAHQ": "4300",
    "PMA": "6000",
    "CPNE4": "6000",
    "EDG": "4300",
    "BDGE": "4300",
    "SET100": "4300",
}

SHINYI_PRODUCT_PART_MAP = {
    "CPNE4R": "L2C9173",
    "SEP73E4": "L269100",
    "SEP73E5": "L2C9100",
    "PMAHQ": "L2C9501",
    "PMAHQ(R)": "L2R9501",
    "PMAHQR": "L2R9501",
}

def get_product_weight(product_name):
    if not product_name:
        return "6000"
    p = str(product_name).strip()
    return PRODUCT_WEIGHT_MAP.get(p, PRODUCT_WEIGHT_MAP.get(p.upper(), "6000"))

def parse_mfg_date_from_batch(batch_str):
    """
    從勝一批號前 5 碼解析製造日期 (ManufactureDate):
    例如 '26B05S93T1' -> 26(2026年), B(11月), 05(5日) -> datetime(2026, 11, 5)
    月份碼: 1~9 為 1~9月, A=10月, B=11月, C=12月 (或 X/Y/Z 備用)
    """
    if not batch_str or len(batch_str) < 5:
        return None
    s = str(batch_str).strip().upper()
    try:
        yy = int(s[0:2])
        m_char = s[2]
        dd = int(s[3:5])
        month_map = {
            '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9,
            'A': 10, 'B': 11, 'C': 12, 'X': 10, 'Y': 11, 'Z': 12
        }
        mm = month_map.get(m_char)
        if mm and 1 <= dd <= 31:
            return datetime(2000 + yy, mm, dd)
    except Exception:
        pass
    return None

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
    """
    將勝一排程中的各種指送地名稱正規化為標準短代號 (如 12P3, A6A0, 15BP5A, AP7P2B, FB30, F20P1, F22P1B, 6廠 等)
    """
    if not loc:
        return ""
    s = str(loc).strip().upper()
    if mapping_dict and s in mapping_dict:
        return s

    # 1. 移除括號內的中文說明 (如 "(竹南A廠）"、"(竹南B廠)")，但保留純英文括號如 (A)、(B)、(R) 轉為無括號後綴
    s_norm = s.replace("（", "(").replace("）", ")")
    s_norm = re.sub(r'\(([A-Z0-9]{1,3})\)', r'\1', s_norm)
    s_norm = re.sub(r'\([^)]*\)', '', s_norm)
    s_norm = re.sub(r'\([^)]*$', '', s_norm)

    # 2. 特殊廠區關鍵字優先匹配
    if "FB30" in s_norm or "B30" in s_norm:
        return "FB30" if (not mapping_dict or "FB30" in mapping_dict) else "B30"
    if "A6A0" in s_norm:
        return "A6A0"
    if "A6B0" in s_norm:
        return "A6B0"
    if "A5B0" in s_norm:
        return "A5B0"
    if "15B" in s_norm and "P5A" in s_norm:
        return "15BP5A"
    if "AP02D" in s_norm:
        return "AP02D"

    # 3. 針對單純幾廠 (如 台積3廠 -> 3廠, 台積8廠 -> 8廠, 台積台南6廠 -> 6廠)
    m_single_fab = re.search(r'(?:台積電?|新竹|台中|中科|台南|南科|高雄|寶山|竹南|龍潭)*([235678])廠(?![A-Z0-9\-]*P)', s_norm)
    if m_single_fab:
        cand = f"{m_single_fab.group(1)}廠"
        if not mapping_dict or cand in mapping_dict:
            return cand

    # 4. 針對 F20 / F22 等代號 (如 台積寶山廠F20P1 -> F20P1, 高雄廠F22P1B -> F22P1B)
    m_f2x = re.search(r'(F2[02]P\d+[A-Z]?)', s_norm)
    if m_f2x:
        cand = m_f2x.group(1)
        if not mapping_dict or cand in mapping_dict:
            return cand
        short_cand = cand[1:]  # 20P1 / 22P1B
        if mapping_dict and short_cand in mapping_dict:
            return short_cand
        return cand

    # 5. 針對 AP 系列 (如 AP7P1, AP7P2A, AP7P2B, AP8)
    m_ap = re.search(r'(AP\d+(?:P\d+[A-Z]?)?)', s_norm)
    if m_ap:
        cand = m_ap.group(1)
        if not mapping_dict or cand in mapping_dict:
            return cand

    # 6. 移除地名與連接符號後直接比對
    cleaned = re.sub(r'台積電?|新竹|台中|中科|台南|南科|高雄|寶山|竹南|龍潭|廠|[-_\s]', '', s_norm)
    if mapping_dict and cleaned in mapping_dict:
        return cleaned
    if cleaned.startswith("F") and len(cleaned) > 1 and mapping_dict and cleaned[1:] in mapping_dict:
        return cleaned[1:]

    # 7. 擷取 12P1~18P8 等標準 P 代號
    m_loc = re.search(r'(\d{1,2}B?P\d+[A-Z]?)', cleaned)
    if m_loc:
        val = m_loc.group(1)
        if not mapping_dict or val in mapping_dict:
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

        # 2. 筆數快速按鈕列 + 全選/全部取消按鈕
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
        tk.Label(count_bar, text="筆", font=("Arial", 9)).pack(side="left", padx=(0, 12))

        tk.Button(
            count_bar,
            text="☑ 全選",
            command=lambda: self.select_all_tree_items(True),
            font=("Arial", 9, "bold"),
            bg="#E8F5E9",
            fg="#1B5E20",
            padx=8,
            cursor="hand2"
        ).pack(side="left", padx=3)

        tk.Button(
            count_bar,
            text="☐ 全部取消",
            command=lambda: self.select_all_tree_items(False),
            font=("Arial", 9, "bold"),
            bg="#FFEBEE",
            fg="#C62828",
            padx=8,
            cursor="hand2"
        ).pack(side="left", padx=3)

        # 預覽表格區 (採用專業 Treeview 多欄呈現，欄寬自由拖拉，全資料完整展示)
        preview_frame = tk.LabelFrame(self, text="📋 即將匯入資料即時預覽 (點擊『☑選取』表頭或上方按鈕可全選/全部取消)", font=("Arial", 10, "bold"), padx=6, pady=6, fg="#002060")
        preview_frame.pack(fill="both", expand=True, pady=(0, 10))

        # 定義 Treeview 欄位
        columns = ("chk", "idx", "sheet", "date", "time", "batch", "tank", "product", "loc", "long_code")
        self.tree = ttk.Treeview(preview_frame, columns=columns, show="headings", selectmode="none")

        col_defs = [
            ("chk", "✅選取 (點我全選/取消)", 135, "center"),
            ("idx", "項次", 50, "center"),
            ("sheet", "來源分頁", 130, "w"),
            ("date", "出貨日期 📅", 105, "center"),
            ("time", "到廠時間", 85, "center"),
            ("batch", "批號 (10~11碼)", 125, "center"),
            ("tank", "槽號", 75, "center"),
            ("product", "品名 (產品)", 95, "center"),
            ("loc", "指送地點", 95, "center"),
            ("long_code", "地點長代號 (全稱)", 220, "w")
        ]

        for col_id, heading_text, width, anchor in col_defs:
            if col_id == "chk":
                self.tree.heading(col_id, text=heading_text, anchor=anchor, command=self.toggle_all_tree_items)
            else:
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

    def select_all_tree_items(self, select=True):
        mark = "☑" if select else "☐"
        items = self.tree.get_children()
        for item_id in items:
            vals = list(self.tree.item(item_id, "values"))
            vals[0] = mark
            self.tree.item(item_id, values=vals)
        checked = len(items) if select else 0
        self.btn_confirm.config(text=f"🚀 確認將這 {checked} 筆匯入系統")

    def toggle_all_tree_items(self):
        items = self.tree.get_children()
        if not items:
            return
        all_checked = all(self.tree.item(item_id, "values")[0] == "☑" for item_id in items)
        self.select_all_tree_items(not all_checked)

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
            long_code_str = rec.get("long_code") or getattr(self.parent_app, "mapping_dict", {}).get(loc_str, "")
            prod_str = rec.get("product") or ""

            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            self.tree.insert(
                "",
                "end",
                values=(
                    "☑",
                    f"[{idx+1:02d}]",
                    sheet_name,
                    d_str,
                    t_str,
                    b_str,
                    tank_str,
                    prod_str,
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

        if not selected_recs:
            messagebox.showwarning("尚未勾選", "請至少勾選 1 筆要匯入的排程資料，或點擊「❌ 取消」關閉視窗！")
            return
                
        self.selected_records = selected_recs
        self.destroy()

# ================= 核心邏輯 =================

def get_tank_from_batch(batch):
    raw = batch.strip()  # 不轉大寫，嚴格要求 T1 本身必須是大寫
    if not raw:
        return ""
    # 10 碼或 11 碼都合法，但最後 2 碼必須嚴格是大寫 T1
    if len(raw) in (10, 11):
        if raw[-2:] != "T1":
            return "批號格式錯誤(尾碼非T1)"
        return raw[5:-2]
    return "長度錯誤"

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
        cell_f3 = ws.cell(row=r3, column=c6, value=time_val)
        
        ws.merge_cells(start_row=r4, start_column=c2, end_row=r4, end_column=c3)
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
        
        if item.get("mod_time", "").strip():
            render_notice_card(curr_row, 8, True, item)
            
        curr_row += 7

    wb.save(output_path)
    wb.close()

def build_single_row_lorry_workbook(src_ws, target_row, max_cols=None, override_fields=None):
    """
    從多列或範本 Chemical_Lorry 工作表擷取單列產生新活頁簿 (表頭 1~6 列 + 資料第 7 列)。
    支援動態偵測第 6 列表頭有效欄數 (12~16 欄)，並支援透過 override_fields 覆寫欄位。
    """
    new_wb = openpyxl.Workbook()
    new_ws = new_wb.active
    new_ws.title = "工作表1" if "履歷" in str(src_ws.title) else src_ws.title

    # 動態偵測第 6 列實際表頭欄數
    if max_cols is None:
        detected = 0
        for c in range(1, min(35, src_ws.max_column + 1)):
            if src_ws.cell(6, c).value is not None:
                detected = c
        max_cols = detected if detected > 0 else min(20, src_ws.max_column)

    # 複製欄寬
    for col_idx in range(1, max_cols + 1):
        col_letter = get_column_letter(col_idx)
        col_dim = src_ws.column_dimensions.get(col_letter)
        if col_dim and col_dim.width:
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

    # 若有指定覆寫欄位 (例如以範本產生新批號履歷時，依第 6 列表頭名稱動態填入)
    if override_fields:
        for c in range(1, max_cols + 1):
            h_val = str(new_ws.cell(6, c).value or "").strip()
            if h_val in override_fields and override_fields[h_val] is not None and override_fields[h_val] != "":
                new_ws.cell(7, c).value = override_fields[h_val]
        
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
        self.title("勝一三合一單產生系統 & 運輸通知表產生器")
        self.geometry("1260x820")
        self.minsize(1080, 620)
        self.configure(padx=15, pady=15)
        
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.template_path = os.path.join(self.base_dir, "台積電槽車barcode三合一單-範本.xlsx")
        self.mapping_path = os.path.join(self.base_dir, "地點代號對照表.xlsx")
        
        self.mapping_dict = {}
        self.part_mapping_dict = {}
        self.imported_lorry_files = []
        self.load_mapping()
        
        self.setup_ui()
        self.entries = []
        self.coa_paths = []
        self.add_input_rows(20)

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

    def resolve_part_no(self, loc_str, prod_str):
        """
        依據 (指送地, 品名) 自動解析台積電槽車料號 (如 L2C9173, L269100, L2C9100, L2C9501, L2R9501)
        """
        loc = clean_location_str(loc_str, self.mapping_dict) if loc_str else ""
        prod = str(prod_str or "").strip().upper()

        # 1. 優先由品名精確對應 (勝一 5 大槽車品項各自有唯一料號)
        if prod in SHINYI_PRODUCT_PART_MAP:
            return SHINYI_PRODUCT_PART_MAP[prod]

        # 2. 查對照表中的 (地點, 品名) 欄位
        if loc in self.part_mapping_dict:
            info = self.part_mapping_dict[loc]
            origins = info.get("origins", {})
            if prod and prod in origins and origins[prod]:
                return origins[prod]
            if not prod and info.get("default"):
                return info["default"]

        return ""

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
                            if loc_key in ("短地點", "長代號", "SHORT", "LOCATION", "KEY", "HEADER"):
                                continue
                            self.mapping_dict[loc_key] = loc_val
                            info = {
                                "default": str(row[2]).strip() if len(row) > 2 and row[2] else "",
                                "origins": {},
                                "tsmcfab": "",
                                "fabphase": "",
                                "raw_loc": ""
                            }
                            for i in range(3, len(headers)):
                                if i < len(row) and row[i] is not None:
                                    h_name = headers[i].upper()
                                    cell_s = str(row[i]).strip()
                                    if h_name == "TSMCFAB":
                                        info["tsmcfab"] = cell_s
                                    elif h_name == "FABPHASE":
                                        info["fabphase"] = cell_s
                                    elif h_name in ("原始指送地", "指送地"):
                                        info["raw_loc"] = cell_s
                                    elif h_name:
                                        info["origins"][h_name] = cell_s
                            self.part_mapping_dict[loc_key] = info
                map_wb.close()
            except Exception as e:
                pass

        if hasattr(self, "lbl_mapping_status"):
            m_color = "green" if os.path.exists(self.mapping_path) else "red"
            m_text = f"對照表檔案 (地點代號對照表.xlsx): ✅ 已找到 (載入 {len(self.mapping_dict)} 筆代號)" if os.path.exists(self.mapping_path) else "對照表檔案 (地點代號對照表.xlsx): ❌ 未找到"
            self.lbl_mapping_status.config(text=m_text, fg=m_color)

        if hasattr(self, "entries"):
            for entry in self.entries:
                self.on_loc_change(entry)

    def update_lorry_status(self):
        if not hasattr(self, "imported_lorry_files"):
            self.imported_lorry_files = []
        if not self.imported_lorry_files:
            defaults = sorted(glob.glob(os.path.join(self.base_dir, "Chemical_Lorry*.xlsx")))
            if defaults:
                self.imported_lorry_files = defaults
        
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

    def _scan_all_lorry_files(self):
        """
        掃描所有已載入的 Chemical_Lorry 活頁簿（支援多檔案與多分頁），
        回傳:
          - batch_info_map: {batch_no: {"b": TSMCFab, "c": DeliveryDate, "f": ManufactureDate, "g": FabPhase, "tank": TankNo, "mat_no": MaterialNo, "file": l_file, "sheet": s_name, "row": r}}
          - schema_sheet_map: {mat_no: (l_file, s_name)}
        """
        batch_info_map = {}
        schema_sheet_map = {}
        lorry_files = list(getattr(self, "imported_lorry_files", []))
        if not lorry_files:
            lorry_files = sorted(glob.glob(os.path.join(self.base_dir, "Chemical_Lorry*.xlsx")))

        for l_file in lorry_files:
            try:
                _wb = openpyxl.load_workbook(l_file, data_only=True)
                for s_name in _wb.sheetnames:
                    _ws = _wb[s_name]
                    c1 = str(_ws.cell(1, 1).value or "").strip()
                    c6 = str(_ws.cell(6, 1).value or "").strip()
                    if c1 != "MaterialNo" and c6 != "FinalBatchID":
                        continue
                    mat_no = str(_ws.cell(1, 2).value or "").strip().upper()
                    if mat_no and mat_no not in schema_sheet_map:
                        schema_sheet_map[mat_no] = (l_file, s_name)

                    # 找出槽車號欄位 (Cylinder/ lorry/trailer No.)
                    tank_col_idx = -1
                    for c_idx in range(1, min(30, _ws.max_column + 1)):
                        h_str = str(_ws.cell(6, c_idx).value or "").strip().lower()
                        if "lorry" in h_str and "raw" not in h_str:
                            tank_col_idx = c_idx
                            break

                    for _r in range(7, _ws.max_row + 1):
                        _val = str(_ws.cell(row=_r, column=1).value or "").strip().upper()
                        if _val and _val not in batch_info_map:
                            col_b = str(_ws.cell(row=_r, column=2).value or "").strip()
                            raw_c = _ws.cell(row=_r, column=3).value
                            if isinstance(raw_c, (datetime, date)):
                                col_c = f"{raw_c.year}/{raw_c.month}/{raw_c.day}"
                            else:
                                col_c = str(raw_c or "").strip().split()[0] if raw_c else ""
                            raw_f = _ws.cell(row=_r, column=6).value
                            if isinstance(raw_f, (datetime, date)):
                                col_f = f"{raw_f.year}/{raw_f.month}/{raw_f.day}"
                            else:
                                col_f = str(raw_f or "").strip().split()[0] if raw_f else ""
                            col_g = str(_ws.cell(row=_r, column=7).value or "").strip()
                            t_val = str(_ws.cell(row=_r, column=tank_col_idx).value or "").strip() if tank_col_idx != -1 else ""
                            batch_info_map[_val] = {
                                "b": col_b,
                                "c": col_c,
                                "f": col_f,
                                "g": col_g,
                                "tank": t_val,
                                "mat_no": mat_no,
                                "file": l_file,
                                "sheet": s_name,
                                "row": _r
                            }
                _wb.close()
            except Exception as e:
                print(f"Scan lorry error ({l_file}): {e}")
        return batch_info_map, schema_sheet_map

    def load_chemical_lorry_file(self):
        filepaths = filedialog.askopenfilenames(
            title="選擇生產履歷檔案 (Chemical_Lorry, 可多選)",
            filetypes=[("Excel 活頁簿", "*.xlsx *.xls"), ("所有檔案", "*.*")]
        )
        if not filepaths:
            return
            
        try:
            self.show_loading("⏳ 正在處理生產履歷，請稍候...")
            self.imported_lorry_files = list(filepaths)
            self.update_lorry_status()
            self.gen_lorry_var.set(True)
            
            import time
            time.sleep(0.3)
            self.update()
        finally:
            self.hide_loading()
            
        # 比對排程批號 vs 生產履歷批號
        try:
            batch_info_map, schema_sheet_map = self._scan_all_lorry_files()
            lorry_batches = set(batch_info_map.keys())

            table_entries = []
            for row in self.entries:
                b = row["batch_var"].get().strip().upper()
                if b:
                    table_entries.append((b, row["long_code_var"].get().strip().upper(), row["part_var"].get().strip().upper()))

            table_batches = [b for b, lc, pn in table_entries]
            missing = [b for b, lc, pn in table_entries if b not in lorry_batches]
            found = [b for b in table_batches if b in lorry_batches]
            
            wrong_factory_msgs = []
            for b, lc, pn in table_entries:
                if b in lorry_batches:
                    l_fac = batch_info_map[b].get("b", "").upper()
                    expected_substr = lc[1:5] if len(lc) >= 5 else lc
                    if not l_fac:
                        wrong_factory_msgs.append(f"⚠️ 批號 {b}：廠區空白 (應含 {expected_substr})")
                    elif l_fac not in lc and expected_substr not in l_fac:
                        wrong_factory_msgs.append(f"⚠️ 批號 {b}：廠區 ({l_fac}) 與長代號 ({lc}) 不同，產生時將以履歷對齊")

            fname = f"已選 {len(self.imported_lorry_files)} 份檔案" if len(self.imported_lorry_files) > 1 else os.path.basename(self.imported_lorry_files[0]) if self.imported_lorry_files else ""
            lines = [f"已成功載入生產履歷檔案：\n{fname}\n\n已為您自動勾選【產生單列生產履歷】！\n"]
            if not table_batches:
                lines.append("ℹ️ 排程表格尚未輸入批號，無法比對。")
            else:
                for b in found:
                    lines.append(f"✅ {b} ─ 生產履歷已核對到")
                for b in missing:
                    lines.append(f"❌ {b} ─ 生產履歷中找不到！(將不會產生此批履歷)")
                if wrong_factory_msgs:
                    lines.append("\n--- 廠區提醒 ---")
                    lines.extend(wrong_factory_msgs)
                    lines.append("----------------\n")

            title = "生產履歷已載入" if not missing else "⚠️ 生產履歷載入 (有缺漏)"
            messagebox.showinfo(title, "\n".join(lines))
        except Exception as _e:
            fname = f"已選 {len(self.imported_lorry_files)} 份檔案" if len(self.imported_lorry_files) > 1 else os.path.basename(self.imported_lorry_files[0]) if self.imported_lorry_files else ""
            messagebox.showinfo(
                "生產履歷已載入",
                f"已成功載入生產履歷檔案：\n{fname}\n\n已為您自動勾選【產生單列生產履歷】！\n稍後點擊【開始批次產生】時，系統會自動核對每筆排程批號並單列輸出。"
            )

    def reload_mapping_with_msg(self):
        """點擊『🔄 重新載入對照表』時執行"""
        self.load_mapping()
        messagebox.showinfo("對照表已更新", f"已重新讀取『地點代號對照表.xlsx』！\n目前共載入 {len(self.mapping_dict)} 筆地點對照碼。\n表格中的地點長代號與料號已同步更新！")

    def open_calendar_dialog(self, target_var):
        CalendarDialog(self, target_var)

    def setup_ui(self):
        # 1. 系統檔案狀態區
        status_frame = tk.LabelFrame(self, text="系統狀態", font=("Microsoft JhengHei", 10, "bold"), padx=10, pady=8)
        status_frame.pack(fill="x", pady=(0, 8))
        
        # 範本狀態
        t_color = "green" if os.path.exists(self.template_path) else "red"
        t_text = "✅ 已找到" if os.path.exists(self.template_path) else "❌ 未找到 (請將檔案放入資料夾)"
        tk.Label(status_frame, text=f"範本檔案 (台積電槽車barcode三合一單-範本.xlsx): {t_text}", fg=t_color).pack(anchor="w")
        
        # 對照表狀態列 + 重新載入按鈕
        map_status_frame = tk.Frame(status_frame)
        map_status_frame.pack(anchor="w", pady=(2, 0))

        m_color = "green" if os.path.exists(self.mapping_path) else "red"
        m_text = f"對照表檔案 (地點代號對照表.xlsx): ✅ 已找到 (載入 {len(self.mapping_dict)} 筆代號)" if os.path.exists(self.mapping_path) else "對照表檔案 (地點代號對照表.xlsx): ❌ 未找到"
        
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

        # 3. 一鍵批次設定列 (純淨獨立，日期與時間欄位寬裕舒適)
        batch_setting_frame = tk.LabelFrame(self, text="一鍵批次設定 (出貨日期)", font=("Microsoft JhengHei", 9, "bold"), padx=10, pady=5)
        batch_setting_frame.pack(fill="x", pady=(0, 6))
        
        # 全選
        self.select_all_var = tk.BooleanVar(value=True)
        tk.Checkbutton(batch_setting_frame, text="☑ 全選所有列", variable=self.select_all_var, command=self.toggle_select_all, font=("Microsoft JhengHei", 9, "bold")).pack(side="left", padx=(0, 15))
        
        # 日期
        tk.Label(batch_setting_frame, text="批次出貨日期:").pack(side="left")
        self.default_date_var = tk.StringVar(value="")
        date_batch_entry = tk.Entry(batch_setting_frame, textvariable=self.default_date_var, width=12)
        date_batch_entry.pack(side="left", padx=2)
        tk.Button(batch_setting_frame, text="📅", command=lambda: self.open_calendar_dialog(self.default_date_var), font=("Arial", 8), width=3).pack(side="left", padx=(0, 2))
        tk.Button(batch_setting_frame, text="套用至全列", command=self.apply_default_date, bg="#607D8B", fg="white", font=("Microsoft JhengHei", 8)).pack(side="left", padx=(2, 16))
        
        # 4. 報表產出勾選專屬區塊 (獨立整列，寬度充裕，文字絕不截斷)
        report_opt_frame = tk.LabelFrame(self, text="📦 欲產生的報表勾選 (可多選，點擊開始產生時將自動產出所勾選項目)", font=("Microsoft JhengHei", 9, "bold"), padx=10, pady=5)
        report_opt_frame.pack(fill="x", pady=(0, 8))

        self.gen_3in1_var = tk.BooleanVar(value=True)
        self.gen_lorry_var = tk.BooleanVar(value=True)

        tk.Checkbutton(report_opt_frame, text="✅ 產生三合一單 Excel (含 Barcode 與 COA)", variable=self.gen_3in1_var, font=("Microsoft JhengHei", 9, "bold"), fg="#1B5E20").pack(side="left", padx=(0, 20))
        tk.Checkbutton(report_opt_frame, text="✅ 產生單列生產履歷 Excel (Chemical_Lorry 槽車充填表)", variable=self.gen_lorry_var, font=("Microsoft JhengHei", 9, "bold"), fg="#E65100").pack(side="left", padx=20)

        # 5. 表格滾動容器 (首列固定凍結 + 欄位自動滿版伸縮對齊)
        table_container = tk.Frame(self, bd=1, relief="solid")
        table_container.pack(fill="both", expand=True)

        # 定義欄位規格: (col_idx, title, min_width_px, stretch_weight)
        self.col_specs = [
            (0,  "☑ 產生 (全選)",          90,  0),
            (1,  "項次",                   46,  0),
            (2,  "批號 (請輸入10~11碼)",   145, 2),
            (3,  "槽號 (自動)",            95,  1),
            (4,  "品名 (貼上)",            105, 1),
            (5,  "地點 (如 15P5)",         110, 1),
            (6,  "長代號 (自動)",          135, 2),
            (7,  "料號 (自動)",            105, 1),
            (8,  "出貨日期 (必填)",        150, 2),
            (9,  "採購單號",               135, 2),
            (10, "單列清除",               74,  0),
        ]

        # 頂部凍結表頭區 (隨水平捲軸同步捲動，但垂直下拉時永遠固定在最上方！)
        header_top_wrap = tk.Frame(table_container, bg="#EAEAEA")
        header_top_wrap.pack(side="top", fill="x")

        self.header_canvas = tk.Canvas(header_top_wrap, height=34, borderwidth=0, highlightthickness=0, bg="#EAEAEA")
        self.header_canvas.pack(side="left", fill="x", expand=True)
        # 右側預留與垂直捲軸同寬的空間，確保表頭與下方資料欄 100% 對齊
        self.header_right_pad = tk.Frame(header_top_wrap, width=17, bg="#EAEAEA")
        self.header_right_pad.pack(side="right", fill="y")

        self.header_frame = tk.Frame(self.header_canvas, padx=5, pady=0, bg="#EAEAEA")
        self.header_window = self.header_canvas.create_window((0, 0), window=self.header_frame, anchor="nw")

        # 下方資料列滾動區
        body_wrap = tk.Frame(table_container)
        body_wrap.pack(side="top", fill="both", expand=True)

        self.canvas = tk.Canvas(body_wrap, borderwidth=0, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(body_wrap, orient="vertical", command=self.canvas.yview)

        def _on_xscroll(*args):
            self.canvas.xview(*args)
            self.header_canvas.xview(*args)

        self.scrollbar_x = ttk.Scrollbar(table_container, orient="horizontal", command=_on_xscroll)
        
        # 單一 Grid 容器 (scrollable_frame)
        self.scrollable_frame = tk.Frame(self.canvas, padx=5, pady=2)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        def _sync_layout(event=None):
            c_w = self.canvas.winfo_width()
            req_w = self.scrollable_frame.winfo_reqwidth()
            target_w = max(c_w, req_w, 1180)
            if target_w > 50:
                self.canvas.itemconfig(self.canvas_window, width=target_w)
                self.header_canvas.itemconfig(self.header_window, width=target_w)
            self.scrollable_frame.update_idletasks()
            # 將凍結表頭每一欄的寬度精準對齊下方資料列每一欄的實際像素寬度
            for col_idx, _, min_w, _ in self.col_specs:
                try:
                    x, y, w, h = self.scrollable_frame.grid_bbox(column=col_idx, row=1)
                    if w > 10:
                        self.header_frame.columnconfigure(col_idx, minsize=w, weight=0)
                except Exception:
                    pass
            bbox = self.canvas.bbox("all")
            if bbox:
                self.canvas.configure(scrollregion=bbox)
                self.header_canvas.configure(scrollregion=(0, 0, max(bbox[2], target_w), 34))

        self.scrollable_frame.bind("<Configure>", _sync_layout)
        self.canvas.bind("<Configure>", _sync_layout)

        def _on_canvas_xset(first, last):
            self.scrollbar_x.set(first, last)
            self.header_canvas.xview_moveto(first)

        self.canvas.configure(yscrollcommand=self.scrollbar.set, xscrollcommand=_on_canvas_xset)

        self.scrollbar.pack(side="right", fill="y")
        self.scrollbar_x.pack(side="bottom", fill="x")
        self.canvas.pack(side="left", fill="both", expand=True)

        # 支援滑鼠滾輪滾動
        self.bind_all("<MouseWheel>", lambda event: self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units"))

        # --- 建立凍結表頭列 (置於 self.header_frame) 與對齊權重 ---
        self.header_widgets = {}
        for col_idx, title, min_w, weight in self.col_specs:
            if col_idx == 0:
                hdr_w = tk.Button(
                    self.header_frame,
                    text=title,
                    font=("Microsoft JhengHei", 9, "bold"),
                    bg="#E3F2FD",
                    fg="#0D47A1",
                    padx=2,
                    pady=4,
                    relief="groove",
                    cursor="hand2",
                    command=self.toggle_all_rows_btn
                )
            else:
                hdr_w = tk.Label(
                    self.header_frame, 
                    text=title, 
                    font=("Microsoft JhengHei", 9, "bold"), 
                    bg="#EAEAEA", 
                    fg="#333333",
                    padx=2, 
                    pady=5,
                    relief="groove"
                )
            hdr_w.grid(row=0, column=col_idx, sticky="nsew", padx=1, pady=0)
            self.header_widgets[col_idx] = hdr_w
            self.header_frame.columnconfigure(col_idx, minsize=min_w, weight=weight)
            self.scrollable_frame.columnconfigure(col_idx, minsize=min_w, weight=weight)

        # 產生按鈕
        btn_frame = tk.Frame(self)
        btn_frame.pack(fill="x", pady=10)
        tk.Button(btn_frame, text="🚀 開始批次產生 Excel 報表", command=self.generate_files, bg="#4CAF50", fg="white", font=("Arial", 12, "bold"), pady=8).pack(fill="x")

    def toggle_all_rows_btn(self):
        new_state = not self.select_all_var.get()
        self.select_all_var.set(new_state)
        self.toggle_select_all()

    def toggle_select_all(self):
        state = self.select_all_var.get()
        for entry in self.entries:
            entry["chk_var"].set(state)
        if hasattr(self, "header_widgets") and 0 in self.header_widgets:
            self.header_widgets[0].config(text="☑ 產生 (全選)" if state else "☐ 產生 (全消)")

    def apply_default_date(self):
        val = self.default_date_var.get().strip()
        for entry in self.entries:
            if entry["batch_var"].get().strip():
                entry["date_var"].set(val)

    def add_input_rows(self, count):
        for i in range(count):
            row_idx = len(self.entries) + 1
            row_grid_idx = row_idx
            
            # Col 0: 勾選
            chk_var = tk.BooleanVar(value=True)
            chk = tk.Checkbutton(self.scrollable_frame, variable=chk_var)
            chk.grid(row=row_grid_idx, column=0, padx=2, pady=2)

            # Col 1: 項次
            lbl_num = tk.Label(self.scrollable_frame, text=str(row_idx), font=("Arial", 10), width=4)
            lbl_num.grid(row=row_grid_idx, column=1, padx=2, pady=2, sticky="ew")
            
            # Col 2: 批號
            batch_var = tk.StringVar()
            batch_entry = tk.Entry(self.scrollable_frame, textvariable=batch_var, width=14, font=("Arial", 10))
            batch_entry.grid(row=row_grid_idx, column=2, padx=2, pady=2, sticky="ew")
            
            # Col 3: 槽號
            tank_var = tk.StringVar()
            tank_entry = tk.Entry(self.scrollable_frame, textvariable=tank_var, state="readonly", width=10, font=("Arial", 10), fg="blue")
            tank_entry.grid(row=row_grid_idx, column=3, padx=2, pady=2, sticky="ew")

            # Col 4: 品名
            prod_var = tk.StringVar()
            prod_entry = tk.Entry(self.scrollable_frame, textvariable=prod_var, width=10, font=("Arial", 10))
            prod_entry.grid(row=row_grid_idx, column=4, padx=2, pady=2, sticky="ew")
            
            # Col 5: 地點
            loc_var = tk.StringVar()
            loc_entry = tk.Entry(self.scrollable_frame, textvariable=loc_var, width=10, font=("Arial", 10))
            loc_entry.grid(row=row_grid_idx, column=5, padx=2, pady=2, sticky="ew")
            
            # Col 6: 長代號
            long_code_var = tk.StringVar()
            long_code_entry = tk.Entry(self.scrollable_frame, textvariable=long_code_var, state="readonly", width=12, font=("Arial", 10), fg="purple")
            long_code_entry.grid(row=row_grid_idx, column=6, padx=2, pady=2, sticky="ew")

            # Col 7: 料號
            part_var = tk.StringVar()
            part_entry = tk.Entry(self.scrollable_frame, textvariable=part_var, state="readonly", width=10, font=("Arial", 10, "bold"), fg="#D32F2F")
            part_entry.grid(row=row_grid_idx, column=7, padx=2, pady=2, sticky="ew")
            
            # Col 8: 出貨日期
            date_frame = tk.Frame(self.scrollable_frame)
            date_frame.grid(row=row_grid_idx, column=8, padx=2, pady=2, sticky="ew")
            
            date_var = tk.StringVar(value="")
            date_entry = tk.Entry(date_frame, textvariable=date_var, width=10, font=("Arial", 10))
            date_entry.pack(side="left", fill="x", expand=True)
            
            btn_cal = tk.Button(date_frame, text="📅", command=lambda dv=date_var: self.open_calendar_dialog(dv), font=("Arial", 8), cursor="hand2")
            btn_cal.pack(side="right", padx=(2, 0))
            
            # Col 9: 採購單號
            po_var = tk.StringVar(value="")
            po_entry = tk.Entry(self.scrollable_frame, textvariable=po_var, width=12, font=("Arial", 10))
            po_entry.grid(row=row_grid_idx, column=9, padx=2, pady=2, sticky="ew")
            
            # Col 10: 單列清除
            btn_clear = tk.Button(self.scrollable_frame, text="清除", 
                                  command=lambda r=row_idx - 1: self.clear_single_row(r),
                                  bg="#FCE4EC", font=("Arial", 9))
            btn_clear.grid(row=row_grid_idx, column=10, padx=2, pady=2, sticky="ew")
            
            row_dict = {
                "chk_var": chk_var,
                "chk_btn": chk,
                "lbl_num": lbl_num,
                "batch_var": batch_var,
                "batch_entry": batch_entry,
                "tank_var": tank_var,
                "tank_entry": tank_entry,
                "prod_var": prod_var,
                "prod_entry": prod_entry,
                "loc_var": loc_var,
                "loc_entry": loc_entry,
                "long_code_var": long_code_var,
                "long_code_entry": long_code_entry,
                "part_var": part_var,
                "part_entry": part_entry,
                "date_var": date_var,
                "date_entry": date_entry,
                "btn_cal": btn_cal,
                "date_frame": date_frame,
                "po_var": po_var,
                "po_entry": po_entry,
                "btn_clear": btn_clear
            }
            
            self.entries.append(row_dict)
            
            # Event bindings & Variable trace (即時同步槽號、長代號、料號)
            batch_var.trace_add("write", lambda *args, r=row_idx: self.on_batch_change(r))
            loc_var.trace_add("write", lambda *args, r=row_idx: self.on_loc_change(r))
            prod_var.trace_add("write", lambda *args, r=row_idx: self.on_loc_change(r))
            batch_entry.bind("<FocusOut>", lambda e, r=row_idx: self.on_batch_change(r))
            loc_entry.bind("<FocusOut>", lambda e, r=row_idx: self.on_loc_change(r))
            prod_entry.bind("<FocusOut>", lambda e, r=row_idx: self.on_loc_change(r))

            # 支援貼上事件
            for w_entry in (batch_entry, prod_entry, loc_entry, date_entry, po_entry):
                w_entry.bind("<Control-v>", lambda e, r=row_idx - 1, w=w_entry: self.on_paste(e, r, w))
                w_entry.bind("<Control-V>", lambda e, r=row_idx - 1, w=w_entry: self.on_paste(e, r, w))

    def clear_all_rows(self):
        """一鍵清除全部輸入欄位 (全清)"""
        if messagebox.askyesno("確認清空", "確定要清空所有已填寫的批號、地點與時間資料嗎？"):
            for entry in self.entries:
                entry["batch_var"].set("")
                entry["loc_var"].set("")
                entry["long_code_var"].set("")
                entry["tank_var"].set("")
                entry["date_var"].set("")
                if "prod_var" in entry: entry["prod_var"].set("")
                if "part_var" in entry: entry["part_var"].set("")
                if "po_var" in entry: entry["po_var"].set("")

    def set_today_all_dates(self):
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
            entry["tank_var"].set("")
            entry["date_var"].set("")
            if "prod_var" in entry: entry["prod_var"].set("")
            if "part_var" in entry: entry["part_var"].set("")
            if "po_var" in entry: entry["po_var"].set("")

    def on_batch_change(self, r_idx):
        if isinstance(r_idx, dict):
            entry = r_idx
        else:
            if r_idx < 1 or r_idx > len(self.entries): return
            entry = self.entries[r_idx - 1]
        batch = entry["batch_var"].get().upper().strip()
        tank = get_tank_from_batch(batch)
        entry["tank_var"].set(tank)

    def on_loc_change(self, r_idx):
        if isinstance(r_idx, dict):
            entry = r_idx
        else:
            if r_idx < 1 or r_idx > len(self.entries): return
            entry = self.entries[r_idx - 1]
        raw_loc = entry["loc_var"].get().strip().upper()
        prod_str = entry.get("prod_var", tk.StringVar()).get().strip().upper()
        loc = clean_location_str(raw_loc, self.mapping_dict) if raw_loc else ""

        if not loc:
            entry["long_code_var"].set("")
        elif loc in self.mapping_dict:
            entry["long_code_var"].set(self.mapping_dict[loc])
        else:
            entry["long_code_var"].set("❌ 未知代號")

        if "part_var" in entry:
            resolved_part = self.resolve_part_no(loc, prod_str)
            entry["part_var"].set(resolved_part)

    def parse_pasted_row_items(self, parts):
        """
        智慧解析貼上行中的元素，自動辨識：出貨日期、批號、槽號、品名、地點、時間。
        支援勝一排程格式（出貨通知單單別號、批號、對象簡稱、指送地、品名、預計到貨日期、到貨時間、運輸方式）
        """
        res = {"batch": "", "loc": "", "prod": "", "date": "", "time": "", "mod_time": ""}
        clean_parts = [p.strip() for p in parts if p.strip()]
        if not clean_parts:
            return res

        unassigned = []
        for p in clean_parts:
            p_upper = p.upper()
            if p_upper in ("台積電", "TSMC") or p_upper.startswith("SNXM") or "勝一" in p_upper or "技服" in p_upper:
                continue

            # 1. 品名 (CPNE4R, SEP73E4, SEP73E5, PMAHQ, PMAHQ(R))
            if not res["prod"] and (p_upper in SHINYI_PRODUCT_PART_MAP or p_upper in PRODUCT_WEIGHT_MAP):
                res["prod"] = p_upper
                continue

            # 2. 日期 (包含 /, -, ., 或月/日，長度 <= 12)
            if not res["date"] and (any(char in p for char in ("/", "-", ".")) or "月" in p or "日" in p):
                if len(p) <= 12 and not p.isalnum():
                    res["date"] = normalize_date_str(p)
                    continue

            # 3. 批號 (10~11 碼英數混合且尾碼 T1)
            if not res["batch"] and (len(p_upper) in (10, 11) and any(c.isdigit() for c in p_upper) and any(c.isalpha() for c in p_upper)):
                res["batch"] = p_upper
                continue

            # 4. 地點
            norm_l = clean_location_str(p_upper, self.mapping_dict)
            if not res["loc"] and (norm_l in self.mapping_dict or "廠" in p or "P" in p_upper or "B30" in p_upper or "A6" in p_upper or "A5" in p_upper):
                res["loc"] = norm_l if norm_l in self.mapping_dict else p_upper
                continue

            # 5. 槽號 (3~5 碼以 S/E/T/P 開頭)
            if len(p_upper) <= 5 and p_upper.startswith(("S", "E", "T", "P")) and any(c.isdigit() for c in p_upper):
                continue

            unassigned.append(p)

        for item in unassigned:
            if not res["batch"] and len(item) >= 8:
                res["batch"] = item.upper()
            elif not res["loc"] and len(item) <= 16:
                res["loc"] = clean_location_str(item.upper(), self.mapping_dict)
            elif not res["date"] and ("/" in item or "-" in item or "." in item):
                res["date"] = normalize_date_str(item)
            elif not res["time"]:
                res["time"] = item
            elif not res["mod_time"]:
                res["mod_time"] = item

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
                    parsed = self.parse_pasted_row_items(parts)
                    if parsed["batch"]:
                        self.entries[curr_row]["batch_var"].set(parsed["batch"])
                    if parsed["prod"] and "prod_var" in self.entries[curr_row]:
                        self.entries[curr_row]["prod_var"].set(parsed["prod"])
                    if parsed["loc"]:
                        self.entries[curr_row]["loc_var"].set(parsed["loc"])
                    if parsed["date"]:
                        self.entries[curr_row]["date_var"].set(parsed["date"])
                    curr_row += 1
                elif len(parts) == 1:
                    val = parts[0].strip()
                    if val:
                        parsed = self.parse_pasted_row_items([val])
                        if parsed["batch"]:
                            self.entries[curr_row]["batch_var"].set(parsed["batch"])
                        elif parsed["prod"] and "prod_var" in self.entries[curr_row]:
                            self.entries[curr_row]["prod_var"].set(parsed["prod"])
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

    def _extract_coa_meta(self, file_path):
        """
        從 COA 檔案 (CSV 或 Excel) 動態讀取 Column A 的關鍵欄位：
        回傳 {"raw_lot_id": ..., "material_no": ...}
        """
        meta = {"raw_lot_id": "", "material_no": ""}
        for enc in ('utf-8-sig', 'cp950', 'utf-8'):
            if not file_path.lower().endswith('.csv'):
                break
            try:
                with open(file_path, 'r', encoding=enc, errors='ignore') as f:
                    for row in csv.reader(f):
                        if len(row) >= 2:
                            k = str(row[0]).strip()
                            v = str(row[1]).strip()
                            if k == "RawLotId" and v:
                                meta["raw_lot_id"] = v.upper()
                            elif k in ("MaterialNo", "SchemaName") and v and not meta["material_no"]:
                                meta["material_no"] = v.upper()
                if meta["raw_lot_id"] or meta["material_no"]:
                    return meta
            except Exception:
                pass

        if file_path.lower().endswith(('.xlsx', '.xls')):
            try:
                wb = openpyxl.load_workbook(file_path, data_only=True)
                for sheet in wb.sheetnames:
                    ws = wb[sheet]
                    for r in range(1, min(25, ws.max_row + 1)):
                        k = str(ws.cell(r, 1).value or "").strip()
                        v = str(ws.cell(r, 2).value or "").strip()
                        if k == "RawLotId" and v:
                            meta["raw_lot_id"] = v.upper()
                        elif k in ("MaterialNo", "SchemaName") and v and not meta["material_no"]:
                            meta["material_no"] = v.upper()
                wb.close()
            except Exception:
                pass
        return meta

    def _extract_batch_from_coa(self, file_path):
        meta = self._extract_coa_meta(file_path)
        return meta.get("raw_lot_id") or None

    def _update_and_write_coa(self, src_path, dst_path, matched_batch, row_entry, lorry_info=None):
        """
        動態以 Column A 的欄位名稱 (Key-Based) 更新勝一 5 大槽車 COA (L2C9173, L269100, L2C9100, L2C9501, L2R9501)：
        不再寫死 B6/B7/B11/B12，徹底支援有無 CoACompletionDate 及不同列序的 COA 格式，
        並自動修復 SEP73 被 Excel 誤轉為 1973-09-01 的問題。
        """
        loc_str = clean_location_str(row_entry["loc_var"].get().strip(), self.mapping_dict)
        prod_str = row_entry.get("prod_var", tk.StringVar()).get().strip().upper()
        part_str = row_entry.get("part_var", tk.StringVar()).get().strip().upper() or self.resolve_part_no(loc_str, prod_str)
        date_str = row_entry["date_var"].get().strip()
        po_full = row_entry.get("po_var", tk.StringVar()).get().strip()
        po_no = po_full[:10] if len(po_full) >= 10 else po_full

        # 解析出貨日 (DeliverDate)
        dt_deliver = None
        if date_str:
            for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%Y%m%d"):
                try:
                    dt_deliver = datetime.strptime(date_str.split()[0], fmt)
                    break
                except ValueError:
                    pass

        # 決定 TSMCFab, FabPhase, DeliverDate, ManufacturingDate
        map_info = self.part_mapping_dict.get(loc_str, {})
        tsmc_fab = (lorry_info.get("b") if lorry_info else "") or map_info.get("tsmcfab") or loc_str
        fab_phase = (lorry_info.get("g") if lorry_info else "") or map_info.get("fabphase") or loc_str

        deliver_date_val = ""
        if lorry_info and lorry_info.get("c"):
            deliver_date_val = lorry_info["c"]
        elif dt_deliver:
            deliver_date_val = f"{dt_deliver.year}/{dt_deliver.month}/{dt_deliver.day}"

        # 解析製造日 (ManufacturingDate) 與有效期限 (ExpiryDate = Mfg + 364 days)
        dt_mfg = parse_mfg_date_from_batch(matched_batch)
        if lorry_info and lorry_info.get("f"):
            for fmt in ("%Y/%m/%d", "%Y-%m-%d"):
                try:
                    dt_mfg = datetime.strptime(lorry_info["f"], fmt)
                    break
                except ValueError:
                    pass
        mfg_date_val = f"{dt_mfg.year}/{dt_mfg.month}/{dt_mfg.day}" if dt_mfg else ""
        dt_exp = (dt_mfg + timedelta(days=364)) if dt_mfg else None
        exp_date_val = f"{dt_exp.year}/{dt_exp.month}/{dt_exp.day}" if dt_exp else ""
        coa_comp_val = deliver_date_val or mfg_date_val

        # 計算 RemainLifeTime (ExpiryDate - DeliverDate)
        remain_days_val = ""
        if dt_exp and dt_deliver:
            remain_days_val = str((dt_exp.date() - dt_deliver.date()).days)

        ext = os.path.splitext(src_path)[1].lower()
        if ext in ('.xlsx', '.xls'):
            wb = openpyxl.load_workbook(src_path)
            ws = wb.active
            schema_no = str(ws.cell(1, 2).value or ws.cell(3, 2).value or part_str).strip().upper()
            for r in range(1, ws.max_row + 1):
                k = str(ws.cell(r, 1).value or "").strip()
                v_curr = ws.cell(r, 2).value
                if k == "TSMCFab" and tsmc_fab:
                    ws.cell(r, 2).value = tsmc_fab
                elif k == "FabPhase" and fab_phase:
                    ws.cell(r, 2).value = fab_phase
                elif k == "ShipQty":
                    ws.cell(r, 2).value = int(get_product_weight(prod_str))
                elif k == "ManufacturingDate" and mfg_date_val:
                    ws.cell(r, 2).value = mfg_date_val
                elif k == "DeliverDate" and deliver_date_val:
                    ws.cell(r, 2).value = deliver_date_val
                elif k == "CoACompletionDate" and coa_comp_val:
                    ws.cell(r, 2).value = coa_comp_val
                elif k == "PONo" and po_no:
                    ws.cell(r, 2).value = po_no
                elif k == "RawLotId" and matched_batch:
                    ws.cell(r, 2).value = matched_batch
                elif k == "ExpiryDate" and exp_date_val:
                    ws.cell(r, 2).value = exp_date_val
                elif k == "MaterialName":
                    if schema_no == "L269100" or (isinstance(v_curr, (datetime, date)) and v_curr.year == 1973):
                        ws.cell(r, 2).value = "SEP73"
                elif k == "RemainLifeTime" and remain_days_val:
                    ws.cell(r, 7).value = int(remain_days_val)
            wb.save(dst_path)
            wb.close()
        elif ext == '.csv':
            reader = []
            for enc in ('utf-8-sig', 'cp950', 'utf-8'):
                try:
                    with open(src_path, 'r', encoding=enc) as f:
                        reader = list(csv.reader(f))
                    break
                except Exception:
                    pass
            if not reader:
                with open(src_path, 'r', encoding='utf-8-sig', errors='ignore') as f:
                    reader = list(csv.reader(f))

            schema_no = part_str
            for r_idx, r_vals in enumerate(reader):
                if not r_vals:
                    continue
                k = str(r_vals[0]).strip()
                while len(r_vals) < 8:
                    r_vals.append("")
                if k in ("SchemaName", "MaterialNo") and r_vals[1]:
                    schema_no = str(r_vals[1]).strip().upper()
                elif k == "TSMCFab" and tsmc_fab:
                    r_vals[1] = tsmc_fab
                elif k == "FabPhase" and fab_phase:
                    r_vals[1] = fab_phase
                elif k == "ShipQty":
                    r_vals[1] = str(get_product_weight(prod_str))
                elif k == "ManufacturingDate" and mfg_date_val:
                    r_vals[1] = mfg_date_val
                elif k == "DeliverDate" and deliver_date_val:
                    r_vals[1] = deliver_date_val
                elif k == "CoACompletionDate" and coa_comp_val:
                    r_vals[1] = coa_comp_val
                elif k == "PONo" and po_no:
                    r_vals[1] = po_no
                elif k == "RawLotId" and matched_batch:
                    r_vals[1] = matched_batch
                elif k == "ExpiryDate" and exp_date_val:
                    r_vals[1] = exp_date_val
                elif k == "MaterialName":
                    if schema_no == "L269100" or "1973" in str(r_vals[1]) or "73" in str(r_vals[1]):
                        if schema_no == "L269100":
                            r_vals[1] = "SEP73"
                elif k == "RemainLifeTime" and remain_days_val:
                    r_vals[6] = remain_days_val

            with open(dst_path, 'w', encoding='big5', errors='ignore', newline='') as f:
                writer = csv.writer(f)
                writer.writerows(reader)

    def load_coa_forms(self):
        file_paths = filedialog.askopenfilenames(
            title="選擇要載入的 COA 表單 (可多選，支援個別批號 COA 或 5 大品項 COA 範本)",
            filetypes=[("Excel 或 CSV", "*.xlsx *.xls *.csv"), ("所有檔案", "*.*")]
        )
        if not file_paths:
            return

        valid_batches = {}
        for row in self.entries:
            if row["chk_var"].get():
                batch = row["batch_var"].get().strip().upper()
                if batch:
                    valid_batches[batch] = row

        if not valid_batches:
            messagebox.showwarning("提示", "請先在列表中填寫並勾選包含批號的資料！")
            return
            
        lorry_data_map, _ = self._scan_all_lorry_files()

        try:
            self.show_loading("⏳ 正在處理 COA 表單，請稍候...")
            success_count = 0
            error_msgs = []

            for file_path in file_paths:
                try:
                    base_name, ext = os.path.splitext(os.path.basename(file_path))
                    meta = self._extract_coa_meta(file_path)
                    coa_lot = meta.get("raw_lot_id", "")
                    coa_mat = meta.get("material_no", "")

                    # 1. 先嘗試以批號精準配對
                    matched_batches_list = []
                    for b in valid_batches:
                        if b in base_name.upper() or (coa_lot and (b == coa_lot or b in coa_lot or coa_lot in b)):
                            matched_batches_list.append(b)
                            break

                    # 2. 若檔名/內容批號未在排程中，嘗試以 MaterialNo / 品名範本配對排程中所有同料號批號
                    if not matched_batches_list and coa_mat:
                        for b, r_entry in valid_batches.items():
                            r_loc = clean_location_str(r_entry["loc_var"].get().strip(), self.mapping_dict)
                            r_prod = r_entry.get("prod_var", tk.StringVar()).get().strip().upper()
                            r_part = r_entry.get("part_var", tk.StringVar()).get().strip().upper() or self.resolve_part_no(r_loc, r_prod)
                            if r_part == coa_mat:
                                matched_batches_list.append(b)

                    if not matched_batches_list:
                        error_msgs.append(f"找不到對應批號或料號 ({coa_mat or '未知'}): {os.path.basename(file_path)}")
                        continue

                    for matched_batch in matched_batches_list:
                        row = valid_batches[matched_batch]
                        loc_str = clean_location_str(row["loc_var"].get().strip(), self.mapping_dict)
                        prod_str = row.get("prod_var", tk.StringVar()).get().strip().upper()
                        part_str = row.get("part_var", tk.StringVar()).get().strip().upper() or self.resolve_part_no(loc_str, prod_str) or coa_mat

                        date_str = row["date_var"].get().strip()
                        formatted_date = date_str.replace("/", "").replace("-", "")
                        date_MMDD = formatted_date[4:8] if len(formatted_date) >= 8 else formatted_date

                        prefix_match = re.match(r'^([A-Za-z0-9_]+)', base_name)
                        product_prefix = prefix_match.group(1) if prefix_match else f"{part_str}_{prod_str}_Lorry_TSMC"

                        new_base = f"{product_prefix} {date_MMDD} {loc_str}_{matched_batch}"
                        output_dir = os.path.join(self.base_dir, f"勝一三合一單輸出_{formatted_date}")

                        tank_str = row["tank_var"].get().strip()
                        safe_loc = "".join(c for c in loc_str if c.isalnum() or c in (' ', '_', '-')).rstrip() or "未命名地點"
                        loc_sub_dir = f"{date_MMDD} {safe_loc} {tank_str}".strip()

                        loc_folder = os.path.join(output_dir, loc_sub_dir)
                        os.makedirs(loc_folder, exist_ok=True)
                        new_file_path = os.path.join(loc_folder, new_base + ext)

                        self._update_and_write_coa(
                            file_path,
                            new_file_path,
                            matched_batch,
                            row,
                            lorry_info=lorry_data_map.get(matched_batch)
                        )
                        success_count += 1
                except Exception as e:
                    error_msgs.append(f"處理 {os.path.basename(file_path)} 失敗: {str(e)}")

        finally:
            self.hide_loading()

        msg = f"成功處理並產出 {success_count} 份 COA 表單。"
        if error_msgs:
            msg += "\n\n錯誤紀錄:\n" + "\n".join(error_msgs)
            messagebox.showwarning("完成", msg)
        else:
            messagebox.showinfo("完成", msg)


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
            title="選擇要匯入的 Excel 或 CSV 檔案 (可多選)",
            filetypes=[("Excel & CSV files", "*.xlsx *.xls *.csv")]
        )
        if not filepaths:
            return
            
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
                        batch_col, loc_col, date_col, tank_col, time_col, mod_time_col, po_col, prod_col = -1, -1, -1, -1, -1, -1, -1, -1
                        start_row = 0
                        for r_idx in range(min(15, len(rows))):
                            row = rows[r_idx]
                            if not row: continue
                            for c_idx, val in enumerate(row):
                                v = str(val or "").strip().upper()
                                if batch_col == -1 and any(k in v for k in ["批號", "BATCH", "LOT"]): batch_col = c_idx
                                if loc_col == -1 and any(k in v for k in ["地點", "指送", "交貨", "到貨地", "送達", "廠區", "LOCATION", "DEST"]): loc_col = c_idx
                                if prod_col == -1 and any(k in v for k in ["品名", "產品", "PRODUCT"]): prod_col = c_idx
                                if date_col == -1 and any(k in v for k in ["到貨日", "出貨日", "出車日", "日期", "DATE"]) and "地" not in v and "點" not in v: date_col = c_idx
                                if tank_col == -1 and any(k in v for k in ["槽號", "槽車", "TANK"]) and not any(k in v for k in ["日", "期", "時間", "TIME", "DATE", "到廠", "出車", "出貨"]): tank_col = c_idx
                                if time_col == -1 and any(k in v for k in ["到貨時間", "預計", "時間", "TIME"]) and "修正" not in v: time_col = c_idx
                                if mod_time_col == -1 and "修正" in v and ("時間" in v or "TIME" in v): mod_time_col = c_idx
                                if po_col == -1 and any(k in v for k in ["採購單", "PO"]): po_col = c_idx
                                if po_col == -1 and any(k in v for k in ["採購單", "PO"]): po_col = c_idx
                            if batch_col != -1 and (loc_col != -1 or date_col != -1):
                                start_row = r_idx + 1
                                break
                        if batch_col == -1 or loc_col == -1:
                            batch_col, date_col, tank_col, loc_col = 2, 1, 3, 4
                            start_row = 2
                        for r_idx in range(start_row, len(rows)):
                            row = rows[r_idx]
                            if not row: continue
                            def get_c(c): return row[c] if c != -1 and c < len(row) else None
                            b_val = str(get_c(batch_col) or "").strip().upper()
                            l_val = str(get_c(loc_col) or "").strip().upper()
                            p_val = str(get_c(prod_col) or "").strip()
                            d_val = get_c(date_col)
                            t_val = str(get_c(tank_col) or "").strip()
                            tm_val = normalize_time_str(get_c(time_col))
                            mt_val = normalize_time_str(get_c(mod_time_col))
                            po_val = str(get_c(po_col) or "").strip()
                            if len(b_val) not in (10, 11) or not re.search(r'[0-9]', b_val):
                                for cell in row:
                                    cs = str(cell or "").strip().upper()
                                    if len(cs) in (10, 11) and re.search(r'[0-9]', cs) and re.search(r'[A-Z]', cs) and "/" not in cs and "-" not in cs:
                                        b_val = cs
                                        break
                            if len(b_val) in (10, 11) and re.search(r'[0-9]', b_val):
                                is_valid_tank = (
                                    t_val and 
                                    len(t_val) <= 6 and 
                                    not any(c in t_val for c in ["-", "/", ":", " "]) and
                                    not (len(t_val) > 4 and t_val.isdigit())
                                )
                                tank_final = t_val if is_valid_tank else get_tank_from_batch(b_val)
                                clean_l = clean_location_str(l_val, self.mapping_dict)
                                records.append({
                                    "sheet": "CSV",
                                    "batch": b_val,
                                    "tank": tank_final,
                                    "product": p_val,
                                    "loc": clean_l,
                                    "long_code": self.mapping_dict.get(clean_l, ""),
                                    "date": normalize_date_str(d_val),
                                    "time": tm_val,
                                    "mod_time": mt_val,
                                "po": po_val
                            })
                else:
                    # 遍歷 Excel 所有分頁 (跨分頁智慧抓取所有有效排程)
                    wb = openpyxl.load_workbook(filepath, data_only=True)
                    sheet_count = len(wb.worksheets)

                    for ws in wb.worksheets:
                        sheet_name = ws.title
                        sn_lower = sheet_name.lower()
                        # 排除非排程功能分頁（如 barcode、coa、生產履歷、廠區及產品對照表）
                        if any(k in sn_lower for k in ["barcode", "coa", "履歷", "廠區及產品", "對照", "chemical_lorry"]):
                            continue

                        rows = list(ws.iter_rows(values_only=True))
                        if not rows or len(rows) == 0:
                            continue

                        first_cell = str(rows[0][0] or "").strip().upper() if rows[0] else ""
                        if any(k in first_cell for k in ["SCHEMANAME", "MATERIALNO", "TSMC CHEMICAL LORRY BARCODE"]):
                            continue

                        # 檢查分頁全域文字是否標記為台積電
                        sheet_has_tsmc = False
                        for r_idx in range(min(5, len(rows))):
                            row_str = " ".join(str(cell or "") for cell in rows[r_idx]).upper()
                            if "TSMC" in row_str or "台積" in row_str:
                                sheet_has_tsmc = True
                                break

                        # 純欄位名稱動態定位：在前 15 列尋找包含「批號」、「指送地/地點」的標題列
                        batch_col = -1
                        loc_col = -1
                        date_col = -1
                        tank_col = -1
                        time_col = -1
                        mod_time_col = -1
                        cust_col = -1
                        po_col = -1
                        prod_col = -1
                        start_row = 0

                        for r_idx in range(min(15, len(rows))):
                            row = rows[r_idx]
                            if not row: continue

                            # 建立該列的 (欄位文字 -> 索引) 字典
                            header_cells = [(c_idx, str(val or "").strip().upper()) for c_idx, val in enumerate(row) if val]
                            if not header_cells: continue

                            temp_batch, temp_loc, temp_date, temp_tank = -1, -1, -1, -1
                            temp_time, temp_mod_time, temp_po, temp_cust, temp_prod = -1, -1, -1, -1, -1

                            for c_idx, v in header_cells:
                                # 批號欄位名稱匹配 (精確優先)
                                if temp_batch == -1 and any(k in v for k in ["批號", "BATCH", "LOT"]):
                                    temp_batch = c_idx
                                # 指送地/地點欄位名稱匹配
                                if temp_loc == -1 and any(k in v for k in ["指送地", "送達地點", "地點", "交貨地", "到貨地", "送達", "廠區", "LOCATION", "DEST"]):
                                    temp_loc = c_idx
                                # 品名欄位名稱匹配
                                if temp_prod == -1 and any(k in v for k in ["品名", "產品", "PRODUCT", "ITEM"]):
                                    temp_prod = c_idx
                                # 到貨日期欄位名稱匹配 (支援「預計到貨日期」、「到貨日期」、「出貨日期」)
                                if temp_date == -1 and any(k in v for k in ["預計到貨日期", "到貨日期", "出貨日期", "出車日", "到貨日", "日期", "DATE"]) and "地" not in v and "點" not in v:
                                    temp_date = c_idx
                                # 槽號欄位名稱匹配
                                if temp_tank == -1 and any(k in v for k in ["槽號", "槽車", "TANK"]) and not any(k in v for k in ["日", "期", "時間", "TIME", "DATE", "到廠", "出車", "出貨"]):
                                    temp_tank = c_idx
                                # 到貨時間欄位名稱匹配 (如「到貨時間」、「時間」)
                                if temp_time == -1 and any(k in v for k in ["到貨時間", "預計時間", "預計到廠", "時間", "TIME"]) and "修正" not in v:
                                    temp_time = c_idx
                                # 修正時間
                                if temp_mod_time == -1 and "修正" in v and ("時間" in v or "TIME" in v):
                                    temp_mod_time = c_idx
                                # 採購單號 / PO
                                if temp_po == -1 and any(k in v for k in ["採購單", "PO"]):
                                    temp_po = c_idx
                                # 對象簡稱 / 客戶
                                if temp_cust == -1 and any(k in v for k in ["對象簡稱", "對象", "客戶", "廠商", "CUSTOMER"]):
                                    temp_cust = c_idx

                            # 只要該列成功辨識出「批號」加上「指送地」或「到貨日期」，即確定為排程標題列！
                            if temp_batch != -1 and (temp_loc != -1 or temp_date != -1):
                                batch_col = temp_batch
                                loc_col = temp_loc
                                date_col = temp_date
                                tank_col = temp_tank
                                time_col = temp_time
                                mod_time_col = temp_mod_time
                                po_col = temp_po
                                cust_col = temp_cust
                                prod_col = temp_prod
                                start_row = r_idx + 1
                                break

                        # 若該分頁找不到具備「批號」與「指送地/日期」的標題列，代表非排程工作表，安全跳過
                        if batch_col == -1 or (loc_col == -1 and date_col == -1):
                            continue

                        for r_idx in range(start_row, len(rows)):
                            row = rows[r_idx]
                            if not row or len(row) == 0: continue

                            def get_cell_val(c):
                                return row[c] if c != -1 and c < len(row) else None

                            b_val = str(get_cell_val(batch_col) or "").strip().upper()
                            l_val = str(get_cell_val(loc_col) or "").strip().upper()
                            d_val = get_cell_val(date_col)
                            t_val = str(get_cell_val(tank_col) or "").strip()
                            time_val = normalize_time_str(get_cell_val(time_col))
                            mt_val = normalize_time_str(get_cell_val(mod_time_col))
                            po_val = str(get_cell_val(po_col) or "").strip()
                            cust_val = str(get_cell_val(cust_col) or "").strip()
                            p_val = str(get_cell_val(prod_col) or "").strip()

                            # 若預設欄位非 10 碼批號，全列搜尋 10 碼英數混合批號
                            if len(b_val) not in (10, 11) or not any(c.isdigit() for c in b_val):
                                for cell in row:
                                    cell_str = str(cell or "").strip().upper()
                                    if len(cell_str) in (10, 11) and any(c.isdigit() for c in cell_str) and any(c.isalpha() for c in cell_str) and "/" not in cell_str and "-" not in cell_str:
                                        b_val = cell_str
                                        break

                            if len(b_val) not in (10, 11) or not any(c.isdigit() for c in b_val):
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
                            is_valid_tank = (
                                t_val and 
                                len(t_val) <= 6 and 
                                not any(sep in t_val for sep in ["-", "/", ":", " "]) and 
                                not (len(t_val) > 4 and t_val.isdigit())
                            )
                            if not is_valid_tank:
                                t_val = get_tank_from_batch(b_val)

                            # 格式化時間 (統一為 4 碼如 0900)
                            t_final = time_val
                            if isinstance(d_val, datetime) and not t_final:
                                hm = f"{d_val.hour:02d}{d_val.minute:02d}"
                                if hm != "0000": t_final = hm

                            records.append({
                                "sheet": sheet_name,
                                "batch": b_val,
                                "tank": t_val,
                                "product": p_val,
                                "loc": clean_loc,
                                "long_code": self.mapping_dict.get(clean_loc, ""),
                                "date": norm_date,
                                "time": t_final,
                                "mod_time": mt_val,
                                "po": po_val
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
                    if "tank_var" in row_e and rec.get("tank"):
                        row_e["tank_var"].set(rec["tank"])
                    row_e["loc_var"].set(rec.get("loc", ""))
                    if "long_code_var" in row_e and rec.get("long_code"): row_e["long_code_var"].set(rec.get("long_code"))
                    if rec.get("date"): row_e["date_var"].set(rec["date"])
                    if rec.get("product") and "prod_var" in row_e: row_e["prod_var"].set(rec["product"])
                    if rec.get("po"): row_e.get("po_var", tk.StringVar()).set(rec["po"])
                    
                total_imported += len(target_records)
                
            except Exception as e:
                messagebox.showerror("匯入錯誤", f"解析檔案 {os.path.basename(filepath)} 時發生錯誤:\n{e}")
                
        if total_imported > 0:
            messagebox.showinfo("匯入成功", f"成功從所選檔案匯入 {total_imported} 筆！")


    def generate_files(self):
        if not os.path.exists(self.template_path):
            messagebox.showerror("錯誤", f"找不到範本檔案:\n{self.template_path}")
            return
        if not os.path.exists(self.mapping_path):
            messagebox.showerror("錯誤", f"找不到對照表檔案:\n{self.mapping_path}")
            return
            
        do_3in1 = self.gen_3in1_var.get()
        do_transport = False
        
        if not do_3in1:
            messagebox.showwarning("提示", "請勾選產生三合一單！")
            return

        valid_data = []
        for idx, row in enumerate(self.entries):
            if not row["chk_var"].get():
                continue
                
            batch = row["batch_var"].get().strip().upper()
            raw_loc = row["loc_var"].get().strip().upper()
            loc = clean_location_str(raw_loc, self.mapping_dict) if raw_loc else ""
            tank = row["tank_var"].get().strip() or get_tank_from_batch(batch)
            prod_str = row.get("prod_var", tk.StringVar()).get().strip().upper()
            date_str = row["date_var"].get().strip()
            time_str = ""
            mod_time_str = ""
            
            if not batch and not loc:
                continue
            if not batch or not loc:
                messagebox.showerror("錯誤", f"第 {idx+1} 項資料不齊全！")
                return
            if len(batch) not in (10, 11):
                messagebox.showerror("錯誤", f"第 {idx+1} 項的批號長度錯誤！\n批號必須為 10~11 碼，目前輸入: {batch} (長度 {len(batch)})")
                return
                
            part_no_str = row.get("part_var", tk.StringVar()).get().strip() if "part_var" in row else ""
            if not part_no_str:
                part_no_str = self.resolve_part_no(loc, prod_str)
            po_str = row.get("po_var", tk.StringVar()).get().strip() if "po_var" in row else ""
            valid_data.append({
                "batch": batch,
                "tank": tank,
                "product": prod_str,
                "loc": loc,
                "date": date_str,
                "time": time_str,
                "mod_time": mod_time_str,
                "raw_part_no": part_no_str[1:] if part_no_str.startswith("4") else part_no_str,
                "part_no": "4" + part_no_str if part_no_str and not part_no_str.startswith("4") else part_no_str,
                "po": po_str
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
            output_dir = os.path.join(self.base_dir, f"勝一三合一單輸出_{_g_date_str}")
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
                    loc_code = self.mapping_dict[loc]
                
                    try:
                        wb = openpyxl.load_workbook(self.template_path)
                        ws = wb.worksheets[0]
                    
                        tank_row = find_row_by_label(ws, ['槽號']) or 5
                        batch_row = find_row_by_label(ws, ['批號']) or 7
                        loc_row = find_row_by_label(ws, ['送達地點', '地點']) or 11
                        mat_row = find_row_by_label(ws, ['料號']) or 3
                        sup_row = find_row_by_label(ws, ['供應商']) or 9
                    
                        # 優先用 UI 已顯示的料號，確保「顯示什麼就寫什麼」
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

                        # 同步更新【TGCM用】批號公式 (=RIGHT(C7,10) 或 =RIGHT(C7,11))，避免 10/11 碼批號截斷或殘留開頭 '6'
                        for r_tgcm in (14, 20):
                            lbl_tgcm = str(ws.cell(row=r_tgcm, column=2).value or "").strip()
                            if "批號" in lbl_tgcm:
                                ws.cell(row=r_tgcm, column=3).value = f"=RIGHT(C7,{len(batch_no)})"
                    
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
                        loc_folder = os.path.join(output_dir, loc_sub_dir)
                    
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

                if getattr(self, "gen_lorry_var", None) and self.gen_lorry_var.get():
                    try:
                        batch_info_map, schema_sheet_map = self._scan_all_lorry_files()
                        opened_wbs = {}
                        lorry_missing_batches = []

                        def _get_ws(f_path, s_name):
                            if f_path not in opened_wbs:
                                opened_wbs[f_path] = openpyxl.load_workbook(f_path, data_only=False)
                            return opened_wbs[f_path][s_name]

                        for item in valid_data:
                            b_no = item["batch"]
                            l_loc = item["loc"]
                            t_no = item["tank"]
                            d_str = item["date"]
                            item_mat_no = item.get("raw_part_no") or self.resolve_part_no(l_loc, item.get("product", ""))

                            # 計算日期 MMDD 與輸出目錄
                            dt_l = None
                            date_MMDD = "0000"
                            if d_str:
                                for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%Y%m%d", "%m/%d/%Y", "%d/%m/%Y"):
                                    try:
                                        dt_l = datetime.strptime(d_str.split()[0], fmt)
                                        date_MMDD = f"{dt_l.month:02d}{dt_l.day:02d}"
                                        break
                                    except ValueError:
                                        pass
                            if not dt_l:
                                dt_l = datetime.now()
                                date_MMDD = f"{dt_l.month:02d}{dt_l.day:02d}"

                            safe_loc = "".join(c for c in l_loc if c.isalnum() or c in (' ', '_', '-')).rstrip()
                            safe_tank = str(t_no).strip() if t_no else ""
                            loc_sub_dir = f"{date_MMDD} {safe_loc} {safe_tank}".strip()
                            current_loc_folder = os.path.join(output_dir, loc_sub_dir)
                            os.makedirs(current_loc_folder, exist_ok=True)

                            # 嚴格核對：只有在生產履歷中核對到該批號時，才擷取該列產生單列生產履歷
                            if b_no in batch_info_map:
                                b_info = batch_info_map[b_no]
                                src_ws_l = _get_ws(b_info["file"], b_info["sheet"])
                                wb_l = build_single_row_lorry_workbook(src_ws_l, b_info["row"])
                                orig_ext = os.path.splitext(b_info["file"])[1] or ".xlsx"
                                base_lorry_name = f"Chemical_Lorry_{b_info.get('mat_no') or item_mat_no}"
                                t_part = f"{t_no} " if t_no else ""
                                lorry_out_name = f"{base_lorry_name}-{date_MMDD} {t_part}{l_loc}{orig_ext}"
                                out_l_path = os.path.join(current_loc_folder, lorry_out_name)
                                wb_l.save(out_l_path)
                                wb_l.close()
                                success_lorry += 1
                            else:
                                lorry_missing_batches.append(b_no)

                        if lorry_missing_batches:
                            error_msgs.append(f"⚠️ 以下批號在生產履歷中找不到，未產生其 Chemical_Lorry：{', '.join(lorry_missing_batches)}")

                        for _wb_open in opened_wbs.values():
                            try:
                                _wb_open.close()
                            except Exception:
                                pass
                    except Exception as le:
                        error_msgs.append(f"產生 Chemical_Lorry 失敗: {le}")

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

        # 全部日期群組跑完後，顯示訊息
        self.hide_loading()
        msg_parts = []
        if do_3in1:
            msg_parts.append(f"• 三合一單：成功產生 {total_success_3in1} 份")
        if do_transport:
            status_str = "成功" if total_success_transport else "失敗"
            total_count = sum(len(g) for g in groups.values())
            msg_parts.append(f"• 運輸通知表：{status_str} (共 {total_count} 筆排程卡片)")
        if getattr(self, "gen_lorry_var", None) and self.gen_lorry_var.get() and total_success_lorry > 0:
            msg_parts.append(f"• 單列 Chemical_Lorry：成功產生 {total_success_lorry} 份 (已自動對齊第 7 列)")

        dirs_str = "\n".join(all_output_dirs)
        msg = "\n".join(msg_parts) + f"\n\n檔案已儲存於資料夾：\n{dirs_str}"

        if total_error_msgs:
            msg += "\n\n部分錯誤:\n" + "\n".join(total_error_msgs[:5])
            messagebox.showwarning("完成 (但有部分錯誤)", msg)
        else:
            messagebox.showinfo("成功", msg)

        for d in all_output_dirs:
            os.startfile(d)

if __name__ == "__main__":
    app = App()
    app.mainloop()
