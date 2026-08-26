"""
各金融機関のウェブサイトからプレスリリース・お知らせを収集するモジュール
"""
import re
import time
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, date
from typing import List, Optional
from urllib.parse import urljoin, urlparse

import feedparser
import requests
from bs4 import BeautifulSoup

from config import REQUEST_TIMEOUT, REQUEST_DELAY, LOOKBACK_DAYS

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# 日本語日付パターン（西暦）
DATE_PATTERNS = [
    re.compile(r'(\d{4})[年/\-.]\s*(\d{1,2})[月/\-.]\s*(\d{1,2})日?'),
    re.compile(r'(\d{4})(\d{2})(\d{2})'),  # 20260311形式
]

# 令和元号パターン（令和N年 = N + 2018）
REIWA_PATTERN = re.compile(r'令和\s*(\d{1,2})年\s*(\d{1,2})月\s*(\d{1,2})日')
_REIWA_BASE = 2018

# URLに埋め込まれた日付パターン（例: _20260331.pdf, -20260219.html）
URL_DATE_PATTERN = re.compile(r'[_\-](\d{4})(\d{2})(\d{2})(?:[_.\-]|$)')

# onclick="window.open('URL', ...)" から遷移先を取り出すパターン
# （href が壊れており onclick 側が正しい機関向け。留萌信用金庫など）
ONCLICK_URL_PATTERN = re.compile(r"""window\.open\(\s*['"]([^'"]+)['"]""")

# 機関ごとの news_paths で見つからなかった場合に試す共通パス
COMMON_NEWS_PATHS = [
    "/news/index.html", "/topics/index.html",
    "/information/", "/release/", "/pr/",
    "/newsrelease/", "/pressrelease/",
    "/",
]


@dataclass
class PressRelease:
    institution: str
    institution_type: str
    title: str
    url: str
    date: Optional[datetime]
    summary: str = ""

    def date_str(self) -> str:
        if self.date:
            return self.date.strftime("%Y年%m月%d日")
        return "日付不明"


def _parse_date(text: str) -> Optional[datetime]:
    """テキストから日付を抽出して返す"""
    for pattern in DATE_PATTERNS:
        m = pattern.search(text)
        if m:
            try:
                y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
                if 2020 <= y <= 2035 and 1 <= mo <= 12 and 1 <= d <= 31:
                    return datetime(y, mo, d)
            except (ValueError, OverflowError):
                pass
    m = REIWA_PATTERN.search(text)
    if m:
        try:
            y = int(m.group(1)) + _REIWA_BASE
            mo, d = int(m.group(2)), int(m.group(3))
            if 2020 <= y <= 2035 and 1 <= mo <= 12 and 1 <= d <= 31:
                return datetime(y, mo, d)
        except (ValueError, OverflowError):
            pass
    return None


def _fetch(url: str) -> Optional[requests.Response]:
    """HTTPリクエストを実行して返す（エラー時はNone）"""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        if resp.status_code == 200:
            resp.encoding = resp.apparent_encoding or "utf-8"
            return resp
        logger.debug(f"HTTP {resp.status_code}: {url}")
    except requests.RequestException as e:
        logger.debug(f"リクエスト失敗 {url}: {e}")
    return None


def _href_of(institution: dict, link_tag) -> str:
    """<a>タグから遷移先URLを取り出す（link_from_onclick 指定時は onclick を優先）"""
    if institution.get("link_from_onclick"):
        m = ONCLICK_URL_PATTERN.search(link_tag.get("onclick", "") or "")
        if m:
            return m.group(1).strip()
    return (link_tag.get("href") or "").strip()


def _try_rss(institution: dict, cutoff: datetime) -> List[PressRelease]:
    """RSSフィードからプレスリリースを取得"""
    base = institution["url"].rstrip("/")
    results = []

    # 共通のRSSパスも追加して試行
    rss_paths = institution.get("rss_paths", []) + [
        "/rss/", "/feed/", "/news/rss/", "/topics/rss/",
        "/rss.xml", "/feed.xml", "/atom.xml",
    ]

    for path in rss_paths:
        feed_url = base + path
        try:
            feed = feedparser.parse(feed_url)
            if not feed.entries:
                continue

            for entry in feed.entries:
                pub = entry.get("published_parsed") or entry.get("updated_parsed")
                pub_dt = datetime(*pub[:6]) if pub else None

                # 日付が取得できない場合はタイトルから試みる
                if not pub_dt:
                    pub_dt = _parse_date(entry.get("title", "") + " " + entry.get("summary", ""))

                if pub_dt and pub_dt < cutoff:
                    continue

                title = entry.get("title", "").strip()
                link = entry.get("link", "").strip()
                summary = BeautifulSoup(entry.get("summary", ""), "html.parser").get_text(strip=True)

                if title and link:
                    results.append(PressRelease(
                        institution=institution["name"],
                        institution_type=institution["type"],
                        title=title,
                        url=link,
                        date=pub_dt,
                        summary=summary[:300],
                    ))

            if results:
                logger.info(f"{institution['name']}: RSSから{len(results)}件取得 ({feed_url})")
                return results

        except Exception as e:
            logger.debug(f"RSS失敗 {feed_url}: {e}")

    return []


def _extract_from_soup(institution: dict, soup: BeautifulSoup, page_url: str, cutoff: datetime) -> List[PressRelease]:
    """BeautifulSoupオブジェクトからプレスリリースを抽出"""
    results = []
    base_url = institution["url"].rstrip("/")
    seen_urls = set()

    # ニュース・お知らせ系の要素を探す
    # パターン1: <li>や<dt>の中に日付とリンクがある
    # パターン2: <tr>の中に日付とリンクがある
    candidates = soup.find_all(["li", "dt", "tr", "article", "div", "p"], limit=500)

    for tag in candidates:
        text = tag.get_text(" ", strip=True)
        if len(text) < 5 or len(text) > 500:
            continue

        date = _parse_date(text)
        if not date:
            continue
        if date < cutoff:
            continue

        # リンクを探す
        link_tag = tag.find("a", href=True)
        if not link_tag:
            continue

        href = _href_of(institution, link_tag)
        if not href or href.startswith("#") or href.startswith("javascript"):
            continue

        # 絶対URLに変換
        full_url = urljoin(page_url, href)

        if full_url in seen_urls:
            continue
        seen_urls.add(full_url)

        title = link_tag.get_text(strip=True)
        if not title:
            title = text[:100]

        # 不要な要素を除外（ナビゲーションリンクなど）
        if len(title) < 4:
            continue
        # 外部ドメインのリンクは除外（ただし信頼できるドメインは許可）
        parsed = urlparse(full_url)
        base_parsed = urlparse(base_url)
        if parsed.netloc and parsed.netloc != base_parsed.netloc:
            # shinkin.co.jpサブパスの場合は許可
            if "shinkin.co.jp" not in parsed.netloc and "shinkin.co.jp" not in base_parsed.netloc:
                continue

        results.append(PressRelease(
            institution=institution["name"],
            institution_type=institution["type"],
            title=title,
            url=full_url,
            date=date,
        ))

    # パターン3: <dt>に日付、隣接する<dd>にリンクがある場合（北見信用金庫等）
    for dt_tag in soup.find_all("dt"):
        text = dt_tag.get_text(" ", strip=True)
        if len(text) < 4 or len(text) > 100:
            continue
        date = _parse_date(text)
        if not date or date < cutoff:
            continue
        dd_tag = dt_tag.find_next_sibling("dd")
        if not dd_tag:
            continue
        link_tag = dd_tag.find("a", href=True)
        if not link_tag:
            continue
        href = _href_of(institution, link_tag)
        if not href or href.startswith("#") or href.startswith("javascript"):
            continue
        full_url = urljoin(page_url, href)
        if full_url in seen_urls:
            continue
        seen_urls.add(full_url)
        title = link_tag.get_text(strip=True)
        if not title or len(title) < 4:
            continue
        parsed = urlparse(full_url)
        base_parsed = urlparse(base_url)
        if parsed.netloc and parsed.netloc != base_parsed.netloc:
            if "shinkin.co.jp" not in parsed.netloc and "shinkin.co.jp" not in base_parsed.netloc:
                continue
        results.append(PressRelease(
            institution=institution["name"],
            institution_type=institution["type"],
            title=title,
            url=full_url,
            date=date,
        ))

    # パターン4: リンクのURL自体に日付が含まれる場合（日高信用金庫等、_YYYYMMDDパターン）
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith("#") or href.startswith("javascript"):
            continue
        m = URL_DATE_PATTERN.search(href)
        if not m:
            continue
        try:
            y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
            if not (2020 <= y <= 2035 and 1 <= mo <= 12 and 1 <= d <= 31):
                continue
            date = datetime(y, mo, d)
        except ValueError:
            continue
        if date < cutoff:
            continue
        full_url = urljoin(page_url, href)
        if full_url in seen_urls:
            continue
        seen_urls.add(full_url)
        title = a.get_text(strip=True)
        if not title or len(title) < 4:
            continue
        parsed = urlparse(full_url)
        base_parsed = urlparse(base_url)
        if parsed.netloc and parsed.netloc != base_parsed.netloc:
            if "shinkin.co.jp" not in parsed.netloc and "shinkin.co.jp" not in base_parsed.netloc:
                continue
        results.append(PressRelease(
            institution=institution["name"],
            institution_type=institution["type"],
            title=title,
            url=full_url,
            date=date,
        ))

    return results


def _unique(paths: list) -> list:
    """重複を除去しながら順序を保持する"""
    seen = set()
    result = []
    for p in paths:
        if p not in seen:
            seen.add(p)
            result.append(p)
    return result


def _scan_paths(institution: dict, paths: list, cutoff: datetime, collect_all: bool) -> List[PressRelease]:
    """指定パスを順に走査する。collect_all=False なら最初にヒットしたパスで打ち切る"""
    base = institution["url"].rstrip("/")
    results = []
    seen_urls = set()

    for i, path in enumerate(paths):
        if i:
            time.sleep(0.3)

        url = base + path
        resp = _fetch(url)
        if not resp:
            continue

        soup = BeautifulSoup(resp.text, "lxml")
        resolve_url = institution.get("link_base", url)
        found = [r for r in _extract_from_soup(institution, soup, resolve_url, cutoff)
                 if r.url not in seen_urls]
        if not found:
            continue

        seen_urls.update(r.url for r in found)
        results.extend(found)
        logger.info(f"{institution['name']}: HTMLから{len(found)}件取得 ({url})")

        if not collect_all:
            break

    return results


def _try_html(institution: dict, cutoff: datetime) -> List[PressRelease]:
    """HTMLページからプレスリリースを取得

    multi_paths=True の機関は news_paths を全て走査してマージする
    （ニュース枠がページごとに分かれている網走・留萌などに対応）。
    """
    configured = _unique(institution.get("news_paths", []))
    multi = bool(institution.get("multi_paths"))

    results = _scan_paths(institution, configured, cutoff, collect_all=multi)
    if results:
        return results

    # 機関固有のパスで取れなければ共通パスを順に試す
    fallback = [p for p in COMMON_NEWS_PATHS if p not in configured]
    return _scan_paths(institution, fallback, cutoff, collect_all=False)


def fetch_all(institutions: list, target_date: date = None,
              lookback_days: int = None) -> List[PressRelease]:
    """
    全金融機関のプレスリリースを収集して返す。

    target_date:   収集対象日（省略時は前日）
    lookback_days: target_date から遡って何日分を対象にするか（省略時は config の値）。
                   掲載が遅れた記事を取りこぼさないための幅で、重複は既読URLフィルタが防ぐ。
    """
    if target_date is None:
        target_date = (datetime.now() - timedelta(days=1)).date()
    if lookback_days is None:
        lookback_days = LOOKBACK_DAYS

    start_date = target_date - timedelta(days=max(1, lookback_days) - 1)
    # 収集範囲: 開始日のさらに前日 00:00 を下限にして余裕を持って取得
    cutoff = datetime.combine(start_date - timedelta(days=1), datetime.min.time())
    all_releases = []

    for inst in institutions:
        logger.info(f"収集開始: {inst['name']}")
        try:
            releases = _try_rss(inst, cutoff)
            if not releases:
                releases = _try_html(inst, cutoff)

            # start_date〜target_date の範囲に絞る（未来日付の誤検出は除外）
            releases = [r for r in releases
                        if r.date and start_date <= r.date.date() <= target_date]

            if releases:
                all_releases.extend(releases)
                logger.info(f"{inst['name']}: {len(releases)}件のプレスリリースを取得")
            else:
                logger.info(f"{inst['name']}: {start_date}〜{target_date} の新着プレスリリースなし")

        except Exception as e:
            logger.error(f"{inst['name']}: 収集エラー - {e}", exc_info=True)

        time.sleep(REQUEST_DELAY)

    logger.info(f"収集完了: 合計{len(all_releases)}件")
    return all_releases
