from wxPython.wx import *
import wxImageViewer
import Numeric
import math

class CompositeImageMaker(object):
	def __init__(self):
		self.circleradius = 1.5e-3
		self.pixelsize = 3.2e-7
		self.binning = 2
		self.imagesize = 512
		self.scale = 4.0

	def imageDiameter(self):
		imagesize = self.pixelsize*self.binning*self.imagesize
		imagediameter = self.circleradius*2.0/imagesize
		print 'imageDiameter =', imagediameter
		return imagediameter

	def makeNumericImage(self):
		imagediameter = math.ceil(self.imageDiameter())

		size = math.ceil(imagediameter*self.imagesize/self.scale)
		numericimage = Numeric.zeros((size, size), Numeric.Int16)

		imagecenters = Numeric.arrayrange(0, imagediameter).astype(Numeric.Int16)
		imagecenters = imagecenters * self.imagesize
		imagecenters = imagecenters - self.imagesize/2.0
		imagecenters = imagecenters / self.scale
		imagecenters = imagecenters.astype(Numeric.Int16)
		foo = []
		for i in imagecenters:
			for j in imagecenters:
				foo.append((i, j))
				numericimage[i, j] = 256
				halfimagesize = int(round(self.imagesize/self.scale/2.0))
				right = halfimagesize - j - 1
				left = halfimagesize + j + 1
				bottom = halfimagesize - i - 1
				top = halfimagesize + i - 1
				numericimage[bottom:top, left] = 256
				numericimage[bottom:top, right] = 256
				numericimage[top, left:right] = 256
				numericimage[bottom, left:right] = 256

		return numericimage

if __name__ == '__main__':
	class MyApp(wxApp):
		def OnInit(self):
			frame = wxFrame(NULL, -1, 'Image Viewer')
			self.SetTopWindow(frame)
			self.panel = wxImageViewer.ImagePanel(frame, -1)
			frame.Fit()
			frame.Show(true)
			return true

	cim = CompositeImageMaker()

	app = MyApp(0)
	app.panel.setNumericImage(cim.makeNumericImage())
	app.MainLoop()

