# standard lib
import os

import scipy.misc

# myami
import pyami.mrc
import pyami.numpil
import pyami.imagic
import pyami.spidernew

# local
from redux.pipe import Pipe

class Read(Pipe):
	cache_file = False
	required_args = {'filename': os.path.abspath}
	optional_args = {'frame': int, 'info': bool}
	optional_defaults = {'info': False}

	def make_dirname(self):
		## disable caching for frame requests
		if 'frame' in self.kwargs:
			self.disable_cache = True
			self._dirname = None
		else:
			self.disable_cache = False
			drive,tail = os.path.splitdrive(self.kwargs['filename'])
			self._dirname = tail[1:]

	def run(self, input, filename, info, frame=None):
		## input ignored
		### determine input format
		if filename.endswith('mrc') or filename.endswith('MRC'):
			## use MRC module to read
			input_format = 'mrc'
		elif filename[-3:].lower() in ('img', 'hed'):
			input_format = 'imagic'
		elif filename[-3:].lower() == 'spi':
			input_format = 'spider'
		else:
			## use PIL to read
			input_format = 'PIL'

		### Read image file
		if input_format == 'mrc':
			# use mrc
			head = pyami.mrc.readHeaderFromFile(filename)
			if info:
				result = head
			else:
				if frame is None and head['nz'] > 1:
					raise ValueError('reading entire stack not allowed: %s' % (filename,))
				result = pyami.mrc.read(filename, frame)
		elif input_format == 'imagic':
			if info:
				result = pyami.imagic.readImagicHeader(filename, frame)
			else:
				result = pyami.imagic.read(filename, frame)
		elif input_format == 'PIL':
			# use PIL
			if info:
				result = pyami.numpil.readInfo(filename)
			else:
				result = scipy.misc.imread(filename)
				if len(result.shape) < 2:
					# some combination of scipy os gives pngimagefile object as the scaler item of array
					result = pyami.numpil.im2numpy(result.item())
		elif input_format == 'spider':
			if info:
				result = pyami.spidernew.read_info(filename, frame)
			else:
				result = pyami.spidernew.read(filename, frame)
		return result

