import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import logging
import datetime

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

load_dotenv()

bot_token = os.environ.get("BOT_TOKEN")
announce_channel = os.environ.get("ANNOUNCE_CHANNEL_ID")

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="$",intents=intents)

roledict = [
    {
        "id": "920712472309149696",
        "name": "The Heroes",
        "color": 0x008002,
        "image": "https://cdn.discordapp.com/emojis/921560361331736627.png",
        "emoji": "<:HEROES:921560361331736627>"
    },
    {
        "id": "920726315617890354",
        "name": "The Pagemasters",
        "color": 0x00688a,
        "image": "https://cdn.discordapp.com/emojis/921120575882133585.png",
        "emoji": "<:PAGEMASTER:921120575882133585>"
    },
    {
        "id": "920729205774372894",
        "name": "The Architects",
        "color": 0xb204d3,
        "image": "https://cdn.discordapp.com/emojis/921450094547570689.png",
        "emoji": "<:ARCHITECT:921450094547570689>"
    },
    {
        "id": "920726084507545680",
        "name": "The Guardians",
        "color": 0xffd100,
        "image": "https://cdn.discordapp.com/emojis/921945964158263356.png",
        "emoji": "<:GUARDIANS:921945964158263356>"
    }
]

@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))
    await bot.change_presence(status=discord.Status.online, activity=discord.Game(name="FACTIONS"))

@bot.event
async def on_member_update(before, after):
    channel = bot.get_channel(int(announce_channel))
    if before.roles != after.roles:
        for r in after.roles:
            if r not in before.roles:
                new_role_id = str(r.id)
                for R in roledict:
                    if new_role_id == R["id"]:
                        emoji = R["emoji"]
                        rolename = R["name"]
                        shortname = rolename.split(' ')[1]
                        emb = discord.Embed(
                            title=f"{emoji} **{rolename}** have a new recruit!",
                            color=R["color"],
                            timestamp=datetime.datetime.utcnow()
                        )
                        emb.set_thumbnail(url=R["image"])
                        emb.add_field(name=f"WELCOME TO {rolename.upper()}!", value=f"Say hello to <@{after.id}> and judge _not_ by which Faction they choose.")
                        emb.set_footer(text=f"There are now {len(r.members)} {shortname} within our ranks.")
                        await channel.send(embed=emb)


if __name__ == "__main__":
    bot.run(bot_token)