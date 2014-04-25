#!/usr/bin/env python

import pyami.mrc
import numpy
import pyami.numraw

def fei_to_mrc(fei_raw_names, mrc_name,int32to16=True):
	'''
	Convert a list of int32 FEI RAW files to
	float32 or int16 mrc image stack
	'''
	# allows single fei_raw_name input as string
	if isinstance(fei_raw_names, basestring):
		fei_raw_names = [fei_raw_names,]
	# get number of images to convert 
	nzslices = len(fei_raw_names)
	mid_zslice = nzslices / 2

	for i,fei_raw_name in enumerate(fei_raw_names):
		a = pyami.numraw.read(fei_raw_name)
		if int32to16:
			a = a.astype(numpy.int16)
		if i == 0:
			pyami.mrc.write(a,mrc_name)
		else:
			pyami.mrc.append(a,mrc_name,i==mid_zslice)

def run():
	import sys
	rawfile = sys.argv[1]
	mrcfile = sys.argv[2]
	fei_to_mrc(rawfile, mrcfile)

if __name__ == '__main__':
	run()
