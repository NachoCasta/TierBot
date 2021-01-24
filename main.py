import sys

import settings
import discord
from os.path import join

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from tasks.base_task import BaseTask
from multiprocessing import Process
from utils import add_activity_log, log_current_users_activity, get_emoji, get_activity_ranking, pretty_time_delta, get_tier, get_activity_data, get_pages
from discord.ext.commands import Bot
from random import randint
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from DiscordUtils import Pagination

# Set to remember if the bot is already running, since on_ready may be called
# more than once on reconnects
this = sys.modules[__name__]
this.running = False

# Scheduler that will be used to manage events
sched = AsyncIOScheduler()


###############################################################################

def main():
    print("Starting up...")
    intents = discord.Intents.all()
    bot = Bot(command_prefix=settings.COMMAND_PREFIX, intents=intents)

    @bot.event
    async def on_ready():
        if this.running:
            return

        this.running = True

        # Set the playing status
        if settings.NOW_PLAYING:
            print("Setting NP game", flush=True)
            await bot.change_presence(
                activity=discord.Game(name=settings.NOW_PLAYING))
        print("Logged in!", flush=True)

        # Load all events
        print("Loading events...", flush=True)
        n_ev = 0
        for ev in BaseTask.__subclasses__():
            event = ev()
            sched.add_job(event.run, 'interval', (bot,),
                          minutes=event.interval_minutes)
            n_ev += 1
        sched.start()
        print(f"{n_ev} events loaded", flush=True)

        log_current_users_activity(bot)

    @bot.event
    async def on_voice_state_update(member, before, after):
        add_activity_log(member, before, after)

    @bot.event
    async def on_member_update(before, after):
        if after.voice:
            add_activity_log(after, before.voice, after.voice)

    @bot.command(help="Displays the current ranking for the server members")
    async def ranking(ctx):
        ranking = get_activity_ranking(ctx.guild.id)
        string = ""
        for i, (user, time) in enumerate(ranking):
            tier = get_tier(i)
            if tier not in string:
                string += f"**{tier}:**\n"
            name = user.split("#")[0]
            string += f"{name}: {pretty_time_delta(time)}\n"
        if string == "":
            string = "Todavía no hay un ranking."
        lines_per_page = 17
        pages = get_pages(string, lines_per_page)
        embeds = [discord.Embed().add_field(name="Ranking", value=page)
                  for page in pages]
        paginator = Pagination.CustomEmbedPaginator(ctx, auto_footer=True)
        paginator.add_reaction('⏪', "back")
        paginator.add_reaction('⏩', "next")
        await paginator.run(embeds)

    @bot.command(help="Generates a plot showing time spent on discord by each member")
    async def wod(ctx):
        activity_data = get_activity_data(ctx.guild.id)
        data = []
        for user, user_data in activity_data.items():
            for time, value in user_data:
                name = user.split("#")[0]
                data.append([name, pd.to_datetime(time, unit='s'), value])
        df = pd.DataFrame(data, columns=["name", "time", "time_spent"])
        df["time_spent"] = df["time_spent"].apply(lambda k: k / (60 * 60))
        df = df.groupby(["time", "name"])[
            "time_spent"].sum().unstack()
        df = df.cumsum().filter(items=df.sum().nlargest(10).index)
        df = df.interpolate(method="time")
        ax = df.plot(title="Wasted on Discord")
        for label in ax.get_xticklabels():
            label.set_rotation(25)
            label.set_horizontalalignment('right')
        plt.ylabel("Hours")
        plt.xlabel("Day")
        locator = mdates.AutoDateLocator()
        formatter = mdates.DateFormatter("%d-%m-%y")
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(formatter)
        ax.legend(loc="upper left", title_fontsize="xx-small",
                  fontsize="xx-small")
        plt.savefig(fname='ranking_plot')
        file_path = join(settings.BASE_DIR, "ranking_plot.png")
        file = discord.File(file_path, filename="ranking_plot.png")
        await ctx.send(file=file)

    # Finally, set the bot running
    bot.run(settings.BOT_TOKEN)

###############################################################################


if __name__ == "__main__":
    main()
