#!/usr/bin/env python

import mrc
import numpy
import shutil

# FIX:  only handling REAL for now
code_to_dtype = {
	numpy.frombuffer('REAL', numpy.int32)[0]:  numpy.dtype(numpy.float32),
	# ...
}

def readImagicHeader(filename,i=0):
	hed_array_int = numpy.fromfile(filename, numpy.int32)
	hed_array_float = hed_array_int.view(numpy.float32)
	hed_dict = {}
	# eman uses i4lp to store number of particles in class average image stack
	hed_dict['i4lp'] = hed_array_int[61+i*256]
	hed_dict['ny'] = hed_array_int[12]
	hed_dict['nx'] = hed_array_int[13]
	hed_dict['nz'] = len(hed_array_int.data) / 1024
	hed_dict['dtype'] = code_to_dtype[hed_array_int[14]]
	hed_dict['amin'] = hed_array_float[22]
	hed_dict['amax'] = hed_array_float[21]
	hed_dict['amean'] = hed_array_float[17]
	hed_dict['rms'] = hed_array_float[18]
	return hed_dict

def readImagicData(filename, header_dict, frame=None):
	dtype = header_dict['dtype']
	if header_dict['nz'] > 1 and frame is None:
		shape = header_dict['nz'], header_dict['ny'], header_dict['nx']
	else:
		shape = header_dict['ny'], header_dict['nx']

	if frame is None:
		start = 0
	else:
		start = frame * shape[-1] * shape[-2] * dtype.itemsize

	nelements = numpy.product(shape)

	a = numpy.memmap(filename, dtype=dtype, mode='r', offset=start, shape=shape, order='C')
	#f = open(filename)
	#f.seek(start)
	#a = numpy.fromfile(f, dtype, nelements)
	#f.close()
	#a.shape = shape
	return a

opposite = {
	'hed': 'img',
	'HED': 'IMG',
	'img': 'hed',
	'IMG': 'HED',
}

def filepair(single):
	ext = single[-3:]
	pair = {}
	if ext in opposite:
		other_ext = opposite[ext]
		pair[ext.lower()] = single
		pair[other_ext.lower()] = single[:-3] + other_ext
	else:
		pair['hed'] = single + '.hed'
		pair['img'] = single + '.img'
	return pair

def read(filename, frame=None):
	pair = filepair(filename)
	header_dict = readImagicHeader(pair['hed'])
	a = readImagicData(pair['img'], header_dict, frame)
	return a
