#!/usr/bin/env python3
"""Regenerate the games grid inside index.html.

Scans games/<slug>/index.html, reads each game's <head> metadata, and rewrites
only the region between the generated markers in index.html. Pure standard
library: runs on macOS default python3 and on ubuntu-latest.
"""
from __future__ import annotations

import html
import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GAMES_DIR = ROOT / "games"
INDEX = ROOT / "index.html"

BEGIN_MARKER = "<!-- BEGIN GENERATED GAMES -->"
END_MARKER = "<!-- END GENERATED GAMES -->"

# House cyan, the SGC game's own --data colour. Used when a game does not
# declare game-accent.
DEFAULT_ACCENT = "#36e0c8"
COVER_NAMES = ("cover.png", "cover.jpg", "cover.webp")

TITLE_RE = re.compile(r"<title>([\s\S]*?)</title>", re.IGNORECASE)
HEX_RE = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")


def meta_re(name: str) -> re.Pattern[str]:
    return re.compile(
        r'<meta\s+name=["\']' + re.escape(name) + r'["\']\s+content=["\']([\s\S]*?)["\']\s*/?>',
        re.IGNORECASE,
    )


DESC_RE = meta_re("description")
KEYWORDS_RE = meta_re("keywords")
ADDED_RE = meta_re("added")
ACCENT_RE = meta_re("game-accent")
CONTROLS_RE = meta_re("game-controls")


@dataclass
class Game:
    slug: str
    title: str
    description: str
    added: date
    tags: list[str]
    accent: str
    controls: str
    cover: str | None


def esc(value: str) -> str:
    """Escape a value for use in HTML text or a quoted attribute."""
    return html.escape(value, quote=True)


def first_group(pattern: re.Pattern[str], text: str) -> str:
    match = pattern.search(text)
    return html.unescape(match.group(1)).strip() if match else ""


def parse_tags(raw: str) -> list[str]:
    return [tag.strip() for tag in raw.split(",") if tag.strip()]


def find_games(games_dir: Path = GAMES_DIR) -> list[Path]:
    """Every games/<slug>/index.html, sorted by slug. One level only."""
    if not games_dir.is_dir():
        return []
    return sorted(p for p in games_dir.glob("*/index.html") if p.is_file())


def find_cover(game_dir: Path) -> str | None:
    for name in COVER_NAMES:
        if (game_dir / name).is_file():
            return name
    return None


def parse_game(path: Path) -> tuple[Game | None, list[str]]:
    """Read one game's metadata.

    Returns (game, []) on success or (None, errors) with every problem found,
    so one build reports all the mistakes rather than one per run.
    """
    rel = path.relative_to(ROOT).as_posix()
    text = path.read_text(encoding="utf-8")
    errors: list[str] = []

    title = first_group(TITLE_RE, text)
    description = first_group(DESC_RE, text)
    added_raw = first_group(ADDED_RE, text)
    accent = first_group(ACCENT_RE, text) or DEFAULT_ACCENT
    controls = first_group(CONTROLS_RE, text)
    tags = parse_tags(first_group(KEYWORDS_RE, text))

    if not title:
        errors.append(f"{rel}: missing <title>")
    if not description:
        errors.append(f'{rel}: missing <meta name="description">')

    added: date | None = None
    if not added_raw:
        errors.append(f'{rel}: missing <meta name="added">')
    else:
        try:
            added = date.fromisoformat(added_raw)
        except ValueError:
            errors.append(
                f'{rel}: <meta name="added"> is not a YYYY-MM-DD date: {added_raw!r}'
            )

    if not HEX_RE.match(accent):
        errors.append(
            f'{rel}: <meta name="game-accent"> is not a hex colour: {accent!r}'
        )

    if errors:
        return None, errors

    return (
        Game(
            slug=path.parent.name,
            title=title,
            description=description,
            added=added,
            tags=tags,
            accent=accent,
            controls=controls,
            cover=find_cover(path.parent),
        ),
        [],
    )


def monogram(slug: str) -> str:
    """Two letters standing in for a game with no cover art.

    Taken from the slug rather than the title, because slugs are short and
    predictable: safeguarded-copy gives SC, tetris gives TE.
    """
    parts = [p for p in re.split(r"[^0-9A-Za-z]+", slug) if p]
    if not parts:
        return "??"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[1][0]).upper()


def fallback_tile(game: Game) -> str:
    """Inline SVG card art for a game that has no cover image."""
    return (
        f'<svg class="tile" viewBox="0 0 320 180" preserveAspectRatio="xMidYMid slice" '
        f'role="img" aria-label="{esc(game.title)} placeholder art">'
        f'<rect width="320" height="180" fill="{game.accent}" fill-opacity="0.10"/>'
        f'<rect x="0.5" y="0.5" width="319" height="179" fill="none" '
        f'stroke="{game.accent}" stroke-opacity="0.40"/>'
        f'<text x="160" y="112" text-anchor="middle" font-size="72" font-weight="700" '
        f'font-family="IBM Plex Mono, ui-monospace, monospace" letter-spacing="6" '
        f'fill="{game.accent}" fill-opacity="0.85">{esc(monogram(game.slug))}</text>'
        f"</svg>"
    )
