import os
import io
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image
import easyocr
import fitz  # PyMuPDF 用於處理 PDF

class OCRCompareApp:
    def __init__(self, root):
        self.root = root
        self.root.title("OCR 單號/文字比對工具 (專用版)")
        self.root.geometry("800x600")
        
        # 標題
        lbl_title = tk.Label(root, text="🔍 OCR 單號/文字比對工具", font=("Microsoft JhengHei", 16, "bold"))
        lbl_title.pack(pady=10)
        
        # 狀態列
        self.label_status = tk.Label(root, text="正在載入 OCR 模型...", fg="orange", font=("Microsoft JhengHei", 11, "bold"))
        self.label_status.pack(pady=5)
        self.root.update()
        
        # 載入 EasyOCR
        try:
            self.reader = easyocr.Reader(['ch_tra', 'en'], gpu=False)
            self.label_status.config(text="✨ 模型載入成功！請輸入比對字樣並選擇檔案進行比對", fg="green")
        except Exception as e:
            self.label_status.config(text=f"❌ 模型載入失敗: {e}", fg="red")
            messagebox.showerror("錯誤", f"無法載入 EasyOCR: {e}")
            
        # 輸入與操作區
        frame_input = ttk.LabelFrame(root, text=" 1. 設定比對參數與選擇檔案 ", padding=15)
        frame_input.pack(fill="x", padx=20, pady=10)
        
        # 關鍵字輸入
        lbl_comp = ttk.Label(frame_input, text="欲比對的值 (單號/關鍵字):", font=("Microsoft JhengHei", 10, "bold"))
        lbl_comp.grid(row=0, column=0, sticky="w", pady=5)
        
        self.entry_compare = ttk.Entry(frame_input, font=("Microsoft JhengHei", 11), width=40)
        self.entry_compare.grid(row=0, column=1, sticky="w", padx=10, pady=5)
        
        # 檔案選取
        self.btn_select = ttk.Button(frame_input, text="2. 選擇比對檔案 (圖片/PDF)", command=self.select_file)
        self.btn_select.grid(row=1, column=0, columnspan=2, sticky="w", pady=10)
        
        self.label_path = ttk.Label(frame_input, text="尚未選擇檔案...", wraplength=700, font=("Microsoft JhengHei", 9))
        self.label_path.grid(row=2, column=0, columnspan=2, sticky="w")
        
        # 比對按鈕
        self.btn_compare = ttk.Button(root, text="🔥 開始讀取並比對", command=self.start_comparison, state="disabled")
        self.btn_compare.pack(pady=15, ipady=5, ipadx=10)
        
        # 比對結果看板 (超大字體顯示成功/失敗)
        self.label_result = tk.Label(root, text="等待比對...", font=("Microsoft JhengHei", 16, "bold"), fg="gray")
        self.label_result.pack(pady=10)
        
        # 辨識文字預覽區
        frame_preview = ttk.LabelFrame(root, text=" 影像中讀取出的文字預覽 ", padding=10)
        frame_preview.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.text_output = tk.Text(frame_preview, font=("Consolas", 10), wrap="word")
        self.text_output.pack(side="left", fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(frame_preview, command=self.text_output.yview)
        scrollbar.pack(side="right", fill="y")
        self.text_output.config(yscrollcommand=scrollbar.set)
        
        self.file_path = None

    def select_file(self):
        path = filedialog.askopenfilename(filetypes=[("支援的格式", "*.jpg;*.jpeg;*.png;*.bmp;*.pdf")])
        if path:
            self.file_path = path
            self.label_path.config(text=f"已選擇檔案：{path}")
            self.btn_compare.config(state="normal")
            self.text_output.delete("1.0", tk.END)
            self.label_result.config(text="等待比對...", fg="gray")
            self.label_status.config(text="檔案已就緒，請輸入比對值後點選「開始讀取並比對」", fg="blue")

    def toggle_ui(self, state):
        self.btn_select.config(state=state)
        self.btn_compare.config(state=state)
        self.entry_compare.config(state=state)

    def start_comparison(self):
        compare_val = self.entry_compare.get().strip()
        if not compare_val:
            messagebox.showwarning("警告", "請先輸入欲比對的值 (例如單號)！")
            return
            
        if not self.file_path:
            return
            
        self.toggle_ui("disabled")
        self.text_output.delete("1.0", tk.END)
        self.label_result.config(text="🔍 正在執行 OCR 讀取文字中...", fg="blue")
        self.root.update()
        
        is_pdf = self.file_path.lower().endswith('.pdf')
        results_all = []
        
        try:
            if is_pdf:
                self.label_status.config(text="⏳ 正在載入 PDF 檔案...", fg="blue")
                self.root.update()
                
                pdf_doc = fitz.open(self.file_path)
                total_pages = len(pdf_doc)
                
                for page_num in range(total_pages):
                    self.label_status.config(text=f"⏳ 正在辨識 PDF 第 {page_num + 1}/{total_pages} 頁...", fg="blue")
                    self.root.update()
                    
                    page = pdf_doc[page_num]
                    pix = page.get_pixmap(dpi=150)
                    img_bytes = pix.tobytes("png")
                    
                    results = self.reader.readtext(img_bytes, detail=0)
                    results_all.extend(results)
            else:
                self.label_status.config(text="⏳ 正在辨識單張圖片...", fg="blue")
                self.root.update()
                
                with open(self.file_path, "rb") as f:
                    img_bytes = f.read()
                results = self.reader.readtext(img_bytes, detail=0)
                results_all.extend(results)
            
            full_text = "\n".join(results_all)
            self.text_output.insert(tk.END, full_text)
            
            # 進行無空白、不分大小寫之精準比對
            clean_ocr = full_text.replace(" ", "").replace("\n", "").replace("\r", "").lower()
            clean_compare = compare_val.replace(" ", "").lower()
            
            if clean_compare in clean_ocr:
                self.label_result.config(text=f"✅ 比對成功！影像中包含「{compare_val}」", fg="green")
                self.label_status.config(text="✅ 比對成功！詳情請看結果顯示。", fg="green")
                messagebox.showinfo("比對成功", f"✅ 比對成功！\n\n影像中確實包含您輸入的文字：\n「{compare_val}」")
            else:
                self.label_result.config(text=f"❌ 比對失敗！未找到「{compare_val}」", fg="red")
                self.label_status.config(text="❌ 比對失敗！詳情請看結果顯示。", fg="red")
                messagebox.showerror("比對失敗", f"❌ 比對失敗！\n\n影像中未找到您輸入的文字：\n「{compare_val}」")
                
        except Exception as e:
            messagebox.showerror("錯誤", f"讀取或比對失敗：{e}")
            self.label_status.config(text="❌ 執行失敗", fg="red")
            self.label_result.config(text="❌ 錯誤發生", fg="red")
        finally:
            self.toggle_ui("normal")

if __name__ == "__main__":
    root = tk.Tk()
    app = OCRCompareApp(root)
    root.mainloop()
