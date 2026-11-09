#!/usr/bin/env python3
"""check_theme.py: kiểm giao diện blog do tools/theme.py dựng. Chỉ thư viện chuẩn Python 3.11.
Dùng: python3 tools/check_theme.py [<thư_mục_site>]
Cần bản gốc tools/_goc/<slug>.html (trang bài thô trước khi qua theme.py, do src/gen.py ghi).
Các kiểm: 1 idempotent, 2 <article> giữ nguyên byte, 3 SEO giữ nguyên, 4 trang chủ + marker, 5 chữ cấm + link ra ngoài,
6 mô phỏng bài mới (không ảnh), 7 file CSS/ảnh tồn tại, 8 khung tĩnh (viewport, ảnh, phông), 9 banner Hưng Phát (riêng).
Dòng cuối: TONG KET: pass X / fail Y"""
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else HERE.parent
TOOLS = ROOT / "tools"
GOC = TOOLS / "_goc"
LOGO_SRC = Path("/home/stevenlam/work/blog-redesign-1011/hp-wide.png")
ART_RE = re.compile(r"<article[^>]*>.*?</article>", re.S)
AD_RE = re.compile(r'<aside class="ad-hp"[^>]*>.*?</aside>', re.S)
MARKER = "<!-- POSTS:START -->"
HERO_RE = re.compile(r'<section class="hero-wrap"[^>]*>.*?</section>', re.S)
PRICE_RE = re.compile(r"\d[\d.,]{3,}\s*(đ|₫|vnđ|vnd)\b|triệu đồng|\d+\s*triệu", re.I)
EMOJI_RE = re.compile("[\U0001F300-\U0001FAFF☀-➿⭐⬆️]")
BANNED = ["chiếc máy này", "hãy cùng", "trong thế giới", "không chỉ", "mà còn", "đáng kinh ngạc", "hoàn hảo", "tuyệt vời",
          "đột phá", "mượt mà", "mọi nhu cầu", "xem thêm", "tham khảo thêm", "trong bài viết này", "đóng vai trò quan trọng",
          "hành trình", "tóm lại,", "nhìn chung,", "kết luận:", "—", "{{", "hưng phát", "hungphat", "phát lâm", "khám phá ngay"]
AD_SENT = "Laptop chính hãng đời 2025-2026 cho văn phòng, đồ hoạ và học tập."

res = []


def ok(cond, msg):
    res.append(bool(cond))
    print(("[ok]  " if cond else "[LOI] ") + msg)
    return bool(cond)


def read(p):
    return Path(p).read_text(encoding="utf-8")


def cfg():
    ns = {}
    exec(read(TOOLS / "config.py"), ns)
    return ns


C = cfg()
BASE = C["BASE_URL"]
BASE_HOST = urlparse(BASE).netloc


def run_theme():
    r = subprocess.run([sys.executable, "-I", str(TOOLS / "theme.py"), str(ROOT), "--init"], capture_output=True, text=True)
    return r.returncode == 0, (r.stdout + r.stderr).strip()


def snapshot():
    out = {}
    for f in sorted(ROOT.rglob("*")):
        if not f.is_file():
            continue
        rel = f.relative_to(ROOT).as_posix()
        if rel.startswith(("tools/_goc/", ".git/")) or "__pycache__" in rel or rel == "tools/state.json":
            continue
        out[rel] = hashlib.sha256(f.read_bytes()).hexdigest()
    return out


def pages():
    r = {"index.html": read(ROOT / "index.html")}
    if (ROOT / "404.html").exists():
        r["404.html"] = read(ROOT / "404.html")
    for f in sorted((ROOT / "bai-viet").glob("*/index.html")):
        r[f.relative_to(ROOT).as_posix()] = read(f)
    return r


def ext_links(s):
    out = []
    for m in re.finditer(r'<a\b[^>]*\bhref="(https?://[^"]+)"', s):
        if urlparse(m.group(1)).netloc != BASE_HOST:
            out.append(m.group(1))
    return out


def meta(s):
    t = re.search(r"<title>(.*?)</title>", s, re.S)
    d = re.search(r'<meta name="description" content="([^"]*)">', s)
    c = re.search(r'<link rel="canonical" href="([^"]*)">', s)
    return (t.group(1) if t else None, d.group(1) if d else None, c.group(1) if c else None)


def main():
    base_files = sorted(GOC.glob("*.html"))
    if not base_files:
        print("thiếu tools/_goc/ (bản gốc để so)")
        print("TONG KET: pass 0 / fail 1")
        return 1

    # 1. idempotent
    a_ok, _ = run_theme()
    h1 = snapshot()
    b_ok, _ = run_theme()
    h2 = snapshot()
    diff = [k for k in set(h1) | set(h2) if h1.get(k) != h2.get(k)]
    ok(a_ok and b_ok and not diff, f"1 chạy theme.py 2 lần, hash {len(h1)} file khớp" + (f" (lệch: {diff[:3]})" if diff else ""))

    # 2. article giữ nguyên
    bad = []
    for f in base_files:
        slug = f.stem
        cur = ROOT / "bai-viet" / slug / "index.html"
        if not cur.exists():
            bad.append(slug + " (mất)")
            continue
        if ART_RE.search(read(f)).group(0) != ART_RE.search(read(cur)).group(0):
            bad.append(slug)
    ok(not bad, f"2 <article> giữ nguyên byte so với bản gốc ({len(base_files)} bài)" + (f" lệch: {bad}" if bad else ""))

    # 3. SEO giữ nguyên
    bad = []
    for f in base_files:
        slug = f.stem
        cur = read(ROOT / "bai-viet" / slug / "index.html")
        if meta(read(f)) != meta(cur):
            bad.append(slug + ":meta")
        ld = re.findall(r'<script type="application/ld\+json">(.*?)</script>', cur, re.S)
        try:
            j = json.loads(ld[0])
            g = re.search(r'<p class="gia">Đăng ngày (\d\d)/(\d\d)/(\d{4})</p>', cur)
            iso = f"{g.group(3)}-{g.group(2)}-{g.group(1)}"
            import html as _h
            if j.get("headline") != _h.unescape(meta(cur)[0]) or j.get("datePublished") != iso or len(ld) != 1:
                bad.append(slug + ":ld")
        except Exception:
            bad.append(slug + ":ld-hỏng")
        if f'<meta property="og:url" content="{BASE}bai-viet/{slug}/">' not in cur:
            bad.append(slug + ":og")
    rb = read(ROOT / "robots.txt")
    ok(not bad and f"Sitemap: {BASE}sitemap.xml" in rb,
       "3 title, description, canonical, JSON-LD, og:url của bài khớp bản gốc; robots.txt còn dòng Sitemap" + (f" lệch: {bad}" if bad else ""))

    # 4. trang chủ
    pg = pages()
    idx = pg["index.html"]
    slugs = [p.stem for p in base_files]
    miss = [s for s in slugs if f'href="bai-viet/{s}/"' not in idx]
    first_card = re.search(r'<a [^>]*href="(bai-viet/[^"]+)"', idx)
    pos = idx.find(MARKER)
    ok(not miss and idx.count(MARKER) == 1, f"4 trang chủ trỏ tới {len(slugs) - len(miss)}/{len(slugs)} bài, đúng 1 marker POSTS:START" + (f" thiếu {miss}" if miss else ""))
    ok(pos > idx.find('id="bai-moi"') > 0 and first_card is not None and HERO_RE.search(idx) is not None,
       "4b marker nằm trong mục Bài mới nhất, trang chủ có hero")
    sm = read(ROOT / "sitemap.xml")
    ok(all(f"{BASE}bai-viet/{s}/" in sm for s in slugs) and f"<loc>{BASE}</loc>" in sm, "4c sitemap.xml đủ trang chủ và các bài")

    # 5. chữ cấm + link ra ngoài
    bad_words, bad_links = [], []
    for rel, s in pg.items():
        body = AD_RE.sub("", s)
        low = body.lower()
        for w in BANNED:
            if w in low:
                bad_words.append(f"{rel}:{w}")
        if PRICE_RE.search(body):
            bad_words.append(f"{rel}:giá")
        if EMOJI_RE.search(body):
            bad_words.append(f"{rel}:emoji")
        no_art = ART_RE.sub("", body)
        if ext_links(no_art):
            bad_links.append(f"{rel}: link ngoài ở khung {ext_links(no_art)[:2]}")
        if rel.startswith("bai-viet/"):
            slug = rel.split("/")[1]
            if ext_links(ART_RE.search(body).group(0)) != ext_links(read(GOC / f"{slug}.html")) and (GOC / f"{slug}.html").exists():
                bad_links.append(f"{rel}: số link ngoài đổi")
    ok(not bad_words, "5 không có chữ cấm, giá, emoji, '—' trong trang (đã bỏ khối banner)" + (f": {bad_words[:4]}" if bad_words else ""))
    n_before = sum(len(ext_links(read(f))) for f in base_files)
    n_after = sum(len(ext_links(ART_RE.sub("", AD_RE.sub("", s))) + ext_links(ART_RE.search(s).group(0))) for rel, s in pg.items() if rel.startswith("bai-viet/") and ART_RE.search(s))
    ok(not bad_links and n_before == n_after, f"5b link ra ngoài trước/sau: {n_before}/{n_after}, khung và sidebar không thêm link ngoài" + (f": {bad_links[:3]}" if bad_links else ""))

    # 6. mô phỏng bài mới không ảnh
    keep = {"state": (TOOLS / "state.json").read_bytes() if (TOOLS / "state.json").exists() else None}
    pre = snapshot()
    src_raw = read(base_files[0])
    test_dir = ROOT / "bai-viet" / "zz-test-bai-moi"
    for label, date in (("khác ngày", "10/11/2026"), ("cùng ngày", "09/11/2026")):
        test_dir.mkdir(exist_ok=True)
        s = src_raw
        old_slug = base_files[0].stem
        s = s.replace(f"bai-viet/{old_slug}/", "bai-viet/zz-test-bai-moi/")
        s = re.sub(r"<title>.*?</title>", "<title>Bài thử nghiệm mới - kiểm giao diện</title>", s, flags=re.S)
        s = re.sub(r"(<article[^>]*>\s*<h1[^>]*>).*?(</h1>)", r"\1Bài thử nghiệm mới - kiểm giao diện\2", s, count=1, flags=re.S)
        s = re.sub(r'<p class="gia">Đăng ngày [\d/]+</p>', f'<p class="gia">Đăng ngày {date}</p>', s)
        (test_dir / "index.html").write_text(s, encoding="utf-8")
        run_theme()
        idx = read(ROOT / "index.html")
        hero = HERO_RE.search(idx)
        hero_s = hero.group(0) if hero else ""
        good = ("zz-test-bai-moi" in hero_s and 'class="ph ' in hero_s and idx.count(MARKER) == 1
                and "<img" not in hero_s and "zz-test-bai-moi" in read(ROOT / "sitemap.xml"))
        ok(good, f"6 bài mới ({label}) không ảnh: là hero, có khung giữ chỗ, 1 marker, có trong sitemap")
        shutil.rmtree(test_dir)
    run_theme()
    if keep["state"] is not None:
        (TOOLS / "state.json").write_bytes(keep["state"])
    post = snapshot()
    ok(post == pre and not test_dir.exists(), "6b xoá bài thử rồi chạy lại theme.py: site về đúng trạng thái trước")

    # 7. file được tham chiếu tồn tại
    pg = pages()
    broken = []
    for rel, s in pg.items():
        here = (ROOT / rel).parent
        for m in re.finditer(r'(?:href|src)="([^"]+)"', s):
            u = m.group(1)
            if re.match(r"(https?:|mailto:|#|data:)", u):
                continue
            path = urlparse(u).path
            if not path:
                continue
            t = (ROOT / path.lstrip("/")) if path.startswith("/") else (here / path)
            t = t.resolve()
            if t.is_dir():
                t = t / "index.html"
            if not t.exists():
                broken.append(f"{rel} -> {u}")
    ok(not broken, f"7 mọi href/src nội bộ trỏ tới file có thật ({len(pg)} trang)" + (f": {broken[:4]}" if broken else ""))

    # 8. khung tĩnh
    css = read(ROOT / "style.css")
    bad = []
    fonts = C["FONTS_URL"]
    if fonts.count("family=") > 2 or "display=swap" not in fonts:
        bad.append("phông")
    if ":focus-visible" not in css or "@media" not in css or "overflow-x:auto" not in css.replace(" ", ""):
        bad.append("css")
    for rel, s in pg.items():
        if 'name="viewport"' not in s or 'class="skip"' not in s or '<html lang="vi">' not in s:
            bad.append(rel + ":head")
        for m in re.finditer(r"<img\b[^>]*>", AD_RE.sub("", s)):
            if "width=" not in m.group(0) or "height=" not in m.group(0):
                bad.append(rel + ":img")
        if rel == "index.html":
            hero = HERO_RE.search(s)
            if hero and 'loading="lazy"' in hero.group(0):
                bad.append("hero lazy")
        if "<form" in s or "<input" in s:
            bad.append(rel + ":form")
    ok(not bad, "8 khung: viewport, skip link, lang, phông ≤2 họ có display=swap, focus-visible, bảng cuộn ngang, ảnh có width/height, không form" + (f": {bad[:4]}" if bad else ""))

    # 9. banner Hưng Phát
    idx = pg["index.html"]
    ads = AD_RE.findall(idx)
    bad = []
    if len(ads) != 1:
        bad.append(f"{len(ads)} banner trên trang chủ")
    else:
        a = ads[0]
        links = re.findall(r'<a\b[^>]*>', a)
        if len(links) != 1 or 'href="https://hungphatlaptop.com/"' not in links[0] or 'target="_blank"' not in links[0] \
                or 'rel="sponsored noopener"' not in links[0]:
            bad.append("link banner")
        if 'data-ad="hungphat"' not in a or "Quảng cáo" not in a or AD_SENT not in a or ">Xem máy<" not in a:
            bad.append("chữ banner")
        if not re.search(r'<img src="assets/hp-wide\.png" width="195" height="64" alt="Hưng Phát Laptop"', a):
            bad.append("ảnh banner")
    total = sum(s.count("hungphatlaptop.com") for s in pg.values())
    if total != 1:
        bad.append(f"{total} link hungphatlaptop.com toàn site")
    logo = ROOT / "assets" / "hp-wide.png"
    if not logo.exists() or not LOGO_SRC.exists() or hashlib.sha256(logo.read_bytes()).digest() != hashlib.sha256(LOGO_SRC.read_bytes()).digest():
        bad.append("sha256 logo")
    for rel, s in pg.items():
        if rel != "index.html" and ("ad-hp" in s or "hungphatlaptop" in s.lower() or "Quảng cáo" in s):
            bad.append(rel + ": có banner")
    ok(not bad, "9 banner: 1 banner trang chủ, 1 link đúng rel, logo trùng sha256 nguồn, bài/404 không có banner" + (f": {bad}" if bad else ""))

    p = sum(res)
    print(f"TONG KET: pass {p} / fail {len(res) - p}")
    return 0 if p == len(res) else 1


if __name__ == "__main__":
    sys.exit(main())
