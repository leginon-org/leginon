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

	def circlePoints(self, numericimage, cx, cy, x, y):
		if x == 0:
			numericimage[cy + y, cx] = 256
			numericimage[cy + y, cx] = 256
			numericimage[cy, cx + y] = 256
			numericimage[cy, cx - y] = 256
		elif x == y:
			numericimage[cy + y, cx + x] = 256
			numericimage[cy + y, cx - x] = 256
			numericimage[cy - y, cx + x] = 256
			numericimage[cy - y, cx - x] = 256
		elif x < y:
			numericimage[cy + y, cx + x] = 256
			numericimage[cy + y, cx - x] = 256
			numericimage[cy - y, cx + x] = 256
			numericimage[cy - y, cx - x] = 256
			numericimage[cy + x, cx + y] = 256
			numericimage[cy + x, cx - y] = 256
			numericimage[cy - x, cx + y] = 256
			numericimage[cy - x, cx - y] = 256

	def circle(self, numericimage):
		x = 0
		radius = numericimage.shape[0]/2
		#radius = int(math.ceil(self.imageDiameter()/2))
		y = radius
		xcenter = radius - 1
		ycenter = radius - 1
		p = (5 - radius*4)/4
		self.circlePoints(numericimage, xcenter, ycenter, x, y)
		while x < y:
			x += 1
			if p < 0:
				p += 2*x + 1
			else:
				y -= 1
				p += 2*(x - y) + 1
			self.circlePoints(numericimage, xcenter, ycenter, x, y)

	def circlePoints2(self, array, cx, cy, x, y):
		if x == 0:
			array[cy + y, cx] = 1
			array[cy + y, cx] = 1
			array[cy, cx + y] = 1
			array[cy, cx - y] = 1
		elif x == y:
			array[cy + y, cx + x] = 1
			array[cy + y, cx - x] = 1
			array[cy - y, cx + x] = 1
			array[cy - y, cx - x] = 1
		elif x < y:
			array[cy + y, cx + x] = 1
			array[cy + y, cx - x] = 1
			array[cy - y, cx + x] = 1
			array[cy - y, cx - x] = 1
			array[cy + x, cx + y] = 1
			array[cy + x, cx - y] = 1
			array[cy - x, cx + y] = 1
			array[cy - x, cx - y] = 1

	def circle2(self, array=None):
		x = 0
		radius = int(math.ceil(self.imageDiameter()/2))
		array = Numeric.zeros((radius*2,radius*2), Numeric.Int16)
		y = radius
		xcenter = 0
		ycenter = 0
		p = (5 - radius*4)/4
		self.circlePoints2(array, xcenter, ycenter, x, y)
		while x < y:
			x += 1
			if p < 0:
				p += 2*x + 1
			else:
				y -= 1
				p += 2*(x - y) + 1
			self.circlePoints2(array, xcenter, ycenter, x, y)
#		for i in range(array.shape[0]):
#			set = 0
#			for j in range(array.shape[1]):
#				if array[i, j] == 0:
#					array[i, j] = set
#				else:
#					if set == 0:
#						set = 1
#					else:
#						set = 0
		print array

	def makeNumericImage(self):
		imagediameter = math.ceil(self.imageDiameter())

		size = math.ceil(imagediameter*self.imagesize/self.scale)
		numericimage = Numeric.zeros((size, size), Numeric.Int16)

		self.circle2()

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

		self.circle(numericimage)

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

