import os
import sys
import io
import argparse
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# 解決 Windows 主機 CP950 編碼問題
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 提升為 modify 權限，允許修改標籤 (封存、分類)
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

# 根據您的 Gmail 標籤清單建立的規則對照表
RULES = [
    # 1. 銀行、信用卡與對帳單
    {"keywords": ["聯邦銀行", "聯邦M卡"], "add_label_id": "Label_35", "label_name": "銀行/信用卡通知與對帳單/聯邦銀行"},
    {"keywords": ["中國信託", "中信銀行"], "add_label_id": "Label_30", "label_name": "銀行/信用卡通知與對帳單/中國信託"},
    {"keywords": ["合作金庫", "合庫證券"], "add_label_id": "Label_34", "label_name": "銀行/信用卡通知與對帳單/合作金庫"},
    {"keywords": ["台新銀行", "台新"], "add_label_id": "Label_31", "label_name": "銀行/信用卡通知與對帳單/台新銀行"},
    {"keywords": ["國泰世華", "國泰"], "add_label_id": "Label_36", "label_name": "銀行/信用卡通知與對帳單/國泰世華"},
    {"keywords": ["永豐", "永豐金"], "add_label_id": "Label_39", "label_name": "銀行/信用卡通知與對帳單/永豐銀行"},
    {"keywords": ["彰化縣鹿港信用合作社", "鹿港信用合作社", "鹿信"], "add_label_id": "Label_37", "label_name": "銀行/信用卡通知與對帳單/鹿信"},
    {"keywords": ["將來銀行", "NEXTBANK"], "add_label_id": "Label_28", "label_name": "銀行/信用卡通知與對帳單/將來銀行"},
    {"keywords": ["群益投信", "CAPITALFUND"], "add_label_id": "Label_26", "label_name": "銀行/信用卡通知與對帳單"}, # 歸入大類
    {"keywords": ["LINE Bank", "連線商業銀行"], "add_label_id": "Label_26", "label_name": "銀行/信用卡通知與對帳單"}, # 先歸到大類
    
    # 2. 促銷與購物
    {"keywords": ["momo購物", "momo購物網", "momo"], "add_label_id": "Label_44", "label_name": "促銷/購物/momo"},
    {"keywords": ["Coupang", "酷澎"], "add_label_id": "Label_47", "label_name": "促銷/購物/Coupang"},
    {"keywords": ["PChome"], "add_label_id": "Label_43", "label_name": "促銷/購物/PChome"},
    {"keywords": ["Uber EAT", "Uber Eats"], "add_label_id": "Label_49", "label_name": "促銷/購物/Uber EAT"},
    {"keywords": ["蝦皮", "Shopee"], "add_label_id": "Label_46", "label_name": "促銷/購物/蝦皮"},
    {"keywords": ["淘宝", "淘寶", "支付宝", "支付寶"], "add_label_id": "Label_48", "label_name": "促銷/購物/購物訂單"},
    {"keywords": ["ALCOPARK", "UncleDanker", "蛋殼北北"], "add_label_id": "Label_48", "label_name": "促銷/購物/購物訂單"},
    {"keywords": ["HOTAI購", "和泰 Points", "三星電子", "Samsung", "Google Play", "配方時代", "FOOTER"], "add_label_id": "Label_25", "label_name": "促銷/購物"}, # 歸入促銷/購物大類
    
    # 3. 其他特定標籤
    {"keywords": ["台灣高鐵", "高鐵"], "add_label_id": "Label_5772367656572430209", "label_name": "台灣高鐵"},
    {"keywords": ["台哥大", "台灣大哥大", "無框行動"], "add_label_id": "Label_7258076503041965341", "label_name": "台哥大/無框行動"},
    {"keywords": ["中國人壽", "富邦人壽"], "add_label_id": "Label_1893357093102357983", "label_name": "中國人壽/富邦"},
    {"keywords": ["電子發票", "ezPay電子發票", "全聯電子發票服務"], "add_label_id": "Label_22", "label_name": "發票/收據"},
    {"keywords": ["KKday", "DJB", "DJB CARD"], "add_label_id": "Label_1072682387686610732", "label_name": "旅遊"},
    {"keywords": ["Netlify", "OpenAI", "Supabase", "Groq", "ngrok", "Cloudflare", "Google AI Studio", "Google Cloud Shell"], "add_label_id": "Label_32", "label_name": "系統監控"},
    {"keywords": ["104人力銀行", "104"], "add_label_id": "Label_1198421407660185230", "label_name": "其他"},
]

def get_gmail_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                print("[錯誤] 找不到 'credentials.json'")
                return None
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)

def match_rule(subject, sender, snippet):
    """檢查郵件是否符合任一分類規則"""
    # 優先比對寄件者 (避免內文提到其他品牌/信用卡造成誤判)
    sender_lower = sender.lower()
    for rule in RULES:
        for keyword in rule["keywords"]:
            if keyword.lower() in sender_lower:
                return rule
                
    # 若寄件者未匹配，其次才比對主旨與摘要
    content_to_check = f"{subject} {snippet}".lower()
    for rule in RULES:
        # 排除以寄件人為主的促銷購物類與特定標籤，避免因內文提及而錯分
        if "促銷/購物" in rule["label_name"] or rule["label_name"] in ["台哥大/無框行動", "中國人壽/富邦"]:
            continue
        for keyword in rule["keywords"]:
            if keyword.lower() in content_to_check:
                return rule
    return None


def archive_and_classify_emails(service, max_results=20):
    """搜尋收件匣中的郵件，進行分類並歸檔(移除收件匣標籤)"""
    try:
        # 只搜尋收件匣 (label:INBOX) 的郵件
        query = "label:INBOX"
        results = service.users().messages().list(userId='me', q=query, maxResults=max_results).execute()
        messages = results.get('messages', [])
        
        if not messages:
            print("收件匣中沒有待處理的郵件。")
            return
            
        print(f"掃描收件匣中最近的 {len(messages)} 封郵件...")
        
        processed_count = 0
        for msg in messages:
            msg_id = msg['id']
            # 取得主旨與寄件人以判斷分類
            detail = service.users().messages().get(userId='me', id=msg_id, format='metadata', metadataHeaders=['Subject', 'From']).execute()
            
            headers = detail.get('payload', {}).get('headers', [])
            subject = "無主旨"
            sender = "未知寄件者"
            for h in headers:
                name = h.get('name', '').lower()
                if name == 'subject':
                    subject = h.get('value')
                elif name == 'from':
                    sender = h.get('value')
                    
            snippet = detail.get('snippet', '')
            
            # 比對分類規則
            rule = match_rule(subject, sender, snippet)
            if rule:
                print(f"\n匹配成功:")
                print(f"  - 郵件: {subject} ({sender})")
                print(f"  - 分類至: {rule['label_name']} (ID: {rule['add_label_id']})")
                
                # 執行 API：加入新標籤，並移除 'INBOX' 標籤 (即歸檔)
                body = {
                    "addLabelIds": [rule['add_label_id']],
                    "removeLabelIds": ["INBOX"]
                }
                service.users().messages().modify(userId='me', id=msg_id, body=body).execute()
                print("  => 已成功移動並從收件匣歸檔！")
                processed_count += 1
            else:
                # 若無匹配則保留在收件匣
                pass
                
        print(f"\n=====================================")
        print(f"處理完成！本次共歸檔與分類了 {processed_count} 封郵件。")
        print(f"=====================================")
        
    except HttpError as error:
        print(f"發生 API 錯誤: {error}")

def main():
    parser = argparse.ArgumentParser(description="Gmail 自動歸檔與分類工具")
    parser.add_argument('--limit', type=int, default=20, help="每次處理的郵件上限")
    args = parser.parse_args()

    print("正在連結 Gmail 服務...")
    service = get_gmail_service()
    if not service:
        return
        
    archive_and_classify_emails(service, max_results=args.limit)

if __name__ == '__main__':
    main()
