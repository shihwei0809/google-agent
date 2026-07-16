import os
import argparse
import base64
import sys
import io

# 解決 Windows 主機 CP950 編碼不支援 Emoji/特殊字元的問題
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


# 設定 Gmail API 的存取範圍 (Scope)
# readonly 權限只能讀取，不能修改或刪除，較安全
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_gmail_service():
    """取得授權後的 Gmail 服務實例"""
    creds = None
    # token.json 儲存使用者的存取權杖，會在首次授權後自動產生
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # 如果沒有有效的憑證，引導使用者登入
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                print("[錯誤] 找不到 'credentials.json' 檔案。")
                print("請參考 SKILL.md 前往 Google Cloud Console 建立 OAuth 憑證並下載存放到此目錄。")
                return None
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # 儲存憑證供下次使用
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
            
    return build('gmail', 'v1', credentials=creds)

def parse_parts(parts):
    """遞迴解析多部分郵件內容以取得純文字 body"""
    text = ""
    for part in parts:
        mime_type = part.get('mimeType')
        body = part.get('body', {})
        data = body.get('data')
        
        if mime_type == 'text/plain' and data:
            text += base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        elif part.get('parts'):
            text += parse_parts(part.get('parts'))
    return text

def get_message_content(service, msg_id):
    """獲取郵件的詳細內容 (寄件者、主旨、時間、正文)"""
    try:
        message = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
        payload = message.get('payload', {})
        headers = payload.get('headers', [])
        
        subject = "無主旨"
        sender = "未知寄件者"
        date = "未知時間"
        
        for header in headers:
            name = header.get('name', '').lower()
            if name == 'subject':
                subject = header.get('value')
            elif name == 'from':
                sender = header.get('value')
            elif name == 'date':
                date = header.get('value')
                
        snippet = message.get('snippet', '')
        
        # 嘗試解析完整正文
        body = ""
        parts = payload.get('parts')
        if parts:
            body = parse_parts(parts)
        else:
            body_data = payload.get('body', {}).get('data')
            if body_data:
                body = base64.urlsafe_b64decode(body_data).decode('utf-8', errors='ignore')
                
        if not body:
            body = snippet # 如果無法解析正文，使用摘要 (snippet)
            
        return {
            'id': msg_id,
            'subject': subject,
            'sender': sender,
            'date': date,
            'snippet': snippet,
            'body': body
        }
    except Exception as e:
        print(f"解析郵件 {msg_id} 失敗: {e}")
        return None

def fetch_emails(service, max_results=10, query="label:UNREAD"):
    """取得郵件列表"""
    try:
        results = service.users().messages().list(userId='me', q=query, maxResults=max_results).execute()
        messages = results.get('messages', [])
        
        if not messages:
            print("找不到符合條件的郵件。")
            return []
            
        print(f"成功取得 {len(messages)} 封郵件，正在解析詳細內容...")
        detailed_messages = []
        for msg in messages:
            detail = get_message_content(service, msg['id'])
            if detail:
                detailed_messages.append(detail)
        return detailed_messages
    except HttpError as error:
        print(f"發生 API 錯誤: {error}")
        return []

def main():
    parser = argparse.ArgumentParser(description="Gmail API 郵件整理工具")
    parser.add_argument('--limit', type=int, default=10, help="最多讀取的郵件數量")
    parser.add_argument('--query', type=str, default="label:UNREAD", help="Gmail 搜尋查詢字串 (例如 'label:INBOX' 或 'is:unread')")
    args = parser.parse_args()

    print("正在連結 Gmail 服務...")
    service = get_gmail_service()
    if not service:
        return
        
    print(f"正在搜尋符合條件的郵件 (查詢條件: '{args.query}', 限制上限: {args.limit} 封)...")
    emails = fetch_emails(service, max_results=args.limit, query=args.query)
    
    print("\n" + "="*50)
    print(f" 郵件整理清單 (共 {len(emails)} 封)")
    print("="*50)
    for idx, mail in enumerate(emails, 1):
        print(f"\n[{idx}] 主旨: {mail['subject']}")
        print(f"    寄件人: {mail['sender']}")
        print(f"    時間: {mail['date']}")
        print(f"    簡短摘要: {mail['snippet']}")
        print("-" * 30)

if __name__ == '__main__':
    main()
