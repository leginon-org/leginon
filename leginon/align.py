import math
import numarray
import numarray.fft
import numarray.linear_algebra
import numarray.mlab
import numarray.nd_image
import numextension

def swapQuadrants(image):
	rows, columns = image.shape
	swap = numarray.zeros(image.shape, image.type())
	swap[rows/2:] = image[:rows/2]
	swap[:rows/2] = image[rows/2:]
	return swap

def phaseCorrelate(image1, image2, fft=False):
	if fft:
		fft1 = image1
		fft2 = image2
	else:
		fft1 = numarray.fft.real_fft2d(image1)
		fft2 = numarray.fft.real_fft2d(image2)
	xc = fft1*fft2.conjugate() + 1e-16
	pc = xc/numarray.absolute(xc)
	pc = numarray.fft.inverse_real_fft2d(pc)
	return pc

def findMax(image):
	columns = image.shape[1]
	i = numarray.argmax(image.flat)
	row = i / columns
	column = i % columns
	return row, column, image.flat[i]

def findPeak(image):
	i, j, value = findMax(image)

	array = numarray.zeros((5,), image.type())

	offset = i - 2
	for k in range(5):
		if k + offset >= image.shape[0]:
			array[k] = image[k + offset - image.shape[0], j]
		else:
			array[k] = image[k + offset, j]
	isubpixel = leastSquaresFindPeak(array)

	offset = j - 2
	for k in range(5):
		if k + offset >= image.shape[1]:
			array[k] = image[i, k + offset - image.shape[1]]
		else:
			array[k] = image[i, k + offset]
	jsubpixel = leastSquaresFindPeak(array)

	if i > image.shape[0]/2.0:
		i -= image.shape[0]
		i -= isubpixel
	else:
		i += isubpixel

	if j > image.shape[1]/2.0:
		j -= image.shape[1]
		j -= jsubpixel
	else:
		j += jsubpixel

	return (i, j), value

def leastSquaresFindPeak(array):
	dm = numarray.zeros((array.shape[0], 3), numarray.Float)
	for i in range(dm.shape[0]):
		dm[i] = (i**2, i, 1)

	fit = numarray.linear_algebra.linear_least_squares(dm, array)
	coeffs = fit[0]
	residuals = fit[1][0]

	try:
		peak = -coeffs[1] / 2.0 / coeffs[0]
	except ZeroDivisionError:
		raise RuntimeError('least squares fit has zero coefficient')

	peak -= array.shape[0]/2.0

	value = coeffs[0]*peak**2 + coeffs[1]*peak + coeffs[2]

	return peak

def findRotationScale(image1, image2, window=None, highpass=None):
	if image1.shape != image2.shape:
		raise ValueError

	shape = image1.shape
	if window is None:
		window = numextension.hanning(shape[0], shape[1], a=0.54)
	image1 = image1 * window
	image2 = image2 * window

	image1 = swapQuadrants(numarray.fft.real_fft2d(image1))
	image2 = swapQuadrants(numarray.fft.real_fft2d(image2))
	shape = image1.shape

	image1 = numarray.absolute(image1)
	image2 = numarray.absolute(image2)

	if highpass is None:
		highpass = numextension.highpass(*shape)
	image1 *= highpass
	image2 *= highpass

	args = (shape[0]/2, shape[0]/2,
					shape[0]/2.0,
					0.0, min(shape[0]/2.0, shape[1]),
					-math.pi/2.0, math.pi/2.0)
	image1, base, phiscale = numextension.logpolar(image1, *args)
	image2, base, phiscale = numextension.logpolar(image2, *args)
	#Mrc.numeric_to_mrc(image1, 'lp1.mrc')
	#Mrc.numeric_to_mrc(image2, 'lp2.mrc')

	pc = phaseCorrelate(image1, image2)
	peak, value = findPeak(pc)
	logrho, theta = peak
	rotation = math.degrees(theta/phiscale)
	scale = base**-logrho

	return rotation, scale, value

def normalize(image):
	min, max = numextension.minmax(image)
	return (image - min)/(max - min)

def findRotationScaleTranslation(image1, image2, window=None, highpass=None):
	image1 = normalize(image1)
	image2 = normalize(image2)

	rotation, scale, value = findRotationScale(image1, image2, window, highpass)

	shape = image2.shape[0]*2, image2.shape[1]*2

	r = rotateScaleOffset(image2, -rotation, 1.0/scale, (0.0, 0.0), shape)

	o = ((shape[0] - image1.shape[0])/2, (shape[1] - image1.shape[1])/2)
	i = numarray.zeros(shape, image1.type())
	i[o[0]:o[0] + image1.shape[0], o[1]:o[1] + image1.shape[1]] = image1

	fft1 = numarray.fft.real_fft2d(i)
	fft2 = numarray.fft.real_fft2d(r)
	pc = phaseCorrelate(fft1, fft2, fft=True)
	peak, value = findPeak(pc)

	images = i - numarray.nd_image.shift(r, peak)

	r = numarray.mlab.rot90(numarray.mlab.rot90(r))
	fft2 = numarray.fft.real_fft2d(r)
	pc = phaseCorrelate(fft1, fft2, fft=True)
	peak180, value180 = findPeak(pc)

	if value < value180:
		peak = peak180
		value = value180
		rotation = (rotation + 180.0) % 360.0

	return rotation, scale, peak, value, images

def getMatrices(rotation, scale):
	mrotation = numarray.identity(2, numarray.Float)
	mrotation[0, 0] = math.cos(math.radians(rotation))
	mrotation[0, 1] = math.sin(math.radians(rotation))
	mrotation[1, 0] = -math.sin(math.radians(rotation))
	mrotation[1, 1] = math.cos(math.radians(rotation))

	mscale = numarray.identity(2, numarray.Float)
	mscale[0, 0] = scale
	mscale[1, 1] = scale

	m = numarray.identity(2, numarray.Float)
	m = numarray.matrixmultiply(mrotation, m)
	m = numarray.matrixmultiply(mscale, m)

	imrotation = numarray.transpose(mrotation)

	imscale = numarray.identity(2, numarray.Float)
	imscale[0, 0] = 1.0/mscale[0, 0]
	imscale[1, 1] = 1.0/mscale[1, 1]

	im = numarray.identity(2, numarray.Float)
	im = numarray.matrixmultiply(imscale, im)
	im = numarray.matrixmultiply(imrotation, im)

	return m, im

def rotateScaleOffset(image, rotation, scale, offset, shape=None):
	m, im = getMatrices(rotation, scale)

	if shape is None:
		shape = image.shape

	o = numarray.zeros((2,), numarray.Float)
	o = (offset[0] - image.shape[0]/2.0, offset[1] - image.shape[1]/2.0)
	o = numarray.matrixmultiply(im, o)
	o = (-(o[0] + shape[0]/2.0), -(o[1] + shape[1]/2.0))
	o = numarray.matrixmultiply(m, o)

	return numarray.nd_image.affine_transform(image, m, o, shape)

if __name__ == '__main__':
	import Mrc
	import sys
	import time

	window = numextension.hanning(1024, 1024, a=0.54)
	highpass = numextension.highpass(1024, 513)

	for i in range(16):
	#for i in [0]:
		#for j in range(9):
		for j in [4]:
			f1 = '04dec17b_000%d_0000%dgr.mrc' % (749 + i, j + 1)
			f2 = '05jan20a_000%d_0000%dgr.mrc' % (749 + i, j + 1)
			image1 = Mrc.mrc_to_numeric(f1)
			image2 = Mrc.mrc_to_numeric(f2)
			#image2 = rotateScaleOffset(image1, 0.0, 1.0, (0.0, 0.0))

			result = findRotationScaleTranslation(image1, image2, window, highpass)
			#rotation, scale, shift, value = result
			rotation, scale, shift, value, image = result
			Mrc.numeric_to_mrc(image, '%d_%d.mrc' % (749 + i, j + 1))
			string = 'rotation: %g, scale: %g, shift: (%g, %g), value: %g'
			print string % ((rotation, scale) + shift + (value,))

