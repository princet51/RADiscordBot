import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
from supabase import create_client, Client
from datetime import datetime, timezone
import requests
import urllib3
import os

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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
    await bot.change_presence(activity=discord.CustomActivity(name = "🛡️ Monitoring for raids 🛡️ /pair"))
    await bot.tree.sync()
    print("Bot Synced")


class InitialButtons(discord.ui.View):

    @discord.ui.button(label = "Yes, I am already paired", style = discord.ButtonStyle.green)
    async def yes_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.message.edit(view = None)
        await interaction.response.send_message("```Enter the email your RustAlert account is under using /email```", ephemeral = True)

    @discord.ui.button(label = "No, I need to pair with a server", style = discord.ButtonStyle.red)
    async def no_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.message.edit(view = None)
        await interaction.response.send_message("works as well")

class RegisterWithRustPlus(discord.ui.View):

     embed = discord.Embed(title="RustAlert Pairing Process", description= "", color = discord.Color.from_rgb(216, 0, 0))
     embed.set_thumbnail(url = "https://cdn.discordapp.com/attachments/1382848303674167357/1382853711377731754/maybeicon.png?ex=685887e0&is=68573660&hm=8189d9fa99a4b66dfc319408cae701c495e97a436ddd33215c3131757b91604f&")
     embed.add_field(name = "Step 2", value = "```Are you currently paired to a server using the RustAlert website dashboard?```")


# Bot tree commands

@bot.tree.command(name="pair", description="Start the pairing process")
async def startprocess(interaction: discord.Interaction):
    embed = discord.Embed(title="RustAlert Pairing Process", description= "", color = discord.Color.from_rgb(216, 0, 0))
    embed.set_thumbnail(url = "https://cdn.discordapp.com/attachments/1382848303674167357/1382853711377731754/maybeicon.png?ex=685887e0&is=68573660&hm=8189d9fa99a4b66dfc319408cae701c495e97a436ddd33215c3131757b91604f&")
    embed.add_field(name = "Step 1", value = "```Are you currently paired to a server using the RustAlert website dashboard?```")
    await interaction.response.send_message(embed = embed, view  =InitialButtons())

@bot.tree.command(name="email",description='Enter your RustAlert email address')
async def inputemail(interaction: discord.Interaction, your_email: str):

        response = requests.post('https://backapi.rustalert.com/get-steamid', json={"email": your_email}, verify=False)

        data = response.json()

        if data:
             print(data)
             steamid = data['data']['steam_id']

        else:
             await interaction.response.send_message(f"No email found. Make sure {your_email} is paired to a server on the RustAlert website dashboard", ephemeral = True)
             print(response.status_code)
             return

        server_response = requests.post('https://backapi.rustalert.com/server-info', json={"steamID": steamid}, verify=False)
        
        serverData = server_response.json()
        print(serverData)

        if serverData:
             serverName = serverData['name']
             activeStatus = serverData['alarmStatus']
             triggers = serverData['triggers']
             triggerTime = serverData['triggerTime']

        else:
             await interaction.response.send_message(f"Email found, but you are not paired with a server. Pair with a server and try again.", ephemeral = True)
             return
        
        if triggerTime is not None and triggerTime != 0:
          eventTime = datetime.fromisoformat(triggerTime)
          now = datetime.now(timezone.utc)
          timeDiff = now - eventTime
          timeDiff = timeDiff.total_seconds()

        else:
          time = "WAITING"
          timeDiff = None

        if timeDiff is not None:
            if timeDiff < 60:
                 time = f"{int(timeDiff)} seconds ago"
            elif timeDiff < 3600:
                 time = f"{int(timeDiff // 60)} minutes ago"
            elif timeDiff < 86400:
                 time = f"{int(timeDiff // 3600)} hours ago"
            else:
                 time = f"{int(timeDiff // 86400)} days ago"

        if activeStatus == "triggered":
             alarmStatus = "TRIGGERED"

        else:
             alarmStatus = "CONNECTED"

        embed = discord.Embed(title = "RustAlert Server Status", description = "", color = discord.Color.from_rgb(216, 0, 0))
        embed.set_thumbnail(url = "https://cdn.discordapp.com/attachments/1382848303674167357/1382853711377731754/maybeicon.png?ex=685887e0&is=68573660&hm=8189d9fa99a4b66dfc319408cae701c495e97a436ddd33215c3131757b91604f&")
        embed.add_field(name = "SERVER NAME: ", value = f"```{serverName}```", inline = False)
        embed.add_field(name = "STATUS: ", value = f"```{alarmStatus}```")
        embed.add_field(name = "TRIGGERS: ", value = f"```{triggers}```")
        embed.add_field(name = "LAST CALL: ", value = f"```{time}```")

        await interaction.response.send_message(embed = embed)

@bot.tree.command(name="setup", description="Link your account to pair with a server")
async def inputToken(interaction: discord.Interaction, paste_here: str):
     start_index = paste_here.index("SteamId")
     start_index += 12

     SteamID = ""
     while paste_here[start_index] != '\\':
          SteamID += paste_here[start_index]
          start_index += 1

     start_index += 15

     PlayerToken = ""
     while paste_here[start_index] != '\\':
          PlayerToken += paste_here[start_index]
          start_index += 1

     print(SteamID)
     print(PlayerToken)

     response = requests.post('https://backapi.rustalert.com/pair-with-server', json={"steamid": SteamID, "token": PlayerToken}, verify=False)

     data = response.json()

     await interaction.response.send_message("Account successfully linked, do not use the Rust+ app, RustAlert works independently of it. Now go in-game, press escape and click Rust+, and click Pair with Server")


     

@bot.tree.command(name="disconnect", description="Disconnect from a server")
async def disconnect(interaction: discord.Interaction, steam_id: str):

     #serverResponse = requests.post('https://backapi.rustalert.com/check-steamid', json={"SteamID": steam_id, "Intention": "server"}, verify=False)

     #if serverResponse.success == False:
     #     await interaction.response.send_message(f'No active server pair found for the SteamID: {steam_id}. Pair with a server and try again. Use /help for additional help.', ephemeral=True)
     #     return

     response = requests.post('https://backapi.rustalert.com/disconnect', json={"steamId": steam_id}, verify=False)

     print(response)

     await interaction.response.send_message('disconnected')  


@bot.tree.command(name="help", description="List all commands and what they do")
async def help(interaction: discord.Interaction):
        
     embed = discord.Embed(title = "RustAlert Bot Commands", description = "", color = discord.Color.from_rgb(216, 0, 0))
     embed.set_thumbnail(url = "https://cdn.discordapp.com/attachments/1382848303674167357/1382853711377731754/maybeicon.png?ex=685887e0&is=68573660&hm=8189d9fa99a4b66dfc319408cae701c495e97a436ddd33215c3131757b91604f&")
     embed.add_field(name = "```/pair```", value = "```Start here if you're new to the discord bot. It will walk you through the steps you need to take```", inline=False)
     embed.add_field(name = "```/email```", value = "```Use this if you are already paired with a server on the RustAlert website dashboard.```", inline=False)
     embed.add_field(name = "```/setup```", value = "```Use this if this is your first time pairing using the discord bot. Follow the steps it says to start the server pairing process.```", inline=False)
     embed.add_field(name = "```/steamid```", value = "```Use this if you have paired with a server using the discord bot in the past. This will start the server pairing process.```", inline=False)
     embed.add_field(name = "```/disconnect```", value = "```Use this if you are paired with a server using the discord bot and wish to disconnect from the server.```", inline=False)
     embed.add_field(name = "```For additional help:```", value = "```Join our discord server and open a ticket```", inline=False)
     await interaction.response.send_message(embed = embed)



@bot.tree.command(name="steamid", description="Use this if you have paired with a server using the discord bot in the past")
async def free(interaction: discord.Interaction, your_steamid: str):

     idResponse = requests.post('https://backapi.rustalert.com/check-steamid', json={"SteamID": your_steamid, "Intention": "token"}, verify=False)

     if idResponse.success == False:
          await interaction.response.send_message('ur free')
          return

     print(idResponse)
        
     serverResponse = requests.post('https://backapi.rustalert.com/check-steamid', json={"SteamID": your_steamid, "Intention": "server"}, verify=False)

     if serverResponse.success == False:
          await interaction.response.send_message('')
          return

     print(serverResponse)

     await interaction.response.send_message('ur free')

# Raid notifications

async def watch_realtime(steamid: str):

     changes = supabase.channel('db-changes').on_postgres_changes(
     "UPDATE",
     schema="public",
     table="discord_servers",
     filter=f"steamid=eq.{steamid}",
     callback=lambda payload: print(payload)
     ).subscribe()

async def handle_trigger(payload: dict):
     ...





bot.run(token, log_handler = handler, log_level = logging.DEBUG)