# sheets_sync.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional
import time

def compute_wr_percent(wins: int, losses: int) -> float:
    games = wins + losses
    if games <= 0:
        return 50.0
    return round((wins / games) * 100.0, 2)

@dataclass
class SheetsCache:
    player_row_map: Dict[str, int]
    last_loaded: float

class SheetSync:
    def __init__(self, gc, spreadsheet_name: str):
        self.gc = gc
        self.ss = gc.open(spreadsheet_name)
        self.players_ws = self.ss.worksheet("Players")
        self.matches_ws = self.ss.worksheet("Matches")

        self.cache: Optional[SheetsCache] = None
        self.cache_ttl_seconds = 300  # refresh every 5 minutes

    def _load_player_row_map(self) -> Dict[str, int]:
        """
        Reads ONLY the player_id column (fast) and builds a map to row index.
        Assumes header in row 1.
        """
        # Column A example: change "A" if player_id is in a different column
        col_vals = self.players_ws.col_values(1)  # includes header at index 0
        row_map: Dict[str, int] = {}

        for i, val in enumerate(col_vals[1:], start=2):  # start=2 because row 1 is header
            if val:
                row_map[str(val).strip()] = i

        return row_map

    def get_player_row(self, player_id: str) -> Optional[int]:
        now = time.time()
        if self.cache is None or (now - self.cache.last_loaded) > self.cache_ttl_seconds:
            self.cache = SheetsCache(player_row_map=self._load_player_row_map(), last_loaded=now)

        return self.cache.player_row_map.get(str(player_id))

def upsert_players_batch(self, players: List[dict]):
        updates = []

        for p in players:
            pid = str(p["player_id"])
            row = self.get_player_row(pid)

            if not row:
                continue

            wins = int(p.get("wins", 0) or 0)
            losses = int(p.get("losses", 0) or 0)
            wr = compute_wr_percent(wins, losses)

            row_values = [
                p.get("game_name", ""),
                p.get("tag_id", ""),
                p.get("tier", ""),
                p.get("rank", ""),
                p.get("role", ""),
                wins,
                losses,
                p.get("manual_tier", ""),
                wr,
                p.get("toxicity_points", 0),
                p.get("mvp_count", 0),
            ]

            updates.append({
                "range": f"B{row}:L{row}",
                "values": [row_values]
            })

        if updates:
            self.players_ws.batch_update(updates)

def append_match_rows(self, match_rows: List[List]):
    if match_rows:
        self.matches_ws.append_rows(
            match_rows,
            value_input_option="USER_ENTERED"
        )