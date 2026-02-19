# Setting Up Google Sheets API for Import/Export

This guide provides step-by-step instructions to set up the Google Sheets API integration for the `/export_players` and `/import_players` commands in the KSU Esports Tournament bot.

## Prerequisites
- Google account
- Python packages: `google-auth`, `google-auth-oauthlib`, `google-auth-httplib2`, `google-api-python-client`

## Step 1: Install Required Python Packages
```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

## Step 2: Create a Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Log in with your Google account
3. Click "Create Project" at the top of the page
   - Enter a project name (e.g., "KSU Esports Tournament")
   - Click "Create"
4. Make sure your new project is selected in the top dropdown

## Step 3: Enable the Google Sheets API

1. From the Google Cloud Console dashboard, go to "APIs & Services" > "Library"
2. Search for "Google Sheets API"
3. Click on "Google Sheets API" in the results
4. Click "Enable"

## Step 4: Create a Service Account

1. Go to "APIs & Services" > "Credentials"
2. Click "Create credentials" and select "Service Account"
3. Enter a service account name (e.g., "tournament-bot")
4. Click "Create and Continue"
5. Under "Select a role", choose "Basic" > "Editor" (or a more restrictive role if desired)
6. Click "Continue"
7. Click "Done"

## Step 5: Create and Download Service Account Key

1. In the Service accounts list, find the one you just created
2. Click the three dots (⋮) in the "Actions" column
3. Select "Manage keys"
4. Click "Add Key" > "Create new key"
5. Select "JSON" format
6. Click "Create"
7. The key file will be automatically downloaded to your computer

## Step 6: Copy Service Account Key to Project

1. Rename the downloaded JSON file to `service_account.json`
2. Move the file to the root directory of your project (`/Users/parker/sppm/ksu_Esports_Tournament-/`)

## Step 7: Create a Google Sheet

1. Go to [Google Sheets](https://docs.google.com/spreadsheets)
2. Create a new blank spreadsheet
3. Rename it to something recognizable (e.g., "KSU Esports Tournament Data")
4. Copy the spreadsheet ID from the URL:
   - Example URL: `https://docs.google.com/spreadsheets/d/1234567890abcdefghijklmnopqrstuvwxyz/edit#gid=0`
   - The ID is the long string between `/d/` and `/edit`: `1234567890abcdefghijklmnopqrstuvwxyz`

## Step 8: Share the Spreadsheet with Service Account

1. Get the service account email from the service_account.json file (look for "client_email" field)
2. In your Google Sheet, click the "Share" button
3. Enter the service account email address
4. Make sure to give it "Editor" access
5. Uncheck "Notify people"
6. Click "Share"

## Step 9: Update Environment Variables

Add the following variables to your .env file:

```
GOOGLE_SHEET_ID=your_spreadsheet_id_here
CELL_RANGE=Sheet1
LOL_SERVICE_PATH=/Users/parker/sppm/ksu_Esports_Tournament-/service_account.json
```

## Step 10: Testing the Integration

1. Restart your bot
2. Run the `/export_players` command
3. Check the Google Sheet to see if data has been exported successfully
4. Make some changes in the sheet and try importing with `/import_players`

## Troubleshooting

- **API Error**: Make sure the Google Sheets API is enabled in your Google Cloud project
- **Authentication Error**: Verify that the service_account.json file is correctly formatted and accessible
- **Permission Error**: Ensure that the service account has Editor access to the spreadsheet
- **Spreadsheet ID Error**: Check that GOOGLE_SHEET_ID is correctly set to your spreadsheet's ID
- **Python Package Error**: Make sure all required packages are installed

For help with specific errors, check the bot's logs at `/Users/parker/sppm/ksu_Esports_Tournament-/Log/info.log`.