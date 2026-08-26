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
2. **スクレイピング**（scraper.py）— 各機関を RSS → HTML フォールバックの順で試行し、対象日から遡って `LOOKBACK_DAYS` 日分のプレスリリースを返す
3. **既読フィルタ**（seen_releases.json）— `--force` なしの場合、送信済みURLを除外。収集期間に幅があるぶん、重複送信はこのフィルタが防ぐ
4. **要約**（summarizer.py）— Claude API（claude-haiku-4-5-20251001）でまとめてバッチ要約、JSON形式で返却
5. **メール送信**（mailer.py）— Gmail SMTP（アプリパスワード認証）でHTML形式送信
6. **既読URL更新** — 送信成功時のみ seen_releases.json を更新。`--test` モードでは更新しない

### スクレイピング戦略（scraper.py）

- RSS優先: 機関ごとの `rss_paths` + 共通パス（`/rss/`, `/feed/` 等）を試行
- HTMLフォールバック: まず機関ごとの `news_paths` を試し、収穫ゼロなら共通パス（`COMMON_NEWS_PATHS`）を試す。`<li>/<tr>/<article>` 等から日付付きリンクを抽出
- **複数ニュース枠**: `multi_paths: True` の機関は `news_paths` を全て走査してURL単位で重複除去しつつマージする（未指定なら最初にヒットしたパスで打ち切り）。網走信用金庫のようにニュース一覧が複数ページに分かれている機関向け
- **収集期間**: 対象日から遡って `LOOKBACK_DAYS`（config.py、既定7日）日分を対象にする。掲載日を遡ってアップされた記事の取りこぼしを防ぐため幅を持たせており、未来日付は除外する。取得カットオフは開始日のさらに前日00:00
- リクエスト間隔: 1.0秒（`REQUEST_DELAY`）、HTMLページ内の複数パス試行時は0.3秒
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
    "news_paths": [...],  # HTMLページのパス候補（優先順）。空リストでも共通パスが自動的に試される
    "rss_paths": [...],   # RSSフィードのパス候補。空リストでも共通パスが自動追加される

    # 以下は任意（必要な機関のみ）
    "multi_paths": True,        # news_paths を全て走査してマージする（ニュース枠が複数ある機関）
    "link_base": "https://...", # 一覧ページ内の相対リンクを解決する基準URL
    "link_from_onclick": True,  # href ではなく onclick の window.open() のURLを使う
}
```

`link_base` は、一覧ページのURLと相対リンクの基準がずれている機関で使う（釧路・北門の `_news/history.html` は親ディレクトリ基準のため、指定しないとパスが二重になり404になる）。
`link_from_onclick` は `href` が壊れている機関で使う（留萌の一覧CGIは `href` の末尾に `;` が付いた無効URLで、正しい遷移先は `onclick` 側にある）。

機関を追加する場合:
1. `institutions.py` の `INSTITUTIONS` リストに辞書を追加する
2. `shinkin.co.jp` 共有ドメインの機関は `url` を `https://www.shinkin.co.jp/{slug}` 形式にする
3. `python main.py --test --force` で動作確認する
4. 抽出できたURLが実際に200を返すか確認する（相対パス解決を誤ると件数は出るのに全て404になる）

### 要約・メール本文生成（summarizer.py）

- `summarize()`: 全プレスリリースを1回のAPIコール（バッチ）でまとめて要約。レスポンスはJSON形式で受け取り、インデックスで各 `PressRelease.summary` に紐付ける。API失敗時は要約なしでそのまま処理続行
- `build_email_body()`: 機関種別（銀行→信用金庫→信用組合）でグループ化したHTML本文と件名を返す。種別ごとにカラーコードで色分けされる

### 環境変数（.env）

```
ANTHROPIC_API_KEY=...
GMAIL_ADDRESS=...
GMAIL_APP_PASSWORD=...   # Googleアプリパスワード（16文字）
RECIPIENT_EMAIL=...
```

GitHub Actions では同名の Secrets（Settings → Secrets and variables → Actions）として設定する。

### 主な設定値（config.py）

- `LOOKBACK_DAYS` — 対象日から遡る収集日数（既定7）。`1` にすると対象日ちょうどのみの旧挙動になる
- `REQUEST_TIMEOUT` / `REQUEST_DELAY` — HTTPタイムアウト（15秒）とリクエスト間隔（1.0秒）

### 自動実行

- **GitHub Actions**（`.github/workflows/daily.yml`）: UTC 22:00（JST 7:00）月〜金に実行。`seen_releases.json` をコミット・プッシュして既読状態を永続化する。`workflow_dispatch` で手動実行も可能
- **Windows タスクスケジューラ**（`setup_task.bat`）: ローカル実行用の代替手段

### 状態管理ファイル

- `seen_releases.json` — 送信済みURLのリスト（GitHub Actions でコミットされる）
- `hokkaido_press_release.log` — 実行ログ（ローカルのみ）
