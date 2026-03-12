"""
Claude APIを使ってプレスリリースを要約し、メール本文を生成するモジュール
"""
import logging
from datetime import datetime
from typing import List

import anthropic

from config import ANTHROPIC_API_KEY
from scraper import PressRelease

logger = logging.getLogger(__name__)

# 要約に使うモデル（コスト効率重視ならHaiku、品質重視ならSonnet）
MODEL = "claude-haiku-4-5-20251001"


def _build_prompt(releases: List[PressRelease], today: datetime) -> str:
    date_str = today.strftime("%Y年%m月%d日（%a）".replace("%a", _weekday_ja(today.weekday())))

    lines = []
    lines.append(f"今日は{date_str}です。")
    lines.append("以下は北海道内の金融機関（銀行・信用金庫・信用組合）のプレスリリース・お知らせ一覧です。")
    lines.append("各項目について、ビジネス担当者向けに重要ポイントを1〜2文で日本語要約してください。")
    lines.append("要約後、以下のJSON形式で返してください：\n")
    lines.append('{"summaries": [{"index": 0, "summary": "要約文"}, ...]}')
    lines.append("\n--- プレスリリース一覧 ---")

    for i, r in enumerate(releases):
        lines.append(f"\n[{i}] 機関: {r.institution}（{r.institution_type}）")
        lines.append(f"    日付: {r.date_str()}")
        lines.append(f"    タイトル: {r.title}")
        if r.summary:
            lines.append(f"    本文抜粋: {r.summary[:200]}")

    return "\n".join(lines)


def _weekday_ja(weekday: int) -> str:
    return ["月", "火", "水", "木", "金", "土", "日"][weekday]


def summarize(releases: List[PressRelease]) -> List[PressRelease]:
    """Claude APIを使って各プレスリリースに要約を付与して返す"""
    if not releases:
        return releases

    if not ANTHROPIC_API_KEY:
        logger.warning("ANTHROPIC_API_KEY が設定されていません。要約をスキップします。")
        return releases

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    today = datetime.now()

    prompt = _build_prompt(releases, today)

    try:
        message = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = message.content[0].text

        # JSON部分を抽出
        import json, re
        json_match = re.search(r'\{[\s\S]*\}', raw)
        if json_match:
            data = json.loads(json_match.group())
            summaries = {item["index"]: item["summary"] for item in data.get("summaries", [])}
            for i, release in enumerate(releases):
                if i in summaries:
                    release.summary = summaries[i]

        logger.info(f"要約完了: {len(releases)}件")

    except anthropic.APIError as e:
        logger.error(f"Claude API エラー: {e}")
    except Exception as e:
        logger.error(f"要約処理エラー: {e}", exc_info=True)

    return releases


def build_email_body(releases: List[PressRelease], today: datetime) -> tuple[str, str]:
    """メール件名と本文（HTML）を生成して返す"""
    date_str = today.strftime("%Y年%m月%d日")
    weekday = _weekday_ja(today.weekday())
    subject = f"【北海道金融機関 プレスリリース速報】{date_str}（{weekday}）"

    if not releases:
        html = f"""
<html><body style="font-family: Meiryo, 'MS PGothic', sans-serif; color: #333;">
<h2 style="color:#1a5276;">北海道金融機関 プレスリリース速報</h2>
<p style="color:#666;">{date_str}（{weekday}）</p>
<hr>
<p>本日（過去30時間以内）の新着プレスリリースはありませんでした。</p>
</body></html>
"""
        return subject, html

    # 機関種別でグループ化
    from collections import defaultdict
    groups = defaultdict(list)
    for r in releases:
        groups[r.institution_type].append(r)

    type_order = ["銀行", "信用金庫", "信用組合"]
    type_colors = {
        "銀行": "#1a5276",
        "信用金庫": "#1d6a39",
        "信用組合": "#6e2f8c",
    }

    body_parts = []
    body_parts.append(f"""
<html><body style="font-family: Meiryo, 'MS PGothic', sans-serif; color: #333; max-width: 800px; margin: 0 auto;">
<h2 style="color:#1a5276; border-bottom: 3px solid #1a5276; padding-bottom: 8px;">
  北海道金融機関 プレスリリース速報
</h2>
<p style="color:#666; margin-top: -8px;">{date_str}（{weekday}）｜合計 {len(releases)} 件</p>
""")

    for type_name in type_order:
        if type_name not in groups:
            continue

        color = type_colors.get(type_name, "#333")
        type_releases = groups[type_name]

        body_parts.append(f"""
<h3 style="color:{color}; border-left: 4px solid {color}; padding-left: 10px; margin-top: 28px;">
  {type_name}（{len(type_releases)}件）
</h3>
""")

        for r in type_releases:
            summary_html = (
                f'<p style="margin: 6px 0 0 0; color: #555; font-size: 0.92em;">{r.summary}</p>'
                if r.summary else ""
            )
            body_parts.append(f"""
<div style="border: 1px solid #ddd; border-radius: 6px; padding: 12px 16px; margin: 10px 0; background: #fafafa;">
  <div style="font-size: 0.85em; color: #888; margin-bottom: 4px;">{r.date_str()} ｜ {r.institution}</div>
  <a href="{r.url}" style="color: {color}; font-weight: bold; text-decoration: none; font-size: 1.02em;">
    {r.title}
  </a>
  {summary_html}
  <div style="margin-top: 8px;">
    <a href="{r.url}" style="font-size: 0.82em; color: #888;">{r.url}</a>
  </div>
</div>
""")

    body_parts.append("""
<hr style="margin-top: 32px; border: none; border-top: 1px solid #ddd;">
<p style="color: #aaa; font-size: 0.8em;">
  このメールは自動送信されています。配信停止・設定変更はシステム管理者にご連絡ください。
</p>
</body></html>
""")

    return subject, "".join(body_parts)
