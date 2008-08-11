import Image
import numpy
import imagefun
import arraystats
import sys

pilformats = '''
BMP
BUFR (identify only)
CUR (read only)
DCX (read only)
EPS (write-only)
FITS (identify only)
FLI, FLC (read only)
FPX (read only)
GBR (read only)
GD (read only)
GIF
GRIB (identify only)
HDF5 (identify only)
ICO (read only)
IM
IMT (read only)
IPTC/NAA (read only)
JPEG
MCIDAS (read only)
MIC (read only)
MPEG (identify only)
MSP
PALM (write only)
PCD (read only)
PCX
PDF (write only)
PIXAR (read only)
PNG
PPM
PSD (read only)
SGI (read only)
SPIDER
TGA (read only)
TIFF
WAL (read only)
WMF (identify only)
XBM
XPM (read only)
XV Thumbnails
'''

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

def write(a, imfile=None, format=None):
	'''
	Convert array to 8 bit gray scale and save to filename.
	Format is determined from filename extension by PIL.
	'''
	mean = arraystats.mean(a)
	std = arraystats.std(a)
	limit = (mean-3*std, mean+3*std)
	a = imagefun.linearscale(a, limit, (0,255))
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
		sys.stderr.write('Bad PIL image format.  Try one of these: %s' % (pilformats,))
