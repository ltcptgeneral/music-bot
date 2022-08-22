import asyncio
import discord
from discord.ext import commands
from config import *
from pytube import YouTube, Playlist
import shutil

from music_queue import music_queue

config_path = "config.json"

ffmpeg_options = {
	'options': '-vn'
}

config = {}
x = load_config(config_path, config)
if x == 1:
	print('Failed to load config, exiting')
	exit(1)
token = config['guild']['token']
prefix = config['guild']['prefix']

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix = prefix, description='very cool', intents = intents)
bot.config = config

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

		bot.config['guild']['prefix'] = prefix
		save_config(config_path, bot.config)

		await ctx.send("set prefix to: {0}".format(prefix))

@bot.command()
async def setrole(ctx, *arg: discord.Role):
	if(len(arg) != 1):
		await ctx.send("usage: setrole @<rolename>")

	else:
		roleid = arg[0].id

		bot.config['guild']['roleid'] = roleid
		save_config(config_path, bot.config)

		await ctx.send("set playable role to {0}".format(arg[0]))

@bot.command()
async def join(ctx):

	roleid = bot.config['guild']['roleid']

	if not ctx.message.author.voice:
		await ctx.send("You are not connected to a voice channel!")
		return
	elif(roleid not in [role.id for role in ctx.author.roles]):
		await ctx.send("you do not have the role to play music")
		return
	else:
		channel = ctx.message.author.voice.channel
		bot.queue = music_queue()
		await ctx.send(f'Connected to ``{channel}``')
		await channel.connect()
		return

@bot.command()
async def leave(ctx):

	await ctx.voice_client.disconnect()

@bot.command()
async def play(ctx, *arg):

	roleid = bot.config['guild']['roleid']

	if(len(arg) != 1):
		await ctx.send("usage: play <YouTube url>")
		return
	elif(ctx.author.voice == None):
		await ctx.send("you're not in a voice channel")
		return
	elif(roleid not in [role.id for role in ctx.author.roles]):
		await ctx.send("you do not have the role to play music")
		return

	url = arg[0]

	if 'list=' in url:
		pl = Playlist(url)
		for video in pl:
			yt = YouTube(video)
			bot.queue.enqueue(yt)
	else:
		yt = YouTube(url)
		bot.queue.enqueue(url)

	if(ctx.voice_client.is_playing()):
		pass
	else:
		await bot.start_playing(ctx.voice_client)

async def start_playing(voice_client):

	event = asyncio.Event()
	event.set()

	while bot.queue.has_next():

		event.clear()

		yt = bot.queue.dequeue()
		name = yt.title
		duration = yt.length

		filepath = 'session/'
		fileprefix = ''
		filename = name

		if duration < 1200:

			yt.streams.filter(only_audio=True, file_extension='mp4').last().download(output_path=filepath, filename=filename, filename_prefix=fileprefix)
			path = filepath + fileprefix + filename
			voice_client.play(discord.FFmpegPCMAudio(path), after=lambda e:event.set())

		else:
			pass

		await event.wait()
	
	await voice_client.disconnect()

bot.start_playing = start_playing

bot.run(token)