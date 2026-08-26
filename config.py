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

# 収集対象期間（対象日から遡る日数。1なら対象日のみ）
# 掲載が遅れた記事・バックデート掲載の取りこぼしを防ぐため幅を持たせる。
# 重複送信は seen_releases.json の既読URLフィルタで防がれる。
LOOKBACK_DAYS = 7

# ログ・状態管理ファイル
LOG_FILE = "hokkaido_press_release.log"
SEEN_RELEASES_FILE = "seen_releases.json"
