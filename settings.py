import os
import redis

if not os.getenv("DISCORD_BOT_TOKEN"):
    from dotenv import load_dotenv
    load_dotenv()


# The prefix that will be used to parse commands.
# It doesn't have to be a single character!
COMMAND_PREFIX = os.getenv("COMMAND_PREFIX")

# The bot token. Keep this secret!
BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# The now playing game. Set this to anything false-y ("", None) to disable it
NOW_PLAYING = COMMAND_PREFIX + "commands"

# Base directory. Feel free to use it if you want.
BASE_DIR = os.path.dirname(os.path.realpath(__file__))


REDIS_URL = os.getenv('REDIS_URL')
redis = redis.from_url(REDIS_URL)
