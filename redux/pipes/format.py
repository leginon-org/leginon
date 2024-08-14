# standard lib
import io

# 3rd party
import scipy.misc
from PIL import Image
import numpy

# myami
import pyami.mrc

# local
import redux.pipe
import redux.utility

class Format(redux.pipe.Pipe):
	required_args = {'oformat': str}
	optional_args = {'rgb': redux.pipe.bool_converter, 'overlay': str, 'overlaycolor': float}
	optional_defaults = {'rgb': False, 'overlay': '', 'overlaycolor': 0.1}
	file_formats = {
		'JPEG': '.jpg',
		'GIF': '.gif',
		'TIFF': '.tif',
		'PNG': '.png',
		'MRC': '.mrc',
		'JSON': '.json',
	}
	def run(self, input, oformat, rgb, overlay, overlaycolor):
		if oformat not in self.file_formats:
			raise ValueError('oformat: %s' % (oformat,))

		if oformat == 'MRC':
			s = self.run_mrc(input)
		elif oformat == 'JSON':
			s = self.run_json(input)
		else:
			s = self.run_pil(input, oformat, rgb, overlay, overlaycolor)

		return s

	def run_mrc(self, input):
		file_object = io.StringIO()
		pyami.mrc.write(input, file_object)
		image_string = file_object.getvalue()
		file_object.close()
		return image_string

	def run_json(self, input):
		outstring = redux.utility.json_encode(input)
		return outstring

	def overlay_mask(self, image, mask, blendRatio=0.1):
		size = image.size
		mode = image.mode
		# read mask, resize it to image size
		# and make sure they are the same mode for the blend function
		maskim = Image.open(mask)
		maskim = maskim.resize(size)
		maskim = maskim.convert(mode)

		# Use PIL Image blend with alpha value between 0.0 and 1.0
		image = Image.blend(image, maskim, blendRatio)
		return image

	def run_pil(self, input, oformat, rgb, overlay, overlaycolor):
		# pil_image = scipy.misc.toimage(input, cmin=0, cmax=255)
		# refs Issue #13 input is float if going through intensity scaling.
		input = input.astype(numpy.uint8)
		pil_image = Image.fromarray(input)
		if rgb or overlay:
			pil_image = pil_image.convert('RGBA')
		if overlay:
			pil_image = self.overlay_mask(pil_image, overlay, overlaycolor)
		file_object = io.BytesIO()

		# -- this is very likely wrong :) but i get an image --
		pil_image = pil_image.convert("RGB")

		pil_image.save(file_object, oformat)
		image = file_object.getvalue()
		file_object.close()
		return image

	def make_dirname(self):
		self._dirname = None

	def make_resultname(self):
		format = self.kwargs['oformat']
		# Issue #4297 overlay in cache not recalculated upon change
		overlay = self.kwargs['overlay']
		overlaycolor = self.kwargs['overlaycolor']
		overlayname = ''
		if overlay:
			bits = overlay.split('/')
			overlayname='.'.join(bits)+'.%s' % (overlaycolor)
		# include overlay options in resultname
		self._resultname = 'result' + self.file_formats[format] + overlayname

	def put_result(self, f, result):
		f.write(result)

	def get_result(self, f):
		return f.read()

