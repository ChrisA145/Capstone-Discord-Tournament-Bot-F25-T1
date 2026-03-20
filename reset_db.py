

import sqlite3





conn = sqlite3.connect("tournament.db")
cursor = conn.cursor()

cursor.execute("DELETE FROM MVP_Votes")
cursor.execute("DELETE FROM BracketMatches")
cursor.execute("DELETE FROM Brackets")
cursor.execute("DELETE FROM Matches")
cursor.execute("DELETE FROM game")
cursor.execute("DELETE FROM playerGameDetail")
cursor.execute("DELETE FROM player")
cursor.execute("UPDATE Counters SET value = 0 WHERE name = 'match_counter'")
cursor.execute("DELETE FROM sqlite_sequence WHERE name = 'Matches'")
cursor.execute("DELETE FROM sqlite_sequence WHERE name = 'MVP_Votes'")
cursor.execute("DELETE FROM sqlite_sequence WHERE name = 'BracketMatches'")

conn.commit()
conn.close()

print("✅ Database reset complete.")