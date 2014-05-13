#!/usr/bin/env python
from PIL import Image
from PIL import ImageDraw
import numpy
import imagefun
import arraystats
import sys
import scipy.ndimage

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
		s = im.tostring()
		a = numpy.fromstring(s, numpy.float32)
	elif im.mode == 'RGB':
		s = im.tostring()
		a = numpy.fromstring(s, numpy.uint8)
		shape = shape + (3,)
	else:
		im = im.convert('L')
		s = im.tostring()
		a = numpy.fromstring(s, numpy.uint8)
	a.shape = shape
	return a

def textArray(text, scale=1):
	im = Image.new('1', (1,1))
	draw = ImageDraw.Draw(im)
	cols,rows = draw.textsize(text)
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
	im = Image.open(imfile)
	info = {}
	info.update(im.info)
	info['nx'], info['ny'] = im.size
	info['nz'] = 1
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

if __name__ == '__main__':
	a = textArray('Hello')
	write(a, 'hello.png')
