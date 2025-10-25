import smtplib
from email.mime.text import MIMEText

def send_email(body):
    """發送 Email"""
    sender = "@gmail.com"
    receiver = "@gmail.com"
    app_password = "" # Gmail 應用程式密碼
    subject = "✈️ 機票價格通知"

    msg = MIMEText(body, 'plain', 'utf-8')
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = receiver

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, app_password)
            server.send_message(msg)
            print("✅ 郵件已寄出！")
            return True
    except Exception as e:
        print(f"❌ 郵件發送失敗: {e}")
        return False

def send_email_from_file(filename="email_content.txt"):
    """從檔案讀取內容並發送 Email"""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            content = f.read()
        
        if not content.strip():
            print("⚠️ 檔案內容為空")
            return False
        
        print(f"📧 正在發送 Email (內容來自 {filename})...")
        return send_email(content)
        
    except FileNotFoundError:
        print(f"❌ 找不到檔案: {filename}")
        return False
    except Exception as e:
        print(f"❌ 讀取檔案失敗: {e}")
        return False

def send_test_email():
    """發送測試郵件"""
    test_content = """
🧪 這是一封測試郵件

如果你收到這封郵件，代表 Email 功能運作正常！

航班價格監控系統已經啟動。
"""
    print("📧 發送測試郵件...")
    return send_email(test_content)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # 如果有指定檔案參數，就從檔案讀取
        filename = sys.argv[1]
        send_email_from_file(filename)
    else:
        # 否則發送測試郵件
        print("使用方式:")
        print("  python mailer.py                  # 發送測試郵件")
        print("  python mailer.py email_content.txt  # 從檔案發送")
        print()
        send_test_email()
