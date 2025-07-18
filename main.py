import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
from supabase import create_client, Client, create_async_client
from supabase.client import ClientOptions
from datetime import datetime, timezone
from discord import FFmpegPCMAudio, FFmpegAudio
import asyncio
import requests
import urllib3
import os

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()
token = os.getenv('DISCORD_TOKEN')
steam_key = os.getenv('STEAM_KEY')

url: str = os.getenv('SUPABASE_URL')
key: str = os.getenv('SUPABASE_KEY')

active_subscriptions = {}

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

# Bot Classes

class InitialButtons(discord.ui.View):

    @discord.ui.button(label = "Yes, I am already paired", style = discord.ButtonStyle.green)
    async def yes_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.message.edit(view = None)
        await interaction.response.send_message("```Enter the email your RustAlert account is under using /email```", ephemeral = True)

    @discord.ui.button(label = "No, I need to pair with a server", style = discord.ButtonStyle.red)
    async def no_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.message.edit(view = ChooseAudio())

class RegisterWithRustPlus(discord.ui.View):

     embed = discord.Embed(title="RustAlert Pairing Process", description= "", color = discord.Color.from_rgb(216, 0, 0))
     embed.set_thumbnail(url = "https://cdn.discordapp.com/attachments/1382848303674167357/1382853711377731754/maybeicon.png?ex=685887e0&is=68573660&hm=8189d9fa99a4b66dfc319408cae701c495e97a436ddd33215c3131757b91604f&")
     embed.add_field(name = "Step 2", value = "```Are you currently paired to a server using the RustAlert website dashboard?```")


class ChooseVC(discord.ui.View):
     def __init__(self):
        super().__init__()
        self.channel_select = discord.ui.ChannelSelect(
            channel_types=[discord.ChannelType.voice],
            placeholder="Select a voice channel",
            min_values=1,
            max_values=1,
            custom_id="voice_channel_select"
        )
        self.channel_select.callback = self.channel_callback
        self.add_item(self.channel_select)

     async def channel_callback(self, interaction: discord.Interaction):
        selected_channel = interaction.data["values"][0]
        selected_channel_id = int(selected_channel)
        channel = interaction.guild.get_channel(int(selected_channel))

        with open('settings.txt', 'w') as w:
             w.write('')
        with open('settings.txt', 'a') as f:
             f.write(f'voice_channel={selected_channel_id}\n')
        await interaction.response.send_message(f"Channel selected", ephemeral=True)


class ChooseAudio(discord.ui.View):
     def __init__(self):
        super().__init__()
        self.select = discord.ui.Select(placeholder="Select an audio", min_values=1, max_values=1,
            options=[
            discord.SelectOption(label="Joey Diaz", value="joey", emoji="🦅", description='If you want to get hype'),
            discord.SelectOption(label="Donald Trump", value="trump", emoji="💵", description='47th President of the US'),
            discord.SelectOption(label="Arthur Morgan", value="trump", emoji="🤠", description='Hey boah hop on'),
            discord.SelectOption(label="Chicken Balls", value="chickenballs", emoji="🐔", description='Hey boah hop on'),
            discord.SelectOption(label="Hot", value="hot", emoji="🔥", description='Old white man'),
            discord.SelectOption(label="Crab Rave", value="crab", emoji="🦀", description='You already know what it is')
        ])
        self.select.callback = self.select_callback
        self.add_item(self.select)

     async def select_callback(self, interaction: discord.Interaction):
        choice = self.select.values[0]
        with open('settings.txt', 'a') as f:
             f.write(f'audio={choice}\n')
        await interaction.response.send_message(f"Server pairing succesfully set up. Now, connect a seismic sensor to a smart alarm and click pair on the smart alarm.", ephemeral=True)

# Bot tree commands

@bot.tree.command(name="pair", description="Start the pairing process")
async def startprocess(interaction: discord.Interaction):
    embed = discord.Embed(title="RustAlert Pairing Process", description= "", color = discord.Color.from_rgb(216, 0, 0))
    embed.set_thumbnail(url = "https://cdn.discordapp.com/attachments/1382848303674167357/1382853711377731754/maybeicon.png?ex=685887e0&is=68573660&hm=8189d9fa99a4b66dfc319408cae701c495e97a436ddd33215c3131757b91604f&")
    embed.add_field(name = "Step 1", value = "```Are you currently paired to a server using the RustAlert website dashboard?```")
    await interaction.response.send_message(embed = embed, view = InitialButtons())


@bot.tree.command(name="email",description='Enter your RustAlert email address')
async def inputemail(interaction: discord.Interaction, your_email: str):

        response = requests.post('https://backapi.rustalert.com/get-steamid', json={"email": your_email}, verify=False)

        data = response.json()

        if data:
             print(data)
             steamid = data['data']['steam_id']
             print(steamid)

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
             await interaction.response.send_message(f"Email found, but you are not paired with a server. Pair with a server on the website dashboard and try again.", ephemeral = True)
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
        await premium_realtime(steamid, interaction.channel)


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

     await interaction.response.send_message("Account successfully linked, do not use the Rust+ app, RustAlert works independently of it. Now go in-game, press escape and click Rust+, and click Pair with Server")

     response = requests.post('https://backapi.rustalert.com/pair-with-server', json={"steamid": SteamID, "token": PlayerToken}, verify=False)

     serverName = ''
     
     for attempt in range(30):
          response = requests.post('https://backapi.rustalert.com/server-stats', json={"SteamID": SteamID}, verify=False)
          if response.ok:
               print(f'Server found after {attempt + 1} attempts')
               data = response.json()
               serverName = data['name']
               await interaction.followup.send(f"✅ Successfully paired with server: ```{serverName}```")
               await interaction.followup.send(f"Select the voice channel you want the bot to join when you get raided", view=ChooseVC(), ephemeral=True)
               break
          print(f'Attempt {attempt + 1}: Server not ready')
          await asyncio.sleep(2)
     else:
          await interaction.followup.send("❌ Pairing for server timed out. Use /steamid to try again when ready")

     await watch_realtime(SteamID, interaction.channel)



     

@bot.tree.command(name="disconnect", description="Disconnect from a server")
async def disconnect(interaction: discord.Interaction, steam_id: str):

     #serverResponse = requests.post('https://backapi.rustalert.com/check-steamid', json={"SteamID": steam_id, "Intention": "server"}, verify=False)

     #if serverResponse.success == False:
     #     await interaction.response.send_message(f'No active server pair found for the SteamID: {steam_id}. Pair with a server and try again. Use /help for additional help.', ephemeral=True)
     #     return

     response = requests.post('https://backapi.rustalert.com/disconnect', json={"steamId": steam_id}, verify=False)

     print(response)

     if steam_id in active_subscriptions:
          try:
               await active_subscriptions[steam_id].unsubscribe()
               del active_subscriptions[steam_id]
               print(f'Unsubscribed from realtime updates for steamid: {steam_id}')
          except Exception as e:
               print(f'Error unsubscribing from realtime updates: {e}')

     await interaction.response.send_message('Succesfully disconnected from server.')  


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

     with open("settings.txt", "r") as f:
        for line in f:
            if line.startswith("voice_channel="):
                channel_id = int(line.strip().split("=")[1])
                break
        else:
            print("❌ No voice channel found in settings.")
            return
        
     channel = await bot.fetch_channel(channel_id)
     voice_client = await channel.connect()

     audio_source = discord.FFmpegPCMAudio("./sounds/default.mp3")
     audio_source = discord.PCMVolumeTransformer(audio_source, volume=0.4)
     voice_client.play(audio_source)
     print('playing')

     while voice_client.is_playing():
          await asyncio.sleep(.1)
            
     await voice_client.disconnect()
       


@bot.tree.command(name="steamid", description="Use this if you have paired with a server using the discord bot in the past")
async def free(interaction: discord.Interaction, your_steamid: str):

     idResponse = requests.post('https://backapi.rustalert.com/check-steamid', json={"SteamID": your_steamid, "Intention": "token"}, verify=False)

     print(idResponse)

     if not idResponse.ok:
          await interaction.response.send_message('No token found for this SteamID. Use /setup and try again.')
          return

        
     serverResponse = requests.post('https://backapi.rustalert.com/check-steamid', json={"SteamID": your_steamid, "Intention": "server"}, verify=False)

     print(serverResponse)

     if not serverResponse.ok:
          await interaction.response.send_message('This SteamID is already paired with a server. Use /disconnect and try again.')
          return

     response = requests.post('https://backapi.rustalert.com/player-token', json={"SteamID": your_steamid}, verify=False)

     responseData = response.json()
     SteamId = responseData['steamid']
     PlayerToken = responseData['token']

     await interaction.response.send_message("Account successfully linked, do not use the Rust+ app, RustAlert works independently of it. Now go in-game, press escape and click Rust+, and click Pair with Server")

     response = requests.post('https://backapi.rustalert.com/pair-with-server', json={"steamid": SteamId, "token": PlayerToken}, verify=False)

     serverName = ''
     
     for attempt in range(30):
          response = requests.post('https://backapi.rustalert.com/server-stats', json={"SteamID": SteamId}, verify=False)
          if response.ok:
               print(f'Server found after {attempt + 1} attempts')
               data = response.json()
               serverName = data['name']
               await interaction.followup.send(f"✅ Successfully paired with server: ```{serverName}```")
               await interaction.followup.send(f"Select the voice channel you want the bot to join when you get raided", view=ChooseVC(), ephemeral=True)
               await interaction.followup.send(f"Select the audio you want the bot to play when you get raided", view=ChooseAudio(), ephemeral=True)
               break
          print(f'Attempt {attempt + 1}: Server not ready')
          await asyncio.sleep(2)
     else:
          await interaction.followup.send("❌ Pairing for server timed out. Use /steamid to try again when ready")

     await watch_realtime(SteamId, interaction.channel)


# Raid notifications

async def watch_realtime(steamid: str, channel=None):

     supabase = create_async_client(
         url,
         key,
         options=ClientOptions(
             schema = "public"
         )
     )
     supabase = await supabase

     def callback(payload):
         print(f"Callback triggered with payload: {payload}")
         asyncio.create_task(handle_trigger(payload, channel))

     changes = supabase.channel('db-changes').on_postgres_changes(
     "UPDATE",
     schema="public",
     table="discord_servers",
     filter=f"steamid=eq.{steamid}",
     callback=callback
     )

     await changes.subscribe()
     print(f'watching for changes on steamid: {steamid}')
     
     active_subscriptions[steamid] = changes
     
     return changes

async def handle_trigger(payload: dict, channel=None):
     
     row = payload["data"]["record"]
     status = row.get("status")
     name = row.get("name")
     steamid = row.get('steamid')
     triggers = 0

     if status == "connected":
        
        embed = discord.Embed(title = "RustAlert Server Status", description = "", color = discord.Color.from_rgb(216, 0, 0))
        embed.set_thumbnail(url = "https://cdn.discordapp.com/attachments/1382848303674167357/1382853711377731754/maybeicon.png?ex=685887e0&is=68573660&hm=8189d9fa99a4b66dfc319408cae701c495e97a436ddd33215c3131757b91604f&")
        embed.add_field(name = "SERVER NAME: ", value = f"```{name}```", inline = False)
        embed.add_field(name = "SMART ALARM: ", value = f"```CONNECTED```")
        embed.add_field(name = "TRIGGERS: ", value = f"```{triggers}```")
        embed.add_field(name = "LAST CALL: ", value = f"```NEVER```")

        await channel.send(f"✅ **Alert:** Smart Alarm was succesfully paired on `{name}`!")
        
        await channel.send(embed=embed)

     if status == 'triggered':
        
        triggers = triggers+1
        
        embed = discord.Embed(title = "RustAlert Server Status", description = "", color = discord.Color.from_rgb(216, 0, 0))
        embed.set_thumbnail(url = "https://cdn.discordapp.com/attachments/1382848303674167357/1382853711377731754/maybeicon.png?ex=685887e0&is=68573660&hm=8189d9fa99a4b66dfc319408cae701c495e97a436ddd33215c3131757b91604f&")
        embed.add_field(name = "SERVER NAME: ", value = f"```{name}```", inline = False)
        embed.add_field(name = "SMART ALARM: ", value = f"```TRIGGERED```")
        embed.add_field(name = "TRIGGERS: ", value = f"```{triggers}```")
        embed.add_field(name = "LAST CALL: ", value = f"```JUST NOW```")

        await channel.send(f"⚠️ **Alert:** Smart Alarm was triggered on `{name}`!")
        await channel.send(embed=embed)
        await join_vc(steamid)

async def write_config(interaction: discord.Interaction):
     await interaction.response.send_message(f"Select the voice channel you want the bot to join when you get raided", view=ChooseVC(), ephemeral=True)

async def join_vc(SteamID: str):
     with open("settings.txt", "r") as f:
        for line in f:
            if line.startswith("voice_channel="):
                channel_id = int(line.strip().split("=")[1])
                break
        else:
            print("❌ No voice channel found in settings.")
            return
        
     with open("settings.txt", "r") as f:
        for line in f:
            if line.startswith("audio="):
                music = int(line.strip().split("=")[1])
                break
        else:
            print("❌ No voice channel found in settings.")
            return
        
     try:
        channel = await bot.fetch_channel(channel_id)
     except discord.NotFound:
        print("Channel not found.")
        return
     
     if isinstance(channel, discord.VoiceChannel):
        voice_client = await channel.connect()

        if check_name(SteamID):
          audio_source = discord.FFmpegPCMAudio(f"./sounds/{music}.mp3")
          audio_source = discord.PCMVolumeTransformer(audio_source, volume=0.4)
        else:
          audio_source = discord.FFmpegPCMAudio("./sounds/default.mp3")
          audio_source = discord.PCMVolumeTransformer(audio_source, volume=0.4)
          print('this would be default')

        voice_client.play(audio_source)

        while voice_client.is_playing():
            await asyncio.sleep(.1)
            
        await voice_client.disconnect()
        print(f"Joined voice channel: {channel.name}")
     else:
        print("❌ Channel ID does not point to a voice channel.")


def check_name(SteamID: str) -> bool:
     response = requests.get(f'http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={steam_key}&steamids={SteamID}', verify=False)
     data = response.json()
     name = data['response']['players'][0]['personaname']
     print(name)

     if 'rustalert' in name.lower() or 'rust alert' in name.lower():
          return True
     else:
          return False
     

# Raid notifications for premium

async def premium_realtime(steamid: str, channel=None):

     print(f'stating realtime with steamid {steamid}')

     supabase = create_async_client(
         url,
         key,
         options=ClientOptions(
             schema = "public"
         )
     )
     supabase = await supabase

     def callback(payload):
         print(f"Callback triggered with payload: {payload}")
         asyncio.create_task(premium_trigger(payload, channel))

     changes = supabase.channel('premium-changes').on_postgres_changes(
     "UPDATE",
     schema="public",
     table="servers",
     filter=f"steam_id=eq.{steamid}",
     callback=callback
     )

     await changes.subscribe()
     print(f'watching for changes on steamid: {steamid}')
     
     active_subscriptions[steamid] = changes
     
     return changes


async def premium_trigger(payload: dict, channel=None):
     
     row = payload["data"]["record"]
     status = row.get("status")
     name = row.get("name")
     new_triggers = row.get("triggers")
     triggers = 0


     if new_triggers > triggers:
        
        triggers = new_triggers
        
        embed = discord.Embed(title = "RustAlert Server Status", description = "", color = discord.Color.from_rgb(216, 0, 0))
        embed.set_thumbnail(url = "https://cdn.discordapp.com/attachments/1382848303674167357/1382853711377731754/maybeicon.png?ex=685887e0&is=68573660&hm=8189d9fa99a4b66dfc319408cae701c495e97a436ddd33215c3131757b91604f&")
        embed.add_field(name = "SERVER NAME: ", value = f"```{name}```", inline = False)
        embed.add_field(name = "SMART ALARM: ", value = f"```TRIGGERED```")
        embed.add_field(name = "TRIGGERS: ", value = f"```{triggers}```")
        embed.add_field(name = "LAST CALL: ", value = f"```JUST NOW```")

        await channel.send(f"⚠️ **Alert:** Smart Alarm was triggered on `{name}`!")
        await channel.send(embed=embed)
        await premium_vc()


async def premium_vc():

     with open("settings.txt", "r") as f:
        for line in f:
            if line.startswith("voice_channel="):
                channel_id = int(line.strip().split("=")[1])
                break
        else:
            print("❌ No voice channel found in settings.")
            return
        
     with open("settings.txt", "r") as f:
        for line in f:
            if line.startswith("audio="):
                music = int(line.strip().split("=")[1])
                break
        else:
            print("❌ No voice channel found in settings.")
            return
        
     try:
        channel = await bot.fetch_channel(channel_id)
     except discord.NotFound:
        print("Channel not found.")
        return
     
     if isinstance(channel, discord.VoiceChannel):
        voice_client = await channel.connect()
        audio_source = discord.FFmpegPCMAudio(f"./sounds/{music}.mp3")
        voice_client.play(audio_source)
        await voice_client.disconnect()
        print(f"Joined voice channel: {channel.name}")
     else:
        print("❌ Channel ID does not point to a voice channel.")



bot.run(token, log_handler = handler, log_level = logging.DEBUG)