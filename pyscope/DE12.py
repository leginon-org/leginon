import array
import ccdcamera
import copy
import numpy
import os
import signal
import socket
import struct
import sys
import time

class DE12(ccdcamera.CCDCamera):
	name = 'DE12'
	def __init__(self):
		self.debugPrint = True
		ccdcamera.CCDCamera.__init__(self)
		self.camera_size = {'x': 4096, 'y': 3072}
		self.binning_values = {'x': [1], 'y': []}
		self.pixel_size = {'x': 2.5e-5, 'y': 2.5e-5}

		self.exposure_types = ['normal', 'dark']
		self.exposure_types_indices = {'normal': 0, 'dark': 1}
		self.exposure_type = 'normal'
		self.exposure_type_index = self.exposure_types_indices[self.exposure_type]

		self.binning = {'x': 1, 'y': 1}
		self.offset = {'x': 0, 'y': 0}
		self.dimension = copy.copy(self.camera_size)
		self.exposure_time = 0.010

		self.exposure_modes = ['count', 'integrate']
		self.exposure_modes_indices = {'count': 0, 'integrate': 1}
		self.exposure_mode = 'count'
		self.exposure_mode_index = self.exposure_modes_indices[self.exposure_mode]

		# DE12 does not use these, here for Leginon
		self.energy_filter = False
		self.energy_filter_width = 0.0

		self.cmdTypes = {
		'getBinning': 0,
		'setBinning': 1,
		'getOffset': 2,
		'setOffset': 3,
		'getDimension': 4,
		'setDimension': 5,
		'getExposureTime': 6,
		'setExposureTime': 7,
		'getExposureTypes': 8,
		'getExposureType': 9,
		'setExposureType': 10,
		'getCameraSize': 11,
		'_getImage': 12,
		'getPixelSize': 13,
		'getExposureModes': 14,
		'getExposureMode': 15,
		'setExposureMode': 16
		}


		# Define connection parameters for talking to our server

		self.HOST = os.getenv("DE12SERVERIP")	# The DE12_Server host machine IP address
		if self.HOST is not None:
			#self.HOST = 'localhost'# We have met the DE12_Server host machine and he is us
			self.PORT_READ = 48879	# The read port as used by the server
			self.PORT_WRITE = 48880	# The write port as used by the server
			# Create the sockets
			try:
				self.sr = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			except socket.error, (value, message):
				raise ValueError(message)
			try:
				self.sw = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			except socket.error, (value, message):
				raise ValueError(message)
			# Connect when the object is created since Leginon does not have a
			# button to invoke the function
			self.connectToServer()

	def connectToServer(self):

		# Connect to the command socket
		try:
			self.sr.connect((self.HOST, self.PORT_READ))	
			time.sleep(5)
		except socket.error, (value, message):
				raise ValueError(message)
		# Connect to the data socket
		try:
			self.sw.connect((self.HOST, self.PORT_WRITE))
			time.sleep(5)
		except socket.error, (value, message):
				raise ValueError(message)

	def _functionId(self, nFramesUp):

		""" Create a string naming the function n frames up on the stack.
		"""
		co = sys._getframe(nFramesUp+1).f_code
		return "%d" % (self.cmdTypes[co.co_name])

	def sendIntCommand(self, cmd, value1, value2):

		# Send command to the server
		cmdpkt = struct.pack('LLL', cmd, value1, value2)
		self.sr.send(cmdpkt)

	def sendFloatCommand(self, cmd, value1, value2):

		# Send command to the server
		cmdpkt = struct.pack('Lff', cmd, value1, value2)
		self.sr.send(cmdpkt)

	def getCountBytesOfDataFromSocket(self, sck, count):

		data = ''
		sck.settimeout(None)  # Don't timeout
		data = sck.recv(count)   # Try to get count bytes

		if len(data) < count:
			sck.settimeout(.5)
			while len(data) < count:
				line = ''
				try:
					line = sck.recv(4096)
				except socket.timeout:
					break
				if line == '':
					break
				data += line

		return data

	def dummyCmdAndResponse(self, Id):

		cmd = int(Id)
		value1 = cmd
		value2 = cmd + 1
		self.sendIntCommand(cmd, value1, value2)
		# Get the command response
		data = self.getCountBytesOfDataFromSocket(self.sw, 12)
		if len(data) == 12:
			responsePkt = struct.unpack('LLL', data)
			if (self.debugPrint): print "responsePkt =", responsePkt

	def find_key(self, dic, val):
		"""Return the key of dictionary dic given the value"""
		return [k for k, v in dic.iteritems() if v == val][0]

	def getBinning(self):

		self.sendIntCommand(int(self._functionId(0)), 0, 0)  # Parameters not used
		# Get the command response
		data = self.getCountBytesOfDataFromSocket(self.sw, 8)
		if len(data) == 8:
			responsePkt = struct.unpack('LL', data)
			if (self.debugPrint): print "getBinning: responsePkt =", responsePkt
			self.binning['x'] = responsePkt[0]
			self.binning['y'] = responsePkt[1]
			return copy.copy(self.binning)
		else:
			raise ValueError('unable to obtain binning values')

	def setBinning(self, value):

		for axis in self.binning.keys():
			try:
				if value[axis] not in self.binning_values[axis]:
					raise ValueError('invalid binning')
			except KeyError:
				pass

		value1 = value['x']
		value2 = value['y']
		self.sendIntCommand(int(self._functionId(0)), value1, value2)

	def getOffset(self):

		self.sendIntCommand(int(self._functionId(0)), 0, 0)  # Parameters not used
		# Get the command response
		data = self.getCountBytesOfDataFromSocket(self.sw, 8)
		if len(data) == 8:
			responsePkt = struct.unpack('LL', data)
			if (self.debugPrint): print "getOffset: responsePkt =", responsePkt
			self.offset['x'] = responsePkt[0]
			self.offset['y'] = responsePkt[1]
			return copy.copy(self.offset)
		else:
			raise ValueError('unable to obtain offset values')

	def setOffset(self, value):

		for axis in self.offset.keys():
			try:
				if value[axis] < 0 or value[axis] >= self.camera_size[axis]:
					raise ValueError('invalid offset')
			except KeyError:
				pass

		value1 = value['x']
		value2 = value['y']
		self.sendIntCommand(int(self._functionId(0)), value1, value2)

	def getDimension(self):

		self.sendIntCommand(int(self._functionId(0)), 0, 0)  # Parameters not used
		# Get the command response
		data = self.getCountBytesOfDataFromSocket(self.sw, 8)
		if len(data) == 8:
			responsePkt = struct.unpack('LL', data)
			if (self.debugPrint): print "getDimension: responsePkt =", responsePkt
			self.dimension['x'] = responsePkt[0]
			self.dimension['y'] = responsePkt[1]
			return copy.copy(self.dimension)
		else:
			raise ValueError('unable to obtain dimension values')

	def setDimension(self, value):

		for axis in self.dimension.keys():
			try:
				if value[axis] < 1 or value[axis] > self.camera_size[axis]:
					raise ValueError('invalid dimension')
			except KeyError:
				pass

		value1 = value['x']
		value2 = value['y']
		self.sendIntCommand(int(self._functionId(0)), value1, value2)

	def getExposureTime(self):

		self.sendFloatCommand(int(self._functionId(0)), 0, 0)  # Parameters not used
		# Get the command response
		data = self.getCountBytesOfDataFromSocket(self.sw, 8)
		if len(data) == 8:
			responsePkt = struct.unpack('ff', data)
			if (self.debugPrint): print "getExposureTime: responsePkt =", responsePkt
			self.exposure_time = responsePkt[0]
			return int(round(self.exposure_time*1000, 0))
		else:
			raise ValueError('unable to obtain exposure time')

	def setExposureTime(self, value):

		if value < 0:
			raise ValueError('invalid exposure time')
		value1 = float(value)/1000.0
		self.sendFloatCommand(int(self._functionId(0)), value1, 0.0)

	def getExposureTypes(self):

		return self.exposure_types

	def getExposureType(self):

		self.sendIntCommand(int(self._functionId(0)), 0, 0)  # Parameters not used
		# Get the command response
		data = self.getCountBytesOfDataFromSocket(self.sw, 8)
		if len(data) == 8:
			responsePkt = struct.unpack('LL', data)
			if (self.debugPrint): print "getExposureType: responsePkt =", responsePkt
			self.exposure_type_index = responsePkt[0]
			self.exposure_type = self.find_key(self.exposure_types_indices, responsePkt[0])
			return self.exposure_type
		else:
			raise ValueError('unable to obtain exposure type')

	def setExposureType(self, value):

		if value not in self.exposure_types:
			raise ValueError('invalid exposure type')
		value1 = self.exposure_types_indices[value]
		self.sendIntCommand(int(self._functionId(0)), value1, 0)

	def getCameraSize(self):

		self.sendIntCommand(int(self._functionId(0)), 0, 0)  # Parameters not used
		# Get the command response
		data = self.getCountBytesOfDataFromSocket(self.sw, 8)
		if len(data) == 8:
			responsePkt = struct.unpack('LL', data)
			if (self.debugPrint): print "getCameraSize: responsePkt =", responsePkt
			self.camera_size['x'] = responsePkt[0]
			self.camera_size['y'] = responsePkt[1]
			return copy.copy(self.camera_size)
		else:
			raise ValueError('unable to obtain camera size values')

	def _getImage(self):

		if not self.validateGeometry():
			raise ValueError('invalid image geometry')

		for axis in ['x', 'y']:
			if self.dimension[axis] % self.binning[axis] != 0:
				raise ValueError('invalid dimension/binning combination')

		columns = self.dimension['x']
		rows = self.dimension['y']

		shape = (rows, columns)
		numberOfPixels = rows * columns
		byteCount = numberOfPixels * struct.calcsize('H')
		if (self.debugPrint): print 'shape =', shape
		if (self.debugPrint): print 'numberOfPixels =', numberOfPixels
		if (self.debugPrint): print 'byteCount =', byteCount

		# Send the command to get the image
		self.sendIntCommand(int(self._functionId(0)), 0, 0)  # Parameters not used
		# Readt the image data
		data = self.getCountBytesOfDataFromSocket(self.sw, byteCount)
		if (self.debugPrint): print 'len(data) =', len(data)
		# If we received a complete image
		if len(data) == byteCount:
			if (self.debugPrint): print 'Data received'
			# Create a format string to unpack the data
			formatString = '%dH' % (numberOfPixels)
			# Unpack the data into a tuple
			imageTuple = struct.unpack(formatString, data)
			if (self.debugPrint): print 'Data unpacked'
			# Create a numpy array from the tuple
			image = numpy.asarray(imageTuple, numpy.uint16)
			if (self.debugPrint): print 'numpy array created'
			# Reshape the array
			image.shape = shape
			if (self.debugPrint): print 'numpy array re-shaped'
			# Save the image in a temp file
			if (self.debugPrint): numpy.save('numpytemp', image)
			# Return the image in the correct shape
			return image
		else:
			raise ValueError('unable to retrieve image')

	def getPixelSize(self):

		self.sendFloatCommand(int(self._functionId(0)), 0, 0)  # Parameters not used
		# Get the command response
		data = self.getCountBytesOfDataFromSocket(self.sw, 8)
		if len(data) == 8:
			responsePkt = struct.unpack('ff', data)
			if (self.debugPrint): print "getPixelSize: responsePkt =", responsePkt
			self.pixel_size['x'] = round(responsePkt[0], 6)
			self.pixel_size['y'] = round(responsePkt[1], 6)
			return dict(self.pixel_size)
		else:
			raise ValueError('unable to obtain pixel size')

	def getExposureModes(self):

		return self.exposure_modes

	def getExposureMode(self):

		self.sendIntCommand(int(self._functionId(0)), 0, 0)  # Parameters not used
		# Get the command response
		data = self.getCountBytesOfDataFromSocket(self.sw, 8)
		if len(data) == 8:
			responsePkt = struct.unpack('LL', data)
			if (self.debugPrint): print "getExposureMode: responsePkt =", responsePkt
			self.exposure_mode_index = responsePkt[0]
			self.exposure_mode = self.find_key(self.exposure_modes_indices, responsePkt[0])
			return self.exposure_mode
		else:
			raise ValueError('unable to obtain exposure mode')

	def setExposureMode(self, value):

		if value not in self.exposure_modes:
			raise ValueError('invalid exposure mode')
		value1 = self.exposure_modes_indices[value]
		self.sendIntCommand(int(self._functionId(0)), value1, 0)

