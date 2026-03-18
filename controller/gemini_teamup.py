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