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
	bot.queue = None

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
	bot.queue = None
	shutil.rmtree('session/') # temporary cleanup procedure, will add caching later

@bot.command()
async def skip(ctx):

	ctx.voice_client.stop() # stops and skips the current track

@bot.command()
async def shuffle(ctx):

	if bot.queue:
		bot.queue.random = not bot.queue.random
		await ctx.send("shuffle set to {0}".format(bot.queue.random))
	else:
		await ctx.send("not in a voice chat, use {0}join".format(bot.config['guild']['prefix']))

@bot.command()
async def play(ctx, *arg):

	roleid = bot.config['guild']['roleid']

	if(len(arg) != 1):
		await ctx.send("usage: play <YouTube url>")
		return
	elif(ctx.author.voice == None):
		await ctx.send("you are not in a voice channel")
		return
	elif(roleid not in [role.id for role in ctx.author.roles]):
		await ctx.send("you do not have the role to play music")
		return
	elif(bot.queue == None):
		await ctx.send("not in a voice chat, use {0}join".format(bot.config['guild']['prefix']))
		return

	url = arg[0]

	count = 0

	if 'list=' in url:
		pl = Playlist(url)
		for video in pl:
			yt = YouTube(video)
			bot.queue.enqueue(yt)
			count += 1
		await ctx.send('added {0} tracks to queue'.format(len(pl)))
	else:
		yt = YouTube(url)
		bot.queue.enqueue(yt)
		await ctx.send('added {0} to queue'.format(yt.title))

	if(ctx.voice_client.is_playing()):
		pass
	else:
		await bot.start_playing(ctx)

async def start_playing(ctx):

	event = asyncio.Event()
	event.set()

	try:

		while bot.queue.has_next():

			event.clear()

			yt = bot.queue.dequeue()
			name = yt.title
			duration = yt.length

			filepath = 'session/'
			fileprefix = ''
			filename = name

			if duration < bot.config['max-length']:

				await ctx.send('playing {0} | {1} tracks remaining in queue'.format(name, len(bot.queue.elem)))

				yt.streams.filter(only_audio=True, file_extension='mp4').last().download(output_path=filepath, filename=filename, filename_prefix=fileprefix)
				path = filepath + fileprefix + filename
				ctx.voice_client.play(discord.FFmpegPCMAudio(path), after=lambda e:event.set())

			else:
				await ctx.send('{0} is too long: {1} > {2}'.format(name, duration, bot.config['max-length']))

			await event.wait()

	except AttributeError:
		pass

	except Exception as e:
		print(e)

	bot.queue = None

bot.start_playing = start_playing

bot.run(token)