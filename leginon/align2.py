import math
import numarray
import numarray.fft
import numextension

def zeroEdges(image, n=4):
	z = numarray.zeros(image.shape, image.type())
	z[n:-n, n:-n] = image[n:-n, n:-n]
	return z

def pad(image):
	shape = (image.shape[0]*2, image.shape[1]*2)
	padded = numarray.zeros(shape, image.type())
	offset = ((shape[0] - image.shape[0])/2, (shape[1] - image.shape[1])/2)
	padded[offset[0]:-offset[0], offset[1]:-offset[1]] = image
	return padded

def swapQuadrants(image):
	rows, columns = image.shape
	swap = numarray.zeros(image.shape, image.type())
	swap[rows/2:] = image[:rows/2]
	swap[:rows/2] = image[rows/2:]
	return swap

def logMagnitude(image):
	return numarray.log(1.0 + numarray.absolute(image))

def magnitude(image):
	return numarray.absolute(image)

def hanningWindow(image):
	hanning = numarray.zeros(image.shape, image.type())
	rows, columns = hanning.shape
	for i in range(rows):
		for j in range(columns):
			x = ((0.5 - 0.5*math.cos(2*math.pi*i/(rows - 1)))
						*(0.5 - 0.5*math.cos(2*math.pi*j/(columns - 1))))
			hanning[i, j] = x
	return image*hanning

def hammingWindow(image):
	hamming = numarray.zeros(image.shape, image.type())
	rows, columns = hamming.shape
	for i in range(rows):
		for j in range(columns):
			x = ((0.54 - 0.46*math.cos(2*math.pi*i/(rows - 1)))
						*(0.54 - 0.46*math.cos(2*math.pi*j/(columns - 1))))
			hamming[i, j] = x
	return image*hamming

def highPass(image):
	highpass = numarray.zeros(image.shape, image.type())
	rows, columns = highpass.shape
	for i in range(rows):
		for j in range(columns):
			xi = float(i)/rows - 0.5
			eta = j/(2.0*columns)
			x = math.cos(math.pi*xi)*math.cos(math.pi*eta)
			highpass[i, j] = (1.0 - x)*(2.0 - x)
	return image*highpass

def bilinear(image, x, y):
	rows, columns = image.shape
	x0, y0 = int(x), int(y)
	x1, y1 = x0 + 1, y0 + 1
	v = numarray.zeros((2, 2), image.type())
	if x0 < columns and y0 < rows and x0 >= 0 and y0 >= 0:
		v[0, 0] = image[y0, x0]
	if x1 < columns and y0 < rows and x1 >= 0 and y0 >= 0:
		v[0, 1] = image[y0, x1]
	if x0 < columns and y1 < rows and x0 >= 0 and y1 >= 0:
		v[1, 0] = image[y1, x0]
	if x1 < columns and y1 < rows and x1 >= 0 and y1 >= 0:
		v[1, 1] = image[y1, x1]
	s = numarray.zeros((2, 2), image.type())
	s[0, 0] = (y1 - y)*(x1 - x)
	s[0, 1] = (y1 - y)*(x - x0)
	s[1, 0] = (y - y0)*(x1 - x)
	s[1, 1] = (y - y0)*(x - x0)
	return numarray.sum((v*s).flat)

def xclip(image, x):
	if x < 0:
		return 0
	elif x < image.shape[1]:
		return x
	else:
		return image.shape[1] - 1

def yclip(image, y):
	if y < 0:
		return 0
	elif y < image.shape[0]:
		return y
	else:
		return image.shape[0] - 1

def _bicubic(v1, v2, v3, v4, d):
	p1 = v2
	p2 = -v1 + v3
	p3 = 2*(v1 - v2) + v3 - v4
	p4 = -v1 + v2 - v3 + v4
	return p1 + d*(p2 + d*(p3 + d*p4))

def bicubic(image, xin, yin):
	if xin < 0.0 or xin >= image.shape[1] or yin < 0.0 or yin >= image.shape[0]:
		return 0
	xin -= 0.5
	yin -= 0.5
	x = int(xin)
	y = int(yin)
	dx = xin - x
	dy = yin - y
	x -= 1
	y -= 1

	i = image[yclip(image, y)]
	x0 = xclip(image, x + 0)
	x1 = xclip(image, x + 1)
	x2 = xclip(image, x + 2)
	x3 = xclip(image, x + 3)

	v1 = _bicubic(i[x0], i[x1], i[x2], i[x3], dx)
	if y + 1 >= 0 and y + 1 < image.shape[0]:
		i = image[y + 1]
		v2 = _bicubic(i[x0], i[x1], i[x2], i[x3], dx)
	else:
		v2 = v1
	if y + 2 >= 0 and y + 2 < image.shape[0]:
		i = image[y + 2]
		v3 = _bicubic(i[x0], i[x1], i[x2], i[x3], dx)
	else:
		v3 = v2
	if y + 3 >= 0 and y + 3 < image.shape[0]:
		i = image[y + 3]
		v4 = _bicubic(i[x0], i[x1], i[x2], i[x3], dx)
	else:
		v4 = v3
	v1 = _bicubic(v1, v2, v3, v4, dy)

	return v1

def nearestNeighbor(image, x, y):
	i = int(round(y))
	j = int(round(x))
	if i < 0 or i >= image.shape[0] or j < 0 or j >= image.shape[1]:
		return 0
	return image[i, j]

def logPolar(image, thetas=256, logrhos=256):
	size = min(image.shape[0]/2.0, image.shape[1])
	base = size**(1.0/logrhos)
	logpolar = numarray.zeros((thetas, logrhos), numarray.Float)
	rows, columns = image.shape
	for theta in range(thetas):
		for logrho in range(logrhos):
			r = base**logrho - 1
			x = r*math.cos(math.radians(theta/(thetas/180.0) - 90.0))
			y = r*math.sin(math.radians(theta/(thetas/180.0) - 90.0)) + rows/2.0
			logpolar[theta, logrho] = nearestNeighbor(image, x, y)
			#logpolar[theta, logrho] = bilinear(image, x, y)
			#logpolar[theta, logrho] = bicubic(image, x, y)
	return logpolar

def crossCorrelation(image1, image2):
	fft1 = numarray.fft.real_fft2d(image1)
	fft2 = numarray.fft.real_fft2d(image2)
	xc = fft1*fft2.conjugate()
	return numarray.fft.inverse_real_fft2d(xc)

def phaseCorrelation(image1, image2):
	fft1 = numarray.fft.real_fft2d(image1)
	fft2 = numarray.fft.real_fft2d(image2)
	xc = fft1*fft2.conjugate()
	pc = xc/numarray.absolute(xc)
	return numarray.fft.inverse_real_fft2d(pc)

def findMax(image):
	columns = image.shape[1]
	i = numarray.argmax(image.flat)
	row = i / columns
	column = i % columns
	return row, column, image.flat[i]

def findPeak(image):
	i, j, value = findMax(image)
	if i > image.shape[0]/2.0:
		i -= image.shape[0]
	if j > image.shape[1]/2.0:
		j -= image.shape[1]
	return i, j, value

def findRotationAndScale(image1, image2, window=None, highpass=None):
	if image1.shape != image2.shape:
		raise ValueError

	shape = image1.shape
	if window is None:
		window = numextension.hanning(shape[0], shape[1], a=0.54)
	image1 *= window
	image2 *= window

	image1 = swapQuadrants(numarray.fft.real_fft2d(image1))
	image2 = swapQuadrants(numarray.fft.real_fft2d(image2))
	shape = image1.shape

	image1 = magnitude(image1)
	image2 = magnitude(image2)

	if highpass is None:
		highpass = numextension.highpass(*shape)
	image1 *= highpass
	image2 *= highpass

	logpolarshape = (256, 256)
	image1 = numextension.logpolar(image1, *logpolarshape)
	image2 = numextension.logpolar(image2, *logpolarshape)

	pc = phaseCorrelation(image1, image2)

	theta, logrho, value = findPeak(pc)

	rotation = (180.0*theta)/logpolarshape[0]
	base = shape[1]**(1.0/logpolarshape[1])
	scale = base**logrho

	return rotation, scale, value

	'''
	images = [hammingWindow(i) for i in [image1, image2]]
	ffts = [swapQuadrants(numarray.fft.real_fft2d(i)) for i in images]
	#ffts = [logMagnitude(f) for f in ffts]
	ffts = [magnitude(f) for f in ffts]
	ffts = [highPass(f) for f in ffts]
	lps = [logPolar(f) for f in ffts]
	pc = phaseCorrelation(*lps)
	theta, logrho, value = findPeak(pc)
	rotation = (180.0*theta)/lps[0].shape[0]
	base = ffts[0].shape[1]**(1.0/lps[0].shape[1])
	scale = base**logrho
	return rotation, scale, value
	'''

if __name__ == '__main__':
	import Mrc
	import sys
	import time

	window = numextension.hanning(1024, 1024, a=0.54)
	highpass = numextension.highpass(1024, 513)
	for i in range(16):
		for j in range(9):
			f1 = '04dec17b_000%d_0000%dgr.mrc' % (749 + i, j + 1)
			f2 = '05jan20a_000%d_0000%dgr.mrc' % (749 + i, j + 1)
			image1 = Mrc.mrc_to_numeric(f1)
			image2 = Mrc.mrc_to_numeric(f2)
			t = time.time()
			results = findRotationAndScale(image1, image2, window, highpass)
			t = time.time() - t
			print results, t

