import imagewatcher
import threading
import Mrc
import xmlrpclib
xmlbinlib = xmlrpclib

class ImageCollector(imagewatcher.ImageWatcher):
	def __init__(self, id, session, nodelocations, **kwargs):
		self.imagelistlock = threading.Lock()
		self.imagelist = {}
		imagewatcher.ImageWatcher.__init__(self, id, session, nodelocations,
																																**kwargs)
		# ???
		self.defineUserInterface()
		self.start()

	def processData(self, imagedata):
		self.imagelistlock.acquire()
		imagewatcher.ImageWatcher.processData(self, imagedata)
		self.imagelist[str(self.imagedata.id)] = self.numarray
		self.imagelistselect.set({'list': self.imagelist.keys(), 'selected': []})
		self.imagelistlock.release()

	def defineUserInterface(self):
		iwspec = imagewatcher.ImageWatcher.defineUserInterface(self)
#		self.dataqueuetoggle.set(1)
		self.imagelistselect = self.registerUIData('Select', 'struct',
																			default={'list': [], 'selected': []},
																		permissions='rw', subtype='selected list')
		self.ui_image = self.registerUIData('Image', 'binary', permissions='r')
		selectspec = self.registerUIMethod(self.selectImage, 'Select Image', ())
		imagecontainer = self.registerUIContainer('Images',	
											(self.ui_image, self.imagelistselect, selectspec))
		spec = self.registerUISpec('Image Collector', (imagecontainer,))
		spec += iwspec
		return spec

	def selectImage(self):
		self.imagelistlock.acquire()
		try:
			key = self.imagelistselect.get()['selected'][0]
			mrcstr = Mrc.numeric_to_mrcstr(self.imagelist[key])
		except:
			self.printerror('invalid image for selection')
			mrcstr = ''
		self.ui_image.set(xmlbinlib.Binary(mrcstr))
		self.imagelistlock.release()
		return self.imagelistselect.get()

