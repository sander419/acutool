# -*- coding: utf-8 -*-
"""Собирает автономную версию презентации одним файлом.

Шрифты Google Fonts и картинки вшиваются как data: URI, поэтому
получившийся файл открывается двойным кликом без интернета —
для показа партнёрам с ноутбука в цеху.

Запуск:  python build-offline.py
Итог:    dist/АкуТул-презентация.html
"""
import base64, io, os, re, urllib.request

SRC, OUT_DIR = "index.html", "dist"
OUT = os.path.join(OUT_DIR, "АкуТул-презентация.html")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
KEEP_SUBSETS = ("cyrillic", "latin")


def get(url, headers=None):
    req = urllib.request.Request(url, headers=headers or UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def fonts_css(href):
    """Скачивает CSS Google Fonts и подменяет ссылки на woff2 их base64."""
    css = get(href).decode("utf-8")
    blocks, subset = [], None
    for line in css.splitlines():
        m = re.match(r"\s*/\*\s*([a-z-]+)\s*\*/\s*$", line)
        if m:
            subset = m.group(1)
        blocks.append((subset, line))

    out, cache = [], {}
    keep = True
    for subset, line in blocks:
        if line.strip().startswith("@font-face"):
            keep = subset in KEEP_SUBSETS
        if not keep:
            continue
        m = re.search(r"url\((https://[^)]+\.woff2)\)", line)
        if m:
            u = m.group(1)
            if u not in cache:
                cache[u] = base64.b64encode(get(u)).decode()
                print("   woff2", subset, len(cache[u]) // 1024, "KB b64")
            line = line.replace(u, "data:font/woff2;base64," + cache[u])
        out.append(line)
    return "\n".join(out)


def data_uri(path):
    mime = "image/jpeg" if path.endswith((".jpg", ".jpeg")) else \
           "image/svg+xml" if path.endswith(".svg") else "image/png"
    return "data:%s;base64,%s" % (mime, base64.b64encode(open(path, "rb").read()).decode())


html = io.open(SRC, encoding="utf-8").read()

# 1. шрифты
href = re.search(r'<link rel="stylesheet" href="(https://fonts\.googleapis\.com[^"]+)">', html).group(1)
print("-> шрифты:", href)
css = fonts_css(href)
html = re.sub(r'<link rel="preconnect"[^>]*>\s*', "", html)
html = re.sub(r'<link rel="preload" as="image"[^>]*>\s*', "", html)
html = html.replace('<link rel="stylesheet" href="%s">' % href,
                    "<style>\n%s\n</style>" % css)

# 2. картинки, иконки
for name in ("hero-sensor.jpg", "chip-macro.jpg", "install-magnet.jpg",
             "mvp-board.jpg", "favicon.svg"):
    p = os.path.join("assets", name)
    html = html.replace('"assets/%s"' % name, '"%s"' % data_uri(p))
    print("-> вшито", name, os.path.getsize(p) // 1024, "KB")

# офлайн-копии эти ссылки не нужны: превью и ico тянутся только из сети
html = re.sub(r'\s*<link rel="alternate icon"[^>]*>', "", html)
html = re.sub(r'\s*<link rel="apple-touch-icon"[^>]*>', "", html)
html = re.sub(r'\s*<meta (?:property="og:image[^"]*"|name="twitter:image")[^>]*>', "", html)

os.makedirs(OUT_DIR, exist_ok=True)
io.open(OUT, "w", encoding="utf-8", newline="").write(html)
print("\nГотово:", OUT, os.path.getsize(OUT) // 1024, "KB")
