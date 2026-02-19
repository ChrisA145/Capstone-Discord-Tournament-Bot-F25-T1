import sqlite3
import pandas as pd

# file is there but might be hidden
conn = sqlite3.connect('KSU_Tournament.db')

c = conn.cursor()

c.execute("""DROP TABLE IF EXISTS PlayerStats""")
c.execute("""DROP TABLE IF EXISTS PlayerTiers""")

# Should change the Role_Preference to Boolean for all types of roles
c.execute("""CREATE TABLE IF NOT EXISTS PlayerStats (
            [Discord_Username] text PRIMARY KEY,
            [Discord_ID] text,
            [Riot_ID] text,
            [Participation_Stats] integer,
            [Wins] real,
            [MVPs] integer,
            [Toxicity_Points] integer,
            [Games_Played] real,
            [Win_Rate] real,
            [Total_Points] integer,
            [Player_Tier] integer,
            [Player_Rank] text,
            [Role_Preference] text,
            CHECK ([Player_Tier] IN (1,2,3,4,5,6))
        )""")

c.execute("""CREATE TABLE IF NOT EXISTS PlayerTiers (
            [Discord_Username] text PRIMARY KEY,
            [Rank] text,
            [Roles_Preference] text,
            [Tier] text,
            CHECK ([Tier] IN (1,2,3,4,5,6))
        )""")

file_path = 'M:/Documents/Schools/Kennesaw State/Spring2025/SWE 7903/PlayerInfo.xlsx'


# Load Excel file
def import_excel_to_sqlite(table_name, column_mapping, sheet_keyword):
    # Load all sheet names
    xls = pd.ExcelFile(file_path)

    # Find the sheet name that contains the keyword
    sheet_name = next((sheet for sheet in xls.sheet_names if sheet_keyword in sheet), None)

    if not sheet_name:
        raise ValueError(f"No sheet found containing the keyword: {sheet_keyword}")

    # Read the matched sheet into a DataFrame
    df = pd.read_excel(xls, sheet_name=sheet_name)

    # Rename columns based on mapping
    df.rename(columns=column_mapping, inplace=True)

    # Get existing columns in the database table
    c.execute(f"PRAGMA table_info({table_name})")
    existing_columns = [row[1] for row in c.fetchall()]

    # Filter DataFrame to match existing columns
    df = df[[col for col in df.columns if col in existing_columns]]

    # Insert DataFrame into SQLite table
    df.to_sql(table_name, conn, if_exists='append', index=False)


columns = {
    'Players1': 'Discord_Username',
    'Discord ID': 'Discord_ID',
    'Participation': 'Participation_Stats',
    'Wins': 'Wins',
    'MVPs': 'MVPs',
    'Toxicity': 'Toxicity_Points',
    'Games Played': 'Games_Played',
    'Point Total': 'Total_Points'
}

columns2 = {
    'Players': 'Discord_Username',
    'Rank': 'Rank',
    'Roles Pref': 'Roles_Preference',
    'Tier': 'Tier'
}

import_excel_to_sqlite('PlayerStats', columns, 'Points')
import_excel_to_sqlite('PlayerTiers', columns2, 'Player Tiers')

c.execute("UPDATE PlayerStats "
          "SET Player_Tier ="
          "(SELECT Tier FROM PlayerTiers WHERE PlayerTiers.Discord_Username = PlayerStats.Discord_Username) "
          "WHERE EXISTS (SELECT 1 FROM PlayerTiers "
          "WHERE PlayerTiers.Discord_Username = PlayerStats.Discord_Username)")

c.execute("UPDATE PlayerStats "
          "SET Player_Rank ="
          "(SELECT Rank FROM PlayerTiers WHERE PlayerTiers.Discord_Username = PlayerStats.Discord_Username) "
          "WHERE EXISTS (SELECT 1 FROM PlayerTiers "
          "WHERE PlayerTiers.Discord_Username = PlayerStats.Discord_Username)")

c.execute("UPDATE PlayerStats "
          "SET Win_Rate = (Wins/Games_Played) ")

c.execute("SELECT * FROM PlayerStats WHERE [Player_Rank] = 'Diamond'")
# c.execute("SELECT * FROM PlayerStats")
print(c.fetchall())

conn.close()
