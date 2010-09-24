# standard lib
import os

# myami
import pyami.mrc
import pyami.numpil

# local
from redux.pipe import Pipe

class Read(Pipe):
	cache_file = False
	required_args = {'filename': os.path.abspath}

	def make_dirname(self):
		abs = os.path.abspath(self.kwargs['filename'])
		drive,tail = os.path.splitdrive(self.kwargs['filename'])
		self._dirname = tail[1:]

	def run(self, input, filename):
		## input ignored
		### determine input format
		if filename.endswith('mrc') or filename.endswith('MRC'):
			## use MRC module to read
			input_format = 'mrc'
		else:
			## use PIL to read
			input_format = 'PIL'

		### Read image file
		if input_format == 'mrc':
			# use mrc
			image_array = pyami.mrc.read(filename)
		elif input_format == 'PIL':
			# use PIL
			image_array = pyami.numpil.read(filename)
		return image_array

