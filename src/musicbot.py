from asyncio import sleep
import discord
from discord.ext import commands
import yt_dlp
from config import *

config_path = "config.json"

ffmpeg_options = {
	'options': '-vn'
}

token = get_token(config_path)

async def determine_prefix(bot, message):
	return get_prefix(config_path)

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix = determine_prefix, description='very cool', intents = intents)

@bot.event
async def on_ready():
	print('Logged in as {0} ({0.id})'.format(bot.user))
	print('------')

@bot.command()
async def setprefix(ctx, *arg):
	if(len(arg) != 1):
		await ctx.send("usage: setprefix <prefix>")

	else:
		prefix = arg[0]

		with open("prefix", "w") as f:
			f.write(prefix)
			f.close()

		await ctx.send("set prefix to: {0}".format(prefix))

@bot.command()
async def setrole(ctx, *arg: discord.Role):
	if(len(arg) != 1):
		await ctx.send("usage: setrole @<rolename>")

	else:
		roleid = arg[0].id

		with open("roleid", "w") as f:
			f.write(str(roleid))
			f.close()

		await ctx.send("set followable role to {0}".format(arg[0]))

@bot.command()
async def playmusic(ctx, *arg):

	ydl_opts = {
		'format': 'mp4',
		'quiet': True,
		'paths': {
			'home': './session/'
		},
		'outtmpl': {
			'default': '%(autonumber)s.%(ext)s',
		},
		'postprocessors': [{
			'key': 'FFmpegExtractAudio',
		}],
	}

	try:
		await ctx.voice_client.disconnect()
	except:
		pass

	url = arg[0]

	with yt_dlp.YoutubeDL(ydl_opts) as ydl:
		info = ydl.extract_info(url, download=False)
		duration = info.get('duration')
		name = info.get('title')
		if duration < 1200:
			await ctx.send("downloading music requested: {0}".format(name))
			ydl.download([url])
			audio = "session/00001.m4a"
			await ctx.author.voice.channel.connect()
			ctx.voice_client.play(discord.FFmpegPCMAudio(audio), after=lambda e: print('Player error: %s' % e) if e else None)
			while ctx.voice_client.is_playing():
				await sleep(0.01)
			await ctx.voice_client.disconnect()
		else:
			await ctx.send("music requested was too long ({0} > 1200)".format(duration))

bot.run(token)