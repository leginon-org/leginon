# myami
import pyami.imagefun

# local
from redux.pipe import Pipe

# 3rd party
import scipy.ndimage

class LPF(Pipe):
	required_args = {'lpf': float}
	def run(self, input, lpf):
		lpf = float(lpf)
		output = scipy.ndimage.gaussian_filter(input, lpf)
		return output
