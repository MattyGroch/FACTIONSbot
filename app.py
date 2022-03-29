import discord
from discord.ext import commands
import os
import json
from dotenv import load_dotenv
import logging
import datetime
import psycopg2
from psycopg2 import OperationalError
import random
import re

# setup logging
logger = logging.getLogger('discord')
logger.setLevel(logging.WARNING)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

load_dotenv()

# load env vars
bot_token = os.environ.get("BOT_TOKEN")
announce_channel = os.environ.get("ANNOUNCE_CHANNEL_ID")
db_URL = os.environ.get("DATABASE_URL", None)
bot_admin = int(os.environ.get("BOT_ADMIN"))

# set bot
intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="$",intents=intents)

# define dict for roles
print(os.getcwd())
Z = open('./roles.json')
roledict = json.load(Z)
Z.close()

# connect to db
conn = psycopg2.connect(db_URL, sslmode='require')


def diceRoll(count,faces):
    rolls = []
    for _ in range(count):
        roll = random.randint(1, faces)
        rolls.append(roll)
    return rolls


def execute_query(connection, query):
    connection.autocommit = True
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        print("Query executed successfully")
    except OperationalError as e:
        print(f"The error '{e}' occurred")


def get_info(connection,fid):
    cursor = connection.cursor()
    cursor.execute(f"""SELECT name FROM factions WHERE id = '{fid}'""")
    name = cursor.fetchone()
    cursor.execute(f"""SELECT exp FROM factions WHERE id = '{fid}'""")
    exp = cursor.fetchone()
    return name[0], exp[0]


def initDB():
    table_init = """
    CREATE TABLE IF NOT EXISTS factions (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        exp INTEGER
        )
        """
    execute_query(conn, table_init)
    for h in roledict:
        r_id = h["id"]
        r_name = h["name"]
        query = f"""
            INSERT INTO
                factions (id, name)
            VALUES
                ( '{r_id}' , '{r_name}' )
            ON CONFLICT (id)
            DO NOTHING;
            UPDATE factions
            SET exp=0
            WHERE id='{r_id}' AND exp IS NULL;
            """
        execute_query(conn, query)


def add_faction_xp(fid,amt):
    query = f"""
        UPDATE factions
        SET exp = exp + {amt}
        WHERE id = '{fid}';
        """
    execute_query(conn, query)


def reset_faction_xp(fid):
    query = f"""
        UPDATE factions
        SET exp = 0
        WHERE id = '{fid}';
        """
    execute_query(conn, query)


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
                        rolecolor = discord.Color.from_rgb(R["r"], R["g"], R["b"])
                        emb = discord.Embed(
                            title=f"{emoji} **{rolename}** have a new recruit!",
                            color=rolecolor,
                            timestamp=datetime.datetime.utcnow()
                        )
                        emb.set_thumbnail(url=R["image"])
                        emb.add_field(name=f"WELCOME TO {rolename.upper()}!", value=f"Say hello to <@{after.id}> and judge _not_ by which Faction they choose.")
                        emb.set_footer(text=f"There are now {len(r.members)} {shortname} within our ranks.")
                        await channel.send(embed=emb)


@bot.event
async def on_message(msg):
    if msg.author.bot == True:
        return
    if msg.channel.category_id == 822162540955566121 or not msg.channel.category_id:
        await bot.process_commands(msg)
        return
    else:
        for x in roledict:
            if x["id"] in [str(y.id) for y in msg.author.roles]:
                user_faction = x["id"]
                if user_faction:
                    if msg.channel.category_id == 921399950657601547:
                        add_faction_xp(user_faction,1)
                    elif msg.channel.category_id == int(x["category"]):
                        add_faction_xp(user_faction,10)
                    else:
                        add_faction_xp(user_faction,5)
        await bot.process_commands(msg)


@bot.command()
@commands.has_any_role(bot_admin)
async def resetall(ctx):
    for x in roledict:
        reset_faction_xp(x["id"])
    await ctx.send("All Faction points were reset.")


@bot.command()
async def leaderboard(ctx):
    list = []
    def sort_key(faction):
        return faction[1]
    for x in roledict:
        fid = x["id"]
        list.append(get_info(conn,fid))
    list.sort(key=sort_key, reverse=True)
    embed = discord.Embed(title="FACTIONS Leaderboard", color=0xffffff)
    for z in list:
        name, points = z[0], z[1]
        for y in roledict:
            if name == y["name"]:
                emoji = y["emoji"]
        embed.add_field(name=f"{emoji}  {name}", value=f"{points} Points", inline=False)
    embed.set_footer(text="Who will be crowned champion?")
    await ctx.send(embed=embed)


@bot.command()
async def roll(ctx,arg=None):
    if arg:
        check = re.match('(\d+)d(\d+)',arg)
        if check:
            dice = int(check.group(1))
            face = int(check.group(2))
            roll = diceRoll(dice, face)
        else:
            await ctx.send("Use `$roll 2d4` where 2 is the number of dice and 4 is the number of faces.", delete_after=5)
    else:
        arg, dice, face = "1d20", 1, 20
        roll = diceRoll(1, 20)
    embed = discord.Embed(title=f"Rolling {arg}...", color=0xffffff)
    c = 0
    for r in roll:
        c = c + 1
        if r == face:
            r = f"**{r}**"
        embed.add_field(name=f"Die {c}", value=f"{r}", inline=True)
    if dice > 1:
        embed.add_field(name="Total", value=sum(roll), inline=False)
    await ctx.send(embed=embed)


@bot.command()
async def roll20(ctx):
    roll = diceRoll(1, 20)
    for r in roll:
        await ctx.send("Hi")




@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, (commands.MissingRole, commands.MissingAnyRole)):
        await ctx.send(f"Hey, you need to be <@&{bot_admin}> to do that!")


if __name__ == "__main__":
    initDB()
    bot.run(bot_token)
