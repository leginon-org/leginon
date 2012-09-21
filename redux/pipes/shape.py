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
				binfactors.append(input.shape[i] / shape[i])

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
					output = scipy.ndimage.zoom(output, zoomfactors)
					break

		return output

	def make_dirname(self):
		dims = map(str, self.kwargs['shape'])
		dims = 'x'.join(dims)
		self._dirname = dims

