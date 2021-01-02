from commands.base_command import BaseCommand
from utils import get_emoji, get_activity_ranking, pretty_time_delta, get_tier
from random import randint


# Your friendly example event
# Keep in mind that the command name will be derived from the class name
# but in lowercase

# So, a command class named Random will generate a 'random' command


class Ranking(BaseCommand):

    def __init__(self):
        description = "Displays the current ranking for the server members"
        params = []
        super().__init__(description, params)

    # Override the handle() method
    # It will be called every time the command is received
    async def handle(self, params, message, client):
        ranking = get_activity_ranking(message.guild.id)
        string = ""
        for i, (user, time) in enumerate(ranking):
            tier = get_tier(i)
            if tier not in string:
                string += f"**{tier}:**\n"
            name = user.split("#")[0]
            string += f"{name}: {pretty_time_delta(time)}\n"
        if string == "":
            string = "Todavía no hay un ranking."
        await message.channel.send(string)
