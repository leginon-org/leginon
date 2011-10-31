#!/usr/bin/env python

import pyami.mrc
import numpy
import shutil
import pyami.imagic

def imagic_to_mrc(imagic_name, mrc_name):
	# read imagic header
	hed_name = imagic_name + '.hed'
	dat_name = imagic_name + '.img'
	imagic_header = pyami.imagic.readImagicHeader(hed_name)

	## create generic mrc header
	mrc_header = pyami.mrc.newHeader()
	pyami.mrc.updateHeaderDefaults(mrc_header)
	## copy some values from imagic header to mrc header
	for key in imagic_header.keys():
		mrc_header[key] = imagic_header[key]
	mrc_header['mode'] = pyami.mrc.numpy2mrc[mrc_header['dtype']]
	mrc_header_data = pyami.mrc.makeHeaderData(mrc_header)

	## write mrc header to file
	fmrc = open(mrc_name, 'w')
	fmrc.write(mrc_header_data)

	## append imagic data file to mrc file
	fdat = open(dat_name)
	shutil.copyfileobj(fdat, fmrc)
	fmrc.close()
	fdat.close()

def run():
	import sys
	imagicfile = sys.argv[1]
	mrcfile = sys.argv[2]
	imagic_to_mrc(imagicfile, mrcfile)

if __name__ == '__main__':
	run()
