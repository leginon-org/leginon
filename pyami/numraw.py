#!/usr/bin/env python
import numpy
import imagefun
import arraystats
import sys
import scipy.ndimage

class NumRaw(object):
	'''
	This reader is based on FEI Falcon intermediate frame RAW format
	'''
	def __init__(self,filepath):
		self.fobj = open(filepath)
		self.defineHeader()
		self.header = self.parseHeader()

	def defineHeader(self):
		self.numheader_offset = 13
		self.numheader_type = numpy.int32
		self.data_offset = 49
		self.data_type = numpy.int32
		self.header_keys = [1,'nx','ny','channels','bits','encoding','offset','stride_x','stride_y']

	def parseHeader(self):
		self.fobj.seek(self.numheader_offset)
		datalen = (self.data_offset - self.numheader_offset) / numpy.dtype(self.numheader_type).itemsize
		if datalen != len(self.header_keys):
			print 'ERROR datalen ', datalen, '!= header keys len'
			return False
		# make headerdict
		headerdict = {}

		header_values = numpy.fromfile(self.fobj, dtype=self.data_type, count=datalen).tolist()
		for i,k in enumerate(self.header_keys):
			headerdict[k] = header_values[i]
		headerdict['dtype'] = numpy.dtype(self.data_type)
		headerdict['shape'] = (headerdict['ny'],headerdict['ny'])
		return headerdict

	def readDataFromFile(self, fobj, headerdict, zslice=None):
		'''
		Read data portion of RAW file from the file object fobj.
		Returns a new numpy ndarray object. similar to mrc.py
		'''
		bytes_per_pixel = headerdict['dtype'].itemsize
		framesize = bytes_per_pixel * headerdict['nx'] * headerdict['ny']
		if zslice is None:
			start = self.data_offset  # right after header
			shape = headerdict['shape']
		else:
			start = self.data_offset + zslice * framesize
			shape = headerdict['shape'][-2:]  # only a 2-D slice
		datalen = reduce(numpy.multiply, shape)
		fobj.seek(start)
		a = numpy.fromfile(fobj, dtype=headerdict['dtype'], count=datalen)
		a.shape = shape
		return a

def read(imfile):
	'''
	Read imagefile, then convert to a int32 numpy array.
	'''
	reader = NumRaw(imfile)
	h = reader.parseHeader()
	im = reader.readDataFromFile(reader.fobj,reader.header)
	return im

def readHeaderFromFile(imfile):
	reader = NumRaw(imfile)
	return reader.header

if __name__ == '__main__':
	a = read('n0.raw')
	print a
	print readHeaderFromFile('n0.raw')
