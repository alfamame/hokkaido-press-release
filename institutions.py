# 収集対象の金融機関リスト（北海道内23機関＋道外の主要信用金庫4庫）
#
# news_paths:        プレスリリース・お知らせページのURLパス候補（優先順）
# rss_paths:         RSSフィードのパス候補
# multi_paths:       True なら news_paths を全て走査してマージする（ニュース枠が複数ある機関向け）
#                    未指定なら最初にヒットしたパスで打ち切る
# link_base:         一覧ページ内の相対リンクを解決する基準URL（ページURLと基準がずれる機関向け）
# link_from_onclick: True なら <a> の href ではなく onclick の window.open() のURLを使う
# json_feed:         一覧をJavaScriptで描画する機関向け。JSONを直接読む設定（詳細は CLAUDE.md）

INSTITUTIONS = [
    # ===== 銀行 =====
    {
        "name": "北洋銀行",
        "type": "銀行",
        "url": "https://www.hokuyobank.co.jp",
        "news_paths": ["/news/", "/topics/", "/newsrelease/", "/news/index.html"],
        "rss_paths": ["/rss/news.xml", "/feed/", "/rss.xml"],
    },
    {
        "name": "北海道銀行",
        "type": "銀行",
        "url": "https://www.hokkaidobank.co.jp",
        "news_paths": ["/news/", "/topics/", "/release/", "/information/"],
        "rss_paths": ["/rss/", "/feed/", "/rss.xml"],
    },

    # ===== 信用金庫 =====
    {
        "name": "北海道信用金庫",
        "type": "信用金庫",
        "url": "https://www.shinkin.co.jp/hokkaido",
        "news_paths": ["/news/", "/topics/", "/info/", "/"],
        "rss_paths": [],
    },
    {
        "name": "室蘭信用金庫",
        "type": "信用金庫",
        "url": "https://www.shinkin.co.jp/muroshin",
        "news_paths": ["/_news/history.html", "/news/", "/topics/", "/info/", "/"],
        "rss_paths": [],
    },
    {
        "name": "空知信用金庫",
        "type": "信用金庫",
        "url": "https://www.shinkin.co.jp/sorachi",
        "news_paths": ["/news/", "/topics/", "/info/", "/"],
        "rss_paths": [],
    },
    {
        "name": "苫小牧信用金庫",
        "type": "信用金庫",
        "url": "https://www.shinkin.co.jp/tomashin",
        "news_paths": ["/index.htm"],
        "rss_paths": [],
    },
    {
        "name": "北門信用金庫",
        "type": "信用金庫",
        "url": "https://www.shinkin.co.jp/hokumon",
        "news_paths": ["/_news/history.html", "/news.html", "/"],
        "rss_paths": [],
        # _news/history.html のリンクが親ディレクトリ(hokumon/)基準の相対パスのため
        "link_base": "https://www.shinkin.co.jp/hokumon/",
    },
    {
        "name": "伊達信用金庫",
        "type": "信用金庫",
        "url": "https://www.shinkin.co.jp/dateshin",
        "news_paths": ["/_news/history.html", "/news/", "/topics/", "/info/", "/"],
        "rss_paths": [],
    },
    {
        "name": "北空知信用金庫",
        "type": "信用金庫",
        "url": "https://www.kitashin-bank.co.jp",
        "news_paths": ["/news/"],
        "rss_paths": [],
    },
    {
        "name": "日高信用金庫",
        "type": "信用金庫",
        "url": "https://www.shinkin.co.jp/hidaka",
        "news_paths": ["/"],
        "rss_paths": [],
    },
    {
        "name": "渡島信用金庫",
        "type": "信用金庫",
        "url": "https://www.shinkin.co.jp/oshima",
        "news_paths": ["/_news/history.html", "/news/", "/topics/", "/info/", "/"],
        "rss_paths": [],
    },
    {
        "name": "道南うみ街信用金庫",
        "type": "信用金庫",
        "url": "https://www.d-umishin.co.jp",
        "news_paths": ["/news/", "/topics/", "/info/", "/newsrelease/", "/"],
        "rss_paths": ["/feed/", "/rss/", "/rss.xml"],
    },
    {
        "name": "旭川信用金庫",
        "type": "信用金庫",
        "url": "https://www.shinkin.co.jp/ask",
        "news_paths": ["/news/", "/topics/", "/info/", "/"],
        "rss_paths": [],
    },
    {
        "name": "稚内信用金庫",
        "type": "信用金庫",
        "url": "https://www.shinkin.co.jp/wakashin",
        "news_paths": ["/news/", "/topics/", "/info/", "/"],
        "rss_paths": [],
    },
    {
        "name": "留萌信用金庫",
        "type": "信用金庫",
        "url": "https://www.shinkin.co.jp/rumoi",
        # お知らせはトップページのiframe内CGIで配信されている（大切なお知らせ／新着情報の2枠）
        "news_paths": ["/cgi-bin/new_info.cgi", "/cgi-bin/new_whats.cgi"],
        "rss_paths": [],
        "multi_paths": True,
        # href が末尾に ";" の付いた無効URLのため、onclick の window.open() 側を使う
        "link_from_onclick": True,
    },
    {
        "name": "北星信用金庫",
        "type": "信用金庫",
        "url": "https://www.hokusei-shinkin.co.jp",
        "news_paths": ["/news/", "/topics/", "/info/", "/"],
        "rss_paths": ["/feed/", "/rss/", "/rss.xml"],
    },
    {
        "name": "帯広信用金庫",
        "type": "信用金庫",
        "url": "https://www.shinkin.co.jp/obishin",
        "news_paths": ["/news/", "/topics/", "/info/", "/"],
        "rss_paths": [],
    },
    {
        "name": "釧路信用金庫",
        "type": "信用金庫",
        "url": "https://www.shinkin.co.jp/kushiro",
        "news_paths": ["/_news/history.html"],
        "rss_paths": [],
        # _news/history.html のリンクが親ディレクトリ(kushiro/)基準の相対パスのため
        "link_base": "https://www.shinkin.co.jp/kushiro/",
    },
    {
        "name": "大地みらい信用金庫",
        "type": "信用金庫",
        "url": "https://www.daichimirai.co.jp",
        "news_paths": ["/news/", "/topics/", "/info/", "/newsrelease/", "/"],
        "rss_paths": ["/feed/", "/rss/", "/rss.xml"],
    },
    {
        "name": "北見信用金庫",
        "type": "信用金庫",
        "url": "https://www.shinkin.co.jp/kitami",
        "news_paths": ["/"],
        "rss_paths": [],
    },
    {
        "name": "網走信用金庫",
        "type": "信用金庫",
        "url": "https://www.shinkin.co.jp/abashiri",
        # ニュース枠がトップページ上に4本並んでおり、それぞれ別の一覧ページを持つ
        "news_paths": [
            "/_news/history.html",
            "/_news-1/history.html",
            "/_news-2/history.html",
            "/_news-3/history.html",
        ],
        "rss_paths": [],
        "multi_paths": True,
    },
    {
        "name": "遠軽信用金庫",
        "type": "信用金庫",
        "url": "https://www.shinkin.co.jp/engaru",
        "news_paths": ["/news/", "/topics/", "/info/", "/"],
        "rss_paths": [],
    },

    # ===== 道外の信用金庫 =====
    {
        "name": "京都中央信用金庫",
        "type": "信用金庫",
        "url": "https://www.chushin.co.jp",
        "news_paths": [],
        "rss_paths": [],
        # お知らせ一覧はJavaScriptが年度別JSONを読んで描画するため、JSONを直接取得する
        "json_feed": {
            "paths": ["/common/js/data/news_list_{fy}.json"],
            "date_key": "v_update",    # YYYYMMDD形式
            "title_key": "v_title",
            "url_keys": ["v_pdf", "v_external_link"],
            "detail_path": "/news/{v_id}.html",  # PDFも外部リンクも無い場合の詳細ページ
            "require": {"v_release_flg": "〇"},   # 公開済みのみ
        },
    },
    {
        "name": "城南信用金庫",
        "type": "信用金庫",
        "url": "https://www.jsbank.co.jp",
        "news_paths": ["/news/"],
        "rss_paths": [],
    },
    {
        "name": "京都信用金庫",
        "type": "信用金庫",
        "url": "https://www.kyoto-shinkin.co.jp",
        # 「お知らせ一覧」と「重要なお知らせ一覧」の2枠に分かれている
        "news_paths": ["/_news/history.html", "/_news-3/history.html"],
        "rss_paths": [],
        "multi_paths": True,
    },
    {
        "name": "大阪シティ信用金庫",
        "type": "信用金庫",
        "url": "https://www.osaka-city-shinkin.co.jp",
        # /news/index.html は年度別インデックスのみ。日付付き一覧はトップページにある
        "news_paths": ["/"],
        "rss_paths": [],
    },

    # ===== 信用組合 =====
    {
        "name": "十勝信用組合",
        "type": "信用組合",
        "url": "https://www.tokachishinkumi.com",
        "news_paths": ["/news/", "/topics/", "/info/", "/newsrelease/", "/"],
        "rss_paths": ["/feed/", "/rss/", "/rss.xml"],
    },
]
