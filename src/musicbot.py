import asyncio
from re import L
from config import *
import nextcord
from nextcord.ext import commands
from embed import *
from pytube import Playlist, Search, exceptions
import shutil
from embed import get_search_results
from parse import search, parse
from typing import Optional

from pytubefix import YouTube
from pytubefix.cli import on_progress

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

intents = nextcord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(description='very cool', intents = intents)
bot.config = config

@bot.event
async def on_ready():
	print('Logged in as {0} ({0.id})'.format(bot.user))
	print('------')
	bot.queue = music_queue()
	bot.currently_playing = ""
	bot.previous_search = None
	print('Initialized queue')

@bot.slash_command()
async def setrole(ctx, role: nextcord.Role):
	await ctx.response.defer()
	roleid = role.id

	bot.config['guild']['roleid'] = roleid
	save_config(config_path, bot.config)

	await ctx.send(embed=get_success("set playable role to {0}".format(role[0])))

@bot.slash_command()
async def leave(ctx):
	await ctx.response.defer()
	bot.queue.purge()
	bot.previous_search = None
	await ctx.guild.voice_client.disconnect()
	await ctx.send(embed=get_success("left voice channel and cleared queue"))
	try:
		shutil.rmtree('session/') # temporary cleanup procedure, will add caching later
	except FileNotFoundError: # if there is no session folder that's probably ok, just continue
		pass

@bot.slash_command()
async def skip(ctx, track: Optional[str] = nextcord.SlashOption(required=False)):
	await ctx.response.defer()
	if (track == None): # stops and skips the current track
		ctx.guild.voice_client.stop()
		x = bot.currently_playing
		await ctx.send(embed=get_success("skipped {0}".format(x.title)))
	elif track == "next": # skips the next track
		x = bot.queue.dequeue()
		await ctx.send(embed=get_success("skipped {0}".format(x.title)))
		await ctx.send(embed=get_status(ctx.guild.voice_client.channel, bot.queue, bot.currently_playing))
	elif await search("{:d}", track): 
		index = await parse("{:d}", track)[0]
		if(index >= bot.queue.num_remaining() or index < 0):
			await ctx.send(embed=get_error("index {0} out of range in queue of length {1}".format(index, bot.queue.num_remaining())))
		else:
			x = bot.queue.elem.pop(index)
			await ctx.send(embed=get_success("skipped {0}".format(x.title)))
			await ctx.send(embed=get_status(ctx.guild.voice_client.channel, bot.queue, bot.currently_playing))
	else:
		await ctx.send(embed=get_error("usage:\nskip | skips this track\nskip next | skips the next track\nskip <index> | skips the track at index\n"))

@bot.slash_command()
async def shuffle(ctx):
	await ctx.response.defer()
	roleid = bot.config['guild']['roleid']

	if(ctx.user.voice == None):
		await ctx.send(embed=get_error("you are not in a voice channel"))
		return
	elif(roleid not in [role.id for role in ctx.user.roles]):
		await ctx.send(embed=get_error("you do not have the role to play music"))
		return
	elif(ctx.guild.voice_client == None):
		await ctx.send(embed=get_error("bot is not connected to a voice channel"))
	else:
		bot.queue.shuffle()
		await ctx.send(embed=get_status(ctx.guild.voice_client.channel, bot.queue, bot.currently_playing))

@bot.slash_command()
async def play(ctx: nextcord.Interaction, url: str):
	await ctx.response.defer()
	roleid = bot.config['guild']['roleid']

	if(ctx.user.voice == None):
		await ctx.send(embed=get_error("you are not in a voice channel"))
		return
	elif(roleid not in [role.id for role in ctx.user.roles]):
		await ctx.send(embed=get_error("you do not have the role to play music"))
		return

	if url.lstrip('-+').isdigit():
		if bot.previous_search:
			index = int(url)
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
		count = 0
		if 'list=' in url:
			pl = Playlist(url)
			for video in pl:
				yt = YouTube(video, on_progress_callback = on_progress)
				bot.queue.enqueue(yt)
				count += 1
			await ctx.send(embed=get_success('added {0} tracks to queue'.format(len(pl))))
		else:
			yt = YouTube(url, on_progress_callback = on_progress)
			bot.queue.enqueue(yt)
			await ctx.send(embed=get_success('added {0} to queue'.format(yt.title)))

	if(ctx.guild.voice_client == None): # if not in vc, join
		channel = ctx.user.voice.channel
		await ctx.send(embed=get_success('Connected to ``{0}``'.format(channel)))
		await channel.connect()
		bot.queue.random = False
	elif (ctx.guild.voice_client.channel != ctx.user.voice.channel): # if in another vc than author, ignore
		await ctx.send(embed=get_error("bot already connected to another channel, use {0}leave".format(prefix)))
		return

	if(ctx.guild.voice_client.is_playing()):
		pass
	else:
		await bot.start_playing(ctx)

async def start_playing(ctx): # should guarantee ctx.guild.voice_client.is_playing() is True
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

			await ctx.send(embed=get_status(ctx.guild.voice_client.channel, bot.queue, bot.currently_playing))
			try: # try to get the music and then start playing
				yt.streams.filter(only_audio=True, file_extension='mp4').last().download(output_path=filepath, filename=filename, filename_prefix=fileprefix)
				path = filepath + fileprefix + filename
				ctx.guild.voice_client.play(nextcord.FFmpegPCMAudio(path), after=lambda e:event.set())
			except exceptions.AgeRestrictedError: # if it is age restricted, just skip
				await ctx.send(embed=get_error('{0} is age restricted'.format(name, duration, bot.config['max-length'])))
				event.set()

		else:
			await ctx.send(embed=get_error('{0} is too long: {1} > {2}'.format(name, duration, bot.config['max-length'])))

		await event.wait()

bot.start_playing = start_playing

@bot.slash_command()
async def search(ctx, query: str):
	await ctx.response.defer()
	roleid = bot.config['guild']['roleid']

	if(ctx.user.voice == None):
		await ctx.send(embed=get_error("you are not in a voice channel"))
		return
	elif(roleid not in [role.id for role in ctx.user.roles]):
		await ctx.send(embed=get_error("you do not have the role to play music"))
		return

	s = Search(query)
	bot.previous_search = s.results
	await ctx.send(embed=get_search_results(query, s.results))

@bot.slash_command()
async def peek(ctx):
	await ctx.response.defer()
	roleid = bot.config['guild']['roleid']

	if(ctx.user.voice == None):
		await ctx.send(embed=get_error("you are not in a voice channel"))
		return
	elif(roleid not in [role.id for role in ctx.user.roles]):
		await ctx.send(embed=get_error("you do not have the role to play music"))
		return
	elif(ctx.guild.voice_client == None):
		await ctx.send(embed=get_error("bot is not connected to a voice channel"))

	await ctx.send(embed=get_queue(ctx.guild.voice_client.channel, bot.queue, bot.currently_playing))

@bot.slash_command()
async def pause(ctx):
	await ctx.response.defer()
	roleid = bot.config['guild']['roleid']
	
	if(ctx.user.voice == None):
		await ctx.send(embed=get_error("you are not in a voice channel"))
		return
	elif(roleid not in [role.id for role in ctx.user.roles]):
		await ctx.send(embed=get_error("you do not have the role to play music"))
		return
	elif(ctx.guild.voice_client == None):
		await ctx.send(embed=get_error("bot is not connected to a voice channel"))

	ctx.guild.voice_client.pause()
	await ctx.send(embed=get_success("paused"))

@bot.slash_command()
async def resume(ctx):
	await ctx.response.defer()
	roleid = bot.config['guild']['roleid']

	if(ctx.user.voice == None):
		await ctx.send(embed=get_error("you are not in a voice channel"))
		return
	elif(roleid not in [role.id for role in ctx.user.roles]):
		await ctx.send(embed=get_error("you do not have the role to play music"))
		return
	elif(ctx.guild.voice_client == None):
		await ctx.send(embed=get_error("bot is not connected to a voice channel"))

	ctx.guild.voice_client.resume()
	await ctx.send(embed=get_success("resumed"))

bot.run(token)