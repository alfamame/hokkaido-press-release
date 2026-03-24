"""
北海道内金融機関 プレスリリース自動収集・要約・メール送信スクリプト
毎朝8時にWindowsタスクスケジューラから実行される想定

動作ルール:
    月〜金: 前営業日分のプレスリリースを収集してメール送信（月曜は金曜分）
    土・日: 配信しない（スキップ）

使い方:
    python main.py                 # 通常実行
    python main.py --test          # テスト（メール送信せず結果を表示）
    python main.py --force         # 曜日・既読フィルタをスキップ（動作確認用）
"""
import argparse
import json
import logging
import os
import sys
from datetime import datetime, timedelta, date
from pathlib import Path

from config import (
    ANTHROPIC_API_KEY,
    LOG_FILE,
    RECIPIENT_EMAIL,
    SEEN_RELEASES_FILE,
)
from institutions import INSTITUTIONS
from mailer import send_email
from scraper import PressRelease, fetch_all
from summarizer import build_email_body, summarize

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


def load_seen_urls() -> set:
    """既読URLセットを読み込む"""
    if not os.path.exists(SEEN_RELEASES_FILE):
        return set()
    try:
        with open(SEEN_RELEASES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return set(data.get("urls", []))
    except Exception:
        return set()


def save_seen_urls(urls: set) -> None:
    """既読URLセットを保存する"""
    try:
        with open(SEEN_RELEASES_FILE, "w", encoding="utf-8") as f:
            json.dump({"urls": list(urls), "updated": datetime.now().isoformat()}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"既読URL保存エラー: {e}")


def filter_new_releases(releases: list[PressRelease], seen_urls: set) -> list[PressRelease]:
    """既読プレスリリースを除外する"""
    return [r for r in releases if r.url not in seen_urls]


def main():
    parser = argparse.ArgumentParser(description="北海道金融機関 プレスリリース自動収集・送信")
    parser.add_argument("--test", action="store_true", help="テストモード（メール送信しない）")
    parser.add_argument("--force", action="store_true", help="曜日・既読フィルタをスキップ（動作確認用）")
    args = parser.parse_args()

    today = datetime.now()
    weekday = today.weekday()  # 0=月, 1=火, ..., 5=土, 6=日

    logger.info("=" * 60)
    logger.info("北海道金融機関 プレスリリース収集開始")

    # 土・日は配信しない（--force で強制実行可）
    if weekday >= 5 and not args.force:
        day_name = "土曜日" if weekday == 5 else "日曜日"
        logger.info(f"本日は{day_name}のため配信をスキップします。")
        logger.info("=" * 60)
        sys.exit(0)

    # 前営業日を算出（月曜日は金曜日=3日前、それ以外は前日）
    days_back = 3 if weekday == 0 else 1
    target_date = (today - timedelta(days=days_back)).date()

    logger.info(f"対象機関数: {len(INSTITUTIONS)}、収集対象日: {target_date}（前営業日）")
    if args.test:
        logger.info("[テストモード] メールは送信しません")

    # 1. 前営業日分のプレスリリースを収集（余裕を持って取得し、後で日付フィルタ）
    releases = fetch_all(INSTITUTIONS, target_date=target_date)

    # 2. 既読フィルタ
    seen_urls = load_seen_urls()
    if not args.force:
        releases = filter_new_releases(releases, seen_urls)
        logger.info(f"既読除外後: {len(releases)}件")

    # 3. 日付・機関名でソート
    releases.sort(key=lambda r: (r.institution_type, r.institution, r.date or datetime.min), reverse=False)

    # 4. Claude APIで要約
    if releases and ANTHROPIC_API_KEY:
        releases = summarize(releases)
    elif releases and not ANTHROPIC_API_KEY:
        logger.warning("ANTHROPIC_API_KEY未設定のため要約なしで送信します")

    # 5. メール本文生成
    subject, html_body = build_email_body(releases, today)

    # 6. テストモードの場合はコンソールに表示して終了
    if args.test:
        print("\n" + "=" * 60)
        print(f"件名: {subject}")
        print("=" * 60)
        print(f"取得件数: {len(releases)}件")
        for r in releases:
            print(f"\n  [{r.institution_type}] {r.institution}")
            print(f"  {r.date_str()} - {r.title}")
            print(f"  URL: {r.url}")
            if r.summary:
                print(f"  要約: {r.summary}")
        return

    # 7. メール送信
    success = send_email(
        to=RECIPIENT_EMAIL,
        subject=subject,
        html_body=html_body,
    )

    # 8. 送信成功時に既読URLを更新
    if success and releases:
        seen_urls.update(r.url for r in releases)
        save_seen_urls(seen_urls)
        logger.info(f"既読URL更新: 合計{len(seen_urls)}件")

    logger.info(f"処理完了: {'送信成功' if success else '送信失敗'}")
    logger.info("=" * 60)
    sys.exit(0 if success or not releases else 1)


if __name__ == "__main__":
    main()
