"""
Main script to run

This script initializes extensions and starts the bot
"""
import os
import sys

import interactions
from dotenv import load_dotenv

from config import DEBUG, DEV_GUILD
from src import logutil

load_dotenv()

# Configure logging for this main.py handler
logger = logutil.init_logger("main.py")
logger.debug(
    "Debug mode is %s; This is not a warning, \
just an indicator. You may safely ignore",
    DEBUG,
)


if not os.environ.get("TOKEN"):
    logger.critical("TOKEN variable not set. Cannot continue")
    sys.exit(1)

client = interactions.Client(
    token=os.environ.get("TOKEN"),
    intents=interactions.Intents.MESSAGE_CONTENT | interactions.Intents.GUILD_MESSAGES,
    activity=interactions.Activity(
        name=".gg/mikuscafe", type=interactions.ActivityType.WATCHING
    ),
    debug_scope=DEV_GUILD,
    delete_unused_application_cmds = True,
)


@interactions.listen()
async def on_startup():
    """Called when the bot starts"""
    logger.info(f"Logged in as {client.user}")


# get all python files in "extensions" folder
extensions = [
    f"extensions.{f[:-3]}"
    for f in os.listdir("extensions")
    if f.endswith(".py") and not f.startswith("_")
]
for extension in extensions:
    try:
        client.load_extension(extension)
        logger.info(f"Loaded extension {extension}")
    except interactions.errors.ExtensionLoadException as e:
        logger.exception(f"Failed to load extension {extension}.", exc_info=e)


@interactions.slash_command(
    name="reload",
    description="Reloads econ extension",
)
async def reload_extension(ctx: interactions.SlashContext):
    client.reload_extension("extensions.economy")
    client.reload_extension("extensions.help")
    logger.info("extension.economy reloaded")
    logger.info("extensions.help reloaded")
    await ctx.send("`extension.economy` reloaded\n`extensions.help` reloaded </help:1372399261097918597>")

client.start()
