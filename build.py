#!/usr/bin/env python3
"""Convertit les fiches Markdown du vault Obsidian HSK2 en pages HTML."""
import re
import unicodedata
from pathlib import Path

import markdown

SRC = Path("/home/alexis/Documents/Obsidian/LearnChinese/HSK2")
OUT = Path("/home/alexis/Documents/learnChinese/HSK2")

PAGE = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<header class="site">
  <h1>{header}</h1>
  <p>{subtitle}</p>
</header>
<nav class="top"><a href="index.html">&#8962; Accueil</a></nav>
<main>
{body}
{pager}
</main>
<footer class="site">HSK 2 — Standard Course · fiches personnelles</footer>
</body>
</html>
"""


def slugify(name: str) -> str:
    m = re.search(r"Leçon (\d+)", name)
    if m:
        return f"lecon-{int(m.group(1)):02d}"
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_name).strip("-").lower()
    return slug or "page"


def parse_meta(name: str, text: str):
    """Retourne (numéro de leçon ou None, titre chinois, sous-titre français)."""
    m = re.match(r"HSK 2 — Leçon (\d+)\s+(.*)", name)
    num, zh = (int(m.group(1)), m.group(2).strip()) if m else (None, name)
    sub = ""
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("_") and line.endswith("_"):
            sub = line.strip("_").strip().strip('"').strip("«»").strip()
            break
    return num, zh, sub


def main():
    files = sorted(SRC.glob("*.md"), key=lambda p: (0, int(m.group(1))) if (m := re.search(r"Leçon (\d+)", p.stem)) else (1, 0))
    pages = []
    for f in files:
        text = f.read_text(encoding="utf-8")
        num, zh, sub = parse_meta(f.stem, text)
        pages.append({"src": text, "num": num, "zh": zh, "sub": sub, "slug": slugify(f.stem)})

    md = markdown.Markdown(extensions=["tables", "sane_lists"])
    for i, p in enumerate(pages):
        md.reset()
        body = md.convert(p["src"])
        prev_link = f'<a href="{pages[i-1]["slug"]}.html">&larr; {pages[i-1]["zh"]}</a>' if i > 0 else '<span class="spacer"></span>'
        next_link = f'<a href="{pages[i+1]["slug"]}.html">{pages[i+1]["zh"]} &rarr;</a>' if i + 1 < len(pages) else '<span class="spacer"></span>'
        pager = f'<nav class="pager">{prev_link}{next_link}</nav>'
        header = f"Leçon {p['num']} — {p['zh']}" if p["num"] else p["zh"]
        html = PAGE.format(title=header, header=header, subtitle=p["sub"], body=body, pager=pager)
        (OUT / f"{p['slug']}.html").write_text(html, encoding="utf-8")
        print(f"OK  {p['slug']}.html")

    cards = []
    for p in pages:
        label = f"Leçon {p['num']}" if p["num"] else "Note de grammaire"
        cards.append(
            f'<li><a href="{p["slug"]}.html"><span class="num">{label}</span>'
            f'<span class="zh">{p["zh"]}</span><span class="fr">{p["sub"]}</span></a></li>'
        )
    index_body = '<h1>Sommaire des leçons</h1>\n<ul class="lessons">\n' + "\n".join(cards) + "\n</ul>"
    html = PAGE.format(title="HSK 2 — Fiches de cours", header="HSK 2 — Fiches de cours",
                       subtitle="Standard Course · vocabulaire, grammaire, dialogues",
                       body=index_body, pager="")
    (OUT / "index.html").write_text(html, encoding="utf-8")
    print("OK  index.html")


if __name__ == "__main__":
    main()
