#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

try:
	import numarray as Numeric
except:
	import Numeric
import Mrc
import Image
import re
import sys

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
	rangefrom = float(maxfrom - minfrom)
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
	(Numeric.UInt8,1) : ('L','L'),
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
	type = final.type()
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
	'Convert MRC -> JPEG [quality]'
	info = read_mrc(mrc_filename)
	ndata = info['array']
	datamin = info['min']
	datamax = info['max']
	sys.stderr.write('MIN ' + str(datamin) + '\n')
	sys.stderr.write('MAX ' + str(datamax) + '\n')
	if clip is None:
		clip = (datamin,datamax)

	img = Numeric_to_Image(ndata, clip, newsize)
	write_jpeg(img, None, quality)

if __name__ == '__main__':
	import sys

	mrc_filename = sys.argv[1]
	try:
		newsizex = int(sys.argv[2])
		newsizey = int(sys.argv[3])
	except IndexError:
		newsize = None
	else:
		newsize = (newsizex, newsizey)
	mrc2jpg2out(mrc_filename, clip=None, quality=100, newsize=newsize)
