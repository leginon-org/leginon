#!/usr/bin/env python
import Numeric
import Mrc
import Image
import re
import sys
import getopt

"""
Convert MRC -> JPEG
"""

def linearscale(input, boundfrom, boundto):
	"""
	Rescale the data in the range 'boundfrom' to the range 'boundto'.
	"""

	### check args
	if len(input) < 1:
		return input
	if len(boundfrom) != 2:
		raise ValueError, 'boundfrom must be length 2'
	if len(boundto) != 2:
		raise ValueError, 'boundto must be length 2'

	minfrom,maxfrom = boundfrom
	minto,maxto = boundto

	## prepare for fast math
	rangefrom = Numeric.array((maxfrom - minfrom)).astype('f')
	rangeto = Numeric.array((maxto - minto)).astype('f')
	minfrom = Numeric.array(minfrom).astype('f')

	# this is a hack to prevent zero division
	# is there a better way to do this with some sort of 
	# float limits module rather than hard coding 1e-99?
	if not rangefrom:
		rangefrom = 1e-99

	scale = rangeto / rangefrom
	offset = minfrom * scale
	output = input * scale - offset

	return output

def resize(pil_image, size):
	if size:
		if size != pil_image.size:
			new_image = pil_image.resize(size, Image.NEAREST)
		else:
			new_image = pil_image
	else:
		new_image = pil_image
	return new_image

## (Numeric typcode,size) => (PIL mode,  PIL rawmode)
ntype_itype = {
	(Numeric.UnsignedInt8,1) : ('L','L'),
	(Numeric.Int16,2) : ('I','I;16NS'),
	(Numeric.Int,2) : ('I','I;16NS'),
	(Numeric.Int,4) : ('I','I;32NS'),
	(Numeric.Int32,4) : ('I','I;32NS'),
	(Numeric.Float,4) : ('F','F;32NF'),
	(Numeric.Float,8) : ('F','F;64NF'),
	(Numeric.Float32,4) : ('F','F;32NF'),
	(Numeric.Float64,8) : ('F','F;64NF')
	}

def Numeric_to_Image(numarray, clip, outputsize=None):
	"""
	generates the PIL Image representation of this Numeric array
	"""
	## scale everything between clip[0] and clip[1] to (0,255)
	final = linearscale(numarray, clip, (0,255))
	type = final.typecode()
	h,w = final.shape
	imsize = w,h
	itemsize = final.itemsize()
	immode = ntype_itype[type,itemsize][0]
	rawmode = ntype_itype[type,itemsize][1]
	nstr = final.tostring()
	stride = 0
	orientation = 1
	image = Image.fromstring(immode, imsize, nstr, 'raw', rawmode, stride, orientation)
	if outputsize is not None:
		image = resize(image, outputsize)
	return image

def read_mrc(filename):
	# read header, data
	f = open(filename, 'rb')
	hdr = Mrc.MrcHeader(f)
	dat = Mrc.MrcData()
	dat.useheader(hdr)
	dat.fromfile(f)
	f.close()
	## make info dict
	info = {}
	info['array'] = dat.toNumeric()
	if dat.min==0 and dat.max==0:
		#search min max	
		newmin = Numeric.argmin(Numeric.ravel(info['array']))
		info['min'] = Numeric.ravel(info['array'])[newmin]
		newmax = Numeric.argmax(Numeric.ravel(info['array']))
		info['max'] = Numeric.ravel(info['array'])[newmax]
	else:
		info['min'] = dat.min
		info['max'] = dat.max

	return info

def write_jpeg(pil_image, filename=None, quality=100):
	'''
	Convert numeric -> JPEG [quality]
	filename defaults to stdout
	quality defaults to 100
	'''
	if filename is None:
		filename = sys.stdout
	pil_image.convert('L').save(filename, "JPEG", quality=quality)

def mrc2jpg2out(mrc_filename, clip=None, quality=100, newsize=None):
	'Convert MRC -> min/MAX -> JPEG [quality]'
	info = read_mrc(mrc_filename)
	ndata = info['array']
	datamin = info['min']
	datamax = info['max']
	max_jpg_value=255

	min = datamin
	max = datamax
	if clip[0] is not None:
		min = datamin + clip[0] * (datamax-datamin)/max_jpg_value
	if clip[1] is not None:
		max = datamin + clip[1] * (datamax-datamin)/max_jpg_value
	clip = (min,max)

	img = Numeric_to_Image(ndata, clip, newsize)
	write_jpeg(img, None, quality)

if __name__ == '__main__':
	strarg = sys.argv[1:]
	args = getopt.getopt(strarg, 'n:x:s:q', ['min=', 'max=', 'size=', 'quality='])
	opts = dict(args[0])
	mrc_filename = args[1][0]

	minpix = None
	if opts.has_key('--min'):
		minpix = opts['--min']
	if opts.has_key('-n'):
		minpix = opts['-n']
	maxpix = None
	if opts.has_key('--max'):
		maxpix = opts['--max']
	if opts.has_key('-x'):
		maxpix = opts['-x']
	sizestr = None
	if opts.has_key('-s'):
		sizestr = opts['-s']
	if opts.has_key('--size'):
		sizestr = opts['--size']

	qualitystr = None
	if opts.has_key('-q'):
		qualitystr = opts['-q']
	if opts.has_key('--quality'):
		qualitystr = opts['--quality']

	if minpix is not None:
		minpix = eval(minpix)

	if maxpix is not None:
		maxpix = eval(maxpix)

	if sizestr is not None:
		size = sizestr.split('x')
		if len(size)>1:
			size = (eval(size[0]),eval(size[1]))
		else:
			size = (eval(size),eval(size))
	else:
		size = None

	quality=100
	if qualitystr is not None:
		quality = eval(qualitystr)

	mrc2jpg2out(mrc_filename, clip=(minpix,maxpix), quality=quality, newsize=size)
