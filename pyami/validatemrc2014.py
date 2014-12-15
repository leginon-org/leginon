#!/usr/bin/env python
import os
import numpy
from pyami import mrc
import sys

class MRC2014Check(object):
	def __init__(self,filepath):
		if not os.path.isfile(filepath):
			print "ERROR: file does not exist"
		self.file_bytes = os.path.getsize(filepath)
		self.header = mrc.readHeaderFromFile(filepath)
		self.valid_exttypes = ['CCP4','MRCO','SERI','AGAR','FEI1']
		self.is2D = True
		self.isCrystal = False
		self.errors = []
		self.updates = []
		self.infos = []

	def getNDimensions(self):
		return self.header['nx'],self.header['ny'],self.header['nz']

	def printError(self,message):
		self.errors.append(message)

	def printNeedUpdate(self,message):
		self.updates.append(message)

	def printInfo(self,message):
		self.infos.append(message)

	def printSuccess(self,message):
		print ("Success: "+message)

	def summary(self):
		print ''
		if self.errors:
			print "ERRORS that must be corrected-----------"
			for e in self.errors:
				print e
		if self.updates:
			print "UPDATES recommended--------------"
			for u in self.updates:
				print u
		if not self.errors:
			print ''
			print "Summary--------------"
			for i in self.infos:
				print i

	def checkEXTTYPE(self):
		word27 = self.header['exttype'].strip(chr(0))
		bytes_ext_header = self.getNSYMBYTE()
		if bytes_ext_header != 0:
			if word27 == '':
				self.printNeedUpdate('EXTTYPE (word 27) is required for non-zero NSYMBT value %d' % (bytes_ext_header))
			else:
				if word27 not in self.valid_exttypes:
					self.printError("EXTTYPE %s not valid" % (word27,))
		else:
			self.printSuccess('EXTTYPE is empty with no conflict')

	def getNSYMBYTE(self):
		return self.header['nsymbt']

	def getModeLength(self,mode):
		lengths = [1,2,4,2,4,2,2,4]
		if mode > len(lengths):
			self.printError("mode error: Mode %d not defined" % (mode,0))
		return lengths[mode]

	def checkFileSize(self):
		mode = self.header['mode']
		data_valuelength = self.getModeLength(mode)
		nx,ny,nz = self.getNDimensions()
		bytes_ext_header = self.getNSYMBYTE()
		self.data_offset = 1024 + bytes_ext_header
		expected_size = self.data_offset + nx * ny * nz * data_valuelength
		if expected_size != self.file_bytes:
			self.printError("File length %d not consistent with header expectation %d" % (self.file_bytes,expected_size))
		else:
			self.printSuccess("File size test")

	def checkISPG(self):
		'''
		check for valid ISPG
		'''
		# Must guess whether this is 2D image (stack) first
		ispg = self.header['ispg']
		if self.is2D:
			if ispg > 0:
				self.printNeedUpdate("Images should have ISPG=0")
				return
		else:
			if self.header['mz'] == 1:
				self.printError("3D volume should not have mz=1")
				return
			else:
				if self.header['nz'] // self.header['mz'] > 1:
					if not self.isCrystal and self.header['ispg'] < 401:
						self.printNeedUpdate("ISPG need to be at least 401 for a volume stack")
						return
				else:
					if ispg < 1 or ispg >= 401:
						self.printNeedUpdate("ISPG need to be between 1 and 400 for a single volume\n Most likely 1")
						return
		self.printSuccess("ISPG value is %d" % ispg)

	def checkMZ(self):
		nz = self.header['nz']
		mz = self.header['mz']
		if mz <= 0:
			self.printError("mz %d is invalid" % mz)
			return
		else:
			if not self.isCrystal and self.header['nz'] % self.header['mz'] != 0:
				self.printError("Volume stack nz must be multiple of mz")
				return

	def setIs2D(self):
		'''
		Guess whether the file is a single/collection of 2D images.
		'''
		nz = self.header['nz']
		mz = self.header['mz']
		if nz == 1:
			print ('Check as single image....')
			return
		else:
			if nz == mz:
				if self.header['ispg'] == 0:
					# backward compatible
					self.is2D = True
					print ('Check as image stack....')
				else:
					self.is2D = False
					print ('Check as single 3D volume....')
			elif mz == 1:
				self.is2D = True
				print ('Check as image stack....')
			else:
				self.is2D = False
				if self.header['ispg'] < 400:
					self.isCrystal = True
					print ('Check as crystallographic map....')
				else:
					print ('Check as 3D volume stack....')

	def getEndianess(self):
		try:
			self.printInfo('Endianess: %s' % mrc.intbyteorder[self.header['byteorder']])
		except:
			self.printError('Machine stamp not defined properly')

	def getDataType(self):
		try:
			self.printInfo('Data type: %s' % (mrc.mrc2numpy[self.header['mode']](1).dtype.name))
		except:
			if self.header['mode'] == 3:
				self.printInfo('Data type: %s' % 'complex16')
			else:
				self.printError('Unknown data type')

	def getMapType(self):
		try:
			self.printInfo('Map type: %s' % mrc.mrcmaptype[self.header['mode']])
		except:
			self.printInfo('Failed map type mapping from mode %d' % self.header['mode'])

	def getAxisOrder(self):
		axis_map = {1:'X',2:'Y',3:'Z'}
		axis_labels = map((lambda x:axis_map[self.header[x]]),('mapc','mapr','maps'))
		axis_order_string = 'Axis Order: Fast-%s, Medium-%s, Slow-%s' % tuple(axis_labels)
		self.printInfo(axis_order_string)

	def getDimension(self):
		if self.header['mz']:
			if not self.is2D:
				slices_label = '(Z)Slices x '
				slices_string = ' x %d' % (self.header['mz'])
			else:
				slices_label = ''
				slices_string = ''
		if not self.isCrystal:
			dimension_string = 'Dimensions: %d%s x %d x %d ((N)Objects at %s(Y)Rows x (X)Columns)' % (self.header['nz']/self.header['mz'],slices_string,self.header['my'],self.header['mx'],slices_label) 
		else:
			dimension_string = 'Unit Cell Samples: %d x %d x %d (Z x Y x X)' % (self.header['mz'],self.header['my'],self.header['mx']) 
		self.printInfo(dimension_string)

	def getPixelSize(self):
		if self.header['mx']>0 and self.header['my']>0 and self.header['mz']>0:
			self.printInfo('Sampling rate:')
			self.printInfo('   X (Angstrom/pixel)= %.3e' % (self.header['xlen']/self.header['mx']))
			self.printInfo('   Y (Angstrom/pixel)= %.3e' % (self.header['ylen']/self.header['my']))
			if not self.is2D:
				self.printInfo('   Z (Angstrom/pixel)= %.3e' % (self.header['zlen']/self.header['mz']))
		else:
			self.printError('MX,MY,MZ must be larger than 0. Currently MX=%d, MY=%d, MZ=%d ' % (self.header['mx'],self.header['my'],self.header['mz']))

	def getInfos(self):
		self.getEndianess()
		self.getDataType()
		self.getMapType()
		self.getDimension()
		self.getAxisOrder()
		self.getPixelSize()

	def printHeader(self):
		print "-----------------------------------------------"
		print "Basic file header (first 1024 bytes)"
		print "-----------------------------------------------"
		mrc.printHeader(self.header)
		print "-----------------------------------------------"

	def checkFormatChange(self):
		self.printHeader()
		self.checkFileSize()
		self.checkEXTTYPE()
		self.setIs2D()
		self.checkISPG()
		self.checkMZ()
		self.getInfos()
		self.summary()

if __name__ == "__main__":
	if len(sys.argv) != 2:
		print "Usage: validatemrc2014.py filepath"
	filepath = sys.argv[1]
	m = MRC2014Check(filepath)
	m.printHeader()
	m.checkFileSize()
	m.checkEXTTYPE()
	m.setIs2D()
	m.checkISPG()
	m.checkMZ()
	m.getInfos()
	m.summary()
