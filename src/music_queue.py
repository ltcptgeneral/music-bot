import random

class music_queue:
	def __init__(self, random=False):
		self.elem = []
		self.random=random
	def enqueue(self, a):
		self.elem.append(a)
	def dequeue(self):
		if self.random:
			return self.elem.pop(random.randrange(0, len(self.elem)))
		else:
			return self.elem.pop(0)
	def has_next(self):
		return len(self.elem) != 0