import asyncio
from re import L
from config import *
import discord
from discord.ext import commands
from embed import *
from pytube import YouTube, Playlist, Search, exceptions
import shutil
from embed import get_search_results

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
	bot.queue = music_queue()
	bot.currently_playing = ""
	bot.previous_search = None

@bot.command()
async def setprefix(ctx, *arg):
	if(len(arg) != 1):
		await ctx.send(embed=get_error("usage: setprefix <prefix>"))

	else:
		prefix = arg[0]

		bot.config['guild']['prefix'] = prefix
		save_config(config_path, bot.config)

		await ctx.send(embed=get_success("set prefix to: {0}".format(prefix)))

@bot.command()
async def setrole(ctx, *arg: discord.Role):
	if(len(arg) != 1):
		await ctx.send(embed=get_error("usage: setrole @<rolename>"))

	else:
		roleid = arg[0].id

		bot.config['guild']['roleid'] = roleid
		save_config(config_path, bot.config)

		await ctx.send(embed=get_success("set playable role to {0}".format(arg[0])))

@bot.command()
async def leave(ctx):

	bot.queue.purge()
	bot.previous_search = None
	await ctx.voice_client.disconnect()
	try:
		shutil.rmtree('session/') # temporary cleanup procedure, will add caching later
	except FileNotFoundError: # if there is no session folder that's probably ok, just continue
		pass

@bot.command()
async def skip(ctx, *args):

	if (len(args) == 0):
		ctx.voice_client.stop() # stops and skips the current track
	elif (len(args) == 1) and args[0] == "next":
		x = bot.queue.dequeue()
		await ctx.send(embed=get_success("skipped {0}".format(x.title)))
		await ctx.send(embed=get_status(ctx.voice_client.channel, bot.queue, bot.currently_playing))
	elif (len(args) == 1) and args[0].lstrip('-+').isdigit(): 
		index = int(args[0])
		if(index >= bot.queue.num_remaining() or index < 0):
			await ctx.send(embed=get_error("index {0} out of range in queue of length {1}".format(index, bot.queue.num_remaining())))
		else:
			x = bot.queue.elem.pop(index)
			await ctx.send(embed=get_success("skipped {0}".format(x.title)))
			await ctx.send(embed=get_status(ctx.voice_client.channel, bot.queue, bot.currently_playing))
	else:
		await ctx.send(embed=get_error("usage:\nskip | skips this track\nskip next | skips the next track\nskip <index> | skips the track at index\n"))

@bot.command()
async def shuffle(ctx):

	roleid = bot.config['guild']['roleid']

	if(ctx.author.voice == None):
		await ctx.send(embed=get_error("you are not in a voice channel"))
		return
	elif(roleid not in [role.id for role in ctx.author.roles]):
		await ctx.send(embed=get_error("you do not have the role to play music"))
		return
	elif(not ctx.voice_client.is_connected()):
		await ctx.send(embed=get_error("bot is not connected to a voice channel"))
	else:
		bot.queue.shuffle()
		await ctx.send(embed=get_status(ctx.voice_client.channel, bot.queue, bot.currently_playing))

@bot.command()
async def play(ctx, *args):

	roleid = bot.config['guild']['roleid']
	prefix = bot.config['guild']['prefix']

	if(len(args) != 1):
		await ctx.send(embed=get_error("usage: {0}play <YouTube url>".format(prefix)))
		return
	elif(ctx.author.voice == None):
		await ctx.send(embed=get_error("you are not in a voice channel"))
		return
	elif(roleid not in [role.id for role in ctx.author.roles]):
		await ctx.send(embed=get_error("you do not have the role to play music"))
		return

	if args[0].lstrip('-+').isdigit():
		if bot.previous_search:
			index = int(args[0])
			if index >= len(bot.previous_search) or index < 0:
				await ctx.send(embed=get_error('index {0} out of range in results of length {1}'.format(index, len(bot.previous_search))))
				return
			else:
				yt = bot.previous_search[index]
				bot.queue.enqueue(yt)
				await ctx.send(embed=get_success('added {0} to queue'.format(yt.title)))
		else:
			await ctx.send(embed=get_error('no previous search found, use {0}search'.format(prefix)))
			return
	else:
		url = args[0]
		count = 0
		if 'list=' in url:
			pl = Playlist(url)
			for video in pl:
				yt = YouTube(video)
				bot.queue.enqueue(yt)
				count += 1
			await ctx.send(embed=get_success('added {0} tracks to queue'.format(len(pl))))
		else:
			yt = YouTube(url)
			bot.queue.enqueue(yt)
			await ctx.send(embed=get_success('added {0} to queue'.format(yt.title)))

	if(ctx.voice_client == None): # if not in vc, join
		channel = ctx.message.author.voice.channel
		await ctx.send(embed=get_success('Connected to ``{0}``'.format(channel)))
		await channel.connect()
		bot.queue.random = False
	elif (ctx.voice_client.channel != ctx.author.voice.channel): # if in another vc than author, ignore
		await ctx.send(embed=get_error("bot already connected to another channel, use {0}leave".format(prefix)))
		return

	if(ctx.voice_client.is_playing()):
		pass
	else:
		await bot.start_playing(ctx)

async def start_playing(ctx): # should guarantee ctx.voice_client.is_playing() is True

	event = asyncio.Event()
	event.set()

	while bot.queue.has_next():

		event.clear()

		yt = bot.queue.dequeue()
		name = yt.title
		id = yt.vid_info['videoDetails']['videoId']
		duration = yt.length

		bot.currently_playing = yt

		filepath = 'session/'
		fileprefix = ''
		filename = id

		if duration < bot.config['max-length']:

			await ctx.send(embed=get_status(ctx.voice_client.channel, bot.queue, bot.currently_playing))
			try: # try to get the music and then start playing
				yt.streams.filter(only_audio=True, file_extension='mp4').last().download(output_path=filepath, filename=filename, filename_prefix=fileprefix)
				path = filepath + fileprefix + filename
				ctx.voice_client.play(discord.FFmpegPCMAudio(path), after=lambda e:event.set())
			except exceptions.AgeRestrictedError: # if it is age restricted, just skip
				await ctx.send(embed=get_error('{0} is age restricted'.format(name, duration, bot.config['max-length'])))
				event.set()

		else:
			await ctx.send(embed=get_error('{0} is too long: {1} > {2}'.format(name, duration, bot.config['max-length'])))

		await event.wait()

bot.start_playing = start_playing

@bot.command()
async def search(ctx, *args):

	roleid = bot.config['guild']['roleid']
	prefix = bot.config['guild']['prefix']

	if(len(args) == 0):
		await ctx.send(embed=get_error("usage: {0}search <query>".format(prefix)))
		return
	elif(ctx.author.voice == None):
		await ctx.send(embed=get_error("you are not in a voice channel"))
		return
	elif(roleid not in [role.id for role in ctx.author.roles]):
		await ctx.send(embed=get_error("you do not have the role to play music"))
		return

	query = ""

	for w in args:
		query += w + " "

	s = Search(query)
	bot.previous_search = s.results
	await ctx.send(embed=get_search_results(query, s.results))

@bot.command()
async def peek(ctx, *args):

	roleid = bot.config['guild']['roleid']
	prefix = bot.config['guild']['prefix']

	if(len(args) != 0):
		await ctx.send(embed=get_error("usage: {0}peek".format(prefix)))
		return
	elif(ctx.author.voice == None):
		await ctx.send(embed=get_error("you are not in a voice channel"))
		return
	elif(roleid not in [role.id for role in ctx.author.roles]):
		await ctx.send(embed=get_error("you do not have the role to play music"))
		return

	await ctx.send(embed=get_queue(ctx.voice_client.channel, bot.queue, bot.currently_playing))

@bot.command()
async def pause(ctx, *args):

	roleid = bot.config['guild']['roleid']
	prefix = bot.config['guild']['prefix']

	if(len(args) != 0):
		await ctx.send(embed=get_error("usage: {0}pause".format(prefix)))
		return
	elif(ctx.author.voice == None):
		await ctx.send(embed=get_error("you are not in a voice channel"))
		return
	elif(roleid not in [role.id for role in ctx.author.roles]):
		await ctx.send(embed=get_error("you do not have the role to play music"))
		return

	ctx.voice_client.pause()
	await ctx.send(embed=get_success("paused"))

@bot.command()
async def resume(ctx, *args):

	roleid = bot.config['guild']['roleid']
	prefix = bot.config['guild']['prefix']

	if(len(args) != 0):
		await ctx.send(embed=get_error("usage: {0}resume".format(prefix)))
		return
	elif(ctx.author.voice == None):
		await ctx.send(embed=get_error("you are not in a voice channel"))
		return
	elif(roleid not in [role.id for role in ctx.author.roles]):
		await ctx.send(embed=get_error("you do not have the role to play music"))
		return

	ctx.voice_client.resume()
	await ctx.send(embed=get_success("resumed"))

bot.run(token)