class music_queue:
	def __init__(self):
		self.elem = []
	def enqueue(self, a):
		self.elem.append(a)
	def dequeue(self):
		return self.elem.pop(0)
	def has_next(self):
		return self.elem