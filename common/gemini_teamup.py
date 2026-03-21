# gemini_teamup.py
from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, List, Optional

from google import genai
from config import settings

_client: Optional[genai.Client] = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return _client


SYSTEM_PROMPT = """
You are helping form two balanced 5v5 League of Legends teams.

Priorities:
1. Balance overall team skill first.
2. Then assign players to preferred roles when possible.
3. Each team must have exactly one of:
   top, jungle, mid, bottom, support

Return only valid JSON with this shape:
{
  "team1": [{"user_id": "123", "assigned_role": "top"}],
  "team2": [{"user_id": "456", "assigned_role": "mid"}]
}

Rules:
- Each team must contain exactly 5 unique players.
- Every input player must appear exactly once.
- assigned_role must be one of: top, jungle, mid, bottom, support
"""


def _validate_teamup_result(result: Dict[str, Any], expected_ids: set[str]) -> bool:
    try:
        team1 = result["team1"]
        team2 = result["team2"]

        if len(team1) != 5 or len(team2) != 5:
            return False

        valid_roles = {"top", "jungle", "mid", "bottom", "support"}

        ids = []
        for entry in team1 + team2:
            if "user_id" not in entry or "assigned_role" not in entry:
                return False
            if entry["assigned_role"] not in valid_roles:
                return False
            ids.append(str(entry["user_id"]))

        if len(set(ids)) != 10:
            return False

        if set(ids) != expected_ids:
            return False

        if {e["assigned_role"] for e in team1} != valid_roles:
            return False

        if {e["assigned_role"] for e in team2} != valid_roles:
            return False

        return True
    except Exception:
        return False


async def gemini_teamup(players: List[Dict[str, Any]]) -> Dict[str, Any]:
    client = _get_client()
    expected_ids = {str(p["user_id"]) for p in players}

    response_schema = {
        "type": "object",
        "properties": {
            "team1": {
                "type": "array",
                "minItems": 5,
                "maxItems": 5,
                "items": {
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string"},
                        "assigned_role": {
                            "type": "string",
                            "enum": ["top", "jungle", "mid", "bottom", "support"]
                        }
                    },
                    "required": ["user_id", "assigned_role"]
                }
            },
            "team2": {
                "type": "array",
                "minItems": 5,
                "maxItems": 5,
                "items": {
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string"},
                        "assigned_role": {
                            "type": "string",
                            "enum": ["top", "jungle", "mid", "bottom", "support"]
                        }
                    },
                    "required": ["user_id", "assigned_role"]
                }
            }
        },
        "required": ["team1", "team2"]
    }

    def _call_gemini():
        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"{SYSTEM_PROMPT}\n\nPlayers:\n{json.dumps(players, indent=2)}",
            config={
                "response_mime_type": "application/json",
                "response_schema": response_schema,
            },
        )

        result = json.loads(resp.text)

        if not _validate_teamup_result(result, expected_ids):
            raise ValueError("Gemini returned invalid team structure")

        return result

    return await asyncio.to_thread(_call_gemini)


# ── NEW: Bracket Seeding ──────────────────────────────────────────────────────

SEEDING_PROMPT = """
You are an expert League of Legends tournament organizer.

You are given 4 teams that have already been formed. Your job is to seed them
for a single-elimination bracket (seed 1 = strongest, seed 4 = weakest).

Consider all of the following when seeding:
- Overall team skill (manual_tier values, where higher = stronger)
- Win rates of individual players
- Role coverage and whether players are in preferred roles
- Skill distribution within a team (a balanced team vs one carrying player)
- Any notable strengths or weaknesses per team

Return only valid JSON with this exact shape:
{
  "seeding": [
    {
      "team_id": "match_1_team1",
      "seed": 1,
      "tier_sum": 32.5,
      "reason": "Short explanation of why this team is seeded here"
    }
  ]
}

Rules:
- The "seeding" array must contain exactly 4 entries
- Seeds must be 1, 2, 3, 4 with no duplicates
- Every input team_id must appear exactly once
- "reason" must be 1-2 sentences maximum, specific to this team's strengths/weaknesses
- Be direct and analytical, not generic
"""


def _validate_seeding_result(result: Dict[str, Any], expected_team_ids: set[str]) -> bool:
    """Validate Gemini's seeding response structure."""
    try:
        seeding = result.get("seeding", [])

        if len(seeding) != 4:
            return False

        seeds_seen = set()
        ids_seen = set()

        for entry in seeding:
            if "team_id" not in entry or "seed" not in entry or "reason" not in entry:
                return False
            if entry["seed"] not in [1, 2, 3, 4]:
                return False
            if entry["seed"] in seeds_seen:
                return False  # duplicate seed
            if entry["team_id"] in ids_seen:
                return False  # duplicate team
            if entry["team_id"] not in expected_team_ids:
                return False  # unknown team

            seeds_seen.add(entry["seed"])
            ids_seen.add(entry["team_id"])

        return seeds_seen == {1, 2, 3, 4}

    except Exception:
        return False


def _build_team_payload(team_id: str, db) -> Dict[str, Any]:
    """
    Build a rich team data dict for Gemini from the Matches + game + player tables.
    team_id format: "match_1_team1"
    """
    if team_id.endswith("_team1"):
        match_code = team_id[:-6]
        team_up = "team1"
    elif team_id.endswith("_team2"):
        match_code = team_id[:-6]
        team_up = "team2"
    else:
        return {"team_id": team_id, "players": []}

    db.cursor.execute(
        """
        SELECT
            p.user_id,
            p.game_name,
            g.tier,
            g.rank,
            g.role,
            g.wins,
            g.losses,
            g.manual_tier,
            g.wr
        FROM Matches m
        JOIN player p ON m.user_id = p.user_id
        JOIN game g ON m.user_id = g.user_id
        WHERE m.teamId = ? AND m.teamUp = ?
        AND g.game_date = (
            SELECT MAX(game_date) FROM game WHERE user_id = m.user_id
        )
        """,
        (match_code, team_up),
    )
    rows = db.cursor.fetchall()

    players = []
    tier_sum = 0.0
    for row in rows:
        user_id, game_name, tier, rank, role_json, wins, losses, manual_tier, wr = row

        # Parse role JSON safely
        try:
            roles = json.loads(role_json) if role_json else []
        except (json.JSONDecodeError, TypeError):
            roles = []

        manual_tier = round(float(manual_tier), 2) if manual_tier else 0.0
        tier_sum += manual_tier

        players.append({
            "game_name": game_name,
            "tier": tier or "default",
            "rank": rank or "V",
            "preferred_roles": roles,
            "wins": wins or 0,
            "losses": losses or 0,
            "winrate_pct": round(float(wr) * 100, 1) if wr else 50.0,
            "manual_tier": manual_tier,
        })

    return {
        "team_id": team_id,
        "tier_sum": round(tier_sum, 2),
        "players": players,
    }


async def gemini_seed_teams(
    team_ids: List[str],
    db,
) -> Optional[List[Dict[str, Any]]]:
    """
    Ask Gemini to seed 4 teams for a bracket.

    Args:
        team_ids: List of 4 team ID strings e.g. ["match_1_team1", ...]
        db: Tournament_DB instance (must be called from same thread)

    Returns:
        List of seeding dicts sorted by seed ascending:
        [{"team_id": ..., "seed": 1, "tier_sum": ..., "reason": ...}, ...]
        Returns None if Gemini fails or returns invalid data.
    """
    if len(team_ids) != 4:
        raise ValueError("gemini_seed_teams requires exactly 4 team IDs")

    client = _get_client()
    expected_ids = set(team_ids)

    # Build rich team payloads from DB (must happen on calling thread)
    teams_payload = [_build_team_payload(tid, db) for tid in team_ids]

    response_schema = {
        "type": "object",
        "properties": {
            "seeding": {
                "type": "array",
                "minItems": 4,
                "maxItems": 4,
                "items": {
                    "type": "object",
                    "properties": {
                        "team_id":  {"type": "string"},
                        "seed":     {"type": "integer"},
                        "tier_sum": {"type": "number"},
                        "reason":   {"type": "string"},
                    },
                    "required": ["team_id", "seed", "tier_sum", "reason"]
                }
            }
        },
        "required": ["seeding"]
    }

    def _call_gemini():
        prompt = (
            f"{SEEDING_PROMPT}\n\n"
            f"Teams to seed:\n{json.dumps(teams_payload, indent=2)}"
        )
        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": response_schema,
            },
        )
        result = json.loads(resp.text)

        if not _validate_seeding_result(result, expected_ids):
            raise ValueError("Gemini returned invalid seeding structure")

        # Sort by seed ascending before returning
        result["seeding"].sort(key=lambda x: x["seed"])
        return result["seeding"]

    try:
        return await asyncio.to_thread(_call_gemini)
    except Exception as e:
        # Return None so callers can fall back to manual_tier sum gracefully
        import logging
        logging.getLogger("discord").error(f"gemini_seed_teams failed: {e}")
        return None