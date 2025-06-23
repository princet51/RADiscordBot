import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
from supabase import create_client, Client
import os

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

url: str = os.getenv('SUPABASE_URL')
key: str = os.getenv('SUPABASE_KEY')
supabase: Client = create_client(url, key)

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix = '/', intents = intents)

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.CustomActivity(name = "🛡️ Monitoring for raid alerts"))
    await bot.tree.sync()
    print("Bot Synced")


class InitialButtons(discord.ui.View):

    @discord.ui.button(label = "Yes, I am already paired", style = discord.ButtonStyle.green)
    async def yes_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.message.edit(view = None)
        await interaction.response.send_message("Enter the email your RustAlert account is under using /email", ephemeral = True)

    @discord.ui.button(label = "No, I need to pair with a server", style = discord.ButtonStyle.red)
    async def no_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.message.edit(view = None)
        await interaction.response.send_message("works as well")


# Bot tree commands

@bot.tree.command(name="pair", description="Start the pairing process")
async def startprocess(interaction: discord.Interaction):
    embed = discord.Embed(title="RustAlert Pairing Process", description= "", color = discord.Color.from_rgb(216, 0, 0))
    embed.set_thumbnail(url = "https://cdn.discordapp.com/attachments/1382848303674167357/1382853711377731754/maybeicon.png?ex=685887e0&is=68573660&hm=8189d9fa99a4b66dfc319408cae701c495e97a436ddd33215c3131757b91604f&")
    embed.add_field(name = "Step 1", value = "Are you currently paired to a server using the RustAlert website dashboard?")
    await interaction.response.send_message(embed = embed, view  =InitialButtons())

@bot.tree.command(name="email",description='Enter your RustAlert email address')
async def inputemail(interaction: discord.Interaction, your_email: str):
        embed = discord.Embed(title = "RustAlert Server Status", description = "", color = discord.Color.from_rgb(216, 0, 0))
        embed.set_thumbnail(url = "https://cdn.discordapp.com/attachments/1382848303674167357/1382853711377731754/maybeicon.png?ex=685887e0&is=68573660&hm=8189d9fa99a4b66dfc319408cae701c495e97a436ddd33215c3131757b91604f&")
        embed.add_field(name = "Step 1", value = your_email)

        response = (
             supabase.table("rust_tokens")
             .select("steam_id")
             .eq("email", your_email)
             .execute()
        )

        if not response.data:
             await interaction.response.send_message(f"No email found. Make sure {your_email} is paired to a server on the RustAlert website dashboard", ephemeral = True)
             return


        steamid = str(response.data[0]['steam_id'])
        print(steamid)

        server_response = (
             supabase.table("servers")
             .select("name")
             .eq("steam_id", steamid)
             .execute()
        )
        
        
        if not server_response.data:
             await interaction.response.send_message(f"Email found, but you are not paired with a server. Pair with a server and try again.", ephemeral = True)
             return

        print(server_response.data)


        await interaction.response.send_message(embed = embed)






bot.run(token, log_handler = handler, log_level = logging.DEBUG)