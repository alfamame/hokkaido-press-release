"""
GmailのSMTP（アプリパスワード）でメールを送信するモジュール
"""
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import GMAIL_ADDRESS, GMAIL_APP_PASSWORD

logger = logging.getLogger(__name__)


def send_email(to: str, subject: str, html_body: str) -> bool:
    """
    HTMLメールをGmail SMTPで送信する。

    Returns:
        True: 送信成功
        False: 送信失敗
    """
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = GMAIL_ADDRESS
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.send_message(msg)

        logger.info(f"メール送信完了: to={to}, subject={subject}")
        return True

    except smtplib.SMTPAuthenticationError:
        logger.error("Gmail認証エラー: GMAIL_ADDRESS / GMAIL_APP_PASSWORD を確認してください")
        return False
    except Exception as e:
        logger.error(f"メール送信エラー: {e}", exc_info=True)
        return False
