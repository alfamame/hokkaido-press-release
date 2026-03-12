# 北海道金融機関 プレスリリース自動メール 設定手順

## 概要

北海道内の銀行・信用金庫・信用組合のプレスリリースを毎朝8時に自動収集し、
`eigyo@obihiro.shinkin.jp` へメール送信するシステムです。

---

## セットアップ手順

### 1. Pythonパッケージのインストール

```
pip install -r requirements.txt
```

---

### 2. Anthropic APIキーの設定

1. https://console.anthropic.com/ でAPIキーを取得
2. `.env.example` を `.env` にコピーして編集：

```
cp .env.example .env
```

`.env` を開いて APIキーを入力：
```
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxx
```

---

### 3. Gmail OAuth2認証の設定

#### 3-1. Google Cloud Console でOAuth認証情報を作成

1. https://console.cloud.google.com/ にアクセス
2. プロジェクトを新規作成（または既存を選択）
3. 「APIとサービス」→「ライブラリ」→ **「Gmail API」** を検索して有効化
4. 「APIとサービス」→「認証情報」→「認証情報を作成」→「OAuth クライアントID」
5. アプリケーションの種類: **「デスクトップアプリ」** を選択して作成
6. 作成後、**「JSONをダウンロード」** をクリック
7. ダウンロードしたファイルを **`credentials.json`** という名前でこのフォルダに保存

#### 3-2. 初回認証を実行

```
python gmail_setup.py
```

ブラウザが開くのでGoogleアカウントでログインして「許可」します。
成功すると `token.json` が作成されます。

#### 3-3. .env に送信元アドレスを追記

```
SENDER_EMAIL=あなたのgmail@gmail.com
```

---

### 4. 動作確認

```
python main.py --test
```

テストモードではメールを送信せず、取得結果をコンソールに表示します。

---

### 5. タスクスケジューラへの登録（毎日8時自動実行）

`setup_task.bat` を **管理者権限** で実行してください。

```
右クリック → 「管理者として実行」
```

登録されたタスクの確認：
```
schtasks /query /tn HokkaidoPressRelease
```

今すぐ手動実行してテスト：
```
schtasks /run /tn HokkaidoPressRelease
```

---

## ファイル構成

| ファイル | 説明 |
|---|---|
| `main.py` | メインスクリプト |
| `scraper.py` | ウェブスクレイピングモジュール |
| `summarizer.py` | Claude API要約モジュール |
| `mailer.py` | Gmail送信モジュール |
| `institutions.py` | 対象金融機関リスト |
| `config.py` | 設定値 |
| `gmail_setup.py` | Gmail認証初期設定（初回のみ） |
| `setup_task.bat` | タスクスケジューラ登録 |
| `credentials.json` | Google OAuth認証情報（要作成） |
| `token.json` | Gmail認証トークン（自動生成） |
| `.env` | APIキー等（要作成） |
| `seen_releases.json` | 既読プレスリリース管理（自動生成） |
| `hokkaido_press_release.log` | 実行ログ（自動生成） |

---

## よくある質問

**Q: メールが届かない場合は？**
A: `hokkaido_press_release.log` を確認してください。Gmail APIのエラーが記録されています。

**Q: プレスリリースが取得できない金融機関がある場合は？**
A: `institutions.py` の `news_paths` にそのサイトのお知らせページURLパスを追加してください。

**Q: 要約なしで送りたい場合は？**
A: `.env` の `ANTHROPIC_API_KEY` を空にすると要約なしで送信されます。

**Q: 送信先を変更したい場合は？**
A: `config.py` の `RECIPIENT_EMAIL` を編集してください。
