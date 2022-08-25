import discord
from pytube import YouTube

def get_status(channel, queue, playing):
	desc = 'playing {0} in {1}'.format(playing, channel)
	emb = discord.Embed(title='music-bot', description=desc,color=0x00FF00)
	lst = ""
	for i in range(0, min(10, queue.num_remaining())):
		title = queue.elem[i].title
		lst += "{0}: {1}\n".format(str(i), title)
	if lst == "":
		lst = "empty queue"
	emb.add_field(name="next up: ", value=lst)
	return emb
	