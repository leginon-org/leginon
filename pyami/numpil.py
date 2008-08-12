import Image
import numpy
import imagefun
import arraystats
import sys

pilformats = [
	'BMP',
	'GIF',
	'IM',
	'JPEG',
	'MSP',
	'PCX',
	'PDF',
	'PNG',
	'PPM',
	'SPIDER',
	'TIFF',
	'XBM',
]

def read(imfile):
	'''
	Read imagefile using PIL and convert to a 8 bit gray image in numpy array.
	'''
	im = Image.open(imfile)
	im = im.convert('L')
	width,height = im.size
	s = im.tostring()
	im = numpy.fromstring(s, numpy.uint8)
	im.shape = height,width
	return im

def write(a, imfile=None, format=None, limits=None):
	'''
	Convert array to 8 bit gray scale and save to filename.
	Format is determined from filename extension by PIL.
	'''
	if limits is None:
		mean = arraystats.mean(a)
		std = arraystats.std(a)
		limits = (mean-3*std, mean+3*std)
	a = imagefun.linearscale(a, limits, (0,255))
	a = a.clip(0,255)
	a = numpy.asarray(a, numpy.uint8)
	size = a.shape[1], a.shape[0]
	im = Image.frombuffer('L', size, a, 'raw', 'L', 0, 1)
	if imfile is None:
		imfile = sys.stdout
	try:
		im.save(imfile, format=format)
	except KeyError:
		## bad file format
		sys.stderr.write('Bad PIL image format.  Try one of these: %s\n' % (pilformats,))
