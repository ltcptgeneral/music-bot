import random

class music_queue:
	def __init__(self):
		self.elem = []
	def enqueue(self, a):
		self.elem.append(a)
	def shuffle(self):
		random.shuffle(self.elem)
	def dequeue(self):
		return self.elem.pop(0)
	def purge(self):
		self.elem = []
	def has_next(self):
		return len(self.elem) != 0
	def num_remaining(self):
		return len(self.elem)