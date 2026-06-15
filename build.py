#!/usr/bin/env python3
"""Convertit les fiches Markdown du vault Obsidian HSK2 en pages HTML bilingues (FR/EN).

Le français vient du vault Obsidian (SRC). L'anglais vient des fiches miroir
dans EN_SRC (dossier `en/` du repo). Chaque page contient les deux langues ;
un bouton bascule l'affichage (mémorisé via localStorage)."""
import re
import unicodedata
from pathlib import Path

import markdown

SRC = Path("/home/alexis/Documents/Obsidian/LearnChinese/HSK2")
OUT = Path("/home/alexis/Documents/learnChinese/HSK2")
EN_SRC = OUT / "en"

# Titres anglais pour les pages qui ne sont pas des leçons numérotées.
EN_TITLES = {
    "les-demonstratifs": "The demonstratives — 这 那 哪",
}

PAGE = """<!DOCTYPE html>
<html lang="fr" data-title-fr="{title_fr}" data-title-en="{title_en}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title_fr}</title>
<link rel="stylesheet" href="style.css">
<script>try{{if(localStorage.getItem('hsk2-lang')==='en')document.documentElement.classList.add('en');}}catch(e){{}}</script>
</head>
<body>
<header class="site">
  <h1><span class="lang-fr">{header_fr}</span><span class="lang-en">{header_en}</span></h1>
  <p><span class="lang-fr">{subtitle_fr}</span><span class="lang-en">{subtitle_en}</span></p>
</header>
<nav class="top">
  <a href="index.html"><span class="lang-fr">&#8962; Accueil</span><span class="lang-en">&#8962; Home</span></a>
  <button id="lang-toggle" type="button" aria-label="Changer de langue / Switch language"><span class="lang-fr">English</span><span class="lang-en">Français</span></button>
</nav>
<main>
<div class="lang-fr">
{body_fr}
</div>
<div class="lang-en">
{body_en}
</div>
{pager}
</main>
<footer class="site"><span class="lang-fr">HSK 2 — Standard Course · fiches personnelles</span><span class="lang-en">HSK 2 — Standard Course · personal notes</span></footer>
<script>
(function(){{
  var KEY='hsk2-lang', root=document.documentElement;
  function apply(en){{
    root.classList.toggle('en', en);
    root.lang = en ? 'en' : 'fr';
    var t = root.getAttribute(en ? 'data-title-en' : 'data-title-fr');
    if (t) document.title = t;
  }}
  apply((function(){{try{{return localStorage.getItem(KEY)==='en';}}catch(e){{return false;}}}})());
  document.addEventListener('click', function(e){{
    if(!e.target.closest('#lang-toggle')) return;
    var en = !root.classList.contains('en');
    try{{localStorage.setItem(KEY, en ? 'en' : 'fr');}}catch(e){{}}
    apply(en);
  }});
}})();
</script>
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
    sub = first_italic(text)
    return num, zh, sub


def first_italic(text: str) -> str:
    """Extrait la première ligne en italique (_..._) d'un texte markdown."""
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("_") and line.endswith("_") and len(line) > 1:
            return line.strip("_").strip().strip('"').strip("«»").strip()
    return ""


def main():
    files = sorted(SRC.glob("*.md"), key=lambda p: (0, int(m.group(1))) if (m := re.search(r"Leçon (\d+)", p.stem)) else (1, 0))
    pages = []
    for f in files:
        text = f.read_text(encoding="utf-8")
        num, zh, sub = parse_meta(f.stem, text)
        slug = slugify(f.stem)
        en_path = EN_SRC / f"{slug}.md"
        if en_path.exists():
            en_text = en_path.read_text(encoding="utf-8")
            en_sub = first_italic(en_text)
        else:
            en_text, en_sub = text, sub  # fallback : pas encore traduit
        pages.append({
            "src": text, "en_src": en_text, "num": num, "zh": zh,
            "sub": sub, "en_sub": en_sub, "slug": slug,
            "translated": en_path.exists(),
        })

    md = markdown.Markdown(extensions=["tables", "sane_lists"])
    for i, p in enumerate(pages):
        md.reset(); body_fr = md.convert(p["src"])
        md.reset(); body_en = md.convert(p["en_src"])
        prev_link = f'<a href="{pages[i-1]["slug"]}.html">&larr; {pages[i-1]["zh"]}</a>' if i > 0 else '<span class="spacer"></span>'
        next_link = f'<a href="{pages[i+1]["slug"]}.html">{pages[i+1]["zh"]} &rarr;</a>' if i + 1 < len(pages) else '<span class="spacer"></span>'
        pager = f'<nav class="pager">{prev_link}{next_link}</nav>'

        if p["num"]:
            header_fr = f"Leçon {p['num']} — {p['zh']}"
            header_en = f"Lesson {p['num']} — {p['zh']}"
        else:
            header_fr = p["zh"]
            header_en = EN_TITLES.get(p["slug"], p["zh"])

        html = PAGE.format(
            title_fr=header_fr, title_en=header_en,
            header_fr=header_fr, header_en=header_en,
            subtitle_fr=p["sub"], subtitle_en=p["en_sub"],
            body_fr=body_fr, body_en=body_en, pager=pager,
        )
        (OUT / f"{p['slug']}.html").write_text(html, encoding="utf-8")
        flag = "" if p["translated"] else "  (EN manquant → FR par défaut)"
        print(f"OK  {p['slug']}.html{flag}")

    cards = []
    for p in pages:
        if p["num"]:
            label_fr, label_en = f"Leçon {p['num']}", f"Lesson {p['num']}"
        else:
            label_fr, label_en = "Note de grammaire", "Grammar note"
        cards.append(
            f'<li><a href="{p["slug"]}.html">'
            f'<span class="num"><span class="lang-fr">{label_fr}</span><span class="lang-en">{label_en}</span></span>'
            f'<span class="zh">{p["zh"]}</span>'
            f'<span class="sub"><span class="lang-fr">{p["sub"]}</span><span class="lang-en">{p["en_sub"]}</span></span>'
            f'</a></li>'
        )
    index_body_fr = '<h1>Sommaire des leçons</h1>\n<ul class="lessons">\n' + "\n".join(cards) + "\n</ul>"
    index_body_en = '<h1>Lesson index</h1>\n<ul class="lessons">\n' + "\n".join(cards) + "\n</ul>"
    # Les cartes sont identiques dans les deux corps (elles gèrent la langue en interne) ;
    # seul le titre H1 change, donc on injecte le H1 via les deux corps de langue.
    html = PAGE.format(
        title_fr="HSK 2 — Fiches de cours", title_en="HSK 2 — Course notes",
        header_fr="HSK 2 — Fiches de cours", header_en="HSK 2 — Course notes",
        subtitle_fr="Standard Course · vocabulaire, grammaire, dialogues",
        subtitle_en="Standard Course · vocabulary, grammar, dialogues",
        body_fr=index_body_fr, body_en=index_body_en, pager="",
    )
    (OUT / "index.html").write_text(html, encoding="utf-8")
    print("OK  index.html")


if __name__ == "__main__":
    main()
