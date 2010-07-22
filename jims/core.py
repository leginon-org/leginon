#!/usr/bin/env python

# standard library
import cStringIO

# third party
import scipy.misc
import scipy.ndimage

# myami
import pyami.mrc
import pyami.numpil
import pyami.imagefun

def read_mrc(filename, region=None):
	image_array = pyami.mrc.mmap(filename)
	return image_array

def read_pil(filename, region=None):
	image_array = pyami.numpil.read(filename)
	return image_array

def array_to_pil(image_array):
	pil_image = scipy.misc.toimage(image_array)
	return pil_image

def output_to_string(pil_image, output_format):
	file_object = cStringIO.StringIO()
	output_to_file(pil_image, output_format, file_object)
	image_string = file_object.getvalue()
	file_object.close()
	return image_string

def output_to_file(pil_image, output_format, file_object):
	pil_image.save(file_object, output_format)

def process(filename, **kwargs):
	### determine input format
	if 'input_format' in kwargs:
		input_format = kwargs['in_format']
	elif filename.endswith('mrc') or filename.endswith('MRC'):
		## use MRC module to read
		input_format = 'mrc'
	else:
		## use PIL to read
		input_format = 'PIL'

	### Read image file
	if input_format == 'mrc':
		# use mrc
		image_array = read_mrc(filename)
	elif input_format == 'PIL':
		# use PIL
		image_array = read_pil(filename)

	### fft
	if 'fft' in kwargs and int(kwargs['fft']):
		image_array = pyami.imagefun.power(image_array)

	### simple binning
	if 'bin' in kwargs:
		bin = int(kwargs['bin'])
		image_array = pyami.imagefun.bin(image_array, bin)

	### convert array to PIL image
	pil_image = array_to_pil(image_array)

	### generate desired output format
	if 'output_format' in kwargs:
		output_format = kwargs['output_format']
	else:
		output_format = 'JPEG'

	if 'output_file' in kwargs:
		output_to_file(pil_image, output_format, kwargs['output_file'])
		return None
	else:
		s = output_to_string(pil_image, output_format)
		return s

def test_defaults(filename):
	'''test processing with defaults.  should output jpeg'''
	output = process(test_filename)
	f = open('test.jpg', 'w')
	f.write(output)
	f.close()
