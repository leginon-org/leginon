# myami
import pyami.imagefun

# local
from redux.pipe import Pipe
from redux.pipe import int_converter

class Mask(Pipe):
	required_args = {'maskradius': int_converter}
	def run(self, input, maskradius):
		maskradius = int(maskradius)
		output = pyami.imagefun.center_mask(input, maskradius, copy=True)
		return output

	def make_dirname(self):
		# only one arg, which is desriptive enough, so keeping it simple
		args = ['%s:%s' % (a,b) for (a,b) in self.args_tuple]
		self._dirname = ','.join(args)

