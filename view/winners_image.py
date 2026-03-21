"""
Winners Image Generator Module

Generates a celebration image for the tournament winners.
Matches the style of team_announcement_image.py (same background, fonts, palette).

Place this file in: view/winners_image.py
"""

import os
import pathlib
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from config import settings

logger = settings.logging.getLogger("discord")

# ── Paths (identical to team_announcement_image.py) ──────────────────────────
BASE_DIR        = pathlib.Path(__file__).parent.parent
BACKGROUND_PATH = BASE_DIR / "common" / "images" / "background.png"
FONTS_DIR       = BASE_DIR / "view" / "fonts"
OUTPUT_DIR      = BASE_DIR / "temp"

os.makedirs(OUTPUT_DIR, exist_ok=True)

BOLD_FONT    = FONTS_DIR / "Roboto-Bold.ttf"
REGULAR_FONT = FONTS_DIR / "Roboto-Regular.ttf"

# ── Palette (same as team_announcement_image.py) ─────────────────────────────
GOLD         = (255, 215,   0)
GOLD_DARK    = (180, 140,   0)
WHITE        = (255, 255, 255)
BLACK        = ( 20,  20,  20)
DARK_GRAY    = ( 40,  40,  40)
GRAY         = (180, 180, 180)
BACKGROUND_TOP    = ( 15,  15,  25)
BACKGROUND_BOTTOM = ( 40,  40,  60)

WIDTH  = 1920
HEIGHT = 1080


# ── Helpers ───────────────────────────────────────────────────────────────────

def _load_background() -> Image.Image:
    try:
        if BACKGROUND_PATH.exists():
            img = Image.open(BACKGROUND_PATH)
            if img.size != (WIDTH, HEIGHT):
                method = Image.LANCZOS if hasattr(Image, "LANCZOS") else Image.ANTIALIAS
                img = img.resize((WIDTH, HEIGHT), method)
            if img.mode != "RGB":
                img = img.convert("RGB")
            return img
    except Exception as e:
        logger.warning(f"winners_image: background load failed ({e}), using gradient")

    img = Image.new("RGB", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(img)
    bands = 100
    for i in range(bands):
        y0 = int(i * HEIGHT / bands)
        y1 = int((i + 1) * HEIGHT / bands)
        r = int(BACKGROUND_TOP[0] + (BACKGROUND_BOTTOM[0] - BACKGROUND_TOP[0]) * i / bands)
        g = int(BACKGROUND_TOP[1] + (BACKGROUND_BOTTOM[1] - BACKGROUND_TOP[1]) * i / bands)
        b = int(BACKGROUND_TOP[2] + (BACKGROUND_BOTTOM[2] - BACKGROUND_TOP[2]) * i / bands)
        draw.rectangle([(0, y0), (WIDTH, y1)], fill=(r, g, b))
    return img


def _load_fonts() -> dict:
    try:
        if BOLD_FONT.exists() and REGULAR_FONT.exists():
            return {
                "champion": ImageFont.truetype(str(BOLD_FONT),    110),
                "title":    ImageFont.truetype(str(BOLD_FONT),     80),
                "name":     ImageFont.truetype(str(BOLD_FONT),     52),
                "sub":      ImageFont.truetype(str(REGULAR_FONT),  36),
                "footer":   ImageFont.truetype(str(REGULAR_FONT),  30),
            }
    except Exception as e:
        logger.warning(f"winners_image: font load failed ({e}), using defaults")

    default = ImageFont.load_default()
    return {k: default for k in ("champion", "title", "name", "sub", "footer")}


def _draw_trophy(draw: ImageDraw.ImageDraw, cx: int, cy: int, size: int = 120):
    """
    Draw a geometric trophy shape using Pillow primitives.
    cx, cy = center of trophy base
    """
    gold     = GOLD
    gold_dim = GOLD_DARK

    # Cup body (trapezoid approximated as polygon)
    half_top = size // 2
    half_bot = size // 3
    cup_top  = cy - size
    cup_mid  = cy - size // 3

    cup_body = [
        (cx - half_top, cup_top),
        (cx + half_top, cup_top),
        (cx + half_bot, cup_mid),
        (cx - half_bot, cup_mid),
    ]
    draw.polygon(cup_body, fill=gold)

    # Cup inner shadow
    inner = [
        (cx - half_top + 12, cup_top + 12),
        (cx + half_top - 12, cup_top + 12),
        (cx + half_bot - 8,  cup_mid - 8),
        (cx - half_bot + 8,  cup_mid - 8),
    ]
    draw.polygon(inner, fill=gold_dim)

    # Handles (left & right arcs approximated as ellipses)
    handle_w = size // 4
    handle_h = size // 3
    # Left handle
    draw.arc(
        [(cx - half_top - handle_w, cup_top + 10),
         (cx - half_top + handle_w, cup_top + 10 + handle_h)],
        start=90, end=270, fill=gold, width=10
    )
    # Right handle
    draw.arc(
        [(cx + half_top - handle_w, cup_top + 10),
         (cx + half_top + handle_w, cup_top + 10 + handle_h)],
        start=270, end=90, fill=gold, width=10
    )

    # Stem
    stem_w = size // 8
    stem_h = size // 3
    draw.rectangle(
        [(cx - stem_w, cup_mid), (cx + stem_w, cup_mid + stem_h)],
        fill=gold
    )

    # Base
    base_w = size // 2
    base_h = size // 10
    draw.rectangle(
        [(cx - base_w, cup_mid + stem_h),
         (cx + base_w, cup_mid + stem_h + base_h)],
        fill=gold
    )

    # Star on cup
    draw.text((cx, cup_top + (cup_mid - cup_top) // 2), "★",
              fill=WHITE, anchor="mm",
              font=ImageFont.truetype(str(BOLD_FONT), size // 2)
              if BOLD_FONT.exists() else ImageFont.load_default())


def _draw_gold_divider(draw: ImageDraw.ImageDraw, y: int, margin: int = 200):
    """Draw a horizontal gold divider line."""
    draw.line([(margin, y), (WIDTH - margin, y)], fill=GOLD, width=3)


def _draw_player_card(
    draw: ImageDraw.ImageDraw,
    img: Image.Image,
    fonts: dict,
    cx: int, cy: int,
    card_w: int, card_h: int,
    name: str,
    rank_str: str,
):
    """Draw a single winner player card centered at (cx, cy)."""
    x = cx - card_w // 2
    y = cy - card_h // 2

    # Card background
    card_bg = Image.new("RGB", (card_w, card_h), DARK_GRAY)
    img.paste(card_bg, (x, y))

    # Gold border
    draw.rectangle([(x, y), (x + card_w, y + card_h)], outline=GOLD, width=3)

    # Player name
    draw.text(
        (cx, cy - 15),
        name,
        fill=GOLD,
        font=fonts["name"],
        anchor="mm"
    )

    # Rank subtitle
    draw.text(
        (cx, cy + 28),
        rank_str,
        fill=GRAY,
        font=fonts["sub"],
        anchor="mm"
    )


# ── Public API ────────────────────────────────────────────────────────────────

def create_winners_image(
    bracket_id: str,
    winner_team_id: str,
    db,
) -> str:
    """
    Generate a winners celebration image.

    Args:
        bracket_id:     e.g. "bracket_match_1_match_2"
        winner_team_id: e.g. "match_1_team1"
        db:             Tournament_DB instance (same thread)

    Returns:
        str: absolute path to saved PNG
    """
    # 1. Fetch winner players from DB
    if winner_team_id.endswith("_team1"):
        match_code = winner_team_id[:-6]
        team_up    = "team1"
    elif winner_team_id.endswith("_team2"):
        match_code = winner_team_id[:-6]
        team_up    = "team2"
    else:
        match_code = winner_team_id
        team_up    = "team1"

    db.cursor.execute(
        """
        SELECT p.game_name, g.tier, g.rank
        FROM Matches m
        JOIN player p ON m.user_id = p.user_id
        JOIN game g ON m.user_id = g.user_id
        WHERE m.teamId = ? AND m.teamUp = ?
        AND g.game_date = (
            SELECT MAX(game_date) FROM game WHERE user_id = m.user_id
        )
        ORDER BY g.manual_tier DESC
        """,
        (match_code, team_up),
    )
    players = db.cursor.fetchall()  # [(game_name, tier, rank), ...]

    # 2. Build image
    img   = _load_background()
    draw  = ImageDraw.Draw(img)
    fonts = _load_fonts()

    # ── Dark overlay for readability ──────────────────────────────────────────
    overlay = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
    img = Image.blend(img, overlay, alpha=0.35)
    draw = ImageDraw.Draw(img)

    # ── Trophy (top center) ───────────────────────────────────────────────────
    trophy_cx = WIDTH // 2
    trophy_cy = 220
    _draw_trophy(draw, trophy_cx, trophy_cy, size=110)

    # ── "TOURNAMENT CHAMPIONS" title ──────────────────────────────────────────
    draw.text(
        (WIDTH // 2, 330),
        "TOURNAMENT CHAMPIONS",
        fill=GOLD,
        font=fonts["champion"],
        anchor="mm",
    )

    # ── Gold divider ──────────────────────────────────────────────────────────
    _draw_gold_divider(draw, y=430, margin=300)

    # ── Player cards ──────────────────────────────────────────────────────────
    card_w    = 300
    card_h    = 90
    n         = len(players)
    total_w   = n * card_w + (n - 1) * 30  # 30px gap
    start_x   = (WIDTH - total_w) // 2

    for i, (name, tier, rank) in enumerate(players):
        cx = start_x + i * (card_w + 30) + card_w // 2
        cy = 560
        tier_str = f"{(tier or 'Unknown').capitalize()} {rank or ''}".strip()
        _draw_player_card(draw, img, fonts, cx, cy, card_w, card_h, name, tier_str)

    # ── Gold divider ──────────────────────────────────────────────────────────
    _draw_gold_divider(draw, y=640, margin=300)

    # ── Bracket ID ────────────────────────────────────────────────────────────
    draw.text(
        (WIDTH // 2, 700),
        f"Bracket: {bracket_id}",
        fill=GRAY,
        font=fonts["sub"],
        anchor="mm",
    )

    # ── Footer ────────────────────────────────────────────────────────────────
    footer_overlay = Image.new("RGB", (WIDTH, 50), BLACK)
    img.paste(footer_overlay, (0, HEIGHT - 50))
    draw.text(
        (WIDTH // 2, HEIGHT - 25),
        datetime.now().strftime("%Y-%m-%d"),
        fill=GRAY,
        font=fonts["footer"],
        anchor="mm",
    )

    # ── Save ──────────────────────────────────────────────────────────────────
    try:
        out_path = OUTPUT_DIR / f"winners_{bracket_id}.png"
        img.save(str(out_path), quality=95, optimize=True)
    except (PermissionError, OSError) as e:
        import tempfile
        out_path = pathlib.Path(tempfile.gettempdir()) / f"winners_{bracket_id}.png"
        img.save(str(out_path), quality=95, optimize=True)
        logger.warning(f"winners_image: saved to temp dir ({e})")

    logger.info(f"Winners image saved: {out_path}")
    return str(out_path)