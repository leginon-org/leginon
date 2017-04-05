#!/usr/bin/env python

import time
import numpy
import pyami.imagefun
import scipy.ndimage
import scipy.misc
import scipy.stats
from appionlib.apImage import imagefile

def scale(input, shape, order=1, binfirst=True):
		# that was easy
		if input.shape == shape:
			return input

		# make sure shape is same dimensions as input image
		# rgb input image would have one extra dimension
		if len(shape) != len(input.shape):
			if len(shape) +1 != len(input.shape):
				raise ValueError('mismatch in number of dimensions: %s -> %s' % (input.shape, shape))
			else:
				is_rgb=True
		else:
			is_rgb=False

		# determine whether to use imagefun.bin or scipy.ndimage.zoom
		binfactors = []
		zoomfactors = []
		for i in range(len(shape)):
			zoomfactors.append(float(shape[i])/float(input.shape[i]))

			## for rgb, binning not implemented
			if is_rgb:
				binfactors.append(1)
				continue
			else:
				## added int() to avoid future python 3 problems
				binfactors.append(int(input.shape[i] / shape[i]))

			# bin <1 not allowed (when output bigger than input)
			if binfactors[i] == 0:
				binfactors[i] = 1

			# check original shape is divisible by new shape
			if input.shape[i] % shape[i]:
				# binning alone will not work, try initial bin, then interp
				start = binfactors[i]
				for trybin in range(start, 0, -1):
					if input.shape[i] % trybin:
						continue
					binfactors[i] = trybin
					zoomfactors[i] *= binfactors[i]
					break
			else:
				# just use bin
				zoomfactors[i] = 1.0

		## don't zoom 3rd axis of rgb image
		if is_rgb:
			zoomfactors.append(1.0)

		output = input

		#print "binfactors", binfactors
		#print "zoomfactors", zoomfactors

		### non-integer scaling (zoom) should happen before binning to reduce noise
		### non-integer scaling (zoom) should happen after binning to increase speed

		if binFirst is True:
			## run bin if any bin factors not 1
			if binfactors:
				for binfactor in binfactors:
					if binfactor != 1:
						output = pyami.imagefun.bin(output, binfactors[0], binfactors[1])
						break
			## run zoom if any zoom factors not 1.0
			if zoomfactors:
				for zoomfactor in zoomfactors:
					if zoomfactor != 1.0:
						## use bilinear interpolation, rather than bicubic;
						## bilinear is faster and works better with noisy images
						output = scipy.ndimage.zoom(output, zoomfactors, order=order)
						break

		else:
			## run zoom if any zoom factors not 1.0
			if zoomfactors:
				for zoomfactor in zoomfactors:
					if zoomfactor != 1.0:
						## use bilinear interpolation, rather than bicubic;
						## bilinear is faster and works better with noisy images
						output = scipy.ndimage.zoom(output, zoomfactors, order=order)
						break
			## run bin if any bin factors not 1
			if binfactors:
				for binfactor in binfactors:
					if binfactor != 1:
						output = pyami.imagefun.bin(output, binfactors[0], binfactors[1])
						break
					
		return output

def makeImage(inshape, noiselevel=1):
	raccoon_rgb = scipy.misc.face()
	raccoon_gray = numpy.mean(raccoon_rgb, 2)
	zoomfactors = numpy.array(inshape)/numpy.array(raccoon_gray.shape, dtype=float)
	raccoon_scaled = scipy.ndimage.zoom(raccoon_gray, zoomfactors, order=3)
	raccoon_scaled = raccoon_scaled - raccoon_scaled.mean()
	raccoon = raccoon_scaled / raccoon_scaled.std()
	im = numpy.random.normal(0,1,inshape)*noiselevel + raccoon
	return im

if __name__ == '__main__':
	inshape = (5763, 7684)
	finalshape = (512,512)
	noiselevel = 1

	final = makeImage(finalshape, 0)
	#inshape = (1326, 1768)
	im = makeImage(inshape, noiselevel)

	cca = numpy.zeros((4,2))
	timea = numpy.zeros((4,2))
	for order in (0,1,2,3):
		for binFirst in [True, False]:
			imagefile.arrayToJpeg(im, "input.jpg")
			t0 = time.time()
			output = scale(im, (512,512), order, binFirst)
			tdiff = (time.time() - t0)
			print "TIME %.3f seconds"%(tdiff)
			timea[order,int(binFirst)] = tdiff*1e3
			cc = scipy.stats.pearsonr(output.ravel(), final.ravel())[0]
			cca[order,int(binFirst)] = cc
			print "CORRELATION: %.8f"%(cc)
			outname = "output_order%d_%s.jpg"%(order, str(binFirst))
			imagefile.arrayToJpeg(output, outname)
	for cc in cca:
		print cc[0], cc[1]
	for t in timea:
		print t[0], t[1]
