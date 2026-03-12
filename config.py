import os
from dotenv import load_dotenv

load_dotenv()

# 送信先メールアドレス
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL", "")

# Gmail送信元
GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")

# Anthropic APIキー
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# スクレイピング設定
REQUEST_TIMEOUT = 15  # HTTPリクエストのタイムアウト（秒）
REQUEST_DELAY = 1.0   # リクエスト間の待機時間（秒）

# ログ・状態管理ファイル
LOG_FILE = "hokkaido_press_release.log"
SEEN_RELEASES_FILE = "seen_releases.json"
