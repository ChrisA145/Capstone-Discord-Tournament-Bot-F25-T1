# Export/Import Player Data with Google Sheets

This document provides instructions on how to set up and use the Export/Import functionality for player data between the KSU Esports Tournament database and Google Sheets.

## Prerequisites

1. Google Cloud Platform account with Google Sheets API enabled
2. Service account with appropriate permissions
3. A Google Sheet created for import/export operations

## Configuration

Add the following environment variables to your `.env` file:

```
# Google Sheets configuration
GOOGLE_SHEET_ID=your_google_sheet_id
LOL_service_path=/path/to/your/service_account_credentials.json
CELL_RANGE=Sheet1
```

Where:
- `GOOGLE_SHEET_ID`: The ID of your Google Sheet (found in the URL)
- `LOL_service_path`: Path to your service account credentials JSON file
- `CELL_RANGE`: Default sheet name for import operations

## Usage

### Export Player Data

This command exports all player information to a Google Sheet.

1. Execute the Discord slash command:
```
/export_players
```

This will:
- Create a new sheet with today's date (format: `players_MMDDYYYY`)
- Export all player data from the database
- Return a link to the Google Sheet

### Import Player Data

This command imports player data from a Google Sheet into the database.

1. Prepare your Google Sheet with the appropriate headers matching the database columns
2. Execute the Discord slash command:
```
/import_players [sheet_name]
```

Where `sheet_name` is optional. If not provided, it will use the default value from your `.env` file.

## Data Format

### Required Column Format

The import functionality will match columns in your Google Sheet with database fields. At minimum, these columns are required:

- `player_id`: Discord user ID (required)
- Other player columns: Any columns that match the `player` table in the database
- Game info columns: Any columns that match the `playerGameDetail` table

### Player Behavior Data

The export/import system now includes player behavior tracking data:

- `toxicity_points`: Number of recorded toxicity incidents for a player
- `mvp_count`: How many times a player has been voted MVP

Administrators can use this data to:
- Track player behavior across tournaments
- Identify players with recurring toxicity issues
- Recognize consistently positive players with high MVP counts

### How It Works

The import process:
1. Reads headers from the Google Sheet
2. Matches headers with database columns
3. For each row:
   - Updates or inserts player information
   - Updates or inserts player game details

## Permissions

Both import and export commands require administrator permissions in the Discord server.

## Troubleshooting

- Verify your Google API credentials are correctly set up
- Check that your Google Sheet ID is correct
- Ensure your sheet has proper headers that match database columns
- If rows aren't importing, verify the `player_id` column exists and contains valid Discord IDs