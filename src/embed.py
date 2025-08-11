import nextcord
from pytube import YouTube

def get_status(channel, queue, playing):
	desc = 'playing {0} in {1}'.format(playing.title, channel)
	emb = nextcord.Embed(title='music-bot', description=desc,color=0x0000FF)
	if(queue.has_next()):
		lst = "next up: {0}".format(queue.elem[0].title)
	else:
		lst = "empty queue"
	emb.add_field(name="{0} tracks left in queue".format(queue.num_remaining()), value=lst)
	emb.set_thumbnail(url=playing.thumbnail_url)
	return emb

def get_queue(channel, queue, playing):
	desc = 'playing {0} in {1}'.format(playing.title, channel)
	emb = nextcord.Embed(title='music-bot', description=desc,color=0x0000FF)
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
	emb = nextcord.Embed(title='music-bot', description=message,color=0xFF0000)
	return emb

def get_success(message):
	emb = nextcord.Embed(title='music-bot', description=message,color=0x00FF00)
	return emb

def get_search_results(query, results, max_results = 10):
	desc = 'search for: {0}'.format(query)
	emb = nextcord.Embed(title='music-bot', description=desc,color=0x0000FF)
	# need to limit number of results because of embedded message limit
	num_results = min(max_results, len(results))
	lst = ""
	for i in range(0, num_results):
		# need to limit length of each search result because of embedded message limit
		title = results[i].title
		title_trunc = title[0:70]
		author = results[i].author
		author_trunc = author[0:20]
		lst += "{0}: {1} | {2}\n".format(str(i), author_trunc, title_trunc)
	if lst == "":
		lst = "no results"
	emb.add_field(name="{0} results found: ".format(num_results), value=lst)
	return emb