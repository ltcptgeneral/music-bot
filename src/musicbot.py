from asyncio import sleep
import discord
from discord.ext import commands
from config import *
from pytube import YouTube, Playlist
import shutil

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
async def play(ctx, *arg):

	roleid = bot.config['guild']['roleid']

	if(len(arg) != 1):
		await ctx.send("usage: play <YouTube url>")
		return
	elif(ctx.author.voice == None):
		await ctx.send("you're not in a voice channel")
		return
	elif(roleid not in [role.id for role in ctx.author.roles]):
		print()
		await ctx.send("you do not have the role to play music")
		return

	try:
		await ctx.voice_client.disconnect()
	except:
		pass

	url = arg[0]

	yt = YouTube(url)
	name = yt.title
	duration = yt.length

	filepath = 'session/'
	fileprefix = ''
	filename = name

	if duration < 1200:
		await ctx.send("downloading music requested: {0}".format(name))

		yt.streams.filter(only_audio=True, file_extension='mp4').last().download(output_path=filepath, filename=filename, filename_prefix=fileprefix)

		path = filepath + fileprefix + filename

		await ctx.author.voice.channel.connect()
		ctx.voice_client.play(discord.FFmpegPCMAudio(path), after=lambda e: print('Player error: %s' % e) if e else None)

		while ctx.voice_client.is_playing():
			await sleep(0.01)
		await ctx.voice_client.disconnect()

	else:
		await ctx.send("music requested was too long ({0} > 1200)".format(duration))

	shutil.rmtree('session/') # temporary cleanup procedure, will add caching later

bot.run(token)