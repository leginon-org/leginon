# standard lib
import cStringIO

# 3rd party
import numpy
import scipy.misc

# myami
import pyami.mrc

# local
import redux.pipe
import redux.utility

class Format(redux.pipe.Pipe):
	required_args = {'oformat': str}
	optional_args = {'rgb': redux.pipe.bool_converter}
	optional_defaults = {'rgb': False}
	file_formats = {
		'JPEG': '.jpg',
		'GIF': '.gif',
		'TIFF': '.tif',
		'PNG': '.png',
		'MRC': '.mrc',
		'JSON': '.json',
	}
	def run(self, input, oformat, rgb):
		if oformat not in self.file_formats:
			raise ValueError('oformat: %s' % (oformat,))

		if oformat == 'MRC':
			s = self.run_mrc(input)
		elif oformat == 'JSON':
			s = self.run_json(input)
		else:
			s = self.run_pil(input, oformat, rgb)

		return s

	def run_mrc(self, input):
		file_object = cStringIO.StringIO()
		pyami.mrc.write(input, file_object)
		image_string = file_object.getvalue()
		file_object.close()
		return image_string

	def run_json(self, input):
		outstring = redux.utility.json_encode(input)
		return outstring

	def run_pil(self, input, oformat, rgb):
		pil_image = scipy.misc.toimage(input, cmin=0, cmax=255)
		if rgb:
			pil_image = pil_image.convert('RGB')
		file_object = cStringIO.StringIO()
		pil_image.save(file_object, oformat)
		image_string = file_object.getvalue()
		file_object.close()
		return image_string

	def make_dirname(self):
		self._dirname = None

	def make_resultname(self):
		format = self.kwargs['oformat']
		self._resultname = 'result' + self.file_formats[format]

	def put_result(self, f, result):
		f.write(result)

	def get_result(self, f):
		return f.read()

