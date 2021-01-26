#!/usr/bin/env python
import numpy
import glob
import sys
import os
import datetime
from functools import reduce

class Tvips(object):
	'''
	This reader is based on Tvips format
	data_types: 8 or 16 bit integer ? defined in series header
	'''
	data_types = {8: numpy.int8, 16:numpy.int16}
	series_header_bytes = 256
	def __init__(self,folderpath):
		if not os.path.isdir(folderpath):
			raise ValueError('Folder %s does not exists' % (folderpath,))
		pattern = os.path.join(folderpath,'*')
		files = glob.glob(pattern)
		files.sort()
		self.imagesets = files
		for imagesetpath in files:
			self.filebytes = os.path.getsize(imagesetpath)
			if '_000.tvips' in imagesetpath:
				#first image has series header
				self.fobj = open(imagesetpath)
				self.defineHeader()
				self.header = self.parseHeader()
				self.fobj.close()
				# set z length in the image
				self.header['mzs'] = [(self.filebytes - self.series_header_bytes) // self.image_bytes,]
			else:
				#When Image_000 is too large, it makes additional ones.
				# append z length in the image
				self.header['mzs'].append(self.filebytes // self.image_bytes)
			# add up length from each Image file.
			self.header['nz'] = sum(self.header['mzs'])

	def defineHeader(self):
		self.header_offset = 0 # in bytes
		self.img_header_offset = None # in bytes, defined after parsing series header.
		self.data_offset = 0 # in bytes
		self.header_keys = ['dtype','nx','ny','shape']

	def getDataType(self, type_value):
		'''
		Get data type based on header
		'''
		if type_value not in list(self.data_types.keys()):
			raise ValueError('Data type not decodable')
		self.data_type = self.data_types[type_value]
		return self.data_type

	def parseHeader(self):
		self.fobj.seek(self.header_offset, 0)
		headerdict = {}
		# data first 48 items are 32-bit integer
		int_values = numpy.fromfile(self.fobj, dtype=numpy.int32, count=48).tolist()
		headerdict['dtype'] = numpy.dtype(self.getDataType(int_values[4]))
		headerdict['pixel_bytes'] = int_values[4] // 8 
		headerdict['nx'] = int_values[2]
		headerdict['ny'] = int_values[3]
		headerdict['shape'] = (headerdict['ny'],headerdict['nx'])
		headerdict['img_header_bytes'] = int_values[12]
		# set image header bytes
		self.img_header_offset = headerdict['img_header_bytes']
		self.image_bytes = headerdict['nx']*headerdict['ny']*headerdict['pixel_bytes'] + headerdict['img_header_bytes']

		return headerdict

	def getZlength(self):
		return self.header['nz']

	def getImageHeaderStart(self, z):
		if z > self.header['nz']-1:
			raise ValueError('z value %d is beyond series length' % z)

		z_temp = int(z)
		i = 0
		while z_temp >= self.header['mzs'][i]:
			i += 1
			z_temp -= self.header['mzs']
		if i == 0:
			start = self.series_header_bytes + self.image_bytes*z_temp
		else:
			start = self.image_bytes*z_temp
		setpath = self.imagesets[i]
		fobj = open(setpath,'r')
		return fobj, start

	def parseImageHeader(self, z):
		'''
		Parse header for a specified image in the series. Bass=0
		'''
		fobj, start = self.getImageHeaderStart(z)
		fobj.seek(start, 0)
		int_values = numpy.fromfile(fobj, dtype=numpy.int32, count=3).tolist()
		fobj.close()
		headerdict = {}
		headerdict['counter'] = int_values[0]
		headerdict['datetime'] = datetime.datetime.fromtimestamp(int_values[1]+0.001*int_values[2])
		return headerdict
		
	def readData(self, z=0):
		'''
		Read data portion of RAW file from the file object fobj.
		Returns a new numpy ndarray object. similar to mrc.py
		'''
		if z >= self.header['nz']:
			raise ValueError('z slice selected is not accessible.')
		fobj, start = self.getImageHeaderStart(z)
		# shift to data
		start += self.img_header_offset
		shape = self.header['shape']
		datalen = reduce(numpy.multiply, shape)
		fobj.seek(start, 0)
		a = numpy.fromfile(fobj, dtype=self.header['dtype'], count=datalen)
		a = numpy.reshape(a,shape)
		fobj.close()
		return a

def read(imfolder, z=0):
	'''
	Read imagefile, then convert to a numpy array.
	'''
	reader = Tvips(imfolder)
	im = reader.readData(z)
	return im

def readHeaderFromFile(imfolder):
	reader = Tvips(imfolder)
	return reader.header

def readImageHeaderFromFile(imfolder, z=0):
	'''
	header for specific z value, base=0
	'''
	reader = Tvips(imfolder)
	return reader.parseImageHeader(z)

if __name__ == '__main__':
	filepath = input('Enter the path to the tvips imageset folder: ') 
	a = read(filepath, 0)
	print(('First image Max:',a.max(), 'Min:',a.min()))
	print('Series Header')
	print(readHeaderFromFile(filepath))
