import discord
from datetime import datetime
from discord import app_commands
from discord.ext import commands
import os
from config import settings
from model.dbc_model import Tournament_DB, Player, Player_game_info

# Import Google API libraries safely
try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    GOOGLE_APIS_AVAILABLE = True
except ImportError:
    GOOGLE_APIS_AVAILABLE = False

scopes = ['https://www.googleapis.com/auth/spreadsheets']
logger = settings.logging.getLogger("discord")

class Import_Export(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.google_apis_enabled = GOOGLE_APIS_AVAILABLE
        
        # Check if service account file exists
        if not os.path.exists(settings.LOL_service_path):
            self.google_apis_enabled = False
            logger.warning(f"Google Sheets service account file not found at {settings.LOL_service_path}")
        
        # Try to set up sheets service if everything is available
        if self.google_apis_enabled:
            try:
                self.spreadsheets_service = self.sheet_service()
                self.googleSheetId = settings.GOOGLE_SHEET_ID
            except Exception as e:
                self.google_apis_enabled = False
                logger.error(f"Failed to initialize Google Sheets API: {e}")
        else:
            logger.warning("Google API libraries not available, export/import functionality will be limited")

    '''A method to get the spreedsheet service
    '''
    def sheet_service(self):
        credentials = service_account.Credentials.from_service_account_file(
            filename=settings.LOL_service_path, scopes=scopes
        )
        serviceSheet = build('sheets', 'v4', credentials=credentials)

        spreadsheets_service = serviceSheet.spreadsheets()

        return spreadsheets_service
    
    #Method to check if a sheet exists, returns True/False
    def isSheetExists(self, sheet_name):
        spreadsheet = self.spreadsheets_service.get(spreadsheetId=self.googleSheetId).execute()
        sheets = spreadsheet.get('sheets', [])

        for sheet in sheets:
            if sheet['properties']['title'] == sheet_name:
                return True
        return False
    
    '''Method to create a sheet with the name passed in and a bool to clear the sheet if it already exists
        steps:
            Check if the sheet name already exist, 
                if not then create it 
                    Call the API to add a new sheet
                    Get the new sheet's ID from the response and return the value
                if exist then check if the clear parm is True to delete the data
    '''
    async def sheets_create(self, sheet_name, clear):
        if not self.isSheetExists(sheet_name):
            request_body = {'requests': [{'addSheet': {'properties': {'title': sheet_name}}}]}

            response = self.spreadsheets_service.batchUpdate(spreadsheetId=self.googleSheetId, body=request_body).execute()

            return response['replies'][0]['addSheet']['properties']['sheetId']
        
        elif clear:
            range_to_clear = f'{sheet_name}'

            request_body = {}
            self.spreadsheets_service.values().clear(spreadsheetId=self.googleSheetId,range=range_to_clear,body=request_body).execute()

        # Get the sheet ID from the sheet name by looping through each sheet until it matches
        spreadsheet = self.spreadsheets_service.get(spreadsheetId=self.googleSheetId).execute()
        sheets = spreadsheet.get('sheets', [])
        for sheet in sheets:
            if sheet['properties']['title'] == sheet_name:
                return sheet['properties']['sheetId']
    
    '''Method to export the points data from the database to the sheet
        steps:
            check if the sheet exists, if yes clear it out
            get playeres data based on model 'exportToGoogleSheet' then:
                Convert fetched data to a list of lists suitable for Google Sheets
                update into googlesheet
            defer the responce to make sure no time out error
    '''  
    @app_commands.command(name="export_players", description="Export all player information to Google Sheets")  
    @app_commands.describe(custom_name="Optional custom sheet name (default: timestamp-based name)")
    async def exportToGoogleSheet(self, interaction:discord.Interaction, custom_name: str = None):
        if interaction.user.guild_permissions.administrator:
            # Check if Google APIs are available
            if not self.google_apis_enabled:
                await interaction.response.send_message(
                    "⚠️ Google Sheets API is not properly configured. Please check server logs for details.",
                    ephemeral=True
                )
                return
                
            # Use custom name if provided, otherwise use timestamp format
            if custom_name:
                # Replace spaces with underscores for better sheet naming
                sheet_name = custom_name.replace(' ', '_')
            else:
                # Use a detailed timestamp format: date-day-year-hour-minute
                today = datetime.now()
                sheet_name = f"players_{str(today.strftime('%m-%d-%Y-%H-%M'))}"
            
            try:
                await interaction.response.defer()
                
                # Create or clear sheet
                try:
                    await self.sheets_create(sheet_name, True)
                except Exception as sheet_error:
                    logger.error(f"Error creating/clearing sheet: {sheet_error}")
                    await interaction.followup.send(
                        f"⚠️ Error preparing Google Sheet: {str(sheet_error)}",
                        ephemeral=True
                    )
                    return

                # Export player data
                db = Tournament_DB()
                header, list_of_playeres = Player_game_info.exportToGoogleSheet(db)
                db.close_db()
                
                if not list_of_playeres:
                    await interaction.followup.send("No player data found to export.", ephemeral=True)
                    return

                # Format data for Google Sheets
                data = [list(map(str, row)) for row in list_of_playeres]
                data.insert(0, header)

                # Define range and update sheet
                start_cell = 'A1'
                end_cell = f'{chr(ord("A") + len(data[0]) - 1)}{len(data)}'
                range_name = f'{sheet_name}!{start_cell}:{end_cell}'

                body = {'values': data}
                self.spreadsheets_service.values().update(
                    spreadsheetId=self.googleSheetId,
                    range=range_name,
                    valueInputOption='RAW',
                    body=body
                ).execute()
                
                # Create sheet URL and send success message
                sheet_url = f"https://docs.google.com/spreadsheets/d/{self.googleSheetId}/edit#gid=0"
                
                # More descriptive success message
                if custom_name:
                    message = f"✅ Player data exported to custom sheet: **{sheet_name}**"
                else:
                    message = f"✅ Player data exported with timestamp: **{sheet_name}**"
                    
                await interaction.followup.send(
                    f"{message}\n\n**Total Players Exported:** {len(list_of_playeres)}\n\n[View in Google Sheets]({sheet_url})"
                )

            except Exception as e:
                logger.error(f'Export error: {e}')
                await interaction.followup.send(
                    f"❌ Error exporting player data: {str(e)}",
                    ephemeral=True
                )
        else:
            await interaction.response.send_message(
                "Sorry, you don't have administrator permissions to use this command.",
                ephemeral=True
            )



    '''Method to import playeres data from googlesheet to db
        Steps:
            pass a sheet_name with the command or configure in .env, else it takes a defult name one 'sheet'
            get the headere and row data from sheet_name
            get colums name from 'playerGameDetail' table
            add player information to db accordingly
    '''
    @app_commands.command(name="import_players", description="Import player data from Google Sheets")
    @app_commands.describe(sheet_name="Name of the sheet to import data from (default from settings)")
    async def importFromGoogleSheet(self, interaction:discord.Interaction, sheet_name: str = None):
        if interaction.user.guild_permissions.administrator:
            # Check if Google APIs are available
            if not self.google_apis_enabled:
                await interaction.response.send_message(
                    "⚠️ Google Sheets API is not properly configured. Please check server logs for details.",
                    ephemeral=True
                )
                return
                
            # Use provided sheet_name or default from settings
            if not sheet_name:
                sheet_name = settings.CELL_RANGE
                
            try:
                await interaction.response.defer()
                
                # Fetch data from Google Sheet
                try:
                    sheet_data = self.spreadsheets_service.values().get(
                        spreadsheetId=self.googleSheetId, range=sheet_name
                    ).execute()
                    
                    values = sheet_data.get("values", [])
                    if not values:
                        await interaction.followup.send(
                            f"❌ No data found in the Google Sheet: {sheet_name}",
                            ephemeral=True
                        )
                        return
                        
                except Exception as sheet_error:
                    logger.error(f"Error fetching sheet data: {sheet_error}")
                    await interaction.followup.send(
                        f"❌ Error fetching data from Google Sheet: {str(sheet_error)}",
                        ephemeral=True
                    )
                    return

                # Process headers and rows
                headers = [header.strip() for header in values[0]]
                rows = values[1:]
                db = Tournament_DB()
                
                records_updated = 0
                records_created = 0

                # Get table columns for both tables
                table_columns = Player_game_info.metadata(db)
                table_columns = {row[1]: row[1] for row in table_columns}  
                valid_columns = [col for col in headers if col in table_columns]

                player_columns = Player.metadata(db)
                p_table_columns = {row[1]: row[1] for row in player_columns}
                p_valid_columns = [col for col in headers if col in p_table_columns]
                
                # Process each row
                for row in rows:
                    # If row is shorter than headers, extend it with None values
                    if len(row) < len(headers):
                        row = row + [None] * (len(headers) - len(row))
                        
                    # Convert row into {header: value} format
                    row_data = dict(zip(headers, row))
                    
                    values_to_insert = [row_data.get(col, None) for col in valid_columns]
                    p_values_to_insert = [row_data.get(col, None) for col in p_valid_columns]

                    if "player_id" in row_data:
                        # Update player table first
                        sql_query = f"""
                            INSERT INTO player ({', '.join(p_valid_columns)}) 
                            VALUES ({', '.join(['?' for _ in p_valid_columns])}) 
                            ON CONFLICT(player_id) DO UPDATE SET 
                            {', '.join([f"{col} = EXCLUDED.{col}" for col in p_valid_columns if col != 'player_id'])};
                        """
                        result = Player.generalplayerQuery(db, sql_query, p_values_to_insert)
                        
                        # Then update playerGameDetail table
                        column_names = ', '.join(valid_columns)
                        placeholders = ', '.join(['?' for _ in valid_columns])
                        query = "SELECT COUNT(*) FROM playerGameDetail WHERE player_id = ?"
                        query_params = (row_data["player_id"],)

                        isExistPlayerId = Player_game_info.isExistPlayerId(db, query=query, query_param=query_params)

                        if isExistPlayerId:
                            update_query = f"""
                                UPDATE playerGameDetail
                                SET {', '.join([f"{col} = ?" for col in valid_columns if col != 'player_id'])}
                                WHERE player_id = ?;
                            """
                            Player_game_info.importToDb(db, update_query, [row_data.get(col, None) for col in valid_columns if col != 'player_id'] + [row_data["player_id"]])
                            records_updated += 1
                        else:
                            insert_query = f"""
                                INSERT INTO playerGameDetail ({column_names}) 
                                VALUES ({placeholders});
                            """
                            Player_game_info.importToDb(db, insert_query, [row_data.get(col, None) for col in valid_columns])
                            records_created += 1

                db.close_db()
                
                # Success message with stats
                await interaction.followup.send(
                    f"✅ Import completed successfully!\n\n**Sheet:** {sheet_name}\n**Records processed:** {len(rows)}\n**Records created:** {records_created}\n**Records updated:** {records_updated}"
                )
                
            except Exception as ex:
                logger.error(f"Import error: {ex}")
                await interaction.followup.send(
                    f"❌ Error importing data: {str(ex)}",
                    ephemeral=True
                )
        else:
            await interaction.response.send_message(
                "Sorry, you don't have administrator permissions to use this command.",
                ephemeral=True
            )
        

async def setup(bot):
    await bot.add_cog(Import_Export(bot))