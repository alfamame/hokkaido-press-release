# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands

```bash
# 通常実行（前営業日分を収集してメール送信）
python main.py

# テストモード（メール送信なし、結果をコンソールに表示）
python main.py --test

# 強制実行（曜日・既読フィルタをスキップ、動作確認用）
python main.py --force

# デバッグ推奨: 両フラグ併用（曜日・既読スキップ＋メール送信なし）
python main.py --test --force

# 依存パッケージインストール
pip install -r requirements.txt
```

終了コード: 0 = 成功（または新着なし）、1 = メール送信失敗

## Architecture Overview

このシステムは毎朝7時（JST）に GitHub Actions または Windows タスクスケジューラから実行される。

### 実行フロー（main.py）

1. **曜日判定** — 土・日はスキップ。月曜は「前営業日 = 金曜」として3日前を対象日とする
2. **スクレイピング**（scraper.py）— 各機関を RSS → HTML フォールバックの順で試行し、対象日付のプレスリリースのみ返す
3. **既読フィルタ**（seen_releases.json）— 送信済みURLを除外
4. **要約**（summarizer.py）— Claude API（claude-haiku-4-5-20251001）でまとめてバッチ要約、JSON形式で返却
5. **メール送信**（mailer.py）— Gmail SMTP（アプリパスワード認証）でHTML形式送信
6. **既読URL更新** — 送信成功時のみ seen_releases.json を更新

### スクレイピング戦略（scraper.py）

- RSS優先: 機関ごとの `rss_paths` + 共通パス（`/rss/`, `/feed/` 等）を試行
- HTMLフォールバック: 機関ごとの `news_paths` + 共通パスを試行、`<li>/<tr>/<article>` 等から日付付きリンクを抽出
- カットオフ: 対象日の前日00:00以降を取得してから、対象日のみに絞る
- リクエスト間隔: 1.0秒（`REQUEST_DELAY`）
- **`shinkin.co.jp` 共有ドメイン**: 複数の信用金庫が `https://www.shinkin.co.jp/{slug}` を共有している。`_extract_from_soup` の外部ドメイン除外ロジックでこのドメインは特別扱い（除外しない）

`PressRelease` データクラスのフィールド:
```python
institution: str        # 機関名
institution_type: str   # "銀行" | "信用金庫" | "信用組合"
title: str
url: str
date: Optional[datetime]
summary: str = ""       # Claude APIによる要約（初期値は空文字）
```

### 機関定義（institutions.py）

各機関は辞書で定義:
```python
{
    "name": "機関名",
    "type": "銀行"|"信用金庫"|"信用組合",
    "url": "https://...",
    "news_paths": [...],  # HTMLページのパス候補（優先順）。空リストでも共通パスが自動追加される
    "rss_paths": [...],   # RSSフィードのパス候補。空リストでも共通パスが自動追加される
}
```

### 要約（summarizer.py）

全プレスリリースを1回のAPIコール（バッチ）でまとめて要約する。レスポンスはJSON形式で受け取り、インデックスで各 `PressRelease.summary` に紐付ける。API失敗時は要約なしでそのまま処理続行。

### 環境変数（.env）

```
ANTHROPIC_API_KEY=...
GMAIL_ADDRESS=...
GMAIL_APP_PASSWORD=...
RECIPIENT_EMAIL=...
```

### 自動実行

- **GitHub Actions**（`.github/workflows/daily.yml`）: UTC 22:00（JST 7:00）月〜金に実行。`seen_releases.json` をコミット・プッシュして既読状態を永続化する
- **Windows タスクスケジューラ**（`setup_task.bat`）: ローカル実行用の代替手段

### 状態管理ファイル

- `seen_releases.json` — 送信済みURLのリスト（GitHub Actions でコミットされる）
- `hokkaido_press_release.log` — 実行ログ（ローカルのみ）
