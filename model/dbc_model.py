# import peewee
# from common.database_connection import tournament_dbc
from datetime import datetime
import os
from config import settings
import sqlite3
import json

logger = settings.logging.getLogger("discord")

class Tournament_DB:
    def __init__(self, db_name=settings.DATABASE_NAME):
        self.db_name = db_name
        self.connection = None
        self.cursor = None
        self.db_connect()

    #connection to DB
    #The default out put of sqlit3 is a list of tubles
    #Inorder to get list of dictionary data format, we use row_factory
    def db_connect(self):
        db_path = os.path.abspath(self.db_name)
        logger.info(f"[DB] Opening SQLite DB at: {db_path}")
        self.connection = sqlite3.connect(self.db_name)
        # self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()

    def close_db(self):
        if self.connection:
            self.connection.commit()
            self.connection.close()
    
    def calculate_manual_tier(self, tier, rank):
        """Calculate a manual tier value (0-10) based on tier and rank"""
        # Base tier values mapped to 0-10 scale 
        tier_values = {
            "iron": 0,
            "bronze": 1,
            "silver": 3,
            "gold": 5,
            "platinum": 6.5,
            "emerald": 7.5,
            "diamond": 8.5,
            "master": 9.0,
            "grandmaster": 9.5,
            "challenger": 10.0,
            "default": 0
        }
        
        # Rank adjustments (divisions within tier)
        rank_adjustments = {
            "IV": 0.0,
            "III": 0.25,
            "II": 0.5,
            "I": 0.75
        }
        
        # Get base tier value
        tier_value = tier_values.get(tier.lower(), tier_values["default"])
        
        # Add rank adjustment
        if rank in rank_adjustments:
            # For tiers below master, add the rank adjustment
            if tier.lower() not in ["master", "grandmaster", "challenger"]:
                tier_value += rank_adjustments[rank]
        
        return round(tier_value, 2)

class Player(Tournament_DB):
    
    def createTable(self):
        player_table_query = """
            create table if not exists player (
            user_id bigint PRIMARY KEY,
            game_name text not null,
            game_id text,
            tag_id text text not null,
            isAdmin integer not null default 0,
            mvp_count integer not null default 0,
            toxicity_points integer not null default 0,
            last_modified text default (datetime('now'))
        )
        """
        self.cursor.execute(player_table_query)
        self.connection.commit()
        
    @staticmethod
    def metadata(db):
        """Get metadata about the player table columns"""
        try:
            db.cursor.execute("PRAGMA table_info(player)")
            return db.cursor.fetchall()
        except Exception as ex:
            logger.error(f"Error getting player metadata: {ex}")
            return []
            
    @staticmethod
    def generalplayerQuery(db, query, params):
        """Execute a general query on the player table"""
        try:
            db.cursor.execute(query, params)
            db.connection.commit()
            return True
        except Exception as ex:
            logger.error(f"Error executing player query: {ex}")
            return False

    def register(self, interaction, gamename, tagid):
        register_query = "insert into player(user_id, game_name, tag_id) values(?, ?, ?)"

        try:
            uniq_user_id = interaction.user.id
            if uniq_user_id:
                self.cursor.execute(register_query, (uniq_user_id, gamename, tagid))
                self.connection.commit()
            else:
                logger.error(f"Registration ahs failed because of Non user id")
        except Exception as ex:
            logger.error(f"Registration has failed with error {ex}")

    def fetch(self, interaction):
        query = "select * from player where user_id = ?"
        try:
            uniq_user_id = interaction.user.id
            if uniq_user_id:
                value = (uniq_user_id,)
                self.cursor.execute(query, value)
                return self.cursor.fetchone()
            else:
                logger.error(f"fetch ahs failed because of Non user id")
        except Exception as ex:
            logger.error(f"fetch has failed with error {ex}")
    
    def fetch_by_id(self, user_id):
        query = "select * from player where user_id = ?"
        try:
            value = (user_id,)
            self.cursor.execute(query, value)
            return self.cursor.fetchone()
        except Exception as ex:
            logger.error(f"fetch_by_id has failed with error {ex}")

    def update_details(self, user_id, player_rank):
        register_query = """
            update player
            set rank = ?
            where user_id = ?
        """

        try:
            self.cursor.execute(register_query, (player_rank, user_id))
            self.connection.commit()
            
        except Exception as ex:
            logger.error(f"update player details has failed with error {ex}")

    def isAcountExist(self, interaction):
        query = "select * from player where user_id = ?"
        try:
            uniq_user_id = interaction.user.id
            if uniq_user_id:
                value = (uniq_user_id,)
                self.cursor.execute(query, value)
                result = self.cursor.fetchone()

                return result is not None
            else:
                logger.error(f"is account exsit failed because of Non user id")
                return False
        except Exception as ex:
            logger.error(f"is account exsit  failed with error {ex}")

    def isMemberExist(self, member_id):
        query = "select * from player where user_id = ?"
        try:
            value = (member_id,)
            self.cursor.execute(query, value)
            result = self.cursor.fetchone()

            return result is not None
        except Exception as ex:
            logger.error(f"isMemberExist has failed with error {ex}")

    def get_all_player(self):
        query = "select user_id, game_name, tag_id from player"
        try:
            self.cursor.execute(query)
            return self.cursor.fetchall()
        except Exception as ex:
            logger.error(f"get_all_player has failed with error {ex}")

    def remove_player(self, member_id):
        query = "delete from player where user_id = ?"
        try:
            value = (member_id,)
            self.cursor.execute(query, value)
            self.connection.commit()
        except Exception as ex:
            logger.error(f"unable to delete a user_id {member_id} from db with error {ex}")
            
    def increment_mvp_count(self, player_id):
        """Increment the MVP count for a player"""
        try:
            # Get current MVP count
            query = "SELECT mvp_count FROM player WHERE user_id = ?"
            self.cursor.execute(query, (player_id,))
            result = self.cursor.fetchone()
            
            if result:
                current_count = result[0] if result[0] is not None else 0
                new_count = current_count + 1
                
                # Update the MVP count
                update_query = "UPDATE player SET mvp_count = ? WHERE user_id = ?"
                self.cursor.execute(update_query, (new_count, player_id))
                self.connection.commit()
                return new_count
            return None
        except Exception as ex:
            logger.error(f"increment_mvp_count failed with error {ex}")
            return None
            
    def get_mvp_count(self, player_id):
        """Get the current MVP count for a player"""
        try:
            query = "SELECT mvp_count FROM player WHERE user_id = ?"
            self.cursor.execute(query, (player_id,))
            result = self.cursor.fetchone()
            
            if result:
                return result[0] if result[0] is not None else 0
            return 0
        except Exception as ex:
            logger.error(f"get_mvp_count failed with error {ex}")
            return 0
            
    def add_toxicity_point(self, player_id):
        """Add a toxicity point to a player"""
        try:
            # Get current toxicity points
            query = "SELECT toxicity_points FROM player WHERE user_id = ?"
            self.cursor.execute(query, (player_id,))
            result = self.cursor.fetchone()
            
            if result:
                current_points = result[0] if result[0] is not None else 0
                new_points = current_points + 1
                
                # Update the toxicity points
                update_query = "UPDATE player SET toxicity_points = ? WHERE user_id = ?"
                self.cursor.execute(update_query, (new_points, player_id))
                self.connection.commit()
                return new_points
            return None
        except Exception as ex:
            logger.error(f"add_toxicity_point failed with error {ex}")
            return None
            
    def get_toxicity_points(self, player_id):
        """Get the current toxicity points for a player"""
        try:
            query = "SELECT toxicity_points FROM player WHERE user_id = ?"
            self.cursor.execute(query, (player_id,))
            result = self.cursor.fetchone()
            
            if result:
                return result[0] if result[0] is not None else 0
            return 0
        except Exception as ex:
            logger.error(f"get_toxicity_points failed with error {ex}")
            return 0
            
    def find_player_by_name(self, player_name):
        """Find a player by their game name"""
        try:
            query = "SELECT user_id FROM player WHERE LOWER(game_name) = ?"
            self.cursor.execute(query, (player_name.lower(),))
            result = self.cursor.fetchone()
            
            if result:
                return result[0]
            return None
        except Exception as ex:
            logger.error(f"find_player_by_name failed with error {ex}")
            return None

class Game(Tournament_DB):
    
    def createTable(self):

        game_table_query = """
            CREATE TABLE IF NOT EXISTS game (
            user_id bigint not null,
            game_name text not null,
            tier text,
            rank text,
            role text,
            wins integer,
            losses integer,
            manual_tier float DEFAULT NULL,
            wr float generated always as (wins * 1.0 / (wins + losses)) stored,
            game_date text default (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES player (user_id) ON DELETE CASCADE,
            FOREIGN KEY (game_name) REFERENCES player (game_name) ON DELETE CASCADE
        )
        """
        self.cursor.execute(game_table_query)
        self.connection.commit()

    def update_pref(self, interaction, pref):
        pref = json.dumps(pref)
        try:
            uniq_user_id = interaction.user.id
            if uniq_user_id:
                # Get player's game_name from the player table
                self.cursor.execute("SELECT game_name FROM player WHERE user_id = ?", (uniq_user_id,))
                player_data = self.cursor.fetchone()
                
                if not player_data:
                    # If player not found, use a default game name
                    game_name = "League of Legends"
                else:
                    game_name = player_data[0]
                
                # Check if record already exists
                self.cursor.execute("SELECT COUNT(*) FROM game WHERE user_id = ?", (uniq_user_id,))
                exists = self.cursor.fetchone()[0] > 0
                
                if exists:
                    # Update existing record
                    update_query = "UPDATE game SET role = ? WHERE user_id = ?"
                    self.cursor.execute(update_query, (pref, uniq_user_id))
                else:
                    # Insert new record
                    insert_query = "INSERT INTO game(user_id, game_name, role) VALUES(?, ?, ?)"
                    self.cursor.execute(insert_query, (uniq_user_id, game_name, pref))
                
                self.connection.commit()
            else:
                logger.error(f"update_pref has failed because of Non user id")
        except Exception as ex:
            logger.error(f"update_pref has failed with error {ex}")

    def update_role(self, interaction, role):
        register_query = "insert into game(user_id, game_name, role) values(?, ?, ?)"
        role = json.dumps(role)
        try:
            uniq_user_id = interaction.user.id
            if uniq_user_id:
                # Get player's game_name from the player table
                self.cursor.execute("SELECT game_name FROM player WHERE user_id = ?", (uniq_user_id,))
                player_data = self.cursor.fetchone()
                
                if not player_data:
                    # If player not found, use a default game name
                    game_name = "League of Legends"
                else:
                    game_name = player_data[0]
                
                self.cursor.execute(register_query, (uniq_user_id, game_name, role))
                self.connection.commit()
            else:
                logger.error(f"update_role has failed because of Non user id")
        except Exception as ex:
            logger.error(f"update_role has failed with error {ex}")

    def update_player_API_info(self, player_id, tier, rank, wins, losses):
        # Calculate manual tier value automatically based on tier and rank
        manual_tier = self.calculate_manual_tier(tier, rank)
        
        try:
            # First, fetch the player's game_name from the player table
            self.cursor.execute("SELECT game_name FROM player WHERE user_id = ?", (player_id,))
            player_data = self.cursor.fetchone()
            
            if player_data and player_data[0]:
                game_name = player_data[0]
                
                # Try to update existing entry first
                update_query = """
                    UPDATE game 
                    SET tier = ?, rank = ?, wins = ?, losses = ?, manual_tier = ?
                    WHERE user_id = ? AND game_date = (
                        SELECT MAX(game_date) FROM game WHERE user_id = ?
                    )
                """
                self.cursor.execute(update_query, (tier, rank, wins, losses, manual_tier, player_id, player_id))
                
                # If no rows were updated, insert a new record
                if self.cursor.rowcount == 0:
                    register_query = """
                        INSERT INTO Game(user_id, game_name, tier, rank, wins, losses, manual_tier) 
                        VALUES(?, ?, ?, ?, ?, ?, ?)
                    """
                    self.cursor.execute(register_query, (player_id, game_name, tier, rank, wins, losses, manual_tier))
                
                self.connection.commit()
            else:
                logger.error(f"update_player_API_info could not find game_name for user_id {player_id}")
            
        except Exception as ex:
            logger.error(f"update_player_API_info has failed with error {ex}")
    
    # This function is now defined in the Tournament_DB class
    
    def get_manual_tier(self, player_id):
        """Get a player's manual tier value"""
        query = """
            SELECT manual_tier, tier, rank
            FROM game
            WHERE user_id = ?
            ORDER BY game_date DESC
            LIMIT 1
        """
        
        try:
            self.cursor.execute(query, (player_id,))
            result = self.cursor.fetchone()
            
            if result:
                manual_tier, tier, rank = result
                
                # If manual_tier is None, calculate it based on tier and rank
                if manual_tier is None and tier:
                    calculated_value = self.calculate_manual_tier(tier, rank)
                    self.update_manual_tier(player_id, calculated_value)
                    return calculated_value
                    
                return manual_tier
                
            return None
        except Exception as ex:
            logger.error(f"get_manual_tier failed with error {ex}")
            return None
    
    def update_manual_tier(self, player_id, manual_tier):
        """Update a player's manual tier value directly"""
        # Check if player has a game record
        query = "SELECT COUNT(*) FROM game WHERE user_id = ?"
        
        try:
            self.cursor.execute(query, (player_id,))
            count = self.cursor.fetchone()[0]
            
            if count > 0:
                # Update existing record with the manual tier
                update_query = """
                    UPDATE game 
                    SET manual_tier = ?
                    WHERE user_id = ? AND game_date = (
                        SELECT MAX(game_date) FROM game WHERE user_id = ?
                    )
                """
                self.cursor.execute(update_query, (manual_tier, player_id, player_id))
                self.connection.commit()
                return True
            else:
                # Cannot set manual tier if no game record exists
                return False
                
        except Exception as ex:
            logger.error(f"update_manual_tier failed with error {ex}")
            return False
            
    def update_player_tier(self, player_id, tier, rank):
        """Update a player's tier and rank in the Game table"""
        # First check if the player already has a game entry
        query = "SELECT COUNT(*) FROM game WHERE user_id = ?"
        
        try:
            self.cursor.execute(query, (player_id,))
            count = self.cursor.fetchone()[0]
            
            if count > 0:
                # Update existing record with the most recent game_date
                update_query = """
                    UPDATE game 
                    SET tier = ?, rank = ?
                    WHERE user_id = ? AND game_date = (
                        SELECT MAX(game_date) FROM game WHERE user_id = ?
                    )
                """
                self.cursor.execute(update_query, (tier, rank, player_id, player_id))
            else:
                # Create a new entry
                insert_query = "INSERT INTO game(user_id, tier, rank) VALUES(?, ?, ?)"
                self.cursor.execute(insert_query, (player_id, tier, rank))
                
            self.connection.commit()
            return True
        except Exception as ex:
            logger.error(f"update_player_tier has failed with error {ex}")
            return False

    def fetchGameDetails(self):
        query = "select user_id, game_name, tier, rank, role, wr from Game"
        try:
            self.cursor.execute(query)
            return self.cursor.fetchall()
        except Exception as ex:
            logger.error(f"fetchGameDetails has failed with error {ex}")
    
class Matches(Tournament_DB):
    
    def createTable(self):
        # First, create a table with a custom field for match_num that we control
        game_table_query = """
            CREATE TABLE IF NOT EXISTS Matches (
            match_id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_num INTEGER NOT NULL,  -- This field will store our sequential match numbers
            user_id bigint,
            game_name text,
            win text,
            loss text,
            teamUp text,
            teamId text,
            date_played date,
            FOREIGN KEY (user_id) REFERENCES player (user_id) ON DELETE CASCADE,
            FOREIGN KEY (game_name) REFERENCES player (game_name) ON DELETE CASCADE
        )
        """
        self.cursor.execute(game_table_query)
        self.connection.commit()
        
        # Create a sequence counter table if it doesn't exist
        counter_table_query = """
            CREATE TABLE IF NOT EXISTS Counters (
            name TEXT PRIMARY KEY,
            value INTEGER NOT NULL
        )
        """
        self.cursor.execute(counter_table_query)
        
        # Initialize match counter if not exists
        self.cursor.execute("INSERT OR IGNORE INTO Counters (name, value) VALUES ('match_counter', 0)")
        self.connection.commit()
        
    def get_next_match_id(self):
        """Get the next sequential match ID (1, 2, 3, etc.) for match_1, match_2, match_3"""
        # First try to get it from the database properly
        try:
            # Separate the operations to reduce time inside transaction
            # First get the highest ID currently in use
            highest_match = 0
            try:
                self.cursor.execute("SELECT MAX(CAST(REPLACE(teamId, 'match_', '') AS INTEGER)) FROM Matches WHERE teamId LIKE 'match_%'")
                result = self.cursor.fetchone()
                if result and result[0] is not None:
                    highest_match = result[0]
            except Exception as ex:
                logger.error(f"Error getting highest match ID: {ex}")
                # Continue with highest_match = 0
            
            # Then get the current counter value
            counter_value = 0
            try:
                self.cursor.execute("SELECT value FROM Counters WHERE name = 'match_counter'")
                result = self.cursor.fetchone()
                if result and result[0] is not None:
                    counter_value = result[0]
            except Exception as ex:
                logger.error(f"Error getting counter value: {ex}")
                # Continue with counter_value = 0
            
            # Use the higher of the two values plus 1
            next_id = max(counter_value, highest_match) + 1
            
            # Now update the counter in a short, specific transaction
            try:
                with self.connection:
                    self.cursor.execute("UPDATE Counters SET value = ? WHERE name = 'match_counter'", (next_id,))
            except Exception as ex:
                logger.error(f"Error updating counter: {ex}")
                # We'll still use the calculated next_id even if update fails
            
            logger.info(f"Generated match ID: match_{next_id}")
            return next_id
                
        except Exception as ex:
            logger.error(f"get_next_match_id failed with error {ex}")
            
            # As a fallback, calculate next ID manually by checking existing match IDs
            # This is more reliable than returning a random number
            try:
                self.cursor.execute("SELECT teamId FROM Matches WHERE teamId LIKE 'match_%'")
                matches = self.cursor.fetchall()
                if matches:
                    # Extract numbers from match_X format and find max
                    existing_ids = []
                    for match in matches:
                        if match and match[0]:
                            try:
                                id_str = match[0].replace('match_', '')
                                if id_str.isdigit():
                                    existing_ids.append(int(id_str))
                            except:
                                pass
                    
                    next_id = max(existing_ids) + 1 if existing_ids else 1
                    logger.info(f"Fallback generated match ID: match_{next_id}")
                    return next_id
            except Exception as inner_ex:
                logger.error(f"Fallback match ID calculation failed: {inner_ex}")
            
            # If all else fails, start from 1
            logger.info("Using default match ID: match_1")
            return 1
        
class Player_game_info(Tournament_DB):
    """
    Class for managing player game information for export/import functionality
    """
    
    @staticmethod
    def createTable(db):
        """Create the playerGameDetail table if it doesn't exist"""
        player_game_detail_query = """
            CREATE TABLE IF NOT EXISTS playerGameDetail (
            player_id bigint PRIMARY KEY,
            game_name text,
            tag_id text,
            tier text,
            rank text,
            role text,
            wins integer,
            losses integer,
            manual_tier float,
            wr float,
            toxicity_points integer not null default 0,
            mvp_count integer not null default 0,
            FOREIGN KEY (player_id) REFERENCES player (user_id) ON DELETE CASCADE
        )
        """
        db.cursor.execute(player_game_detail_query)
        db.connection.commit()
    
    @staticmethod
    def exportToGoogleSheet(db):
        """Export player data to Google Sheets format"""
        try:
            # Combine player and game data, including toxicity points and MVP count
            db.cursor.execute("""
                SELECT p.user_id as player_id, p.game_name, p.tag_id, g.tier, g.rank, g.role, 
                       g.wins, g.losses, g.manual_tier, g.wr, p.toxicity_points, p.mvp_count
                FROM player p
                LEFT JOIN (
                    SELECT user_id, tier, rank, role, manual_tier, wins, losses, wr, MAX(game_date) as max_date
                    FROM game
                    GROUP BY user_id
                ) g ON p.user_id = g.user_id
                ORDER BY p.game_name
            """)
            
            # Create header row
            header = ["player_id", "game_name", "tag_id", "tier", "rank", "role", 
                      "wins", "losses", "manual_tier", "wr", "toxicity_points", "mvp_count"]
            
            # Fetch all player data
            players_data = db.cursor.fetchall()
            
            return header, players_data
        except Exception as ex:
            logger.error(f"Error exporting player data: {ex}")
            return [], []
    
    @staticmethod
    def metadata(db):
        """Get metadata about the playerGameDetail table columns"""
        try:
            # First ensure the table exists
            player_game_detail_query = """
                CREATE TABLE IF NOT EXISTS playerGameDetail (
                player_id bigint PRIMARY KEY,
                game_name text,
                tag_id text,
                tier text,
                rank text,
                role text,
                wins integer,
                losses integer,
                manual_tier float,
                wr float,
                toxicity_points integer not null default 0,
                mvp_count integer not null default 0,
                FOREIGN KEY (player_id) REFERENCES player (user_id) ON DELETE CASCADE
            )
            """
            db.cursor.execute(player_game_detail_query)
            db.connection.commit()
            
            # Get column information
            db.cursor.execute("PRAGMA table_info(playerGameDetail)")
            return db.cursor.fetchall()
        except Exception as ex:
            logger.error(f"Error getting playerGameDetail metadata: {ex}")
            return []
    
    @staticmethod
    def isExistPlayerId(db, query, query_param):
        """Check if a player ID exists in the playerGameDetail table"""
        try:
            db.cursor.execute(query, query_param)
            result = db.cursor.fetchone()
            return result[0] > 0 if result else False
        except Exception as ex:
            logger.error(f"Error checking player existence: {ex}")
            return False
    
    @staticmethod
    def importToDb(db, query, values):
        """Import data to the database using the provided query and values"""
        try:
            db.cursor.execute(query, values)
            db.connection.commit()
            return True
        except Exception as ex:
            logger.error(f"Error importing player data: {ex}")
            return False

class MVP_Votes(Tournament_DB):
    
    def createTable(self):
        vote_table_query = """
            CREATE TABLE IF NOT EXISTS MVP_Votes (
            vote_id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_id text NOT NULL,
            voter_id bigint NOT NULL,
            player_id bigint NOT NULL,
            vote_date timestamp DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (voter_id) REFERENCES player (user_id) ON DELETE CASCADE,
            FOREIGN KEY (player_id) REFERENCES player (user_id) ON DELETE CASCADE
        )
        """
        self.cursor.execute(vote_table_query)
        self.connection.commit()
        
    def record_vote(self, match_id, voter_id, player_id):
        """Record an MVP vote"""
        try:
            # Check if voter has already voted in this match
            check_query = "SELECT COUNT(*) FROM MVP_Votes WHERE match_id = ? AND voter_id = ?"
            self.cursor.execute(check_query, (match_id, voter_id))
            count = self.cursor.fetchone()[0]
            
            if count > 0:
                # Voter has already voted, update their vote
                update_query = "UPDATE MVP_Votes SET player_id = ?, vote_date = CURRENT_TIMESTAMP WHERE match_id = ? AND voter_id = ?"
                self.cursor.execute(update_query, (player_id, match_id, voter_id))
            else:
                # New vote
                insert_query = "INSERT INTO MVP_Votes (match_id, voter_id, player_id) VALUES (?, ?, ?)"
                self.cursor.execute(insert_query, (match_id, voter_id, player_id))
                
            self.connection.commit()
            return True
        except Exception as ex:
            logger.error(f"record_vote failed with error {ex}")
            return False
            
    def get_vote_count(self, match_id):
        """Get vote counts for a specific match"""
        try:
            query = """
                SELECT player_id, COUNT(*) as vote_count 
                FROM MVP_Votes 
                WHERE match_id = ? 
                GROUP BY player_id 
                ORDER BY vote_count DESC
            """
            self.cursor.execute(query, (match_id,))
            return self.cursor.fetchall()
        except Exception as ex:
            logger.error(f"get_vote_count failed with error {ex}")
            return []
            
    def has_voted(self, match_id, voter_id):
        """Check if a user has already voted in a match"""
        try:
            query = "SELECT COUNT(*) FROM MVP_Votes WHERE match_id = ? AND voter_id = ?"
            self.cursor.execute(query, (match_id, voter_id))
            count = self.cursor.fetchone()[0]
            return count > 0
        except Exception as ex:
            logger.error(f"has_voted failed with error {ex}")
            return False
    
    def get_mvp_winner(self, match_id):
        """Get the player with the most votes (the MVP)"""
        try:
            # Get vote counts
            results = self.get_vote_count(match_id)
            
            if results and len(results) > 0:
                # Return player_id with most votes
                return results[0][0]
            return None
        except Exception as ex:
            logger.error(f"get_mvp_winner failed with error {ex}")
            return None
            
    def finalize_mvp_voting(self, match_id):
        """Determine the MVP and update their MVP count
        
        Args:
            match_id: The match ID to finalize
            
        Returns:
            Tuple of (player_id, player_name, new_mvp_count) if successful, 
            None otherwise
        """
        try:
            # Get the winner (player with most votes)
            winner_id = self.get_mvp_winner(match_id)
            
            if winner_id:
                # Get player DB
                player_db = Player(db_name=self.db_name)
                
                # Increment MVP count
                new_count = player_db.increment_mvp_count(winner_id)
                
                # Get player name
                self.cursor.execute(
                    "SELECT game_name FROM player WHERE user_id = ?",
                    (winner_id,)
                )
                name_result = self.cursor.fetchone()
                player_name = name_result[0] if name_result else "Unknown Player"
                
                # Mark this match as having a finalized MVP
                vote_counts = self.get_vote_count(match_id)
                vote_count = vote_counts[0][1] if vote_counts else 0
                
                return (winner_id, player_name, new_count, vote_count)
            return None
        except Exception as ex:
            logger.error(f"finalize_mvp_voting failed with error {ex}")
            return None

