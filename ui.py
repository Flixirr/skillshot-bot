import discord


class BotBtnUI(discord.ui.View):
    """
    Discord bot button UI for managing notification roles

    :param dict[str, dict[str, str]] db_cache: cache of database entries
    """

    def __init__(self, db_cache: dict[str, dict[str, str]]) -> None:
        super().__init__(timeout=None)
        self.db_cache = db_cache


    @discord.ui.button(label="Chce powiadomienia!", style=discord.ButtonStyle.primary, custom_id="add_role_btn")
    async def button_callback(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        """
        Adds notification role to user
        """
        ping_role = None
        
        if str(interaction.guild_id) not in self.db_cache:
            await interaction.response.send_message("Dana rola nie istnieje. Skontaktuj się z administracją serwera.")
        else:
            ping_role = interaction.guild.get_role(int(self.db_cache[str(interaction.guild_id)]["role"]))
        
        if ping_role:
            if ping_role not in interaction.user.roles:
                await interaction.user.add_roles(ping_role)
                await interaction.response.send_message(f"{interaction.user.mention} nadano rolę **{ping_role}**", ephemeral=True)
            else:
                await interaction.response.send_message(f"{interaction.user.mention} posiadasz już rolę **{ping_role}**", ephemeral=True)
        else:
            await interaction.response.send_message("Dana rola nie istnieje. Skontaktuj się z administracją serwera.", ephemeral=True)


    @discord.ui.button(label="Nie chcę powiadomień!", style=discord.ButtonStyle.danger, custom_id="rm_role_btn")
    async def remove_button_callback(self, interaction: discord.Interaction, _button: discord.ui.Button) -> None:
        """
        Removes notification role from user
        """
        ping_role = None
        
        if str(interaction.guild_id) not in self.db_cache:
            await interaction.response.send_message("Dana rola nie istnieje. Skontaktuj się z administracją serwera.")
        else:
            ping_role = interaction.guild.get_role(int(self.db_cache[str(interaction.guild_id)]["role"]))
        
        if ping_role:
            if ping_role in interaction.user.roles:
                await interaction.user.remove_roles(ping_role)
                await interaction.response.send_message(f"{interaction.user.mention} odebrano rolę **{ping_role}**", ephemeral=True)
            else:
                await interaction.response.send_message(f"{interaction.user.mention} nie posiadasz roli **{ping_role}**", ephemeral=True)
        else:
            await interaction.response.send_message("Dana rola nie istnieje. Skontaktuj się z administracją serwera.", ephemeral=True)


def generate_eom_plot(data: list[tuple[int, str]]) -> bytes:
    """
    Generates end of month plot as bytes

    :param list[tuple[int, str]] data: list of tuples with the following structure:
                                        (offers_count, seniority)
    :return: plot image as bytes
    :rtype: bytes
    """
    import matplotlib.pyplot as plt
    from datetime import datetime

    # prepare data
    offers_count = [item[0] for item in data]
    seniority = [item[1] for item in data]

    # create plot
    plt.figure(figsize=(10, 6))
    bar = plt.bar(seniority, offers_count, color='black')
    plt.bar_label(bar, label_type='edge')
    plt.xlabel('Seniority')
    plt.ylabel('Number of Job Offers')
    plt.title(f'Job Offers by Seniority - {datetime.now().strftime("%B %Y")}')
    plt.tight_layout()

    plt.savefig("graph.png", format='png')
