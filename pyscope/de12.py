import socket
import sys
import DEServer_pb2
import struct
import types
import numpy
import time
import pyami.imagefun

class DirectElectronServer:	
	debugPrint = False
	connected = False
	host = "localhost" #change to specific IP address if necessary	
	readport, writeport = 48879, 48880	
	active_camera_name = ""
	available_cameras = []	

	#command lists
	kEnumerateCameras = 0
	kEnumerateProperties = 1
	kGetAllowableValues = 2
	kGetProperty =3
	kSetProperty = 4
	k_GetImage = 5

	def __del__(self):
		if self.connected:
			self.disconnect()
	
	def connect(self):		
		self.readsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Create a socket (SOCK_STREAM means a TCP socket)
		self.readsock.connect((self.host, self.readport)) # Connect to server for sending data
		self.writesock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Create a socket (SOCK_STREAM means a TCP socket)
		self.writesock.connect((self.host, self.writeport)) # Connect to server for reading data
		self.connected = True		
		
	def disconnect(self):
		if self.connected:
			self.readsock.close()
			self.writesock.close()

	def getAvailableCameras(self):
		available_cameras = self.getStrings(self.kEnumerateCameras)
		if(available_cameras != False):
			self.available_cameras = available_cameras		
		return self.available_cameras
		
	def setActiveCamera(self, camera_name = None):
		if camera_name is None:			
			return False
		self.active_camera_name = camera_name
		return True
	
	def getActiveCameraProperties(self):
		available_properties = self.getStrings(self.kEnumerateProperties)
		if(available_properties != False):
			self.available_properties = available_properties	
		return self.available_properties
	
	def getProperty(self, label = None):
		if label is None:			
			return False
		command = self.addSingleCommand(self.kGetProperty, label)
		response = self.sendcommand(command)		
		if response != False:
			values = self.getParameters(response.acknowledge[0])
			return values[0] #always return the first value
		else:
			return False

	def setProperty(self, label = None, value = None):
		if label is None:			
			return False
		if value is None:			
			return False		
		command = self.addSingleCommand(self.kSetProperty, label, value)		
		response = self.sendcommand(command)		
		if response != False:
			return self.getParameters(response.acknowledge[0])
		else:
			return False
	
	def GetImage(self):
		width = self.getProperty("Image Size X")
		if(width==False):
			return False
		width = float(width)
		height = self.getProperty("Image Size Y")
		if(height==False):
			return False
		height = float(height)
		exposure_time = self.getProperty("Exposure Time")
		if(exposure_time==False):
			exposure_time = 1.0;
		exposure_time = float(exposure_time)
		'''
		binning_x = self.getProperty("Binning X")
		if(binning_x==False):
			return False
		binning_x = float(binning_x)
		binning_y = self.getProperty("Binning Y")
		if(binning_y==False):
			return False		
		binning_y = float(binning_y)
		'''
		binning_x = binning_y = 1
		real_shape = [height/binning_y, width/binning_x]		
		command = self.addSingleCommand(self.k_GetImage)
		response = self.sendcommand(command)		
		if(response == False):
			return False #expect no error
		
		#get the data header		
		self.writesock.settimeout(None)
		recvbyteSizeString = self.writesock.recv(4) # get the first 4 bytes
		recvbyteSize = struct.unpack('L',recvbyteSizeString) # interpret as size
		received_string = self.writesock.recv(recvbyteSize[0]) # get the rest
		self.writesock.settimeout(0.5) #change to default
		data_header = DEServer_pb2.DEPacket()
		data_header.ParseFromString(received_string)
		bytesize = data_header.data_header.bytesize		
		if(bytesize<=0):
			return False #expect a byte count		
		t1 = time.clock()
		data = self.getCountBytesOfDataFromSocket(self.writesock, bytesize)
		t2 = time.clock()
		if (self.debugPrint): print "Image transfer time: ", t2 - t1, "second"		
		if (self.debugPrint): print "Effective throughput: ", bytesize/(t2-t1)/1024/1024, "MB/sec"
		if len(data) == bytesize:
			image = numpy.fromstring(data, numpy.uint16)						
			if (bytesize == height/binning_y * width/binning_x * 2):				
				image.shape = real_shape
				return image
		return False;
	
	def getCountBytesOfDataFromSocket(self, sck, count):
		from cStringIO import StringIO #use string io to speed up, refer to http://www.skymind.com/~ocrow/python_string/
		sck.settimeout(None)  # Don't timeout
		line = sck.recv(count)		
		if len(line) < count:
			file_str = StringIO()
			file_str.write(line)
			sck.settimeout(.5)
			total_len = len(line)
			while total_len < count:
				line = ''
				try:
					line = sck.recv(1024)
				except socket.timeout:
					break
				if line == '':
					break
				file_str.write(line)				
				total_len = total_len + len(line)
			return file_str.getvalue()
		else :
			return line
	
	def getParameters(self, single_acknowledge = None):
		output = []
		if single_acknowledge is None:			
			return output
		if single_acknowledge.error == True:
			return output
		for one_parameter in single_acknowledge.parameter:
			if(one_parameter.type == DEServer_pb2.AnyParameter.P_STRING):
				output.append(one_parameter.p_string)
			if(one_parameter.type == DEServer_pb2.AnyParameter.P_INT):
				output.append(one_parameter.p_int)
			if(one_parameter.type == DEServer_pb2.AnyParameter.P_FLOAT):
				output.append(one_parameter.p_float)
		return output
				
	#get strings from a single command response
	def getStrings(self, command_id = None):
		if command_id is None:			
			return False
		command = self.addSingleCommand(command_id)
		response = self.sendcommand(command)
		if response != False:			
			return self.getParameters(response.acknowledge[0])			
		else:
			return False			
			
	#add a new command (with optional label and parameter)
	def addSingleCommand(self, command_id = None, label = None, param = None):
		if command_id is None:
			return False		
		command = DEServer_pb2.DEPacket()       # create the command packet
		command.type = DEServer_pb2.DEPacket.P_COMMAND; 
		singlecommand1 = command.command.add() # add the first single command
		singlecommand1.command_id = command_id
		
		if not label is None:
			str_param = command.command[0].parameter.add()
			str_param.type = DEServer_pb2.AnyParameter.P_STRING
			str_param.p_string = label
			str_param.name = "label"
		if not param is None:			
			if type(param) is types.IntType:
				int_param = command.command[0].parameter.add()
				int_param.type = DEServer_pb2.AnyParameter.P_INT
				int_param.p_int = param
				int_param.name = "val"			
			else:			
				if (type(param) is types.StringType) or (type(param) is types.UnicodeType):
					str_param = command.command[0].parameter.add()
					str_param.type = DEServer_pb2.AnyParameter.P_STRING
					str_param.p_string = param			
					str_param.name = "val"
				else:				
					if type(param) is types.FloatType:
						float_param = command.command[0].parameter.add()
						float_param.type = DEServer_pb2.AnyParameter.P_FLOAT
						float_param.p_float = param
						float_param.name = "val"		
		return command
	
	#send single command and get a response, if error occurred, return False
	def sendcommand(self, command = None):
		if command is None:			
			return False
		if(len(command.camera_name)==0):
			command.camera_name = self.active_camera_name # append the active camera name if necessary
		if (self.debugPrint): print command.__str__()
		data = struct.pack('L',command.ByteSize())+command.SerializeToString()		
		self.readsock.send(data)
		
		self.writesock.settimeout(None);
		recvbyteSizeString = self.writesock.recv(4) # get the first 4 bytes
		recvbyteSize = struct.unpack('L',recvbyteSizeString) # interpret as size
		received_string = self.writesock.recv(recvbyteSize[0]) # get the rest		
		self.writesock.settimeout(0.5);
		Acknowledge_return = DEServer_pb2.DEPacket()
		Acknowledge_return.ParseFromString(received_string)		
		if (self.debugPrint): print Acknowledge_return.__str__()
		if (Acknowledge_return.type != DEServer_pb2.DEPacket.P_ACKNOWLEDGE):
			return False #has to be an acknowledge packet
		if (len(command.command) != len(Acknowledge_return.acknowledge)):
			return False #has to be an acknowledge packet
		error = False;
		for one_ack in Acknowledge_return.acknowledge:
			error = error or one_ack.error
		#if (error):
		#	return False #error occurred
		return Acknowledge_return

import ccdcamera
class DE12(ccdcamera.CCDCamera):
	name = 'DE12'
	def __init__(self):
		ccdcamera.CCDCamera.__init__(self)
		self.camera_name = 'DE12'
		self.server = DirectElectronServer()
		self.connect()
		self.offset = {'x': 0, 'y': 0}
		self.dimension = {'x': 4096, 'y': 3072}
		self.binning = {'x': 1, 'y': 1}

	def __del__(self):
		self.disconnect()

	def connect(self):
		self.server.connect()
		self.server.setActiveCamera(self.camera_name)

	def disconnect(self):
		self.server.disconnect()

	def getCameraSize(self):
		return self.getDictProp('Image Size')

	def getCameras(self):
		#self.connect()
		return self.server.getAvailableCameras()
		#self.disconnect()

	def print_props(self):
		#self.connect()
		camera_properties = self.server.getActiveCameraProperties()
		for one_property in camera_properties:
			print one_property, self.server.getProperty(one_property)
		#self.disconnect()

	def getProperty(self, name):
		#self.connect()
		value = self.server.getProperty(name)
		return value

	def setProperty(self, name, value):
		#self.connect()
		value = self.server.setProperty(name, value)
		return value

	def getExposureTime(self):
		seconds = self.getProperty('Exposure Time')
		ms = int(seconds * 1000.0)
		return ms

	def setExposureTime(self, ms):
		seconds = ms / 1000.0
		self.setProperty('Exposure Time', seconds)

	def getDictProp(self, name):
		#self.connect()
		x = int(self.server.getProperty(name + ' X'))
		y = int(self.server.getProperty(name + ' Y'))
		return {'x': x, 'y': y}

	def setDictProp(self, name, xydict):		
		self.server.setProperty(name + ' X', int(xydict['x']))
		self.server.setProperty(name + ' Y', int(xydict['y']))		

	def getDimension(self):
		return self.dimension

	def setDimension(self, dimdict):
		self.dimension = dimdict
	
	def getBinning(self):
		return self.binning

	def setBinning(self, bindict):
		self.binning = bindict

	def getOffset(self):
		return self.offset

	def setOffset(self, offdict):
		self.offset = offdict

	def _getImage(self):
		image = self.server.GetImage()
		if not isinstance(image, numpy.ndarray):
			raise ValueError('DE12 GetImage did not return array')
		image = self.finalizeGeometry(image)
		return image

	def finalizeGeometry(self, image):
		row_start = self.offset['y']
		col_start = self.offset['x']
		nobin_rows = self.dimension['y'] * self.binning['y']
		nobin_cols = self.dimension['x'] * self.binning['x']
		row_end = row_start + nobin_rows
		col_end = col_start + nobin_cols
		nobin_image = image[row_start:row_end, col_start:col_end]
		assert self.binning['x'] == self.binning['y']
		binning = self.binning['x']
		bin_image = pyami.imagefun.bin(nobin_image, binning)
		bin_image = numpy.fliplr(bin_image)
		return bin_image

	def getPixelSize(self):
		psize = 6e-6
		return {'x': psize, 'y': psize}

	def getRetractable(self):
		return True
		
	def setInserted(self, value):
		if value:
			de12value = 'Extended'
		else:
			de12value = 'Retracted'
		self.setProperty("Camera Position", de12value)
		
	def getInserted(self):
		de12value = self.getProperty('Camera Position')
		return de12value == 'Extended'

	def getExposureTypes(self):
		return ['normal','dark']

	def getExposureType(self):
		exposure_type = self.getProperty('Exposure Mode')		
		return exposure_type.lower()
		
	def setExposureType(self, value):
		self.setProperty('Exposure Mode', value.capitalize())

	def getNumberOfFrames(self):
		return self.getProperty('Total Number of Frames')
