"""
Gmailアプリパスワードの動作確認スクリプト（任意実行）

事前準備:
1. Googleアカウントで「2段階認証」を有効にする
   https://myaccount.google.com/security

2. 「アプリパスワード」を作成する
   https://myaccount.google.com/apppasswords
   ※ アプリ名は任意（例: HokkaidoPressRelease）
   ※ 生成された16文字のパスワードをコピー

3. .env に以下を記入:
   GMAIL_ADDRESS=あなたのgmail@gmail.com
   GMAIL_APP_PASSWORD=logu zuim mkss evof（スペースなしでも可）

4. このスクリプトでテスト送信:
   python gmail_setup.py
"""
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv

load_dotenv()

GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL", "")


def test_send():
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        print("エラー: .env に GMAIL_ADDRESS と GMAIL_APP_PASSWORD を設定してください。")
        return

    to = RECIPIENT_EMAIL or GMAIL_ADDRESS
    subject = "【テスト】北海道金融機関プレスリリース Bot"
    body = "このメールはテスト送信です。正常に動作しています。"

    msg = MIMEMultipart()
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    print(f"送信元: {GMAIL_ADDRESS}")
    print(f"送信先: {to}")
    print("接続中...")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.send_message(msg)

    print("送信完了！受信ボックスを確認してください。")


if __name__ == "__main__":
    test_send()
