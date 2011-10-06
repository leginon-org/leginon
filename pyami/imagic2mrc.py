#!/usr/bin/env python

import mrc
import numpy
import shutil

# FIX:  only handling REAL for now
code_to_dtype = {
	numpy.frombuffer('REAL', numpy.int32)[0]:  numpy.float32,
	# ...
}

def readImagicHeader(filename):
	hed_array_int = numpy.fromfile(filename, numpy.int32)
	hed_array_float = hed_array_int.view(numpy.float32)
	hed_dict = {}
	hed_dict['ny'] = hed_array_int[12]
	hed_dict['nx'] = hed_array_int[13]
	hed_dict['nz'] = len(hed_array_int.data) / 1024
	hed_dict['dtype'] = code_to_dtype[hed_array_int[14]]
	return hed_dict

def imagic_to_mrc(imagic_name, mrc_name):
	# read imagic header
	hed_name = imagic_name + '.hed'
	dat_name = imagic_name + '.img'
	imagic_header = readImagicHeader(hed_name)

	## create generic mrc header
	mrc_header = mrc.newHeader()
	mrc.updateHeaderDefaults(mrc_header)
	## copy some values from imagic header to mrc header
	for key in ('nx', 'ny', 'nz', 'dtype'):
		mrc_header[key] = imagic_header[key]
	mrc_header['mode'] = mrc.numpy2mrc[mrc_header['dtype']]
	mrc_header_data = mrc.makeHeaderData(mrc_header)

	## write mrc header to file
	fmrc = open(mrc_name, 'w')
	fmrc.write(mrc_header_data)

	## append imagic data file to mrc file
	fdat = open(dat_name)
	shutil.copyfileobj(fdat, fmrc)

def run():
	import sys
	imagicfile = sys.argv[1]
	mrcfile = sys.argv[2]
	imagic_to_mrc(imagicfile, mrcfile)

if __name__ == '__main__':
	run()
