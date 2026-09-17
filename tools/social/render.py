#!/usr/bin/env python3
"""Render data-driven Fe social cards. See tools/social/README.md."""
from __future__ import annotations

import argparse
from functools import lru_cache
from html import escape
import json
import math
from pathlib import Path
import re
import sys

from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[2]
FONTS = ROOT / "themes/apollo/static/fonts"
W, H, SCALE = 1600, 1000, 2
WHITE, MUTED, MINT, PINK = "#ffffff", "#d1ccff", "#99f4cf", "#ffb4de"
PANEL, BORDER = "#211969", "#7162d1"


@lru_cache(maxsize=128)
def font(size, style="regular"):
    names = {
        "regular": "SpaceGrotesk/SpaceGrotesk-Regular.ttf",
        "bold": "SpaceGrotesk/SpaceGrotesk-Bold.ttf",
        "mono": "JetbrainsMono/JetBrainsMono-Regular.ttf",
    }
    path = FONTS / names[style]
    if not path.exists():
        raise ValueError("Missing theme fonts. Run: git submodule update --init --recursive")
    # Code must display literal characters: no == / != programming ligatures.
    options = {"layout_engine": ImageFont.Layout.BASIC} if style == "mono" else {}
    return ImageFont.truetype(str(path), round(size * SCALE), **options)


@lru_cache(maxsize=1)
def background():
    # Deterministic, procedural violet gradient; no generated image or network asset.
    small = Image.new("RGB", (400, 250))
    pixels = []
    for y in range(250):
        for x in range(400):
            glow = max(0, 1 - math.hypot(x / 400, y / 250) / 1.25)
            pixels.append(tuple(round(a + (b - a) * glow) for a, b in
                                zip((46, 31, 161), (123, 108, 241))))
    small.putdata(pixels)
    return small.resize((W * SCALE, H * SCALE), Image.Resampling.BICUBIC)


class Canvas:
    def __init__(self):
        self.im = background().copy()
        self.draw = ImageDraw.Draw(self.im)

    def box(self, xy, fill=PANEL, outline=BORDER, radius=24):
        self.draw.rounded_rectangle(tuple(round(v * SCALE) for v in xy),
                                    radius=radius * SCALE, fill=fill,
                                    outline=outline, width=2 * SCALE)

    def line(self, xy, color=MUTED, width=2):
        self.draw.line(tuple(round(v * SCALE) for v in xy), fill=color, width=width * SCALE)

    def text(self, x, y, value, size=30, color=WHITE, style="regular"):
        if x < 0 or y < 0 or x + self.width(value, size, style) > W - 40 or y + size > H:
            raise ValueError(f"Text exceeds canvas bounds: {value!r}")
        self.draw.text((round(x * SCALE), round(y * SCALE)), value,
                       # Ascender anchoring keeps separately colored runs on one baseline,
                       # including punctuation (a comma must not float like an apostrophe).
                       font=font(size, style), fill=color, anchor="la")

    def width(self, value, size=30, style="regular"):
        return self.draw.textlength(value, font=font(size, style)) / SCALE

    def paragraph(self, x, y, value, width, size=30, color=MUTED, style="regular", bottom=870):
        lines = []
        for paragraph in value.split("\n"):
            line = ""
            for word in paragraph.split():
                if self.width(word, size, style) > width:
                    raise ValueError(f"Word does not fit: {word!r}")
                candidate = f"{line} {word}".strip()
                if self.width(candidate, size, style) > width:
                    lines.append(line)
                    line = word
                else:
                    line = candidate
            lines.append(line)
        step = size * 1.4
        if y + len(lines) * step > bottom:
            raise ValueError(f"Text overflows its panel: {value!r}")
        for line in lines:
            self.text(x, y, line, size, color, style)
            y += step
        return y

    def label(self, x, y, value, color=MINT):
        self.text(x, y, value.upper(), 22, color, "bold")

    def arrow(self, x, y, length=56):
        self.line((x, y, x + length, y), MINT, 3)
        self.line((x + length - 12, y - 9, x + length, y), MINT, 3)
        self.line((x + length - 12, y + 9, x + length, y), MINT, 3)

    def logo(self, x, y, size=66):
        # Reuse the blog's black/white logo, remapped to the original social palette.
        logo = Image.open(ROOT / "static/fe-box-solid.png").convert("RGBA")
        gray = ImageOps.grayscale(logo)
        colored = ImageOps.colorize(gray, WHITE, "#5344db").convert("RGBA")
        colored.putalpha(logo.getchannel("A"))
        colored = colored.resize((size * SCALE, size * SCALE), Image.Resampling.LANCZOS)
        self.im.paste(colored, (x * SCALE, y * SCALE), colored)

    def header(self, campaign, card):
        self.logo(80, 66)
        self.text(166, 84, campaign["series"], 26, WHITE, "bold")
        self.line((80, 160, 1520, 160), "#a497ef", 1)
        if card["layout"] != "cover":
            self.paragraph(80, 210, card["title"], 1440, 62, WHITE, "bold", bottom=304)
            if card.get("subtitle"):
                self.paragraph(80, 295, card["subtitle"], 1440, 28, MUTED, bottom=344)

    def footer(self, campaign, card):
        if card.get("note"):
            self.paragraph(80, 853, card["note"], 1440, 25, MUTED, bottom=905)
        self.line((80, 920, 1520, 920), "#a497ef", 1)
        self.text(80, 947, campaign["footer"], 23, MUTED)

    def save(self, path):
        self.im.resize((W, H), Image.Resampling.LANCZOS).save(path, optimize=True)


def cover(c, card):
    y = 255
    for line in card["headline"]:
        if c.width(line, 154, "bold") > 1020:
            raise ValueError("Cover headline is too wide")
        c.text(80, y, line, 154, WHITE, "bold")
        y += 166
    # Quiet typographic motif, rather than an unrelated stock illustration.
    c.box((1160, 280, 1515, 635), fill="#5140d0", outline="#9b8af2", radius=52)
    c.logo(1235, 355, 205)
    c.paragraph(88, 655, card["description"], 1000, 36, WHITE, bottom=790)
    x = 88
    for tag in card["chips"]:
        width = c.width(tag, 24) + 40
        if x + width > 1520:
            raise ValueError("Cover chips overflow")
        c.box((x, 800, x + width, 850), fill="#4130b3", radius=25)
        c.text(x + 20, 812, tag, 24)
        x += width + 14


TOKEN = re.compile(r'//.*|"[^"\n]*"|\b(?:let|mut|fn|pub|use|struct|const|return)\b|\b(?:u256|u8|bool|DynArray|MemVec|Address)\b|\b\d+\b|\b(?:true|false)\b')


def code(c, card):
    has_aside = bool(card.get("aside"))
    right = 1090 if has_aside else 1520
    c.box((80, 365, right, 817))
    c.label(112, 397, card.get("code_label", "FE"))
    c.line((112, 438, right - 32, 438), BORDER, 1)
    lines = card["code"].splitlines()
    size = 34
    while size > 22 and max(c.width(line, size, "mono") for line in lines) > right - 150:
        size -= 1
    if max(c.width(line, size, "mono") for line in lines) > right - 150:
        raise ValueError("Code line too long; wrap the source explicitly")
    if len(lines) * size * 1.6 > 335:
        raise ValueError("Too many code lines")
    for i, line in enumerate(lines):
        x, y, pos = 112, 469 + i * size * 1.6, 0
        for token in TOKEN.finditer(line):
            before = line[pos:token.start()]
            c.text(x, y, before, size, WHITE, "mono")
            x += c.width(before, size, "mono")
            word = token.group()
            color = MUTED if word.startswith("//") else MINT if word[:1].isdigit() or word.startswith('"') else PINK
            c.text(x, y, word, size, color, "mono")
            x += c.width(word, size, "mono")
            pos = token.end()
        c.text(x, y, line[pos:], size, WHITE, "mono")
    for i, item in enumerate(card.get("aside", [])):
        top = 388 + i * 142
        c.label(1140, top, item["label"])
        c.paragraph(1140, top + 39, item["text"], 360, 28, WHITE, bottom=top + 135)


def tiles(c, card):
    items = card["items"]
    if len(items) != 4:
        raise ValueError("tiles needs exactly four items")
    for i, item in enumerate(items):
        x, y = 80 + (i % 2) * 736, 365 + (i // 2) * 237
        c.box((x, y, x + 704, y + 217))
        c.label(x + 30, y + 27, item["label"])
        c.paragraph(x + 30, y + 75, item["text"], 644, 32, WHITE, bottom=y + 206)


def flow(c, card):
    steps = card["steps"]
    if not 2 <= len(steps) <= 4:
        raise ValueError("flow needs two to four steps")
    gap = 62
    width = (1440 - gap * (len(steps) - 1)) / len(steps)
    for i, item in enumerate(steps):
        x = 80 + i * (width + gap)
        c.box((x, 409, x + width, 653))
        c.label(x + 24, 436, f"0{i + 1}")
        c.paragraph(x + 24, 484, item["label"], width - 48, 34, WHITE, "bold", bottom=580)
        c.paragraph(x + 24, 588, item["text"], width - 48, 23, MUTED, bottom=642)
        if i < len(steps) - 1:
            c.arrow(x + width + 13, 530, 36)
    c.paragraph(80, 720, card["caption"], 1440, 32, WHITE, bottom=830)


def regions(c, card):
    c.label(80, 375, "MEMBUFFER")
    c.text(80, 415, "Owned allocation", 38, WHITE, "bold")
    start, y, unit = 80, 497, 144
    for i in range(10):
        c.box((start + i * unit, y, start + (i + 1) * unit - 8, y + 100),
              fill="#7770e7" if i < 6 else PANEL, outline="#b6adfa", radius=12)
    c.line((80, 622, 936, 622), MINT, 4)
    c.text(80, 642, "length: bytes in use", 28, MINT)
    c.line((80, 701, 1512, 701), WHITE, 3)
    c.text(80, 722, "capacity: full writable allocation", 28)
    c.box((1030, 365, 1520, 461), fill="#4130b3")
    c.text(1054, 385, "MemSpan", 29, MINT, "bold")
    c.text(1054, 425, "read-only byte view", 24)
    c.line((1050, 462, 1050, 480, 790, 480, 790, 495), MINT, 2)


def packed(c, card):
    c.label(80, 379, "ENCODE_PACKED((VALUE, ADDRESS, FLAG))")
    # Block sizes are intentionally labelled, not drawn to scale.
    for x, width, title, size, shade in [
        (80, 315, "u16", "2 bytes", "#5745cf"),
        (411, 685, "Address", "20 bytes", "#7060df"),
        (1112, 408, "bool", "1 byte", "#4130aa"),
    ]:
        c.box((x, 450, x + width, 621), fill=shade, outline="#b6adfa")
        c.text(x + 28, 480, title, 43, WHITE, "bold")
        c.text(x + 28, 555, size, 29, MINT)
    c.arrow(80, 715, 95)
    c.text(207, 683, "keccak_packed(...)", 42, WHITE, "mono")
    c.text(209, 748, "Hash the same packed bytes directly.", 29)


def outcomes(c, card):
    for i, item in enumerate(card["rows"]):
        y = 367 + i * 110
        c.box((80, y, 1520, y + 94), radius=18)
        c.text(110, y + 27, item["input"], 30)
        c.arrow(1000, y + 47, 78)
        c.text(1120, y + 28, item["result"], 30,
               MINT if item["ok"] else PINK, "bold")


def lanes(c, card):
    for i, row in enumerate(card["rows"]):
        y = 385 + i * 180
        c.label(80, y + 5, row["label"])
        c.box((250, y, 830, y + 110))
        c.text(280, y + 38, row["left"], 32, WHITE, "mono")
        c.arrow(860, y + 55, 110)
        c.box((1000, y, 1520, y + 110), fill="#5140c1")
        c.text(1030, y + 38, row["right"], 32, MINT, "mono")
    c.paragraph(80, 750, card["caption"], 1440, 32, WHITE, bottom=820)


LAYOUTS = {"cover": cover, "code": code, "tiles": tiles, "flow": flow,
           "regions": regions, "packed": packed, "outcomes": outcomes, "lanes": lanes}


def tweet_length(tweet):
    # Campaign copy is ASCII, so URL substitution is the only weighting needed.
    if not tweet.isascii():
        raise ValueError("Tweet copy must be ASCII for this length check; use plain punctuation")
    return len(re.sub(r"https?://\S+", "x" * 23, tweet))


def validate(data):
    for name in ("series", "footer", "cards"):
        if not data.get(name):
            raise ValueError(f"Missing campaign field: {name}")
    seen = set()
    for card in data["cards"]:
        slug = card.get("id", "")
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug) or slug in seen:
            raise ValueError(f"Invalid or duplicate card id: {slug!r}")
        seen.add(slug)
        if card.get("layout") not in LAYOUTS:
            raise ValueError(f"Unknown layout in {slug}")
        for name in ("title", "tweet", "alt"):
            if not card.get(name):
                raise ValueError(f"Missing {name} in {slug}")
        if tweet_length(card["tweet"]) > 280:
            raise ValueError(f"Tweet {slug} exceeds 280 characters")
        if card["layout"] == "lanes" and len(card.get("rows", [])) != 2:
            raise ValueError(f"lanes needs exactly two rows in {slug}")
        if card["layout"] == "outcomes" and not card.get("rows"):
            raise ValueError(f"outcomes needs at least one row in {slug}")
        if len(card.get("rows", [])) > 4 or len(card.get("aside", [])) > 3:
            raise ValueError(f"Too many items in {slug}")


def exports(data, out, filenames):
    markdown = [f"# {data['series']}\n", "Tweet copy and image alt text. URLs count as 23 characters.\n"]
    cards_html = []
    for i, (card, filename) in enumerate(zip(data["cards"], filenames), 1):
        length = tweet_length(card["tweet"])
        markdown.extend([f"## {i:02d}. {card['title']} ({length}/280)\n", card["tweet"] + "\n",
                         f"Image: [{filename}]({filename})\n", f"Alt text: {card['alt']}\n"])
        (out / filename.replace(".png", ".alt.txt")).write_text(card["alt"] + "\n", encoding="utf-8")
        cards_html.append(f'<article><a href="{filename}"><img src="{filename}" alt="{escape(card["alt"], quote=True)}"></a>'
                          f'<h2>{i:02d}. {escape(card["title"])}</h2><small>{length}/280 characters</small>'
                          f'<pre>{escape(card["tweet"])}</pre><details><summary>Alt text</summary><p>{escape(card["alt"])}</p></details>'
                          f'<p><a href="{filename}" download>Download PNG</a></p></article>')
    (out / "thread.md").write_text("\n".join(markdown), encoding="utf-8")
    (out / "index.html").write_text('''<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Fe social cards</title>
<style>body{background:#f4f2ff;color:#241753;font:17px system-ui;margin:0;padding:32px}main{max-width:1600px;margin:auto}
h1{font-size:36px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,540px),1fr));gap:32px}
article{background:white;padding:20px;border-radius:16px}img{width:100%;height:auto;border-radius:8px}h2{font-size:23px}
pre{font:inherit;white-space:pre-wrap;line-height:1.6}a{color:#5141cf}small{color:#6d6486}details{line-height:1.5}</style>
<main>''' + f'<h1>{escape(data["series"])}</h1><p>1600 × 1000 PNGs · <a href="thread.md">Thread text</a> · '
        '<a href="contact-sheet.jpg">Contact sheet</a></p><div class="grid">' + "".join(cards_html) + '</div></main></html>', encoding="utf-8")
    columns, thumb_w, thumb_h = 3, 480, 300
    rows = math.ceil(len(filenames) / columns)
    sheet = Image.new("RGB", (columns * (thumb_w + 20) + 20, rows * (thumb_h + 20) + 20), "#ede9ff")
    for i, filename in enumerate(filenames):
        with Image.open(out / filename) as im:
            thumb = im.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
            sheet.paste(thumb, (20 + i % columns * (thumb_w + 20), 20 + i // columns * (thumb_h + 20)))
    sheet.save(out / "contact-sheet.jpg", quality=92)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("campaign", type=Path, help="Campaign JSON path")
    parser.add_argument("--out", type=Path, help="Output directory (default: target/social/<campaign directory>)")
    args = parser.parse_args()
    try:
        data = json.loads(args.campaign.read_text(encoding="utf-8"))
        validate(data)
        out = args.out or ROOT / "target/social" / args.campaign.resolve().parent.name
        out.mkdir(parents=True, exist_ok=True)
        filenames = []
        for i, card in enumerate(data["cards"], 1):
            c = Canvas()
            try:
                c.header(data, card)
                LAYOUTS[card["layout"]](c, card)
                c.footer(data, card)
            except (ValueError, KeyError) as error:
                raise ValueError(f"Card {card['id']}: {error}") from error
            filename = f"{i:02d}-{card['id']}.png"
            c.save(out / filename)
            filenames.append(filename)
            print(f"Rendered {filename}")
        exports(data, out, filenames)
        print(f"\nPreview: {out / 'index.html'}")
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
