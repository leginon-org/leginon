#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import ccdcamera
import numarray
import re
import sys
import ucsfCamera

class UCSFGatan(ccdcamera.CCDCamera):

	name = 'UCSF Gatan'

	def __init__(self):
		ccdcamera.CCDCamera.__init__(self)
		self.camera = ucsfCamera.GatanCCD()
		self.cameratypes = ('CCD', 'GIF')
		self.cameratype = self.cameratypes[0]
		self.camera.bIsGif = False
		self.fExposure = 0.5

		try:
			self.loadConfigFile()
		except IOError:
			pass

		self.mReadCamera()
		self.exposuretype = 'normal'

	def loadConfigFile(self, filename='C:\\UCSF\\Tomo\\ConfigTomo.dat'):
		options = parseConfigTomo(filename)
		camerasize = {}
		for axis in ['x', 'y']:
			key = 'CCDReadout' + axis.upper()
			if key in options and isinstance(options[key], int):
				camerasize[axis] = options[key]
		if 'x' in camerasize and 'y' in camerasize:
			self.camerasize = camerasize

		self.pixelsizes = {}
		for camera in ('CCD', 'GIF'):
			try:
				mag = options[camera + 'PixelMag']
				pixelsize = options[camera + 'PixelSize']
				self.pixelsizes[camera] = float(mag)*float(pixelsize)*1e-10
			except KeyError:
				pass

	def getCameraType(self):
		return self.cameratype

	def setCameraType(self, cameratype):
		if cameratype not in self.cameratypes:
			raise ValueError('invalid camera \'%s\'' % cameratype)
		self.cameratype = cameratype
		if cameratype == self.cameratypes[0]: self.camera.bIsGif = False
		else: self.camera.bIsGif = True

	def getOffset(self):
		return dict(self.offset)

	def setOffset(self, value):
		self.offset = dict(value)
		self.camera.setReadout(self.offset['x'], self.dimension['x'],
			self.offset['y'], self.dimension['y'])

	def getDimension(self):
		return dict(self.dimension)

	def setDimension(self, value):
		self.dimension = dict(value)
		self.camera.setReadout(self.offset['x'], self.dimension['x'],
			self.offset['y'], self.dimension['y'])

	def getBinning(self):
		return dict(self.binning)

	def setBinning(self, value):
		self.binning = dict(value)
		self.camera.setBinning(self.binning['x'], self.binning['y'])

	def getExposureTime(self):
		fExposure = self.camera.getExposure()
		return int(fExposure*1000)

	def setExposureTime(self, value):
		self.fExposure = float(value)/1000.0
		print 'ucsfGatan: exposure time (s) = ', self.fExposure
		if self.fExposure > 5: self.fExposure = 5
		self.camera.setExposure(self.fExposure)

	def getExposureTypes(self):
		return ['normal', 'dark']

	def getExposureType(self):
		return self.exposuretype

	def setExposureType(self, value):
		if value not in ['normal', 'dark']:
			raise ValueError('invalid exposure type')
		self.exposuretype = value

	def getImage(self):
		self.mWriteCamera()
		if self.getExposureType() == 'dark': 
			pImage = self.camera.acquireDarkImage()
			return pImage
		else:
			if self.fExposure > 10:
				self.setExposureTime(0.5)
				raise "ucsfgatan: exposure time > 10 s!"
			pImage = self.camera.acquireRawImage()
			return pImage

	def getCameraSize(self):
		if hasattr(self, 'camerasize'):
			return self.camerasize
		else:
			raise NotImplementedError

	def getPixelSize(self):
		try:
			pixelsize = self.pixelsizes[self.cameratype]
		except KeyError:
			raise ValueError('no pixel size for camera type')
		return {'x': pixelsize, 'y': pixelsize}

	def getSlitWidth(self):
		if self.camera.bIsGif: return self.camera.getSlitWidth()
		else: return None

	def setSlitWidth(self, width):
		if self.camera.bIsGif: self.camera.setSlitWidth(width)

	def mReadCamera(self):
		pBinning = self.camera.getBinning()
		pReadout = self.camera.getReadout()
		self.binning = {'x': pBinning[0], 'y': pBinning[1]}
		self.offset = {'x': pReadout[0], 'y': pReadout[2]}
		self.dimension = {'x': pReadout[1], 'y': pReadout[3]}

	def mWriteCamera(self):
		self.camera.setBinning(self.binning['x'], self.binning['y'])
		self.camera.setReadout(self.offset['x'], self.dimension['x'],
			self.offset['y'], self.dimension['y'])


def parseConfigTomo(filename):
	fp = open(filename)

	commentre = re.compile('(?P<line>.*)#')
	valuere = re.compile(
		r'(?P<name>[^:=\s][^:=]*)'
		r'\s*([:=])\s*'
		r'(?P<value>.*)$'
	)

	options = {}
	while True:
		line = fp.readline()
		if not line: break
		mo = commentre.match(line)
		if mo: line = mo.group('line')
		mo = valuere.match(line)
		if mo:
			name, value = mo.group('name', 'value')
			name = name.strip()
			value = value.strip()
			for i in [int, float, strToBool]:
				try:
					value = i(value)
				except ValueError:
					pass
				else:
					break
			options[name] = value
	fp.close()
	return options

def strToBool(s):
	if s.lower() == 'true': return True
	elif s.lower() == 'false': return False
	else: raise ValueError

