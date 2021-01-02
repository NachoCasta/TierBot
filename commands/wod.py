from commands.base_command import BaseCommand
from utils import get_emoji, get_activity_data
from random import randint
import discord
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

import settings
from os.path import join


class Wod(BaseCommand):

    def __init__(self):
        description = "Generates a plot showing time spent on discord by each member"
        params = []
        super().__init__(description, params)

    # Override the handle() method
    # It will be called every time the command is received
    async def handle(self, params, message, client):
        activity_data = get_activity_data(message.guild.id)
        data = []
        for user, user_data in activity_data.items():
            for time, value in user_data:
                name = user.split("#")[0]
                data.append([name, pd.to_datetime(time, unit='s'), value])
        df = pd.DataFrame(data, columns=["name", "time", "time_spent"])
        df["time_spent"] = df["time_spent"].apply(lambda k: k / (60 * 60))
        df = df.groupby([df["time"].dt.date, "name"])[
            "time_spent"].sum().unstack()
        df.fillna(0, inplace=True)
        df.plot()
        ax = plt.gca()
        for label in ax.get_xticklabels():
            label.set_rotation(20)
            label.set_horizontalalignment('right')
        plt.xlabel("Days")
        plt.ylabel("Hours")
        locator = mdates.AutoDateLocator()
        formatter = mdates.DateFormatter("%d-%m-%Y")
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(formatter)
        plt.savefig(fname='ranking_plot')
        file_path = join(settings.BASE_DIR, "ranking_plot.png")
        file = discord.File(file_path, filename="ranking_plot.png")
        await message.channel.send(file=file)
