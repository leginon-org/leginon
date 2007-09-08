#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#
from wxPython.wx import *
import gui.wx.ImagePanel
import Numeric
import math

class CompositeImageMaker(object):
	def __init__(self):
		self.circleradius = 0.5e-3
		self.pixelsize = 3.2e-7
		self.binning = 2
		self.imagesize = 512
		self.scale = 4.0

	def imageDiameter(self):
		imagesize = self.pixelsize*self.binning*self.imagesize
		imagediameter = self.circleradius*2.0/imagesize
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
		radius = int(self.circleradius/(self.pixelsize*self.binning*self.scale))
		y = radius
		ycenter = numericimage.shape[0]/2
		xcenter = numericimage.shape[1]/2
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

	def intersection(self):
		pixelradius = self.circleradius/(self.pixelsize*self.binning)
		lines = [self.imagesize/2]
		while lines[-1] < pixelradius - self.imagesize:
			lines.append(lines[-1] + self.imagesize)
		pixels = [pixelradius*2]
		for i in lines:
			pixels.append(pixelradius*math.cos(math.asin(i/pixelradius))*2)
		images = []
		for i in pixels:
			images.append(int(math.ceil(i/self.imagesize)))
		targets = []
		sign = 1
		for n, i in enumerate(images):
			xs = range(-sign*self.imagesize*(i - 1)/2, sign*self.imagesize*(i + 1)/2,
									sign*self.imagesize)
			y = n*512
			for x in xs:
				targets.insert(0, (x, y))
				if y > 0:
					targets.append((x, -y))
			sign = -sign
		return targets

	def makeNumericImage(self):
		imagediameter = math.ceil(self.imageDiameter())

		size = math.ceil(imagediameter*self.imagesize/self.scale)
		numericimage = Numeric.zeros((size + 256, size + 256), Numeric.Int16)

		imagecenters = self.intersection()
		for i, j in imagecenters:
			i = int(i/self.scale) + numericimage.shape[0]/2
			j = int(j/self.scale) + numericimage.shape[1]/2
			try:
				numericimage[i, j] = 256
			except IndexError:
				print i, j
			halfimagesize = int(round(self.imagesize/self.scale/2.0))
			right = halfimagesize - j - 1
			left = halfimagesize + j + 1
			bottom = halfimagesize - i - 1
			top = halfimagesize + i - 1
#			numericimage[bottom:top, left] = 256
#			numericimage[bottom:top, right] = 256
#			numericimage[top, left:right] = 256
#			numericimage[bottom, left:right] = 256

		self.circle(numericimage)

		return numericimage

if __name__ == '__main__':
	class MyApp(wxApp):
		def OnInit(self):
			frame = wxFrame(NULL, -1, 'Image Viewer')
			self.SetTopWindow(frame)
			self.panel = gui.wx.ImagePanel.ImagePanel(frame, -1)
			frame.Fit()
			frame.Show(true)
			return true

	cim = CompositeImageMaker()

	app = MyApp(0)
	app.panel.setNumericImage(cim.makeNumericImage())
	app.MainLoop()

