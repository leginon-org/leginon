#!/usr/bin/env python

# standard library
import cStringIO

# third party
import numpy
import scipy.misc
import scipy.ndimage
import scipy.stats

# myami
import pyami.mrc
pyami.mrc.cache_enabled = True
import pyami.numpil
import pyami.imagefun
import pyami.fft

def read_mrc(filename, region=None):
	image_array = pyami.mrc.mmap(filename)
	return image_array

def read_pil(filename, region=None):
	image_array = pyami.numpil.read(filename)
	return image_array

def array_to_pil(image_array, min=None, max=None):
	pil_image = scipy.misc.toimage(image_array, cmin=min, cmax=max)
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
		if 'fftmask' in kwargs:
			try:
				fftmask = float(kwargs['fftmask'])
			except:
				fftmask = None
		else:
			fftmask = None
		image_array = pyami.fft.calculator.power(image_array, full=True, centered=True, mask=fftmask)

	### simple binning
	if 'bin' in kwargs:
		bin = int(kwargs['bin'])
		image_array = pyami.imagefun.bin(image_array, bin)

	if 'scaletype' in kwargs:
		scaletype = kwargs['scaletype']
		if 'scalemin' in kwargs:
			scalemin = float(kwargs['scalemin'])
		else:
			scalemin = None
		if 'scalemax' in kwargs:
			scalemax = float(kwargs['scalemax'])
		else:
			scalemax = None
		## now convert scalemin,scalemax to values to pass to linearscale
		if scaletype == 'minmax':
			pass
		elif scaletype == 'stdev':
			mean = pyami.arraystats.mean(image_array)
			std = pyami.arraystats.std(image_array)
			scalemin = mean + scalemin * std
			scalemax = mean + scalemax * std
		elif scaletype == 'cdf':
			fmin = pyami.arraystats.min(image_array)
			fmax = pyami.arraystats.max(image_array)
			n = image_array.size
			bins = int(fmax-fmin+1)
			bins = bins/10
			cumfreq, lower, width, x = scipy.stats.cumfreq(image_array, bins)
			cumfreq /= n
			pmin = True
			for j in range(bins):
				if pmin and cumfreq[j] >= scalemin:
					pmin = False
					minval = j
				elif cumfreq[j] >= scalemax:
					maxval = j
					break
			scalemin = lower + (minval+0.5) * width
			scalemax = lower + (maxval+0.5) * width

		image_array = pyami.imagefun.linearscale(image_array, (scalemin, scalemax), (0,255))
		image_array = numpy.clip(image_array, 0, 255)

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

def autoscale(image_array, arg):
	args = arg.split(';')
	if args[0] == '':
		pass
	return image_array

def test_defaults(filename):
	'''test processing with defaults.  should output jpeg'''
	output = process(test_filename)
	f = open('test.jpg', 'w')
	f.write(output)
	f.close()
