#!/usr/bin/env python3
"""theme.py: dựng giao diện blog (khung bài, trang chủ, sitemap, css) từ dữ liệu các bài.

Dùng:  python3 tools/theme.py [<thư_mục_site>] [--offline] [--init]
- Chỉ dùng thư viện chuẩn Python 3.11, không gọi mạng (--offline chỉ để tương thích bộ đăng bài), dưới 5 giây.
- Idempotent: chỉ ghi file khi nội dung đổi. Không đụng chữ bên trong <article>...</article> của bài.
- Mặc định chỉ ghi: index.html, style.css, sitemap.xml, bai-viet/<slug>/index.html (khớp _GH_ALLOWED của bộ đăng bài).
  Cờ --init ghi thêm 404.html (chỉ dùng khi dựng site lần đầu).
- Cấu hình, mẫu HTML và chữ khung nằm ở tools/config.py; CSS nguồn ở tools/theme.css.

Dữ liệu mỗi bài lấy từ bai-viet/<slug>/index.html: <title>, meta description, canonical, <article>, ngày, ảnh featured (og:image).
Thứ tự ưu tiên lấy NGÀY ĐĂNG: (1) dòng <p class="gia">Đăng ngày dd/mm/yyyy</p> trong bài,
(2) datePublished trong JSON-LD của bài, (3) mtime của file.
Thứ tự bài: ngày mới nhất trước; cùng ngày thì bài thêm sau xếp trước (số thứ tự lưu ở tools/state.json,
mất file này thì rơi về thứ tự slug).
"""
import argparse
import hashlib
import html
import json
import re
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import config as C  # noqa: E402

MARKER = "<!-- POSTS:START -->"
DATE_RE = re.compile(r'<p class="gia">\s*Đăng ngày (\d{2})/(\d{2})/(\d{4})\s*</p>')
ART_RE = re.compile(r"<article[^>]*>.*?</article>", re.S)
BASE = C.BASE_URL if C.BASE_URL.endswith("/") else C.BASE_URL + "/"
ALLOWED = re.compile(r"^(index\.html|[A-Za-z0-9_.-]+\.css|sitemap\.xml|bai-viet/[^/]+/index\.html)$")
HP_URL = "https://hungphatlaptop.com/"
AD_TEXT = "Laptop chính hãng đời 2025-2026 cho văn phòng, đồ hoạ và học tập."


def esc(s):
    return html.escape(s, quote=False)


def escq(s):
    return html.escape(s, quote=True)


def fold(s):
    s = unicodedata.normalize("NFD", s.replace("đ", "d").replace("Đ", "D"))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn").lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def render(tpl, **kw):
    for k, v in kw.items():
        tpl = tpl.replace("@" + k + "@", v)
    return tpl


class Site:
    def __init__(self, root: Path, init: bool):
        self.root = root
        self.init = init
        self.posts_dir = root / "bai-viet"
        self.state = HERE / "state.json" if root == HERE.parent else root / "tools" / "state.json"
        self.changed = []
        css_src = (HERE / "theme.css")
        self.css = css_src.read_text(encoding="utf-8") if css_src.exists() else ""
        self.ver = hashlib.sha256(self.css.encode("utf-8")).hexdigest()[:8]

    # ---------- ghi file ----------
    def write(self, rel: str, text: str):
        if not (ALLOWED.match(rel) or (self.init and rel == "404.html")):
            raise SystemExit(f"từ chối ghi file ngoài danh sách cho phép: {rel}")
        p = self.root / rel
        old = p.read_text(encoding="utf-8") if p.exists() else None
        if old != text:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")
            self.changed.append(rel)

    # ---------- đọc bài ----------
    def parse_post(self, f: Path):
        s = f.read_text(encoding="utf-8")
        slug = f.parent.name
        am = ART_RE.search(s)
        if not am:
            return None
        t = re.search(r"<title>(.*?)</title>", s, re.S)
        h = re.search(r"<h1[^>]*>(.*?)</h1>", am.group(0), re.S)
        title = html.unescape((t or h).group(1)).strip() if (t or h) else slug
        d = re.search(r'<meta name="description" content="([^"]*)">', s)
        desc = html.unescape(d.group(1)).strip() if d else ""
        g = DATE_RE.search(s)
        iso = None
        if g:
            iso = f"{g.group(3)}-{g.group(2)}-{g.group(1)}"
        if not iso:
            for ld in re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S):
                try:
                    dp = json.loads(ld).get("datePublished", "")
                except Exception:
                    dp = ""
                if re.match(r"\d{4}-\d{2}-\d{2}", dp or ""):
                    iso = dp[:10]
                    break
        if not iso:
            iso = datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d")
        im = re.search(r'<meta property="og:image" content="([^"]+)">', s)
        image = html.unescape(im.group(1)) if im else ""
        iw = re.search(r'<meta property="og:image:width" content="(\d+)">', s)
        ih = re.search(r'<meta property="og:image:height" content="(\d+)">', s)
        text = html.unescape(re.sub(r"<[^>]+>", " ", am.group(0)))
        words = len(text.split())
        p = {
            "slug": slug, "file": f, "title": title, "desc": desc, "iso": iso, "article": am.group(0),
            "image_abs": image, "iw": iw.group(1) if iw else "1200", "ih": ih.group(1) if ih else "630",
            "read": max(1, round(words / 220)),
        }
        p["vn"] = f"{iso[8:10]}/{iso[5:7]}/{iso[:4]}"
        key, label = classify(slug, title)
        p["cat"], p["cat_label"] = key, label
        p["ph"] = int(hashlib.md5(slug.encode()).hexdigest(), 16) % 3
        return p

    # ---------- khối chung ----------
    def img_src(self, p, R):
        a = p["image_abs"]
        if not a:
            return ""
        return R + a[len(BASE):] if a.startswith(BASE) else a

    def media(self, p, R, eager=False):
        src = self.img_src(p, R)
        if src:
            lazy = "" if eager else ' loading="lazy"'
            return (f'<img src="{escq(src)}" alt="" width="{p["iw"]}" height="{p["ih"]}"{lazy}'
                    + (' fetchpriority="high"' if eager else "") + ">")
        ch = esc(p["title"].strip()[:1].upper())
        return (f'<span class="ph v{p["ph"]} k-{p["cat"]}" aria-hidden="true">'
                f'<b class="ph-cat">{esc(p["cat_label"])}</b><i class="ph-ch">{ch}</i></span>')

    def card(self, kind, p, R, n_total):
        tpl = C.CARDS[kind]
        href = f"{R}bai-viet/{p['slug']}/" if R != "../" else f"../{p['slug']}/"
        return render(
            tpl, HREF=href, TITLE=esc(p["title"]), DESC=esc(p["desc"]), DATE=p["vn"], ISO=p["iso"],
            DAY=p["iso"][8:10], MON=p["iso"][5:7], YEAR=p["iso"][:4],
            CAT=esc(p["cat_label"]), CATKEY=p["cat"], READ=f'{p["read"]} phút đọc',
            ORD=f'{p["ord"]:02d}', MEDIA=self.media(p, R, eager=(kind == "hero")),
        )

    def nav(self, R, posts_cats):
        items = [f'<a href="{R or "./"}">Trang chủ</a>']
        for key, label in posts_cats:
            items.append(f'<a href="{R}#chu-de-{key}">{esc(label)}</a>')
        items.append(f'<a href="{R}#ve-blog">Về blog</a>')
        return "".join(items)

    def frame(self, R, cats):
        nav = self.nav(R, cats)
        kw = dict(R=R, HOME=R or "./", NAME=esc(C.SITE_NAME), PEN=esc(C.PEN), NAV=nav, TAGLINE=esc(C.TAGLINE), YEAR="2026",
                  MARK=esc(C.MARK))
        return render(C.HEADER, **kw), render(C.FOOTER, **kw)

    def w_about(self, R):
        return render(
            C.ABOUT, R=R, PEN=esc(C.PEN), AV=esc(C.AVATAR), ABOUT=C.ABOUT_P)

    def w_cats(self, R, cats, counts):
        lis = []
        for key, label in cats:
            n = f"<em>{counts[key]}</em>" if counts is not None else ""
            lis.append(f'<li><a href="{R}#chu-de-{key}"><span>{esc(label)}</span>{n}</a></li>')
        return f'<section class="w w-cats"><h2 class="w-t">Chủ đề</h2><ul>{"".join(lis)}</ul></section>'

    def ad(self, R):
        return ('<aside class="ad-hp" data-ad="hungphat">'
                '<span class="ad-lb">Quảng cáo</span>'
                f'<img src="{R}assets/hp-wide.png" width="195" height="64" alt="Hưng Phát Laptop" loading="lazy">'
                f'<p>{AD_TEXT}</p>'
                f'<a class="ad-btn" href="{HP_URL}" target="_blank" rel="sponsored noopener">Xem máy</a>'
                '</aside>')

    def head(self, title, desc, canon, R, seo):
        return (
            '<!doctype html>\n<html lang="vi">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
            f'<title>{esc(title)}</title>\n'
            f'<meta name="description" content="{escq(desc)}">\n'
            f'<link rel="canonical" href="{canon}">\n'
            '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
            '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
            f'<link href="{C.FONTS_URL}" rel="stylesheet">\n'
            f'<link rel="stylesheet" href="{R}style.css?v={self.ver}">\n'
            f'{seo}\n</head>\n')

    # ---------- SEO ----------
    def seo_post(self, p):
        url = f"{BASE}bai-viet/{p['slug']}/"
        ld = {
            "@context": "https://schema.org", "@type": "BlogPosting", "headline": p["title"],
            "description": p["desc"], "datePublished": p["iso"], "dateModified": p["iso"], "inLanguage": "vi",
            "mainEntityOfPage": url,
            "author": {"@type": "Organization", "name": C.SITE_NAME},
            "publisher": {"@type": "Organization", "name": C.SITE_NAME},
        }
        img = p["image_abs"]
        if img:
            ld["image"] = img
        ld_s = json.dumps(ld, ensure_ascii=False).replace("</", "<\\/")
        lines = [
            "<!--seo-->", '<meta property="og:type" content="article">',
            f'<meta property="og:title" content="{escq(p["title"])}">',
            f'<meta property="og:description" content="{escq(p["desc"])}">',
            f'<meta property="og:url" content="{url}">', '<meta property="og:locale" content="vi_VN">',
            f'<meta property="og:site_name" content="{escq(C.SITE_NAME)}">',
        ]
        if img:
            lines += [f'<meta property="og:image" content="{escq(img)}">',
                      f'<meta property="og:image:width" content="{p["iw"]}">',
                      f'<meta property="og:image:height" content="{p["ih"]}">',
                      '<meta name="twitter:card" content="summary_large_image">',
                      f'<meta name="twitter:image" content="{escq(img)}">']
        else:
            lines.append('<meta name="twitter:card" content="summary">')
        lines += [f'<script type="application/ld+json">{ld_s}</script>', "<!--/seo-->"]
        return "\n".join(lines)

    def seo_index(self):
        return (
            '<meta property="og:type" content="website">\n'
            f'<meta property="og:title" content="{escq(C.INDEX_OG_TITLE)}">\n'
            f'<meta property="og:description" content="{escq(C.INDEX_OG_DESC)}">\n'
            f'<meta property="og:url" content="{BASE}">\n<meta name="twitter:card" content="summary">')

    # ---------- bài ----------
    def related(self, i, posts):
        me = posts[i]
        others = [q for q in posts if q is not me]
        same = [q for q in others if q["cat"] == me["cat"]]
        pick = (same + [q for q in others if q not in same])[:3]
        if not pick:
            return "<!--related-->\n<!--/related-->"
        lis = "\n".join(f'<li><a href="../{q["slug"]}/">{esc(q["title"])}</a></li>' for q in pick)
        return ('<!--related-->\n<aside class="lq">\n<h2 class="lq-t">Bài cùng chủ đề</h2>\n'
                f"<ul>\n{lis}\n</ul>\n</aside>\n<!--/related-->")

    def build_post(self, i, posts, cats):
        p = posts[i]
        R = "../../"
        header, footer = self.frame(R, cats)
        canon = f'{BASE}bai-viet/{p["slug"]}/'
        body = render(
            C.POST, R=R, HEADER=header, FOOTER=footer, ARTICLE=p["article"], RELATED=self.related(i, posts),
            ABOUT=self.w_about(R), CATS=self.w_cats(R, cats, None), CATKEY=p["cat"], CATLABEL=esc(p["cat_label"]))
        return self.head(p["title"], p["desc"], canon, R, self.seo_post(p)) + body

    # ---------- trang chủ ----------
    def build_index(self, posts, cats, counts):
        R = ""
        header, footer = self.frame(R, cats)
        hero, rest = posts[0], posts[1:]
        latest = rest[: C.LATEST_N]
        cards = "\n".join(self.card("latest", p, R, len(posts)) for p in latest)
        topics = []
        for key, label in cats:
            ps = [p for p in posts if p["cat"] == key]
            lis = "\n".join(
                f'<li><a href="bai-viet/{p["slug"]}/">{esc(p["title"])}</a><time datetime="{p["iso"]}">{p["vn"]}</time></li>'
                for p in ps)
            topics.append(f'<section class="tp" id="chu-de-{key}"><h3>{esc(label)}<span>{len(ps)} bài</span></h3>'
                          f'<ul>\n{lis}\n</ul></section>')
        sidebar = self.w_about(R) + self.w_cats(R, cats, counts) + self.ad(R)
        body = render(
            C.INDEX, HEADER=header, FOOTER=footer, H1=esc(C.INDEX_H1), STRAP=esc(C.STRAP),
            HERO=self.card("hero", hero, R, len(posts)), LATEST=f"{MARKER}\n{cards}",
            TOPICS="\n".join(topics), SIDEBAR=sidebar, ABOUT_HOME=C.ABOUT_HOME, R=R,
            TOTAL=str(len(posts)))
        return self.head(C.INDEX_TITLE, C.INDEX_DESC, BASE, R, self.seo_index()) + body

    def build_404(self, cats):
        R = "/"
        header, footer = self.frame(R, cats)
        body = render(C.NOTFOUND, HEADER=header, FOOTER=footer, R=R)
        return (self.head(f"Không tìm thấy trang - {C.SITE_NAME}", "", "", R, "").replace(
            '<meta name="description" content="">\n<link rel="canonical" href="">\n',
            '<meta name="robots" content="noindex">\n') + body)

    # ---------- chạy ----------
    def load_state(self):
        try:
            st = json.loads(self.state.read_text(encoding="utf-8"))
            if isinstance(st.get("seq"), dict):
                return st
        except Exception:
            pass
        return {"seq": {}, "next": 1}

    def run(self):
        files = sorted(self.posts_dir.glob("*/index.html"))
        posts = [q for q in (self.parse_post(f) for f in files) if q]
        if not posts:
            print("theme.py: chưa có bài nào")
            return 0
        st = self.load_state()
        seq, nxt = st["seq"], int(st.get("next", 1))
        for p in sorted(posts, key=lambda x: (x["iso"], x["slug"])):
            if p["slug"] not in seq:
                seq[p["slug"]] = nxt
                nxt += 1
        slugs = {p["slug"] for p in posts}
        st = {"seq": {k: v for k, v in seq.items() if k in slugs}, "next": nxt}
        asc = sorted(posts, key=lambda p: (p["iso"], st["seq"][p["slug"]]))
        for n, p in enumerate(asc, 1):
            p["ord"] = n
        posts = list(reversed(asc))
        counts = {key: 0 for key, _ in C.CATS}
        for p in posts:
            counts[p["cat"]] += 1
        cats = [(k, lbl) for k, lbl in C.CATS if counts[k]]

        for i, p in enumerate(posts):
            self.write(f"bai-viet/{p['slug']}/index.html", self.build_post(i, posts, cats))
        self.write("index.html", self.build_index(posts, cats, counts))
        if self.init:
            self.write("404.html", self.build_404(cats))
        self.write("style.css", self.css)
        last = max(p["iso"] for p in posts)
        rows = [f"<url><loc>{BASE}</loc><lastmod>{last}</lastmod></url>"]
        rows += [f"<url><loc>{BASE}bai-viet/{p['slug']}/</loc><lastmod>{p['iso']}</lastmod></url>" for p in posts]
        self.write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n'
                   '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(rows) + "\n</urlset>\n")
        try:
            new = json.dumps(st, ensure_ascii=False, indent=1) + "\n"
            if not self.state.exists() or self.state.read_text(encoding="utf-8") != new:
                self.state.write_text(new, encoding="utf-8")
        except OSError:
            pass
        print(f"theme.py: {len(posts)} bài, đã ghi {len(self.changed)} file")
        return 0


def classify(slug, title):
    hay = "-" + slug + "-" + fold(title) + "-"
    for key, label, words in C.CAT_RULES:
        if any(f"-{w}-" in hay for w in words):
            return key, label
    return C.CAT_DEFAULT


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("site_dir", nargs="?")
    ap.add_argument("--offline", action="store_true", help="giữ để tương thích; script không gọi mạng")
    ap.add_argument("--init", action="store_true", help="ghi thêm 404.html (dựng site lần đầu)")
    a = ap.parse_args(argv)
    root = Path(a.site_dir).resolve() if a.site_dir else HERE.parent
    return Site(root, a.init).run()


if __name__ == "__main__":
    sys.exit(main())
