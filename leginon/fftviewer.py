import imagewatcher
import fftengine
import data
import Numeric
import cameraimage
import uidata

class FFTViewer(imagewatcher.ImageWatcher):
	def __init__(self, id, session, nodelocations, **kwargs):
		imagewatcher.ImageWatcher.__init__(self, id, session, nodelocations, **kwargs)

		self.fftengine = fftengine.fftNumeric()

		self.defineUserInterface()
		self.start()

	def defineUserInterface(self):
		imagewatcher.ImageWatcher.defineUserInterface(self)
		self.ui_image = uidata.Image('FFT Image', None, 'r')
		container = uidata.MediumContainer('FFT Viewer')
		container.addObject(self.ui_image)
		self.uiserver.addObject(container)

	def processData(self, imagedata):
		imagewatcher.ImageWatcher.processData(self, imagedata)
		self.numarray = cameraimage.power(self.numarray)
		self.ui_image.set(self.numarray)
		if self.popupvalue:
			self.clearAllTargetCircles()
			self.displayNumericArray()
