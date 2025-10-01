import discord
import os
import datetime
import webserver

from skillshot_scrap import get_hits_from_skillshot
from discord.ext import commands, tasks

token = os.environ['DISCORD_TOKEN']

intents = discord.Intents.default()
intents.message_content = True
ping_role_name = None 
dc_channel = None
bot_channel = None

bot = commands.Bot(command_prefix='^', intents=intents)

hits_pulled_today = []
message_tpl = """
{rola}
# Dzisiejsze oferty pracy (skillshot.pl)
"""


@bot.event
async def on_ready():
    print(datetime.datetime.now())
    print("Running...")
    await send_update.start()


class BotBtnUI(discord.ui.View):
    @discord.ui.button(label="Chce powiadomienia!", style=discord.ButtonStyle.primary, custom_id="add_role_btn")
    async def button_callback(self, interaction, button):
        if ping_role_name not in interaction.user.roles:
            await interaction.user.add_roles(ping_role_name)
            await interaction.response.send_message(f"{interaction.user.mention} nadano rolę **{ping_role_name}**")
        elif not ping_role_name:
            await interaction.response.send_message(f"Rola **{ping_role_name}** nie istnieje")
        else:
            await interaction.response.send_message(f"{interaction.user.mention} posiadasz już rolę **{ping_role_name}**")
    

    @discord.ui.button(label="Nie chcę powiadomień!", style=discord.ButtonStyle.danger, custom_id="rm_role_btn")
    async def remove_button_callback(self, interaction, button):
        if ping_role_name in interaction.user.roles:
            await interaction.user.remove_roles(ping_role_name)
            await interaction.response.send_message(f"{interaction.user.mention} odebrano rolę **{ping_role_name}**")
        elif not ping_role_name:
            await interaction.response.send_message(f"Rola **{ping_role_name}** nie istnieje")
        else:
            await interaction.response.send_message(f"{interaction.user.mention} nie posiadasz roli **{ping_role_name}**")


@bot.event
async def on_message(message):
    await bot.process_commands(message)


@bot.command()
async def set_role(ctx, *, msg):
    global ping_role_name 
    ping_role_name = discord.utils.get(ctx.guild.roles, name=msg)
    if ping_role_name == None:
        await ctx.send(f"Role does not exist")
    else:
        await ctx.send(f"Set ping role to {ping_role_name}")

@bot.command()
async def set_channel(ctx, *, msg):
    global dc_channel
    global bot_channel
    dc_channel = discord.utils.get(ctx.guild.channels, name=msg)

    if dc_channel == None:
        ctx.send("Channel does not exist")
    else:
        bot_channel = bot.get_channel(dc_channel.id)
        print(dc_channel)
        await ctx.send(f"Set ping channel to {msg}")


@bot.command()
@commands.has_permissions(administrator=True)
async def pull(ctx):
    if dc_channel != None and ping_role_name != None:
        hits_pulled_today = get_hits_from_skillshot()    
        embeds = [discord.Embed(title=hit[0], description=hit[1]) for hit in hits_pulled_today]

        await bot_channel.send(message_tpl.format(rola=ping_role_name.mention))
        for embed in embeds:
            job_message = await bot_channel.send(embed=embed)
            await job_message.add_reaction("✅")
    
        await bot_channel.send("Kliknij aby otrzymywać powiadomienia:", view=BotBtnUI())
    else:
        await ctx.send("Channel and ping role not set")

time = datetime.time(hour=18)
@tasks.loop(time=time)
async def send_update():
    print("Trying to send update..")
    if dc_channel != None and ping_role_name != None:
        hits_pulled_today = get_hits_from_skillshot()    
        embeds = [discord.Embed(title=hit[0], description=hit[1]) for hit in hits_pulled_today]

        await bot_channel.send(message_tpl.format(rola=ping_role_name.mention))
        for embed in embeds:
            job_message = await bot_channel.send(embed=embed)
            await job_message.add_reaction("✅")
    
        await bot_channel.send("Kliknij aby otrzymywać powiadomienia:", view=BotBtnUI())




@pull.error
@set_channel.error
@set_role.error
async def whoami_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        ctx.send("Insufficient privilages")

if __name__ == "__main__":
    webserver.keep_alive()
    bot.run(token)