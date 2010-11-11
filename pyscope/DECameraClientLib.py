import socket
import sys
import DECameraClientLib_pb
import struct
import types
import numpy
import time

class DECameraClientLib:	
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
		if (self.debugPrint): print "Connected to server: ", self.host, " read port: ", self.readport, ", write port:", self.writeport
		
	def disconnect(self):
		if self.connected:
			self.readsock.close()
			self.writesock.close()
			self.connected = False
			if (self.debugPrint): print "Disconnected from server: ", self.host, " read port: ", self.readport, ", write port:", self.writeport

	def getAvailableCameras(self):
		available_cameras = self.getStrings(self.kEnumerateCameras)
		if(available_cameras != False):
			self.available_cameras = available_cameras		
		if (self.debugPrint): print "Available cameras: ", available_cameras
		return self.available_cameras
		
	def setActiveCamera(self, camera_name = None):
		if camera_name is None:			
			return False
		self.active_camera_name = camera_name
		if (self.debugPrint): print "Active camera: ", camera_name
		return True
	
	def getActiveCameraProperties(self):
		available_properties = self.getStrings(self.kEnumerateProperties)
		if(available_properties != False):
			self.available_properties = available_properties	
		if (self.debugPrint): print "Available camera properties: ", available_properties
		return self.available_properties
	
	def getProperty(self, label = None):
		if label is None:			
			return False
		command = self.addSingleCommand(self.kGetProperty, label)
		if (self.debugPrint): print "getProperty for: ", label
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
		if (self.debugPrint): print "setProperty for: ", label, ", new value: ", value
		response = self.sendcommand(command)				
		if response != False:
			return self.getParameters(response.acknowledge[0])
		else:
			return False
	
	def GetImage(self):
		width = self.getProperty("Image Size X")
		assert width
		width = float(width)
		height = self.getProperty("Image Size Y")
		assert height
		height = float(height)
		'''
		binning_x = self.getProperty("Binning X")
		assert binning_x
		binning_x = float(binning_x)
		binning_y = self.getProperty("Binning Y")
		assert binning_y
		binning_y = float(binning_y)
		'''
		binning_x = binning_y = 1 #hard code for now
		real_shape = [height/binning_y, width/binning_x]		
		command = self.addSingleCommand(self.k_GetImage)
		response = self.sendcommand(command)
		assert response
		
		#get the data header		
		recvbyteSizeString = self.getCountBytesOfDataFromSocket(self.writesock, 4) # get the first 4 bytes		
		assert len(recvbyteSizeString) == 4
		recvbyteSize = struct.unpack('L',recvbyteSizeString) # interpret as size
		received_string = self.getCountBytesOfDataFromSocket(self.writesock, recvbyteSize[0]) # get the rest
		data_header = DECameraClientLib_pb.DEPacket()
		data_header.ParseFromString(received_string)
		bytesize = data_header.data_header.bytesize		
		assert bytesize > 0		
		t1 = time.clock()
		data = self.getCountBytesOfDataFromSocket(self.writesock, bytesize)
		t2 = time.clock()
		if (self.debugPrint): print "Image transfer time: ", t2 - t1, "second"		
		if (self.debugPrint): print "Effective throughput: ", bytesize/(t2-t1)/1024/1024, "MB/sec"
		assert len(data) == bytesize
		image = numpy.fromstring(data, numpy.uint16)						
		assert bytesize == height/binning_y * width/binning_x * 2
		image.shape = real_shape
		return image
	
	def getCountBytesOfDataFromSocket(self, sck, count):
		from cStringIO import StringIO #use string io to speed up, refer to http://www.skymind.com/~ocrow/python_string/
		orig_timeout = sck.gettimeout()
		sck.settimeout(None)
		line = sck.recv(count)		
		if len(line) < count:
			file_str = StringIO()
			file_str.write(line)
			sck.settimeout(None)
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
			line = file_str.getvalue()
		sck.settimeout(orig_timeout)
		return line
	
	#get multiple parameters from a single acknowledge packet
	def getParameters(self, single_acknowledge = None):
		output = []
		if single_acknowledge is None:			
			return output
		if single_acknowledge.error == True:
			return output
		for one_parameter in single_acknowledge.parameter:
			if(one_parameter.type == DECameraClientLib_pb.AnyParameter.P_STRING):
				output.append(one_parameter.p_string)
			if(one_parameter.type == DECameraClientLib_pb.AnyParameter.P_INT):
				output.append(one_parameter.p_int)
			if(one_parameter.type == DECameraClientLib_pb.AnyParameter.P_FLOAT):
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
		command = DECameraClientLib_pb.DEPacket()       # create the command packet
		command.type = DECameraClientLib_pb.DEPacket.P_COMMAND; 
		singlecommand1 = command.command.add() # add the first single command
		singlecommand1.command_id = command_id
		
		if not label is None:
			str_param = command.command[0].parameter.add()
			str_param.type = DECameraClientLib_pb.AnyParameter.P_STRING
			str_param.p_string = label
			str_param.name = "label"
		if not param is None:			
			if type(param) is types.IntType:
				int_param = command.command[0].parameter.add()
				int_param.type = DECameraClientLib_pb.AnyParameter.P_INT
				int_param.p_int = param
				int_param.name = "val"			
			else:			
				if (type(param) is types.StringType) or (type(param) is types.UnicodeType):
					str_param = command.command[0].parameter.add()
					str_param.type = DECameraClientLib_pb.AnyParameter.P_STRING
					str_param.p_string = param			
					str_param.name = "val"
				else:				
					if type(param) is types.FloatType:
						float_param = command.command[0].parameter.add()
						float_param.type = DECameraClientLib_pb.AnyParameter.P_FLOAT
						float_param.p_float = param
						float_param.name = "val"		
		return command
	
	#send single command and get a response, if error occurred, return False
	def sendcommand(self, command = None):
		if command is None:			
			return False
		if(len(command.camera_name)==0):
			command.camera_name = self.active_camera_name # append the active camera name if necessary		
		data = struct.pack('L',command.ByteSize())+command.SerializeToString()		
		self.readsock.sendall(data)		
		recvbyteSizeString = self.getCountBytesOfDataFromSocket(self.writesock, 4) # get the first 4 bytes
		assert len(recvbyteSizeString) == 4		
		recvbyteSize = struct.unpack('L',recvbyteSizeString) # interpret as size
		received_string = self.getCountBytesOfDataFromSocket(self.writesock, recvbyteSize[0]) # get the rest				
		Acknowledge_return = DECameraClientLib_pb.DEPacket()
		Acknowledge_return.ParseFromString(received_string)	
		if (Acknowledge_return.type != DECameraClientLib_pb.DEPacket.P_ACKNOWLEDGE):
			return False #has to be an acknowledge packet
		if (len(command.command) != len(Acknowledge_return.acknowledge)):
			return False #has to be an acknowledge packet
		error = False;
		for one_ack in Acknowledge_return.acknowledge:
			error = error or one_ack.error
		#if (error):
		#	return False #error occurred
		return Acknowledge_return
