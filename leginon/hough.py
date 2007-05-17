#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#
import Numeric
import LinearAlgebra
import FFT

def gradient(image):
	'''
	Simplistic edge finder.
	'''
	m, n = image.shape

	J = Numeric.zeros((m+2, n+2), 'd')
	J[0, 0] = image[0, 0]
	J[0, 1:n + 1] = image[0]
	J[0, n + 1] = image[0, n - 1]
	J[1:m + 1, 0] = image[0:n,0]
	J[1:m + 1, 1:n + 1] = image
	J[1:m + 1, n + 1] = image[0:n, n - 1]
	J[m + 1, 0] = image[m - 1, 0]
	J[m + 1, 1:n + 1] = image[m - 1]
	J[m + 1, n + 1] = image[m - 1, n - 1]

	Ix = Numeric.zeros(J.shape, 'd')
	Ix[0:m+2,1:n+1] = (J[0:m+2,2:n+2] - J[0:m+2,0:n]) * 0.5
	Ix[0:m+2, 0] = Ix[0:m+2, 1]
	Ix[0:m+2, n+1] = Ix[0:m+2, n]

	Iy = Numeric.zeros(J.shape, 'd')
	Iy[1:m+1,0:n+2] = (J[2:m+2,0:n+2] - J[0:m,0:n+2]) * 0.5
	Iy[0, 0:n+2] = Iy[1, 0:n+2]
	Iy[m+1, 0:n+2] = Iy[m, 0:n+2]

	return Numeric.sqrt(Ix*Ix + Iy*Iy)

sqrtof2 = Numeric.sqrt(2)

def bresenhamCirclePoints(radius):
	'''
	Make a list of points offset by radius (for array indexing) that compose
	a circle defined by Bresenham's circle rastering algorithm.
	'''
	pointlist = []
	i = radius
	d = 0.25 - radius
	for j in range(int(Numeric.ceil(radius/sqrtof2))):
		for nj in (radius - j, j + radius - 1):
			for ni in (radius - i, i + radius - 1):
				pointlist.append((nj, ni))
				pointlist.append((ni, nj))
		d += 2*j + 1
		if d > 0:
			d += 2 - 2*i
			i -= 1
	return pointlist 

def period(image):
	fftimage = Numeric.zeros(image.shape, 'd')
	m = image.shape[0]
	for j in range(image.shape[1]):
		fft = FFT.fft(image[:, j]).real
		fftimage[:m/2, j] = fft[m/2 + 1:]
		fftimage[m/2 + 1:, j] = fft[:m/2]
	return fftimage

def findPeak(image):
	for n in range(image.shape[1]):
		a = Numeric.zeros((image.shape[0], 3))
		b = image[:, n]
		a[:, 0] = Numeric.arrayrange(image.shape[0])
		a[:, 0] **= 2
		a[:, 1] = Numeric.arrayrange(image.shape[0])
		a[:, 2] = Numeric.ones(image.shape[0])
		fit = LinearAlgebra.linear_least_squares(a, b)
		c = fit[0]
		row = -c[1] / (2.0 * c[0])

def houghLine(image, threshold):
	m, n = image.shape

	r = int(Numeric.ceil(Numeric.sqrt(((m/2.0)**2 + (n/2.0)**2))))
	houghimage = Numeric.zeros((r, 360, 5))

	houghimage[:,:,1] = houghimage[:,:,1] + m
	houghimage[:,:,2] = houghimage[:,:,2] + n

	offset = r/2

	hm = int(Numeric.ceil(m/2.0))
	i = Numeric.arrayrange(-hm, hm)
	i.shape = (m, 1)
	hn = int(Numeric.ceil(n/2.0))
	j = Numeric.arrayrange(-hn, hn)
	j.shape = (n, 1)
	conversion = Numeric.pi*2/houghimage.shape[1]
	cos = Numeric.cos(Numeric.arrayrange(houghimage.shape[1])*conversion)
	cos.shape = (1, houghimage.shape[1])
	sin = Numeric.sin(Numeric.arrayrange(houghimage.shape[1])*conversion)
	sin.shape = (1, houghimage.shape[1])

	icos = Numeric.matrixmultiply(i, cos)
	jsin = Numeric.matrixmultiply(j, sin)

#	i = Numeric.transpose(Numeric.array([Numeric.arrayrange(n)]*m)).astype('d')
#	j = Numeric.array([Numeric.arrayrange(m)]*n).astype('d')
#
#	i *= Numeric.cos(theta)
#	j *= Numeric.sin(theta)
#
#	r = i + j + offset

	mrange = range(m)
	nrange = range(n)
	for i in mrange:
		for j in nrange:
			if image[i, j] > threshold: 
				for theta in range(houghimage.shape[1]):
					r = int(round(icos[i - m, theta] + jsin[j - n, theta]))
					houghimage[r, theta, 0] = houghimage[r, theta, 0] + 1

					if i < houghimage[r, theta, 1]:
						houghimage[r, theta, 1] = i
					if j < houghimage[r, theta, 2]:
						houghimage[r, theta, 2] = j
					if i > houghimage[r, theta, 3]:
						houghimage[r, theta, 3] = i
					if j > houghimage[r, theta, 4]:
						houghimage[r, theta, 4] = j

	lengththreshold = 768
	for r in range(houghimage.shape[0]):
		for theta in range(houghimage.shape[1]):
			m = Numeric.sqrt((houghimage[r, theta, 3] - houghimage[r, theta, 1])**2 +
										(houghimage[r, theta, 4] - houghimage[r, theta, 2])**2)
			if m < lengththreshold:
				houghimage[r, theta, 0] = 0

	return houghimage

def houghCircle(image, threshold, radiusrange=None):
	'''
	Computes the Hough transform of a circle on the given image on all points
	with value greater than threshold, for circles with radii in radiusrange.
	If radiusrange is None, radiusrange is defined as 1 to half the minimum
	image size.
	'''
	m, n = image.shape

	# set radius range to all radii that find on the transform accumulator
	if radiusrange is None:
		radiusrange = (1, min(m, n)/2)

	# give the transform accumulator a buffer since a shifted copy will be added
	# inplace. this is probably not the best way if the radius is large
	border = max(radiusrange)
	houghimage = Numeric.zeros((m + border*2, n + border*2), Numeric.Int16)

	# threshold the image, making it a bitmask of above/below threshold
	thresholdimage = image >= threshold
	# convert to type to be added to the accumulator
	thresholdimage = thresholdimage.astype(Numeric.Int16)

	# make a list of all points (offsets) for circles with radii in range
	shifts = []
	for radius in range(radiusrange[0], radiusrange[1] + 1):
		shifts += bresenhamCirclePoints(radius)

	# shift the bitmask of the threshold to each point in each of the circles
	# and add the value to the accumulator
	def set(shift):
		houghimage[shift[0]:shift[0] + m, shift[1]:shift[1] + n] += thresholdimage
	map(set, shifts)

	return houghimage[border - 1:border + m - 1, border - 1:border + n - 1]

if __name__=='__main__':
	from wxPython.wx import *
	import gui.wx.ImageViewer
	import Mrc
	import timer
	import holefinderback
	from pyami import imagefun

	def edges(image):
		hf = holefinderback.HoleFinder()
		hf['original'] = image
		hf.configure_edges(filter='sobel',
												size=9,
												sigma=1.4,
												absvalue=False,
												lp=True,
												lpn=5,
												lpsig=1.0)
		hf.find_edges()
		return hf['edges']

	image = Mrc.mrc_to_numeric('hftest.mrc')

	t = timer.Timer()

	#edgeimage = gradient(image)
	edgeimage = edges(image)

	t.reset()

	houghcircleimage = houghCircle(edgeimage, 300, [28,28])
	houghcircleimage = Numeric.clip(houghcircleimage, 100, 30000)
	houghcircleimage = houghcircleimage - 100
	t.reset()

	mask = houghcircleimage #Numeric.ones(houghcircleimage.shape)
	blobs = imagefun.find_blobs(houghcircleimage, mask, maxblobsize=256)
	blobimage = Numeric.zeros(houghcircleimage.shape)
	for blob in blobs:
		if blob.stats['n'] > 16:
			i, j = blob.stats['center']
			i, j = int(round(i)), int(round(j))
			blobimage[i, j] = 100 #blob.stats['n']
			blobimage[i-1:i+2, j-1:j+2] = blobimage[i-1:i+2, j-1:j+2] + 100
	
#	houghlineimage = houghLine(houghcircleimage, 101)[:,:,0]
	houghlineimage = houghLine(blobimage, 1)[:,:,0]

	tolerance = 5
	angle = 90
	for theta in range(houghlineimage.shape[1]/2):
		sum = 0
		for r in range(houghlineimage.shape[0]):
			for i in range(theta+tolerance, theta+tolerance + 1):
				sum += houghlineimage[r, i % 360]
				sum += houghlineimage[r, (i + 90) % 360]
				sum += houghlineimage[r, (i + 180) % 360]
				sum += houghlineimage[r, (i + 270) % 360]
		print 'theta:', theta, '#'*(sum/100)
			
	t.reset()
#	fftimage = period(houghlineimage)
#	fftimage = Numeric.clip(fftimage, 1000, 100000)

	t.stop()

	class MyApp(wxApp):
		def OnInit(self):
			frame = wxFrame(NULL, -1, 'Image Viewer')
			self.SetTopWindow(frame)
			self.panel = wxScrolledWindow(frame, -1)
			self.panel.SetScrollRate(5, 5)
			self.sizer = wxFlexGridSizer(2, 2, 0, 0)
			self.iv1 = gui.wx.ImageViewer.ImagePanel(self.panel, -1)
			self.iv2 = gui.wx.ImageViewer.ImagePanel(self.panel, -1)
			self.iv3 = gui.wx.ImageViewer.ImagePanel(self.panel, -1)
			self.iv4 = gui.wx.ImageViewer.ImagePanel(self.panel, -1)
			self.sizer.AddMany([(self.iv1,),
													(self.iv2,),
													(self.iv3,),
													(self.iv4,)])
			self.sizer.AddGrowableRow(0)
			self.sizer.AddGrowableRow(1)
			self.sizer.AddGrowableCol(0)
			self.sizer.AddGrowableCol(1)
			self.sizer.Layout()
			self.panel.SetSizer(self.sizer)
			self.panel.Show(true)
			frame.Fit()
			frame.Show(true)
			return true

	app = MyApp(0)
	app.iv1.setNumericImage(edgeimage)
	app.iv2.setNumericImage(houghcircleimage)
#	app.iv3.setNumericImage(houghlineimage)
	app.iv3.setNumericImage(blobimage)
#	app.iv4.setNumericImage(fftimage)
	app.iv4.setNumericImage(houghlineimage)
	app.MainLoop()

