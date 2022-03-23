import discord
from discord.ext import commands, tasks
import os
from dotenv import load_dotenv
import logging
import datetime

# setup logging
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

load_dotenv()

# load bot vars
bot_token = os.environ.get("BOT_TOKEN")
announce_channel = os.environ.get("ANNOUNCE_CHANNEL_ID")

# set up the DB
db_URL = os.environ.get("DATABASE_URL", None)
client.pg_con = await asyncpg.create_pool(db_URL)

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="$",intents=intents)

# define dict for roles
roledict = open('roles.json')

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
