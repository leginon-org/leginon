#!/usr/bin/env python
import numpy
import sys
import os

class NumRaw(object):
	'''
	This reader is based on FEI Falcon intermediate frame RAW format
	'''
	def __init__(self,filepath):
		self.filebytes = os.path.getsize(filepath)
		self.fobj = open(filepath)
		self.defineHeader()
		self.header = self.parseHeader()

	def defineHeader(self):
		self.header_offset = 13 # in bytes
		self.header_type = numpy.int32
		self.header_keys = [1,'nx','ny','channels','bits','encoding','offset','stride_x','stride_y']

	def getDataType(self,headerdict):
		'''
		Get data type based on header
		'''
		bits = headerdict['bits']
		if bits == 32:
			self.data_type = numpy.int32
		else:
			self.data_type = numpy.int16
		return self.data_type

	def parseHeader(self):
		self.fobj.seek(self.header_offset)
		datalen = len(self.header_keys)
		headerdict = {}

		header_values = numpy.fromfile(self.fobj, dtype=self.header_type, count=datalen).tolist()
		for i,k in enumerate(self.header_keys):
			headerdict[k] = header_values[i]

		self.data_offset = self.header_offset + numpy.dtype(self.header_type).itemsize * len(self.header_keys) + headerdict['offset']
		# additional headers
		headerdict['dtype'] = numpy.dtype(self.getDataType(headerdict))
		headerdict['shape'] = (headerdict['ny'],headerdict['nx'])
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
		a = numpy.reshape(a,shape)
		return a

def read(imfile):
	'''
	Read imagefile, then convert to a numpy array.
	'''
	reader = NumRaw(imfile)
	h = reader.parseHeader()
	im = reader.readDataFromFile(reader.fobj,reader.header)
	return im

def readHeaderFromFile(imfile):
	reader = NumRaw(imfile)
	return reader.parseHeader()

if __name__ == '__main__':
	a = read('n0.raw')
	print a
	print readHeaderFromFile('n0.raw')
