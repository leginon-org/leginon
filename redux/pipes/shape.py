# 3rd party
import scipy.ndimage

# myami
import pyami.imagefun

# local
from redux.pipe import Pipe
from redux.pipe import shape_converter

class Shape(Pipe):
	required_args = {'shape': shape_converter}

	@classmethod
	def run(cls, input, shape):

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

		"""
		Neil: based on my tests: zoom first then bin at order =1 is fastest
		  and had the best results

		Correlation Coefficient
		(bigger is better)
		order	zoom first	binning first
		0		0.78			0.79
		1		0.88			0.89
		2		0.83			0.83
		3		0.83			0.83

		Run Time in milliseconds
		(smaller is better)
		order	zoom first	binning first
		0		60.47			164.60
		1		96.07			203.35
		2		2,364.70		299.81
		3		2,455.46		310.77
		"""

		## run zoom if any zoom factors not 1.0
		if zoomfactors:
			for zoomfactor in zoomfactors:
				if zoomfactor != 1.0:
					## use bilinear interpolation, rather than bicubic;
					## bilinear is faster and works better with noisy images
					output = scipy.ndimage.zoom(output, zoomfactors, order=1)
					break

		## run bin if any bin factors not 1
		if binfactors:
			for binfactor in binfactors:
				if binfactor != 1:
					output = pyami.imagefun.bin(output, binfactors[0], binfactors[1])
					break





		return output

	def make_dirname(self):
		dims = map(str, self.kwargs['shape'])
		dims = 'x'.join(dims)
		self._dirname = dims


