# standard lib
import os, sys

# myami
import pyami.mrc
import pyami.numpil
import pyami.imagic
import pyami.spidernew

# local
from redux.pipe import Pipe
import redux.webimg

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
		if os.path.isdir(filename):
			sys.stderr.write('No file specified')
			return
		if not os.path.exists(filename):
			# if the requested filename is an .mrc and does not exist, 
			# check to see if we have a webimg jpg archive. otherwise bail.
			_, ext = os.path.splitext(filename)
			if not ext.lower().startswith(".mrc"):
				raise Exception("Read: file does not exist [%s]" % filename)
			sys.stderr.write(filename + ' does not exist.')
			filename = redux.webimg.path(filename)
			sys.stderr.write('Trying webimg version instead: '+filename)
		if filename.endswith('mrc') or filename.endswith('MRC') or filename.endswith('mrcs'):
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
				result = pyami.numpil.read(filename)
				if len(result.shape) < 2:
					# some combination of scipy os gives pngimagefile object as the scaler item of array
					result = pyami.numpil.im2numpy(result.item())
		elif input_format == 'spider':
			if info:
				result = pyami.spidernew.read_info(filename, frame)
			else:
				result = pyami.spidernew.read(filename, frame)
		return result

