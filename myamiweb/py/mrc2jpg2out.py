#!/usr/bin/env python
import Mrc
import Image
import MyNumericImage
import getopt
import sys


"""
Convert MRC -> JPEG -> Standard Output
"""

def mrc2jpg2out(filename, clip=(None,None), quality=100, newsize=None):
	'Convert MRC -> JPEG [quality] -> Standard Output'
	ndata = Mrc.mrc_to_numeric(filename)
	num_img = MyNumericImage.NumericImage(ndata)

	extrema = num_img.extrema
	curmin = extrema[0]
	curmax = extrema[1]
	valmax = 255
	min = curmin
	if clip[0] >= 0:
		min += clip[0] * (curmax-curmin)/valmax
	max = curmax
	if clip[1] >= 0:
		max = clip[1] * (curmax-curmin)/valmax + curmin
#
#	orig_size  = num_img.orig_size
#	new_width  = size[0]*orig_size[0]/100
#	new_height = size[1]*orig_size[1]/100
#	print orig_size
	num_img.transform['clip'] = (min,max,)
	num_img.jpeg(sys.stdout, quality, newsize)
	
if __name__ == '__main__':
	str = sys.argv[1:]
	args = getopt.getopt(str, 'n:x:s:', ['min=', 'max=', 'size='])
	opts = dict(args[0])
	filename = args[1][0]
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
	mrc2jpg2out(filename, clip=(minpix,maxpix), newsize=size)

