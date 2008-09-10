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
	Read imagefile using PIL.  If it is in PIL mode 'F', then convert to a
	float32 numpy array.  Otherwise, convert to PIL 8 bit gray then, to
	uint8 numpy array.
	'''
	im = Image.open(imfile)
	width,height = im.size
	if im.mode == 'F':
		s = im.tostring()
		im = numpy.fromstring(s, numpy.float32)
	else:
		im = im.convert('L')
		s = im.tostring()
		im = numpy.fromstring(s, numpy.uint8)

	im.shape = height,width
	return im

def write(a, imfile=None, format=None, limits=None, float=False):
	'''
	Convert array to 8 bit gray scale and save to filename.
	Format is determined from filename extension by PIL.
	'''
	if limits is None:
		mean = arraystats.mean(a)
		std = arraystats.std(a)
		limits = (mean-3*std, mean+3*std)

	size = a.shape[1], a.shape[0]

	if imfile is None:
		imfile = sys.stdout

	## try saving float data
	if a.dtype.type in (numpy.int64, numpy.float32):
		a = numpy.asarray(a, numpy.float32)
		im = Image.frombuffer('F', size, a, 'raw', 'F', 0, 1)
		try:
			im.save(imfile, format=format)
			return
		except:
			## assume any exception here means that float32 not supported
			pass

	## save scaled 8 bit data
	a = imagefun.linearscale(a, limits, (0,255))
	a = a.clip(0,255)
	a = numpy.asarray(a, numpy.uint8)
	im = Image.frombuffer('L', size, a, 'raw', 'L', 0, 1)

	try:
		im.save(imfile, format=format)
	except KeyError:
		## bad file format
		sys.stderr.write('Bad PIL image format.  Try one of these: %s\n' % (pilformats,))
