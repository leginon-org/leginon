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
	if (i,j) == (0,0):
		image[(0,0)]=image.min()
		i,j,value = findMax(image)
	if i > image.shape[0]/2.0:
		i -= image.shape[0]
	if j > image.shape[1]/2.0:
		j -= image.shape[1]
	return (i, j), value

def findRotationScale(image1, image2, window=None, highpass=None):
	if image1.shape != image2.shape:
		raise ValueError

	shape = image1.shape
	if window is None:
		window = numextension.hanning(shape[0], shape[1], a=0.54)
	image1 = image1 * window
	image2 = image2 * window

	s = None
	image1 = swapQuadrants(numarray.fft.real_fft2d(image1, s=s))
	image2 = swapQuadrants(numarray.fft.real_fft2d(image2, s=s))
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

	rotation, scale, rsvalue = findRotationScale(image1, image2, window, highpass)

	shape = image2.shape[0]*2, image2.shape[1]*2

	r = rotateScaleOffset(image2, -rotation, 1.0/scale, (0.0, 0.0), shape)

	o = ((shape[0] - image1.shape[0])/2, (shape[1] - image1.shape[1])/2)
	i = numarray.zeros(shape, image1.type())
	i[o[0]:o[0] + image1.shape[0], o[1]:o[1] + image1.shape[1]] = image1

	fft1 = numarray.fft.real_fft2d(i)
	fft2 = numarray.fft.real_fft2d(r)
	pc = phaseCorrelate(fft1, fft2, fft=True)
	peak, value = findPeak(pc)

	r180 = numarray.mlab.rot90(numarray.mlab.rot90(r))
	fft2 = numarray.fft.real_fft2d(r180)
	pc = phaseCorrelate(fft1, fft2, fft=True)
	peak180, value180 = findPeak(pc)

	if value < value180:
		peak = peak180
		value = value180
		rotation = (rotation + 180.0) % 360.0
		r = r180

	#images = i - numarray.nd_image.shift(r, peak)

	return rotation, scale, peak, rsvalue, value#, images

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

def findTranslation(image1, image2):
	pc = phaseCorrelate(image1, image2)
	return findPeak(pc)

if __name__ == '__main__':
	from pyami import mrc
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
			image1 = mrc.read(f1)
			image2 = mrc.read(f2)
			#image2 = rotateScaleOffset(image1, 0.0, 1.0, (0.0, 0.0))

			'''
			result = findRotationScaleTranslation(image1, image2, window, highpass)
			#rotation, scale, shift, value = result
			rotation, scale, shift, value, image = result
			Mrc.numeric_to_mrc(image, '%d_%d.mrc' % (749 + i, j + 1))
			string = 'rotation: %g, scale: %g, shift: (%g, %g), value: %g'
			print string % ((rotation, scale) + shift + (value,))
			'''

			result = findRotationScale(image1, image2)
			rotation, scale, value = result
			string = 'rotation: %g, scale: %g, value: %g'
			print string % (rotation, scale, value)

