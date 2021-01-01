from events.base_event import BaseEvent
from utils import read_activity_log, save_activity_log, get_log
from settings import IS_DEV
from time import time
import discord

from datetime import datetime
from ilock import ILock


# Your friendly example event
# You can name this class as you like, but make sure to set BaseEvent
# as the parent class
class ExampleEvent(BaseEvent):

    def __init__(self):
        interval_minutes = 1  # Set the interval for this event
        super().__init__(interval_minutes)

    # Override the run() method
    # It will be called once every {interval_minutes} minutes
    async def run(self, client):
        for guild in client.guilds:
            print(guild)
            with ILock(str(guild.id)):
                activity_log = read_activity_log(guild.id)
                for member in guild.members:
                    if not member.bot:
                        if member.voice:
                            print(f"{member} está conectado. Progreso guardado.")
                            log = get_log(member.voice)
                            if log["type"] == "JOINED":
                                if activity_log[str(member)][-1]["type"] == "ONLINE":
                                    activity_log[str(
                                        member)][-1]["timestamp"] = time()
                                else:
                                    log["type"] = "ONLINE"
                                    activity_log[str(member)].append(log)
                save_activity_log(guild.id, activity_log)
