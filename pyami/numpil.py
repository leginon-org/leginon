#!/usr/bin/env python
from PIL import Image
from PIL import ImageDraw
from PIL import ImageSequence
from PIL import ImageStat
import numpy
from pyami import imagefun
from pyami import arraystats
import sys
import scipy.ndimage
import tifffile
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

def im2numpy(im):
	width,height = im.size
	shape = height,width
	if im.mode == 'F':
		s = pil_image_tobytes(im, "raw")
		a = numpy.frombuffer(s, numpy.float32)
	elif im.mode == 'RGB':
		s = pil_image_tobytes(im, "raw")
		a = numpy.frombuffer(s, numpy.uint8)
		shape = shape + (3,)
	else:
		im = im.convert('L')
		s = pil_image_tobytes(im, "raw")
		a = numpy.frombuffer(s, numpy.uint8)
	a.shape = shape
	return a

def textArray(text, scale=1):
	im = Image.new('1', (1,1))
	draw = ImageDraw.Draw(im)
	left,top,right,bottom = draw.textbbox((0,0),text)
	cols = right - left
	rows = bottom - top
	im = Image.new('1', (cols,rows))
	draw = ImageDraw.Draw(im)
	draw.text((0,0), text, fill=1)
	a = im2numpy(im)
	a = numpy.where(a,1,0)
	if scale != 1:
		a = scipy.ndimage.zoom(a,scale)
	return a

def read(imfile):
	'''
	Read imagefile using PIL.  If it is in PIL mode 'F', then convert to a
	float32 numpy array.  Otherwise, convert to PIL 8 bit gray then, to
	uint8 numpy array.
	'''
	im = Image.open(imfile)
	im = im2numpy(im)
	return im

def readInfo(imfile):
	info = {}
	try:
		im = Image.open(imfile)
	except:
		tif = tifffile.TiffFile(imfile)
		info['ny'], info['nx'] = tif.pages[0].shape
		info['nz'] = len(tif.pages)
		return info
	info.update(im.info)
	info['nx'], info['ny'] = im.size
	info['nz'] = sum(1 for e in ImageSequence.Iterator(im))
	stat = ImageStat.Stat(im)
	extrema = im.getextrema()
	number_of_bands = len(im.getbands())
	if number_of_bands > 1:
		# multibands, use the most extreme value. Don't know what to do.
		info['amin'] = min(list(map((lambda x:x[0]),extrema)))
		info['amax'] = min(list(map((lambda x:x[1]),extrema)))
	else:
		info['amin'] = extrema[0]
		info['amax'] = extrema[1]
	# always as list
	info['amean'] = sum(stat.mean)/float(len(stat.mean))
	info['rms'] = sum(stat.stddev)/float(len(stat.mean)) #this is actually defined as rmsd in mrc header
	return info

def write(a, imfile=None, format=None, limits=None, writefloat=False):
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
	if writefloat and a.dtype.type in (numpy.int64, numpy.float32):
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

def pil_image_tostring(obj, encoder_name="raw", *args):
	# tostring is deprecated use tobytes
	# obj is an instance of image class in PIL Image module
	return pil_image_tobytes(obj, encoder_name, *args)

def pil_image_tobytes(obj, encoder_name="raw", *args):
	# obj is an instance of image class in PIL Image module
	return obj.tobytes(encoder_name, *args)

def frombytes(data, decoder_name="raw", *args):
	return getattr(Image, 'frombytes')(data,decoder_name, *args)

def fromstring(data, decoder_name="raw", *args):
	return frombytes(decoder_name, *args)

def sumTiffStack(filename):
	try:
		im = Image.open(filename)
	except:
		tif = tifffile.TiffFile(filename)		
		a = tif.pages[0].asarray()
		for item in tif.pages[1:-1]:
			a += item.asarray()
		return a 
	imitr = ImageSequence.Iterator(im)
	for i, frame in enumerate(imitr):
		if i == 0:
			a = numpy.array(frame.convert('L'))
		else:
			a += numpy.array(frame.convert('L'))
	return a

def tiff2numpy_array(filename, section):
	try:
		im = PIL.Image.open(filename)
	except:
		tif = tifffile.TiffFile(filename)
		return tif.pages[selection].asarray()
	im.seek(section)
	return numpy.array(im.convert('L'))

Image2 = Image
###temporary hack for FSU
import PIL
if hasattr(PIL, '__version__'):
	if int(PIL.__version__[0]) >= 3:
		Image2.fromstring = Image.frombytes
elif hasattr(PIL, 'PILLOW_VERSION'):
	if int(PIL.PILLOW_VERSION[0]) >= 3:
		Image2.fromstring = Image.frombytes

if __name__ == '__main__':
	a = textArray('Hello')
	write(a, 'hello.png')
