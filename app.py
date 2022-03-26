import discord
from discord.ext import commands, tasks
import os
import json
from dotenv import load_dotenv
import logging
import datetime
import psycopg2
from psycopg2 import OperationalError

# setup logging
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

load_dotenv()

# load env vars
bot_token = os.environ.get("BOT_TOKEN")
announce_channel = os.environ.get("ANNOUNCE_CHANNEL_ID")
db_URL = os.environ.get("DATABASE_URL", None)
bot_admin = os.environ.get("BOT_ADMIN")

# set bot
intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="$",intents=intents)

# define dict for roles
print(os.getcwd())
Z = open('./FACTIONSbot/roles.json')
roledict = json.load(Z)
Z.close()

# connect to db
# conn = psycopg2.connect(db_URL, sslmode='require')
conn = psycopg2.connect(db_URL)

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
    name = cursor.fetchone();
    cursor.execute(f"""SELECT exp FROM factions WHERE id = '{fid}'""")
    exp = cursor.fetchone();
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
        return
    else:
        for x in roledict:
            if x["id"] in [str(y.id) for y in msg.author.roles]:
                match = x["id"]
                if match:
                    add_faction_xp(match,10)
        await bot.process_commands(msg)


@bot.command()
@commands.has_any_role(bot_admin)
async def resetall(ctx):
    for x in roledict:
        reset_faction_xp(x["id"])
    await ctx.send("All Faction points were reset.")


@bot.command()
async def leaderboard(ctx):
    list = "**Current Points:**"
    for x in roledict:
        emoji = x["emoji"]
        fid = x["id"]
        name, exp = get_info(conn,fid)
        list += f"\n{emoji} {name} - {exp} Points"
    await ctx.send(list)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, (commands.MissingRole, commands.MissingAnyRole)):
        await ctx.send(f"Hey, you need to be <@&{bot_admin}> to do that!")


if __name__ == "__main__":
    initDB()
    bot.run(bot_token)
