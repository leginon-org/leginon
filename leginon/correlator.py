import correlation

class Correlator(object):
	'''
	Provides correlation handling functions.
	A buffer of exactly two images is maintained.  The buffer can act 
	as a fifo in which each image inserted causes a correlation with
	the previous, or each image in the buffer can be set independently
	and the correlation executed independently.
	'''
	def __init__(self, use_phase = 1):
		self.phase = use_phase
		self.clear()

	def insert(self, imagedata, index=None):
		'''
		Insert a new image into the image buffer.  If index is
		specified, it determines which buffer slot to fill (0 or 1).
		If no index is specified, the image is inserted in slot 1, 
		sliding the existing slot 1 image to slot 0 (fifo mode).
		'''
		#self.buffer.append(image)
		#del self.buffer[0]

		if index is None:
			# image1 becomes image0
			for key,value in self.buffer[1].items():
				self.buffer[0][key] = value
			self.buffer[1]['id'] = imagedata.id
			self.buffer[1]['image'] = imagedata.content
			try:
				return self.correlate()
			except EmptySlot:
				return {}
		else:
			self.buffer[index]['id'] = imagedata.id
			self.buffer[index]['image'] = imagedata.content

	def clear(self):
		#self.buffer = [None,None]
		image0 = {}
		image1 = {}
		self.buffer = (image0, image1)

	def correlate(self):
		if {} in self.buffer:
			raise EmptySlot('empty slot in buffer')

		im0 = self.buffer[0]['image']
		im1 = self.buffer[1]['image']

		corrdict = {}
		if self.phase:
			c = correlation.correlation(im0, im1, 0, 1, 1)
		else:
			c = correlation.correlation(im0, im1, 1, 0, 1)

		c['image0 id'] = self.buffer[0]['id']
		c['image1 id'] = self.buffer[1]['id']

		return c


class EmptySlot(Exception):
	pass
