import discord
import os
import sys
import datetime
import psycopg2

from postgres_operations import DBOperations
from skillshot_scrap import get_hits_from_skillshot
from dotenv import load_dotenv
from discord.ext import commands, tasks
from ui import (
    BotBtnUI
    , generate_eom_plot
)

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

# postgres setup
db_name = os.getenv('DB_NAME')
db_user = os.getenv('DB_USER')
db_pass = os.getenv('DB_PASS')
db_url = os.getenv('DB_URL')
db_port = os.getenv('DB_PORT')
db_cache = {}

connection = psycopg2.connect(host=db_url, database=db_name, user=db_user, password=db_pass, port=db_port)
connection.autocommit = True

# discord setup
intents = discord.Intents.default()
intents.message_content = True
ping_role_name = None 
dc_channel = None
bot_channel = None

bot = commands.Bot(command_prefix='^', intents=intents)

# notification config
notification_time_utc = datetime.time(hour=19)
message_tpl = """
{rola}
# Dzisiejsze oferty pracy (skillshot.pl)
"""


async def get_or_fetch_channel(id: int) -> discord.TextChannel:
    """
    Get channel from cache or fetch from discord API

    :param int id: channel ID
    :return: discord channel object
    """
    obj = bot.get_channel(id)
    return obj or await bot.fetch_channel(id)


async def get_or_fetch_guild(id: int) -> discord.Guild:
    """
    Get guild from cache or fetch from discord API

    :param int id: guild ID
    :return: discord guild object
    """
    obj = bot.get_guild(id)
    return obj or await bot.fetch_guild(id)


@bot.event
async def on_ready() -> None:
    """
    Fetch database records into cache on startup
    """
    db_fetch = DBOps.get_all_configs()
    
    for record in db_fetch:
        db_cache[record[0]] = {
            "channel": record[1],
            "role": record[2] 
        }
    
    print(db_cache)
    print(datetime.datetime.now())
    print("Running...")
    await send_update.start()


@bot.event
async def on_message(message: discord.Message) -> None:
    await bot.process_commands(message)


@bot.command()
@commands.has_permissions(administrator=True)
async def show_config(ctx: discord.ext.commands.Context) -> None:
    """
    Show config as message in ctx channel
    """
    guild_id = str(ctx.guild.id)
    if guild_id in db_cache:
        await ctx.send(f"{ctx.author.mention} Current config:\nRole: {db_cache[guild_id]['role']}\nChannel: {db_cache[guild_id]['channel']}")
    else:
        await ctx.send("Not initialized. Run __set_role__ and __set_channel__ commands.")


@bot.command()
@commands.has_permissions(administrator=True)
async def set_role(ctx: discord.ext.commands.Context, *, msg) -> None:
    """
    Sets role to ping for notifications in db and cache
    """
    # if guild exists update role else insert new guild
    guild_id = str(ctx.guild.id)
    ping_role_name = discord.utils.get(ctx.guild.roles, name=msg).id
    

    if ping_role_name == None:
        await ctx.send(f"Role does not exist")
        return

    if DBOps.read(guild_id=guild_id) == []:
        DBOps.insert_guild(guild_id=guild_id, channel_id="", role_id=str(ping_role_name))
    else:
        DBOps.update(guild_id=guild_id, role_id=str(ping_role_name))

    if guild_id in db_cache.keys():
        db_cache[guild_id]["role"] = ping_role_name
    else:
        db_cache[guild_id] = {
            "channel": "",
            "role": ping_role_name 
        }

    await ctx.send(f"Set ping role to {ping_role_name}")


@bot.command()
@commands.has_permissions(administrator=True)
async def set_channel(ctx: discord.ext.commands.Context, *, msg) -> None:
    """
    Sets channel to post notifications in db and cache
    """
    # if guild exists update channel else insert new guild
    guild_id = str(ctx.guild.id)
    dc_channel = discord.utils.get(ctx.guild.channels, name=msg).id

    if dc_channel == None:
        await ctx.send("Channel does not exist")
        return

    if DBOps.read(guild_id=guild_id) == []:
        DBOps.insert_guild(guild_id=guild_id, channel_id=str(dc_channel), role_id="")
    else:
        DBOps.update(guild_id=guild_id, channel_id=str(dc_channel))

    if guild_id in db_cache.keys():
        db_cache[guild_id]["channel"] = dc_channel
    else:
        db_cache[guild_id] = {
            "channel": dc_channel,
            "role": ""
        }

    await ctx.send(f"Set ping channel to {msg}")



async def pull_info(dc_channel: str, ping_role_name: str, guild_id: str) -> None:
    """
    Send job postings to specified channel and ping specified role

    :param str dc_channel: discord channel ID
    :param str ping_role_name: discord role ID
    :param str guild_id: discord guild ID
    :return: None
    """
    # pull info from skillshot and post to channel
    if dc_channel != None and ping_role_name != None:
        try:
            bot_channel = await get_or_fetch_channel(id=int(dc_channel))
            guild = await get_or_fetch_guild(id=int(guild_id))
            hits_pulled_today = get_hits_from_skillshot(pages=1, date_to_compare=datetime.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0))
            embeds = [discord.Embed(title=hit[0], description=hit[1]) for hit in hits_pulled_today]

            if hits_pulled_today != []:
                DBOps.insert_historical(hits_pulled_today)
                await bot_channel.send(message_tpl.format(rola=discord.utils.get(guild.roles, id=int(ping_role_name)).mention))

                for embed in embeds:
                    job_message = await bot_channel.send(embed=embed)
                    await job_message.add_reaction("✅")
    
                await bot_channel.send("Kliknij aby otrzymywać powiadomienia:", view=BotBtnUI(db_cache=db_cache))
        except Exception as e:
            print(e)



@bot.command()
@commands.has_permissions(administrator=True)
async def pull_test(ctx: discord.ext.commands.Context) -> None:
    """
    Manual trigger for pulling notifications
    """
    guild_id = str(ctx.guild.id)
    if guild_id in db_cache.keys():
        role = db_cache[guild_id]["role"]
        channel = db_cache[guild_id]["channel"]
        if role and channel:
            await pull_info(dc_channel=channel, ping_role_name=role, guild_id=guild_id)
        else:
            await ctx.send("Channel or role not set. Run __show_config__ command.")
    else:
        await ctx.send("Not initialized. Run __set_role__ and __set_channel__ commands.")


@tasks.loop(time=notification_time_utc)
async def send_update() -> None:
    """
    Automatic daily trigger for notifications
    """
    print("Trying to send update..")
    for guild_id in db_cache:
        role = db_cache[guild_id]["role"]
        channel = db_cache[guild_id]["channel"]

        await pull_info(dc_channel=channel, ping_role_name=role, guild_id=guild_id)


@bot.command()
async def test_graph(ctx: discord.ext.commands.Context) -> None:
    """
    Sends end of month plot as message attachment
    """
    generate_eom_plot(data=DBOps.read_month_data())
    await ctx.send("\n## :calendar: Podsumowanie miesiąca", file=discord.File("graph.png"))



@pull_test.error
@set_channel.error
@set_role.error
@show_config.error
async def whoami_error(ctx: discord.ext.commands.Context, error) -> None:
    """
    Sends message on missing privileges
    """
    if isinstance(error, commands.CheckFailure):
        await ctx.send("Insufficient privileges")


if __name__ == "__main__":
    with connection.cursor() as cursor:
        DBOps = DBOperations(cursor)
        if sys.argv[1:] and sys.argv[1] == "init":
            print("Creating tables...")
            DBOps.create_tables()
        elif sys.argv[1:] and sys.argv[1] == "backfill":
            if not sys.argv[2:]:
                print("missing date on 2nd argument")
            else:
                try:
                    DBOps.backfill(date_from=datetime.datetime.strptime(sys.argv[2], '%Y-%m-%d'))
                except ValueError as ve:
                    print("Invalid date format. Use YYYY-MM-DD.")
        if sys.argv[1:] and sys.argv[1] == "test_graph":
            generate_eom_plot(data=DBOps.read_month_data())
        else:
            bot.run(token, reconnect=True)
