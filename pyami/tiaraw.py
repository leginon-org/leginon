#!/usr/bin/env python
import numpy
import sys
import os

class TiaRaw(object):
	'''
	This reader is based on TIA image RAW format
	'''
	data_types = {1: numpy.uint8, 2:numpy.uint16, 3:numpy.uint32, 4:numpy.int8, 5:numpy.int16, 6:numpy.int32, 7:numpy.float32, 8:numpy.float64}
	def __init__(self,filepath):
		self.filebytes = os.path.getsize(filepath)
		self.fobj = open(filepath)
		self.defineHeader()
		self.header = self.parseHeader()

	def defineHeader(self):
		self.header_offset = 0 # in bytes
		self.data_offset = 10 # in bytes
		self.header_keys = ['dtype','nx','ny','shape']

	def getDataType(self, type_value):
		'''
		Get data type based on header
		'''
		if type_value > 7 or type_value < 0:
			raise ValueError('Data type not decodable')
		self.data_type = self.data_types[type_value]
		return self.data_type

	def parseHeader(self):
		self.fobj.seek(self.header_offset)
		headerdict = {}
		# data type id is 2-bit integer
		dtype_value = numpy.fromfile(self.fobj, dtype=numpy.int16, count=1).tolist()[0]
		headerdict['dtype'] = numpy.dtype(self.getDataType(dtype_value))

		# additional headers
		shape_values = numpy.fromfile(self.fobj, dtype=numpy.int32, count=2).tolist()
		headerdict['nx'] = shape_values[0]
		headerdict['ny'] = shape_values[1]
		headerdict['shape'] = (shape_values[1],shape_values[0])
		return headerdict

	def readDataFromFile(self, fobj, headerdict):
		'''
		Read data portion of RAW file from the file object fobj.
		Returns a new numpy ndarray object. similar to mrc.py
		'''
		start = self.data_offset  # right after header
		shape = headerdict['shape']
		datalen = reduce(numpy.multiply, shape)
		fobj.seek(start)
		a = numpy.fromfile(fobj, dtype=headerdict['dtype'], count=datalen)
		a = numpy.reshape(a,shape)
		return a

def read(imfile):
	'''
	Read imagefile, then convert to a numpy array.
	'''
	reader = TiaRaw(imfile)
	h = reader.parseHeader()
	im = reader.readDataFromFile(reader.fobj,reader.header)
	return im

def readHeaderFromFile(imfile):
	reader = TiaRaw(imfile)
	return reader.parseHeader()

if __name__ == '__main__':
	a = read('n0.bin')
	print a.max(), a.min()
	print readHeaderFromFile('n0.bin')
