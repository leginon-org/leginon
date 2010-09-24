# standard lib
import cStringIO

# 3rd party
import scipy.misc

# myami
import pyami.mrc

# local
from redux.pipe import Pipe

class Format(Pipe):
	required_args = {'oformat': str}
	file_formats = {'JPEG': '.jpg', 'GIF': '.gif', 'TIFF': '.tif', 'PNG': '.png', 'MRC': '.mrc'}
	def run(self, input, oformat):
		if oformat not in self.file_formats:
			raise ValueError('oformat: %s' % (oformat,))

		if oformat == 'MRC':
			s = self.run_mrc(input)
		else:
			s = self.run_pil(input, oformat)

		return s

	def run_mrc(self, input):
		file_object = cStringIO.StringIO()
		pyami.mrc.write(input, file_object)
		image_string = file_object.getvalue()
		file_object.close()
		return image_string

	def run_pil(self, input, oformat):
		pil_image = scipy.misc.toimage(input)
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

