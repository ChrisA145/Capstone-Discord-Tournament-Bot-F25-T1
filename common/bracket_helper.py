from config import settings
from model.dbc_model import Matches

logger = settings.logging.getLogger("discord")


def create_4_team_bracket(db, bracket_id: str, teams: list[str]):
    """
    Create a 4-team single elimination bracket.

    Args:
        db: Tournament_DB instance
        bracket_id: unique bracket identifier
        teams: ordered list of 4 seeded team IDs
               Example: [seed1, seed2, seed3, seed4]

    Returns:
        dict with bracket_id and generated match codes
    """
    if len(teams) != 4:
        raise ValueError("4-team bracket requires exactly 4 teams")

    try:
        # Create bracket record
        db.cursor.execute("""
            INSERT INTO Brackets (bracket_id, total_teams, status)
            VALUES (?, ?, 'active')
        """, (bracket_id, 4))

        matches_db = Matches()
        matches_db.connection = db.connection
        matches_db.cursor = db.cursor

        semi1_code = f"match_{matches_db.get_next_match_id()}"
        semi2_code = f"match_{matches_db.get_next_match_id()}"
        final_code = f"match_{matches_db.get_next_match_id()}"

        # Final
        db.cursor.execute("""
            INSERT INTO BracketMatches (
                bracket_id, round_num, match_index,
                match_code, teamA_id, teamB_id,
                status, next_match_code, next_slot
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            bracket_id, 2, 1,
            final_code, None, None,
            'pending', None, None
        ))

        # Semi 1: seed 1 vs seed 4
        db.cursor.execute("""
            INSERT INTO BracketMatches (
                bracket_id, round_num, match_index,
                match_code, seed_a, seed_b,
                teamA_id, teamB_id,
                status, next_match_code, next_slot
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            bracket_id, 1, 1,
            semi1_code, 1, 4,
            teams[0], teams[3],
            'ready', final_code, 'A'
        ))

        # Semi 2: seed 2 vs seed 3
        db.cursor.execute("""
            INSERT INTO BracketMatches (
                bracket_id, round_num, match_index,
                match_code, seed_a, seed_b,
                teamA_id, teamB_id,
                status, next_match_code, next_slot
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            bracket_id, 1, 2,
            semi2_code, 2, 3,
            teams[1], teams[2],
            'ready', final_code, 'B'
        ))

        db.connection.commit()

        logger.info(
            f"Created 4-team bracket {bracket_id} with matches "
            f"{semi1_code}, {semi2_code}, {final_code}"
        )

        return {
            "bracket_id": bracket_id,
            "matches": [semi1_code, semi2_code, final_code]
        }

    except Exception as ex:
        db.connection.rollback()
        logger.error(f"create_4_team_bracket failed with error {ex}")
        raise

def resolve_bracket_team(db, bracket_team_id: str) -> list[dict]:
    """
    Resolves 'match_16_team1' → list of player dicts.
    Returns [] if slot is unfilled (future bracket match).
    """
    if not bracket_team_id:
        return []

    if bracket_team_id.endswith("_team1"):
        match_code = bracket_team_id[:-6]
        team_up = "team1"
    elif bracket_team_id.endswith("_team2"):
        match_code = bracket_team_id[:-6]
        team_up = "team2"
    else:
        raise ValueError(f"Invalid bracket_team_id format: '{bracket_team_id}'")

    cursor = db.cursor.execute(
        """
        SELECT p.*
        FROM Matches m
        JOIN player p ON m.user_id = p.user_id
        WHERE m.teamId = ? AND m.teamUp = ?
        """,
        (match_code, team_up)
    )
    rows = db.cursor.fetchall()
    return [dict(row) for row in rows]


def declare_tournament_winner(db, winner_team_id: str):
    """Called when the final match completes."""
    players = resolve_bracket_team(db, winner_team_id)
    # Log it, post to Discord, update player records, etc.
    print(f"🏆 Tournament winner: {winner_team_id}")
    print(f"   Players: {[p['user_id'] for p in players]}")

    # In your result-recording command/handler
