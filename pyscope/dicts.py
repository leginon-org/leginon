import camera

class xydict(dict):
	def __init__(self, initialdata=None):
		self.update({'x': None, 'y': None})
		if initialdata:
			self.update(initialdata)

	def __setitem__(self, key, item):
		if key == 'x' or key == 'y':
			dict.__setitem__(self, key, item)
		else:
			raise ValueError

	def __delitem__(self, key):
		raise NotImplementedError

	def clear(self):
		self['x'] = None
		self['y'] = None

	def update(self, d):
		for k, v in d.items():
			self[k] = v

	def setdefault(self, key, failobj=None):
		raise NotImplementedError

	def popitem(self):
		raise NotImplementedError

