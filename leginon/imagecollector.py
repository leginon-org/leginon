import imagewatcher
import Mrc
import xmlrpclib
import Queue
xmlbinlib = xmlrpclib

class CallbackQueue(Queue.Queue):
	def __init__(self, getcallback=None, putcallback=None, maxsize=0):
		self.getcallback = getcallback
		self.putcallback = putcallback
		Queue.Queue.__init__(self, maxsize)

	def _put(self, item):
		Queue.Queue._put(self, item)
		if self.putcallback is not None:
			self.putcallback(item)

	def _get(self):
		item = Queue.Queue._get(self)
		if self.getcallback is not None:
			self.getcallback(item)
		return item

	def remove(self, item, block=1):
		if block:
			self.esema.acquire()
		elif not self.esema.acquire(0):
			raise Empty
		self.mutex.acquire()
		was_full = self._full()
		if item in self.queue:
			self.queue.remove(item)
			if was_full:
				self.fsema.release()
		else:
			if not self._empty():
				self.esema.release()
			self.mutex.release()
			raise ValueError
		if not self._empty():
			self.esema.release()
		self.mutex.release()
		return item

class ImageCollector(imagewatcher.ImageWatcher):
	def __init__(self, id, session, nodelocations, **kwargs):
		imagewatcher.ImageWatcher.__init__(self, id, session, nodelocations,
																																**kwargs)
#		self.dataqueue = CallbackQueue(self.getCallback, self.putCallback, 0)
		# ???
		self.defineUserInterface()
		self.start()

	def defineUserInterface(self):
		iwspec = imagewatcher.ImageWatcher.defineUserInterface(self)
		self.dataqueuetoggle.set(1)
#		self.queuelist = self.registerUIData('Queue List', 'struct', permissions='rw', default={'list': [], 'selected': []}, subtype='selected list')
		self.ui_image = self.registerUIData('Image', 'binary', permissions='r')
		nextspec = self.registerUIMethod(self.advanceImage, 'Advance Image', ())
		selectspec = self.registerUIMethod(self.selectImage, 'Select Image', ())
		imagecontainer = self.registerUIContainer('Images',	
											(self.ui_image, nextspec, selectspec)) #, self.queuelist))
		spec = self.registerUISpec('Image Collector', (imagecontainer,))
		spec += iwspec
		return spec

	def advanceImage(self):
		if self.processDataFromQueue():
			mrcstr = Mrc.numeric_to_mrcstr(self.numarray)
		else:
			mrcstr = ''
		self.ui_image.set(xmlbinlib.Binary(mrcstr))
		return ''

	def selectImage(self):
		value = self.queuelist.get()
		try:
			item = value['selected'][0]
		except (IndexError, KeyError):
			mrcstr = ''

		try:
			imagedata = self.dataqueue.remove(eval(item))
			mrcstr = Mrc.numeric_to_mrcstr(imagedata['image'])
		except (NameError, ValueError):
			self.printerror('item does not exist in queue: %s' % value)
			mrcstr = ''

		self.ui_image.set(xmlbinlib.Binary(mrcstr))
		return ''
			
	def putCallback(self, item):
		value = self.queuelist.get()
		value['list'].append(str(item))
		self.queuelist.set(value)

	def getCallback(self, item):
		value = self.queuelist.get()
		try:
			value['list'].remove(str(item))
			value['selected'].remove(str(item))
		except:
			pass
		self.queuelist.set(value)

