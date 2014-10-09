#!/usr/bin/env python

import pyami.mrc
import numpy
import shutil
import pyami.imagic

def yflip_copy(mrc_header, fin, fout):
	'''
	copy stack data from fin to fout, but flip data on y axis
	'''
	nx = mrc_header['nx']
	ny = mrc_header['ny']
	nz = mrc_header['nz'] or 1
	bpp = mrc_header['dtype'].itemsize
	ystride = nx * bpp
	zstride = nx * ny * bpp
	inpos0 = fin.tell()
	for z in range(nz):
		for y in range(ny):
			inpos = inpos0 + (z+1) * zstride - (y+1) * ystride
			fin.seek(inpos)
			data = fin.read(ystride)
			fout.write(data)

def imagic_to_mrc(imagic_name, mrc_name, yflip=False):
	# read imagic header
	if imagic_name.endswith('.hed') or imagic_name.endswith('.img'):
		imagic_name = imagic_name[:-4]
	hed_name = imagic_name + '.hed'
	dat_name = imagic_name + '.img'
	imagic_header = pyami.imagic.readImagicHeader(hed_name)

	## create generic mrc header
	mrc_header = pyami.mrc.newHeader()
	pyami.mrc.updateHeaderDefaults(mrc_header)
	## copy some values from imagic header to mrc header
	for key in imagic_header.keys():
		mrc_header[key] = imagic_header[key]
	mrc_header['mode'] = pyami.mrc.numpy2mrc[mrc_header['dtype'].type]
	mrc_header_data = pyami.mrc.makeHeaderData(mrc_header)

	## write mrc header to file
	fmrc = open(mrc_name, 'w')
	fmrc.write(mrc_header_data)

	## append imagic data file to mrc file
	fdat = open(dat_name)
	if yflip:
		yflip_copy(mrc_header, fdat, fmrc)
	else:
		shutil.copyfileobj(fdat, fmrc)
	fmrc.close()
	fdat.close()

def run():
	import sys
	imagicfile = sys.argv[1]
	mrcfile = sys.argv[2]
	yflip = False
	try:
		yflip = sys.argv[3]
		if yflip == 'yflip':
			yflip = True
	except:
		pass
	imagic_to_mrc(imagicfile, mrcfile, yflip)

if __name__ == '__main__':
	run()
