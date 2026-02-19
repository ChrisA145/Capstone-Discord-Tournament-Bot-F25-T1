
import discord
from discord.ext import commands
import asyncio
from config import settings
from discord.ext.commands import errors
from model.dbc_model import Tournament_DB, Player, Game
from common.database_connection import tournament_dbc
from common.cached_details import Details_Cached
import warnings
warnings.filterwarnings("ignore", message="'audioop' is deprecated")
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from sheet_sync import SheetSync   # adjust path if it's in /common or /utils


'''
we use bot.start(): 
    to start bot asynchronously
    we have a chance to customize event loop to increase the performance
    flexibility because of we can set up custom logic or tasks before or after the botstarts running
'''

logger = settings.logging.getLogger("discord")

async def main():
    logger.info("start bot")

    intents = discord.Intents.default()
    intents.members = True  # Make sure to enable the intent to access members' information.
    intents.message_content = True


    sys_client = commands.Bot(command_prefix="$", intents=intents)

    try:
        # Initialize Google Sheets sync ONCE
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            "service_account.json.json",  # <- path to your service account json
            scope
        )
        gc = gspread.authorize(creds)

        
        sys_client.sheet_sync = SheetSync(gc, settings.GOOGLE_SHEET_NAME)
    except Exception as e:
            sys_client.sheet_sync = None
            logger.error(f"Failed to initialize Google Sheets sync: {e}")
    
    

    # Add a flag to track bot initialization state
    sys_client.is_fully_initialized = False

    # Initialize the database and create tables
    db = Tournament_DB()
    Player.createTable(db)
    Game.createTable(db)
    
    # Import and create Matches, MVP_Votes, and Player_game_info tables
    from model.dbc_model import Matches, MVP_Votes, Player_game_info
    Matches.createTable(db)
    MVP_Votes.createTable(db)
    Player_game_info.createTable(db)
    
    # Add a command error handler for app commands
    @sys_client.tree.error
    async def on_app_command_error(interaction, error):
        if not sys_client.is_fully_initialized:
            try:
                # If bot isn't fully initialized, inform the user
                await interaction.response.send_message(
                    "⏳ Bot is still initializing. Please wait about 30 seconds and try again.",
                    ephemeral=True
                )
                return
            except Exception:
                # If we can't respond to the interaction, it's likely already timed out
                pass
                
        # Standard error handling
        logger.error(f"Command error: {error}")
        try:
            await interaction.response.send_message(
                "An error occurred while executing the command. Please try again in a moment.",
                ephemeral=True
            )
        except Exception:
            pass


    @sys_client.event
    async def on_ready():
        logger.info(f"Logged into server as {sys_client.user}")
        logger.info("Bot is starting initialization...")

        start_time = asyncio.get_event_loop().time()
        
        try:
            # Create a channels and save cached created channels on all servers the bot is running
            for guild in sys_client.guilds:
                logger.info(f"Initializing guild: {guild.id} ({guild.name})")
                
                # Log available roles in the server to help with debugging
                logger.info(f"Available roles in guild {guild.name}:")
                for role in guild.roles:
                    logger.info(f"  - Role: {role.name} (ID: {role.id})")
                    
                await Details_Cached.channels_for_tournament(ch_config=settings.CHANNEL_CONFIG, guild=guild)

            # Load the cogs (controllers)
            for cmd_file in settings.controller_dir.glob("*.py"):
                if cmd_file.name != "__init__.py" and cmd_file.name != "signup_shared_logic.py":
                    try:
                        await sys_client.load_extension(f"controller.{cmd_file.stem}")
                        logger.info(f"Loaded controller: {cmd_file.stem}")
                    except errors.ExtensionAlreadyLoaded:
                        logger.info(f"{cmd_file.stem} command is already loaded")
                    except Exception as ex:
                        logger.error(f"Error loading {cmd_file.stem} command: {ex}")
            
            guild = sys_client.get_guild(settings.GUILD_ID)

            # Copy the global slash commands to the specific guild
            sys_client.tree.copy_global_to(guild=guild)
            await sys_client.tree.sync(guild=guild)
            
            # Mark initialization as complete
            sys_client.is_fully_initialized = True
            
            # Calculate and log initialization time
            end_time = asyncio.get_event_loop().time()
            init_time = end_time - start_time
            logger.info(f"Bot fully initialized in {init_time:.2f} seconds!")
            
        except Exception as ex:
            logger.error(f"Error during initialization: {ex}")
            # Even if there's an error, mark as initialized so commands can work
            sys_client.is_fully_initialized = True


    #error handling
    @sys_client.event
    async def on_command_error(ctx, error):
        if isinstance(error, errors.ArgumentParsingError):
            await ctx.send("there is parsing error")
        if isinstance(error, errors.CommandNotFound):
            await ctx.send("Invalid command from global error handler")
        elif isinstance(error, errors.MissingRequiredArgument):
            await ctx.send("Please pass the required arguments from global error handler")
        elif isinstance(error, errors.BadArgument):
            await ctx.send("Please pass the correct arguments from global error handler")
        elif isinstance(error, errors.CommandOnCooldown):
            await ctx.send("This command is on cooldown, please try again later from global error handler")
        else:
            await ctx.send("Something went wrong, from global error handler")
    
    # Run the bot with your token
    try:
        await sys_client.start(settings.DISCORD_API_SECRET, reconnect=True)
    finally:
        await sys_client.close()

if __name__ == "__main__":
    asyncio.run(main())