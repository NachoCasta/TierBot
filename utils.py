from os.path import join
from os import remove
import json
import datetime
from collections import defaultdict

from discord import HTTPException
from emoji import emojize
from time import time

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


def add_activity_log(member, before, after):
    if before.channel != after.channel and not member.bot:
        with open(ACTIVITY_LOG_PATH) as json_file:
            activity_log = json.load(json_file)
        name = str(member)
        guild_id = str(member.guild.id)
        if guild_id not in activity_log:
            activity_log[guild_id] = {}
        if name not in activity_log[guild_id]:
            activity_log[guild_id][name] = []
        log = {"timestamp": time()}
        if after.channel:
            # Se conecto a un canal
            log["type"] = "JOINED"
            print(f"{member} se conectó a {after.channel.name}")
        else:
            log["type"] = "LEFT"
            print(f"{member} se enojó")
            # Se desconecto
        activity_log[guild_id][name].append(log)
        with open(ACTIVITY_LOG_PATH, "w") as json_file:
            json.dump(activity_log, json_file, indent=4)


def get_activity_ranking(guild):
    guild = str(guild)
    with open(ACTIVITY_LOG_PATH) as json_file:
        data = json.load(json_file)
        if guild in data:
            activity_log = data[guild]
        else:
            activity_log = {}
    members = defaultdict(int)
    for user, logs in activity_log.items():
        last_type = "LEFT"
        last_timestamp = 0
        for log in logs:
            timestamp = log["timestamp"]
            if last_type == "JOINED":
                time_online = timestamp - last_timestamp
                members[user] += time_online
            last_type = log["type"]
            last_timestamp = timestamp
        if last_type == "JOINED":
            time_online = time() - last_timestamp
            members[user] += time_online
    return sorted(members.items(), key=lambda k: k[1], reverse=True)


def pretty_time_delta(seconds):
    seconds = int(seconds)
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    string = ""
    if seconds > 0:
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
