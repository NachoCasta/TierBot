from os.path import join
from os import remove
import json
import datetime
from collections import defaultdict

from discord import HTTPException
from emoji import emojize
from time import time
from ilock import ILock

import settings

# Returns a path relative to the bot directory


def get_rel_path(rel_path):
    return join(settings.BASE_DIR, rel_path)


# Returns an emoji as required to send it in a message
# You can pass the emoji name with or without colons
# If fail_silently is True, it will not raise an exception
# if the emoji is not found, it will return the input instead
def get_emoji(emoji_name, fail_silently=False):
    alias = emoji_name if emoji_name[0] == emoji_name[-1] == ":" \
        else f":{emoji_name}:"
    the_emoji = emojize(alias, use_aliases=True)

    if the_emoji == alias and not fail_silently:
        raise ValueError(f"Emoji {alias} not found!")

    return the_emoji


# A shortcut to get a channel by a certain attribute
# Uses the channel name by default
# If many matching channels are found, returns the first one
def get_channel(client, value, attribute="name"):
    channel = next((c for c in client.get_all_channels()
                    if getattr(c, attribute).lower() == value.lower()), None)
    if not channel:
        raise ValueError("No such channel")
    return channel


# Shortcut method to send a message in a channel with a certain name
# You can pass more positional arguments to send_message
# Uses get_channel, so you should be sure that the bot has access to only
# one channel with such name
async def send_in_channel(client, channel_name, *args):
    await client.send_message(get_channel(client, channel_name), *args)


# Attempts to upload a file in a certain channel
# content refers to the additional text that can be sent alongside the file
# delete_after_send can be set to True to delete the file afterwards
async def try_upload_file(client, channel, file_path, content=None,
                          delete_after_send=False, retries=3):
    used_retries = 0
    sent_msg = None

    while not sent_msg and used_retries < retries:
        try:
            sent_msg = await client.send_file(channel, file_path,
                                              content=content)
        except HTTPException:
            used_retries += 1

    if delete_after_send:
        remove(file_path)

    if not sent_msg:
        await client.send_message(channel,
                                  "Oops, something happened. Please try again.")

    return sent_msg

ACTIVITY_LOG_PATH = join(settings.BASE_DIR, "files", "activity_log.json")


def read_activity_log(guild):
    string = settings.redis.get(str(guild))
    if not string:
        return {}
    data = json.loads(string)
    return data


def save_activity_log(guild, data):
    string = json.dumps(data)
    settings.redis.set(str(guild), string)


def get_log_type(status, idle=False):
    if status.channel and not status.afk and not status.self_deaf and not status.self_mute and not idle:
        return "JOINED"
    else:
        return "LEFT"


def get_log(status, idle=False):
    return {"timestamp": time(), "type": get_log_type(status, idle)}


def log_current_users_activity(client):
    for guild in client.guilds:
        print(guild)
        with ILock(str(guild.id)):
            activity_log = read_activity_log(guild.id)
            for member, logs in activity_log.items():
                log = logs[-1].copy()
                log["type"] = "LEFT"
                activity_log[member].append(log)
            for member in guild.members:
                if not member.bot:
                    if member.voice:
                        print(f"{member} está conectado.")
                        idle = str(member.status) == "idle"
                        log = get_log(member.voice, idle=idle)
                        if str(member) not in activity_log:
                            activity_log[str(member)] = []
                        activity_log[str(member)].append(log)
            save_activity_log(guild.id, activity_log)


def add_activity_log(member, before, after):
    if not member.bot:
        with ILock(str(member.guild.id)):
            activity_log = read_activity_log(member.guild.id)
            name = str(member)
            if name not in activity_log:
                activity_log[name] = []
            log = get_log(after, idle=str(member.status) == "idle")
            if log["type"] == "JOINED":
                print(f"{member} se conectó a {after.channel.name}")
            else:
                print(f"{member} se enojó")
            new = True
            if activity_log[name]:
                last_log = activity_log[name][-1]
                if last_log["type"] == log["type"]:
                    new = False
            if new:
                print("Agregado")
                activity_log[name].append(log)
            save_activity_log(member.guild.id, activity_log)


def get_activity_data(guild):
    activity_log = read_activity_log(guild)
    members = defaultdict(list)
    for user, logs in activity_log.items():
        last_type = "LEFT"
        last_timestamp = 0
        for log in logs:
            timestamp = log["timestamp"]
            if last_type in ["JOINED", "ONLINE"]:
                time_online = timestamp - last_timestamp
                members[user].append((last_timestamp, time_online))
            last_type = log["type"]
            last_timestamp = timestamp
        if last_type in ["JOINED", "ONLINE"]:
            time_online = time() - last_timestamp
            members[user].append((last_timestamp, time_online))
    return members


def get_activity_ranking(guild):
    data = get_activity_data(guild)
    members = {user: sum(d[1] for d in user_data)
               for user, user_data in data.items()}
    return sorted(members.items(), key=lambda k: k[1], reverse=True)


def pretty_time_delta(seconds):
    seconds = int(seconds)
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    string = f"{seconds} segundos."
    if minutes > 0:
        string = f"{minutes} minutos y {string}"
    if hours > 0:
        string = f"{hours} horas, {string}"
    if days > 0:
        string = f"{days} días, {string}"
    return string


TIER_LIMITS = [1, 2, 3, 3, 3, 3, 3, 10000]

TIERS = ["S+ Tier", "S Tier", "A Tier", "B Tier",
         "C Tier", "D Tier", "E Tier", "F Tier"]


def get_tier(index):
    total = 0
    for i, tier in enumerate(TIER_LIMITS):
        total += tier
        if index < total:
            return TIERS[i]
