import imagewatcher
import Mrc
import xmlrpclib
xmlbinlib = xmlrpclib

class ImageCollector(imagewatcher.ImageWatcher):
	def __init__(self, id, session, nodelocations, **kwargs):
		imagewatcher.ImageWatcher.__init__(self, id, session, nodelocations,
																																**kwargs)
		# ???
		self.defineUserInterface()
		self.start()

	def defineUserInterface(self):
		iwspec = imagewatcher.ImageWatcher.defineUserInterface(self)
		self.dataqueuetoggle.set(1)
		self.ui_image = self.registerUIData('Image', 'binary', permissions='r')
		nextspec = self.registerUIMethod(self.advanceImage, 'Advance Image', ())
		imagecontainer = self.registerUIContainer('Images',	
																								(self.ui_image, nextspec))
		spec = self.registerUISpec('Image Collector', (imagecontainer,))
		print spec
		spec += iwspec
		return spec

	def advanceImage(self):
		if self.processDataFromQueue():
			mrcstr = Mrc.numeric_to_mrcstr(self.numarray)
		else:
			mrcstr = ''
		self.ui_image.set(xmlbinlib.Binary(mrcstr))
			
