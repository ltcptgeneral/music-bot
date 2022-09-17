import discord
from pytube import YouTube

def get_status(channel, queue, playing):
	desc = 'playing {0} in {1}'.format(playing.title, channel)
	emb = discord.Embed(title='music-bot', description=desc,color=0x0000FF)
	if(queue.has_next()):
		lst = "next up: {0}".format(queue.elem[0].title)
	else:
		lst = "empty queue"
	emb.add_field(name="{0} tracks left in queue".format(queue.num_remaining()), value=lst)
	emb.set_thumbnail(url=playing.thumbnail_url)
	return emb

def get_queue(channel, queue, playing):
	desc = 'playing {0} in {1}'.format(playing.title, channel)
	emb = discord.Embed(title='music-bot', description=desc,color=0x0000FF)
	lst = ""
	for i in range(0, min(10, queue.num_remaining())):
		title = queue.elem[i].title
		lst += "{0}: {1}\n".format(str(i), title)
	if lst == "":
		lst = "empty queue"
	emb.add_field(name="{0} tracks left in queue".format(queue.num_remaining()), value=lst)
	emb.set_thumbnail(url=playing.thumbnail_url)
	return emb

def get_error(message):
	emb = discord.Embed(title='music-bot', description=message,color=0xFF0000)
	return emb

def get_success(message):
	emb = discord.Embed(title='music-bot', description=message,color=0x00FF00)
	return emb

def get_search_results(query, results):
	desc = 'search for: {0}'.format(query)
	emb = discord.Embed(title='music-bot', description=desc,color=0x0000FF)
	lst = ""
	for i in range(0, min(10, len(results))):
		title = results[i].title
		author = results[i].author
		lst += "{0}: {1} | {2}\n".format(str(i), author, title)
	if lst == "":
		lst = "no results"
	emb.add_field(name="{0} results found: ".format(len(results)), value=lst)
	return emb