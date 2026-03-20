"""
Bracket Image Generator Module

Generates a single-elimination bracket visualization image
using Pillow, matching the existing team_announcement_image.py style.

Supports 4-team brackets (semifinals + final).
Designed to extend to 8/16-team brackets later.
"""

import os
import pathlib
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from config import settings

logger = settings.logging.getLogger("discord")

# ── Paths (mirrors team_announcement_image.py) ──────────────────────────────
BASE_DIR    = pathlib.Path(__file__).parent.parent
BACKGROUND_PATH = BASE_DIR / "common" / "images" / "background.png"
FONTS_DIR   = BASE_DIR / "view" / "fonts"
OUTPUT_DIR  = BASE_DIR / "temp"

os.makedirs(OUTPUT_DIR, exist_ok=True)

BOLD_FONT    = FONTS_DIR / "Roboto-Bold.ttf"
REGULAR_FONT = FONTS_DIR / "Roboto-Regular.ttf"

# ── Palette (reuses existing color constants) ────────────────────────────────
TEAM1_COLOR      = (65,  105, 225)   # Royal Blue
TEAM2_COLOR      = (220,  20,  60)   # Crimson
WINNER_COLOR     = (255, 215,   0)   # Gold
PENDING_COLOR    = (100, 100, 100)   # Gray
WHITE            = (255, 255, 255)
BLACK            = ( 20,  20,  20)
DARK_GRAY        = ( 40,  40,  40)
GRAY             = (180, 180, 180)
BACKGROUND_TOP   = ( 15,  15,  25)
BACKGROUND_BOTTOM= ( 40,  40,  60)

# ── Canvas ───────────────────────────────────────────────────────────────────
WIDTH  = 1920
HEIGHT = 1080


# ── Helpers ──────────────────────────────────────────────────────────────────

def _load_background() -> Image.Image:
    """Load background.png or fall back to gradient (same logic as team_announcement_image)."""
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
        logger.warning(f"bracket_image: background load failed ({e}), using gradient")

    # Gradient fallback
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


def _load_fonts():
    """Load Roboto fonts (same sizes/fallback as team_announcement_image)."""
    try:
        if BOLD_FONT.exists() and REGULAR_FONT.exists():
            return {
                "title":   ImageFont.truetype(str(BOLD_FONT),    72),
                "header":  ImageFont.truetype(str(BOLD_FONT),    48),
                "team":    ImageFont.truetype(str(BOLD_FONT),    34),
                "detail":  ImageFont.truetype(str(REGULAR_FONT), 28),
                "label":   ImageFont.truetype(str(REGULAR_FONT), 24),
                "footer":  ImageFont.truetype(str(REGULAR_FONT), 30),
            }
    except Exception as e:
        logger.warning(f"bracket_image: font load failed ({e}), using defaults")

    default = ImageFont.load_default()
    return {k: default for k in ("title", "header", "team", "detail", "label", "footer")}


def _draw_match_card(
    draw: ImageDraw.ImageDraw,
    img: Image.Image,
    fonts: dict,
    x: int, y: int,
    card_w: int, card_h: int,
    label: str,
    team_a: str, team_b: str,
    winner: str | None,
    status: str,
):
    """
    Draw a single match card at (x, y).

    team_a / team_b: display strings (e.g. "BluePlayer1 +4")
    winner: "A", "B", or None
    status: "pending" | "ready" | "completed"
    """
    slot_h = card_h // 2
    border_color = WINNER_COLOR if status == "completed" else (
        WHITE if status == "ready" else PENDING_COLOR
    )

    # ── Card background ──
    overlay = Image.new("RGB", (card_w, card_h), DARK_GRAY)
    img.paste(overlay, (x, y))
    draw.rectangle([(x, y), (x + card_w, y + card_h)], outline=border_color, width=3)

    # ── Divider between slots ──
    mid_y = y + slot_h
    draw.line([(x, mid_y), (x + card_w, mid_y)], fill=GRAY, width=1)

    # ── Team A slot ──────────────────────────────────────────────────────────
    a_fill = WINNER_COLOR if winner == "A" else (
        TEAM1_COLOR if team_a != "TBD" else GRAY
    )
    a_bg = tuple(int(c * 0.25) for c in a_fill)
    slot_bg = Image.new("RGB", (card_w, slot_h), a_bg)
    img.paste(slot_bg, (x, y))
    draw.text(
        (x + card_w // 2, y + slot_h // 2),
        team_a,
        fill=a_fill,
        font=fonts["team"],
        anchor="mm",
    )
    if winner == "A":
        draw.text((x + card_w - 10, y + slot_h // 2), "🏆", font=fonts["detail"], anchor="rm")

    # ── Team B slot ──────────────────────────────────────────────────────────
    b_fill = WINNER_COLOR if winner == "B" else (
        TEAM2_COLOR if team_b != "TBD" else GRAY
    )
    b_bg = tuple(int(c * 0.25) for c in b_fill)
    slot_bg = Image.new("RGB", (card_w, slot_h), b_bg)
    img.paste(slot_bg, (x, y + slot_h))
    draw.text(
        (x + card_w // 2, y + slot_h + slot_h // 2),
        team_b,
        fill=b_fill,
        font=fonts["team"],
        anchor="mm",
    )
    if winner == "B":
        draw.text((x + card_w - 10, y + slot_h + slot_h // 2), "🏆", font=fonts["detail"], anchor="rm")

    # ── Round label above card ────────────────────────────────────────────────
    draw.text(
        (x + card_w // 2, y - 18),
        label,
        fill=GRAY,
        font=fonts["label"],
        anchor="mm",
    )


def _resolve_display_name(team_id: str | None, db) -> str:
    """
    Convert a bracket team_id like 'match_3_team1' into a short display string.
    Returns up to 2 player names or 'TBD' if slot unfilled.
    """
    if not team_id:
        return "TBD"

    if team_id.endswith("_team1"):
        match_code = team_id[:-6]
        team_up = "team1"
    elif team_id.endswith("_team2"):
        match_code = team_id[:-6]
        team_up = "team2"
    else:
        return team_id  # raw fallback

    try:
        db.cursor.execute(
            """
            SELECT p.game_name
            FROM Matches m
            JOIN player p ON m.user_id = p.user_id
            WHERE m.teamId = ? AND m.teamUp = ?
            LIMIT 2
            """,
            (match_code, team_up),
        )
        rows = db.cursor.fetchall()
        if not rows:
            return "TBD"
        names = [r[0] for r in rows]
        suffix = " +more" if len(names) == 2 else ""
        return ", ".join(names) + suffix
    except Exception as e:
        logger.error(f"_resolve_display_name failed: {e}")
        return team_id


def _connector_line(draw, x1, y1, x2, y2):
    """Draw an L-shaped connector between match cards."""
    mid_x = (x1 + x2) // 2
    draw.line([(x1, y1), (mid_x, y1)], fill=GRAY, width=2)
    draw.line([(mid_x, y1), (mid_x, y2)], fill=GRAY, width=2)
    draw.line([(mid_x, y2), (x2, y2)], fill=GRAY, width=2)


# ── Public API ────────────────────────────────────────────────────────────────

def create_bracket_image(bracket_id: str, db) -> str:
    """
    Generate a bracket image for the given bracket_id.

    Fetches all BracketMatches rows, lays them out as:
      Round 1 (left col)  →  Round 2 (right col, final)

    Returns:
        str: absolute path to the saved PNG
    """
    # 1. Fetch bracket matches ordered by round + index
    db.cursor.execute(
        """
        SELECT round_num, match_index, match_code,
               teamA_id, teamB_id,
               winner_team_id, status,
               next_match_code, next_slot
        FROM BracketMatches
        WHERE bracket_id = ?
        ORDER BY round_num ASC, match_index ASC
        """,
        (bracket_id,),
    )
    rows = db.cursor.fetchall()

    if not rows:
        raise ValueError(f"No BracketMatches found for bracket_id='{bracket_id}'")

    # Group by round
    rounds: dict[int, list] = {}
    for row in rows:
        rnum = row[0]
        rounds.setdefault(rnum, []).append(row)

    num_rounds = max(rounds.keys())

    # 2. Build image
    img   = _load_background()
    draw  = ImageDraw.Draw(img)
    fonts = _load_fonts()

    # ── Title ─────────────────────────────────────────────────────────────────
    draw.text(
        (WIDTH // 2, 60),
        f"BRACKET  ·  {bracket_id.upper()}",
        fill=WHITE,
        font=fonts["title"],
        anchor="mm",
    )

    # ── Layout constants ──────────────────────────────────────────────────────
    CARD_W      = 420
    CARD_H      = 120
    COL_MARGIN  = 140          # horizontal gap between rounds
    TOP_OFFSET  = 130          # y start for cards
    USABLE_H    = HEIGHT - TOP_OFFSET - 80

    # Positions of each round's column (left edge of card)
    # Round 1 left, Round 2 (final) right-center, etc.
    total_cols_width = num_rounds * CARD_W + (num_rounds - 1) * COL_MARGIN
    col_start_x = (WIDTH - total_cols_width) // 2

    col_x: dict[int, int] = {}
    for rnum in range(1, num_rounds + 1):
        col_x[rnum] = col_start_x + (rnum - 1) * (CARD_W + COL_MARGIN)

    # Track card center-y per match_code for connector lines
    card_centers: dict[str, tuple[int, int]] = {}

    # ── Draw each round ───────────────────────────────────────────────────────
    for rnum in range(1, num_rounds + 1):
        matches = rounds.get(rnum, [])
        n = len(matches)
        spacing = USABLE_H // n
        cx = col_x[rnum]

        for idx, row in enumerate(matches):
            _, _, match_code, teamA_id, teamB_id, winner_id, status, next_mc, next_slot = row

            # y center of this card
            card_cy = TOP_OFFSET + spacing // 2 + idx * spacing
            card_y  = card_cy - CARD_H // 2

            # Resolve display names
            team_a_str = _resolve_display_name(teamA_id, db)
            team_b_str = _resolve_display_name(teamB_id, db)

            # Determine winner slot ("A", "B", or None)
            winner_slot = None
            if winner_id:
                if winner_id == teamA_id:
                    winner_slot = "A"
                elif winner_id == teamB_id:
                    winner_slot = "B"

            # Round label
            if rnum == num_rounds:
                round_label = "FINAL"
            elif num_rounds - rnum == 1:
                round_label = f"SEMIFINAL {idx + 1}"
            else:
                round_label = f"ROUND {rnum}  –  MATCH {idx + 1}"

            _draw_match_card(
                draw, img, fonts,
                cx, card_y, CARD_W, CARD_H,
                round_label,
                team_a_str, team_b_str,
                winner_slot, status,
            )

            card_centers[match_code] = (cx + CARD_W, card_cy)

    # ── Connector lines ───────────────────────────────────────────────────────
    for rnum in range(1, num_rounds + 1):
        for row in rounds.get(rnum, []):
            _, _, match_code, _, _, _, _, next_mc, next_slot = row
            if not next_mc or next_mc not in card_centers:
                continue

            src_x, src_y = card_centers[match_code]

            # destination: left edge of next card, at the correct slot mid-y
            dst_card_x = col_x[rnum + 1]
            dst_card_y_top = card_centers[next_mc][1] - CARD_H // 2
            slot_h = CARD_H // 2
            if next_slot == "A":
                dst_y = dst_card_y_top + slot_h // 2
            else:
                dst_y = dst_card_y_top + slot_h + slot_h // 2

            _connector_line(draw, src_x, src_y, dst_card_x, dst_y)

    # ── Footer ────────────────────────────────────────────────────────────────
    footer_overlay = Image.new("RGB", (WIDTH, 50), BLACK)
    img.paste(footer_overlay, (0, HEIGHT - 50))
    draw.text((30, HEIGHT - 25),        f"Bracket ID: {bracket_id}",
              fill=GRAY, font=fonts["footer"], anchor="lm")
    draw.text((WIDTH - 30, HEIGHT - 25), datetime.now().strftime("%Y-%m-%d"),
              fill=GRAY, font=fonts["footer"], anchor="rm")

    # ── Save ──────────────────────────────────────────────────────────────────
    try:
        out_path = OUTPUT_DIR / f"bracket_{bracket_id}.png"
        img.save(str(out_path), quality=95, optimize=True)
    except (PermissionError, OSError) as e:
        import tempfile
        out_path = pathlib.Path(tempfile.gettempdir()) / f"bracket_{bracket_id}.png"
        img.save(str(out_path), quality=95, optimize=True)
        logger.warning(f"bracket_image: saved to temp dir ({e})")

    logger.info(f"Bracket image saved: {out_path}")
    return str(out_path)