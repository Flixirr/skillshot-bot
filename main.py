import discord
import os
import datetime
import webserver
import psycopg2

from skillshot_scrap import get_hits_from_skillshot
from dotenv import load_dotenv
from discord.ext import commands, tasks

# load_dotenv()
token = os.environ['DISCORD_TOKEN']

db_name = os.environ['DB_NAME']
db_user = os.environ['DB_USER']
db_pass = os.environ['DB_PASS']
db_url = os.environ['DB_URL']
db_port = os.environ['DB_PORT']

intents = discord.Intents.default()
intents.message_content = True
ping_role_name = None 
dc_channel = None
bot_channel = None

db_cache = {}


bot = commands.Bot(command_prefix='^', intents=intents)

hits_pulled_today = []
message_tpl = """
{rola}
# Dzisiejsze oferty pracy (skillshot.pl)
"""
check_if_exists = "SELECT guild_id FROM configs WHERE guild_id={guild_id};"

insert_new_guild = "INSERT INTO configs (guild_id, channel_id, role_id) VALUES ({guild_id}, {channel_id}, {role_id});"

update_channel_guild = "UPDATE configs SET channel_id={channel_id} WHERE guild_id = {guild_id};"
update_role_guild = "UPDATE configs SET role_id={role_id} WHERE guild_id = {guild_id};"

read_channel_guild = "SELECT channel_id FROM configs WHERE guild_id={guild_id};" 
read_role_guild = "SELECT role_id FROM configs WHERE guild_id={guild_id};"

connection = psycopg2.connect(host=db_url, database=db_name, user=db_user, password=db_pass, port=db_port)
connection.autocommit = True


async def get_or_fetch_channel(id):
    obj = bot.get_channel(id)
    return obj or await bot.fetch_channel(id)


async def get_or_fetch_guild(id):
    obj = bot.get_guild(id)
    return obj or await bot.fetch_guild(id)


@bot.event
async def on_ready():
    cursor.execute("SELECT * FROM configs;")
    db_fetch =  cursor.fetchall()
    
    for record in db_fetch:
        db_cache[record[0]] = {
            "channel": record[1],
            "role": record[2] 
        }
    
    print(db_cache)
    print(datetime.datetime.now())

    print("Running...")
    await send_update.start()


class BotBtnUI(discord.ui.View):
    @discord.ui.button(label="Chce powiadomienia!", style=discord.ButtonStyle.primary, custom_id="add_role_btn")
    async def button_callback(self, interaction: discord.Interaction, button):
        ping_role = None
        
        if str(interaction.guild_id) not in db_cache:
            await interaction.response.send_message("Dana rola nie istnieje. Skontaktuj się z administracją serwera.")
        else:
            ping_role = interaction.guild.get_role(int(db_cache[str(interaction.guild_id)]["role"]))
        
        if ping_role:
            if ping_role not in interaction.user.roles:
                await interaction.user.add_roles(ping_role)
                await interaction.response.send_message(f"{interaction.user.mention} nadano rolę **{ping_role}**", ephemeral=True)
            elif not ping_role:
                await interaction.response.send_message(f"Rola **{ping_role}** nie istnieje", ephemeral=True)
            else:
                await interaction.response.send_message(f"{interaction.user.mention} posiadasz już rolę **{ping_role}**", ephemeral=True)
        else:
            await interaction.response.send_message("Dana rola nie istnieje. Skontaktuj się z administracją serwera.", ephemeral=True)


    @discord.ui.button(label="Nie chcę powiadomień!", style=discord.ButtonStyle.danger, custom_id="rm_role_btn")
    async def remove_button_callback(self, interaction, button):
        ping_role = None
        
        if str(interaction.guild_id) not in db_cache:
            await interaction.response.send_message("Dana rola nie istnieje. Skontaktuj się z administracją serwera.")
        else:
            ping_role = interaction.guild.get_role(int(db_cache[str(interaction.guild_id)]["role"]))
        
        if ping_role:
            if ping_role in interaction.user.roles:
                await interaction.user.remove_roles(ping_role)
                await interaction.response.send_message(f"{interaction.user.mention} odebrano rolę **{ping_role}**", ephemeral=True)
            elif not ping_role:
                await interaction.response.send_message(f"Rola **{ping_role}** nie istnieje", ephemeral=True)
            else:
                await interaction.response.send_message(f"{interaction.user.mention} nie posiadasz roli **{ping_role}**", ephemeral=True)
        else:
            await interaction.response.send_message("Dana rola nie istnieje. Skontaktuj się z administracją serwera.", ephemeral=True)


@bot.event
async def on_message(message):
    await bot.process_commands(message)


@bot.command()
async def show_config(ctx):
    guild_id = str(ctx.guild.id)
    if guild_id in db_cache:
        await ctx.send(f"{ctx.author.mention} Current config:\nRole: {db_cache[guild_id]['role']}\nChannel: {db_cache[guild_id]['channel']}")
    else:
        await ctx.send("Not initialized. Run __set_role__ and __set_channel__ commands.")


@bot.command()
async def set_role(ctx, *, msg):
    cursor.execute(check_if_exists.format(guild_id=f"'{ctx.guild.id}'"))
    guild_id = str(ctx.guild.id)
    ping_role_name = discord.utils.get(ctx.guild.roles, name=msg).id

    if cursor.fetchall() == []:
        cursor.execute(insert_new_guild.format(guild_id=f"'{guild_id}'", role_id=f"'{ping_role_name}'", channel_id="''"))
    else:
        cursor.execute(update_role_guild.format(guild_id=f"'{guild_id}'", role_id=f"'{ping_role_name}'"))

    if guild_id in db_cache.keys():
        db_cache[guild_id]["role"] = ping_role_name
    else:
        db_cache[guild_id] = {
            "channel": "",
            "role": ping_role_name 
        }
    
    if ping_role_name == None:
        await ctx.send(f"Role does not exist")
    else:
        await ctx.send(f"Set ping role to {ping_role_name}")


@bot.command()
async def set_channel(ctx, *, msg):
    cursor.execute(check_if_exists.format(guild_id=f"'{ctx.guild.id}'"))
    guild_id = str(ctx.guild.id)
    dc_channel = discord.utils.get(ctx.guild.channels, name=msg).id

    if cursor.fetchall() == []:
        cursor.execute(insert_new_guild.format(guild_id=f"'{guild_id}'", role_id=f"''", channel_id=f"'{dc_channel}'"))
    else:
        cursor.execute(update_channel_guild.format(guild_id=f"'{guild_id}'", channel_id=f"'{dc_channel}'"))

    if guild_id in db_cache.keys():
        db_cache[guild_id]["channel"] = dc_channel
    else:
        db_cache[guild_id] = {
            "channel": dc_channel,
            "role": ""
        }


    if dc_channel == None:
        await ctx.send("Channel does not exist")
    else:
        await ctx.send(f"Set ping channel to {msg}")



async def pull_info(dc_channel, ping_role_name, guild_id):
    print(dc_channel)
    if dc_channel != None and ping_role_name != None:
        try:
            bot_channel = await get_or_fetch_channel(dc_channel)
            guild = await get_or_fetch_guild(guild_id)
            hits_pulled_today = get_hits_from_skillshot()
            embeds = [discord.Embed(title=hit[0], description=hit[1]) for hit in hits_pulled_today]
            if hits_pulled_today != []:
                await bot_channel.send(message_tpl.format(rola=discord.utils.get(guild.roles, id=int(ping_role_name)).mention))
                for embed in embeds:
                    job_message = await bot_channel.send(embed=embed)
                    await job_message.add_reaction("✅")
    
                await bot_channel.send("Kliknij aby otrzymywać powiadomienia:", view=BotBtnUI())
        except Exception as e:
            print(e)



@bot.command()
@commands.has_permissions(administrator=True)
async def pull_test(ctx):
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


time = datetime.time(hour=17)


@tasks.loop(time=time)
async def send_update():
    print("Trying to send update..")
    for guild_id in db_cache:
        role = db_cache[guild_id]["role"]
        channel = db_cache[guild_id]["channel"]

        await pull_info(dc_channel=channel, ping_role_name=role, guild_id=guild_id)



@pull_test.error
@set_channel.error
@set_role.error
async def whoami_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        ctx.send("Insufficient privilages")

if __name__ == "__main__":
    webserver.keep_alive()
    with connection.cursor() as cursor:
        bot.run(token)