# 3rd party
import scipy.ndimage

# myami
import pyami.imagefun

# local
from redux.pipe import Pipe
from redux.pipe import shape_converter

class Shape(Pipe):
	required_args = {'shape': shape_converter}
	def run(self, input, shape):
		# make sure shape is same dimensions as input image
		if len(shape) != len(input.shape):
			raise ValueError('mismatch in number of dimensions: %s -> %s' % (input.shape, shape))

		# determine whether to use imagefun.bin or scipy.ndimage.zoom
		# for now, bin function only allows same bin factor on all axes
		binfactor = input.shape[0] / shape[0]
		zoomfactors = []
		for i in range(len(shape)):
			# zoom factor on this axis
			zoomfactors.append(float(shape[i])/float(input.shape[i]))

			# check original shape is divisible by new shape
			if input.shape[i] % shape[i]:
				binfactor = None   # binning will not work
				
			# check bin factor on this axis same as other axes
			if input.shape[i] / shape[i] != binfactor:
				binfactor = None  # binning will not work

		if binfactor:
			output = pyami.imagefun.bin(input, binfactor)
		else:
			output = scipy.ndimage.zoom(input, zoomfactors)
		return output

	def make_dirname(self):
		dims = map(str, self.kwargs['shape'])
		dims = 'x'.join(dims)
		self._dirname = dims

