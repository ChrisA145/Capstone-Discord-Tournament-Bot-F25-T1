import os
import logging
from logging.config import dictConfig
import pathlib
import discord
from dotenv import load_dotenv
load_dotenv()

# Define directory paths first so we can use them elsewhere
# pathlib.Path(__file__) this is the current file where the code is present
File_Dir = pathlib.Path(__file__).parent # This will give the current directory path where the file is present
Base_Dir = File_Dir.parent
controller_dir = Base_Dir / "controller"

DISCORD_API_SECRET = os.getenv("DISCORD_APITOKEN")
GUILD_ID = int(os.getenv("DISCORD_GUILD"))
DATABASE_NAME = os.getenv("DATABASE_NAME", "tournament.db")
# FEEDBACK_CH = int(os.getenv("FEEDBACK_CH"))
FEEDBACK_CH = os.getenv("FEEDBACK_CH")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
CHANNEL_CONFIG = os.getenv("CHANNEL_CONFIG")
PLAYERES_CH = os.getenv("CHANNEL_PLAYER")
TOURNAMENT_CH = os.getenv("TOURNAMENT_CH")
PRIVATE_CH = os.getenv("PRIVATE_CH")
API_KEY = os.getenv("API_KEY")
API_URL = os.getenv("API_URL")
STOP_API_TASK = os.getenv("STOP_API_TASK")
START_API_TASK = os.getenv("START_API_TASK")

#for openAi matchmaking
OPEN_AI_KEY = os.getenv("OPEN_AI_KEY")
PROMPT = os.getenv("prompt")

# Google Sheets and API settings for export_import
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "default_sheet_id")
CELL_RANGE = os.getenv("CELL_RANGE", "Sheet1")  # Default sheet name if not specified
LOL_service_path = os.getenv("LOL_SERVICE_PATH", str(Base_Dir / "service_account.json"))


LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "[%(asctime)s] [%(levelname)s] [%(name)s] [%(module)s] [%(filename)s] [%(message)s]",
        },
        "verbose": {
            "format": "%(asctime)-3s - %(levelname)-3s - %(pathname)-3s -%(funcName)-3s : %(message)s",
        },
        "standard": {
            "format": "%(asctime)-3s:%(levelname)-3s:%(thread)d:%(threadName)-3s:%(message)-3s",
        }
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "default",
            "stream": "ext://sys.stdout",
        },
        "console2": {
            "level": "WARNING",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "level": "INFO",
            "formatter": "standard",
            "class": "logging.FileHandler",
            "filename": Base_Dir / "Log/info.log",
            "mode": "w",
        },
    },
    "loggers": {
        "bot": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "discord": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

dictConfig(LOGGING_CONFIG)