from events.base_event import BaseEvent
from utils import get_channel, get_activity_ranking, get_tier, TIERS
from settings import IS_DEV
import discord

from datetime import datetime


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
            ranking = get_activity_ranking(guild.id)
            for i, (name, _) in enumerate(ranking):
                tier = get_tier(i)
                for user in guild.members:
                    if str(user) == name:
                        break
                else:
                    continue
                new_role = discord.utils.get(guild.roles, name=tier)
                for role in user.roles:
                    if role.name == new_role.name:
                        break
                    if role.name in TIERS and role.name != new_role.name:
                        if not IS_DEV:
                            await user.remove_roles(role)
                        print(f"     Rol {role.name} removido a {user.name}.")
                else:
                    if not IS_DEV:
                        await user.add_roles(new_role)
                    print(f"     Rol {new_role.name} agregado a {user.name}")
