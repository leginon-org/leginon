#!/usr/bin/env python
'''
This defines a client class to interface with the socket based DM plugin.
'''

import os
import socket
import numpy
import time

## set this to a file name to log some socket debug messages.
## Set to None to avoid saving a log.
## for example:
debug_log = None
#debug_log = 'gatansocket.log'

# enum function codes as in GatanSocket.cpp and SocketPathway.cpp
# need to match exactly both in number and order
enum_gs = [
	'GS_ExecuteScript',
	'GS_SetDebugMode',
	'GS_SetDMVersion',
	'GS_SetCurrentCamera',
	'GS_QueueScript',
	'GS_GetAcquiredImage',
	'GS_GetDarkReference',
	'GS_GetGainReference',
	'GS_SelectCamera',
	'GS_SetReadMode',
	'GS_GetNumberOfCameras',
	'GS_IsCameraInserted',
	'GS_InsertCamera',
	'GS_GetDMVersion',
	'GS_GetDMCapabilities',
	'GS_SetShutterNormallyClosed',
	'GS_SetNoDMSettling',
	'GS_GetDSProperties',
	'GS_AcquireDSImage',
	'GS_ReturnDSChannel',
	'GS_StopDSAcquisition',
	'GS_CheckReferenceTime',
	'GS_SetK2Parameters',
	'GS_ChunkHandshake',
	'GS_SetupFileSaving',
	'GS_GetFileSaveResult',
	'GS_SetupFileSaving2',
	'GS_GetDefectList',
	'GS_SetK2Parameters2',
	'GS_StopContinuousCamera',
	'GS_GetPluginVersion',
	'GS_GetLastError',
	'GS_FreeK2GainReference',
]
# lookup table of function name to function code, starting with 1
enum_gs = dict([(x,y) for (y,x) in enumerate(enum_gs,1)])

## C "long" -> numpy "int_"
ARGS_BUFFER_SIZE = 1024
MAX_LONG_ARGS = 16
MAX_DBL_ARGS = 8
MAX_BOOL_ARGS = 8
sArgsBuffer = numpy.zeros(ARGS_BUFFER_SIZE, dtype=numpy.byte)

class Message(object):
	'''
Information packet to send and receive on the socket.
Initialize with the sequences of args (longs, bools, doubles)
and optional long array.
	'''
#Strings are packaged as long array using numpy.frombuffer(buffer,numpy.int_)
# and can be converted back with longarray.tostring()
	def __init__(self, longargs=[], boolargs=[], dblargs=[], longarray=[]):
		# add final longarg with size of the longarray
		if len(longarray):
			longargs = list(longargs)
			longargs.append(len(longarray))

		self.dtype = [
			('size', numpy.intc, 1),
			('longargs', numpy.int_, (len(longargs),)),
			('boolargs', numpy.int32, (len(boolargs),)),
			('dblargs', numpy.double, (len(dblargs),)),
			('longarray', numpy.int_, (len(longarray),)),
		]
		size_init = [0]
		self.array = numpy.zeros((), dtype=self.dtype)
		self.array['size'] = len(self.array.data)
		self.array['longargs'] = longargs
		self.array['boolargs'] = boolargs
		self.array['dblargs'] = dblargs
		self.array['longarray'] = longarray

		# create numpy arrays for the args and array
		'''
		self.longargs = numpy.asarray(longargs, dtype=numpy.int_)
		self.dblargs = numpy.asarray(dblargs, dtype=numpy.double)
		self.boolargs = numpy.asarray(boolargs, dtype=numpy.int32)
		self.longarray = numpy.asarray(longarray, dtype=numpy.int_)
		'''

	def pack(self):
		'''
		Serialize the data
		'''
		if len(self.array.data) > ARGS_BUFFER_SIZE:
			raise RuntimeError('Message packet size %d is larger than maximum %d' % (len(packed), ARGS_BUFFER_SIZE))
		return self.array.data

	def unpack(self, buf):
		'''
		unpack buffer into our data structure
		'''
		self.array = numpy.frombuffer(buf, dtype=self.dtype)[0]

def log(message):
	global debug_log
	if debug_log is None:
		return
	f = open(debug_log, 'a')
	line = '%f\t%s\n' % (time.time(), message)
	f.write(line)
	f.close()

## decorator for socket send and recv calls, so they can make log
def logwrap(func):
	def newfunc(*args, **kwargs):
		log('%s\t%s\t%s' % (func,args,kwargs))
		try:
			result = func(*args, **kwargs)
		except Exception, exc:
			log('EXCEPTION: %s' % (exc,))
			raise
		return result
	return newfunc

class GatanSocket(object):
	def __init__(self, host='', port=None):
		self.host = host
		if port is not None:
			self.port = port
		elif 'SERIALEMCCD_PORT' in os.environ:
			self.port = os.environ['SERIALEMCCD_PORT']
		else:
			raise ValueError('need to specify a port to GatanSocket instance, or set environment variable SERIALEMCCD_PORT')
		self.save_frames = False
		self.connect()

		self.script_functions = [ 
			('AFGetSlitState', 'GetEnergyFilter'),
			('AFSetSlitState', 'SetEnergyFilter'),
			('AFGetSlitWidth', 'GetEnergyFilterWidth'),
			('AFSetSlitWidth', 'SetEnergyFilterWidth'),
			('AFDoAlignZeroLoss', 'AlignEnergyFilterZeroLossPeak'),
			('IFCGetSlitState', 'GetEnergyFilter'),
			('IFCSetSlitState', 'SetEnergyFilter'),
			('IFCGetSlitWidth', 'GetEnergyFilterWidth'),
			('IFCSetSlitWidth', 'SetEnergyFilterWidth'),
			('IFCDoAlignZeroLoss', 'AlignEnergyFilterZeroLossPeak'),
			('IFGetSlitIn', 'GetEnergyFilter'),
			('IFSetSlitIn', 'SetEnergyFilter'),
			('IFGetSlitWidth', 'GetEnergyFilterWidth'),
			('IFSetSlitWidth', 'SetEnergyFilterWidth'),
			('GT_CenterZLP', 'AlignEnergyFilterZeroLossPeak'),
		]
		self.filter_functions = {}
		for name, method_name in self.script_functions:
			if self.hasScriptFunction(name):
				self.filter_functions[method_name] = name
		if 'SetEnergyFilter' in self.filter_functions.keys() and self.filter_functions['SetEnergyFilter'] == 'IFSetSlitIn':
			self.wait_for_filter = 'IFWaitForFilter();'
		else:
			self.wait_for_filter = ''

	def hasScriptFunction(self, name):
		script = 'if ( DoesFunctionExist("%s") ) { Exit(1.0); } else { Exit(-1.0); }'
		script %= name
		result = self.ExecuteGetDoubleScript(script)
		return result > 0.0

	def connect(self):
		# recommended by Gatan to use localhost IP to avoid using tcp
		self.sock = socket.create_connection(('127.0.0.1',self.port))

	def disconnect(self):
		self.sock.shutdown(socket.SHUT_RDWR)
		self.sock.close()

	def reconnect(self):
		self.disconnect()
		self.connect()

	@logwrap
	def send_data(self, data):
		return self.sock.sendall(data)

	@logwrap
	def recv_data(self, n):
		return self.sock.recv(n)

	def ExchangeMessages(self, message_send, message_recv=None):
		self.send_data(message_send.pack())
		if message_recv is None:
			return
		recv_buffer = message_recv.pack()
		recv_len = len(recv_buffer)
		total_recv = 0
		parts = []
		while total_recv < recv_len:
			remain = recv_len - total_recv
			new_recv = self.recv_data(remain)
			parts.append(new_recv)
			total_recv += len(new_recv)
		buf = ''.join(parts)
		message_recv.unpack(buf)
		## log the error code from received message
		sendargs = message_send.array['longargs']
		recvargs = message_recv.array['longargs']
		log('Func: %d, Code: %d' % (sendargs[0],recvargs[0]))

	def GetLong(self, funcName):
		'''common class of function that gets a single long'''
		funcCode = enum_gs[funcName]
		message_send = Message(longargs=(funcCode,))
		# First recieved message longargs is error code
		message_recv = Message(longargs=(0,0))
		self.ExchangeMessages(message_send, message_recv)
		result = message_recv.array['longargs'][1]
		return result

	def SendLongGetLong(self, funcName, longarg):
		'''common class of function with one long arg
		that returns a single long'''
		funcCode = enum_gs[funcName]
		message_send = Message(longargs=(funcCode,longarg))
		# First recieved message longargs is error code
		message_recv = Message(longargs=(0,0))
		self.ExchangeMessages(message_send, message_recv)
		result = message_recv.array['longargs'][1]
		return result

	def GetDMVersion(self):
		return self.GetLong('GS_GetDMVersion')

	def GetNumberOfCameras(self):
		return self.GetLong('GS_GetNumberOfCameras')

	def GetPluginVersion(self):
		return self.GetLong('GS_GetPluginVersion')

	def IsCameraInserted(self, camera):
		funcCode = enum_gs['GS_IsCameraInserted']
		message_send = Message(longargs=(funcCode,camera))
		message_recv = Message(longargs=(0,), boolargs=(0,))
		self.ExchangeMessages(message_send, message_recv)
		result = bool(message_recv.array['boolargs'][0])
		return result

	def InsertCamera(self, camera, state):
		funcCode = enum_gs['GS_InsertCamera']
		message_send = Message(longargs=(funcCode,camera), boolargs=(state,))
		message_recv = Message(longargs=(0,))
		self.ExchangeMessages(message_send, message_recv)

	def SetReadMode(self, mode, scaling=1.0):
		funcCode = enum_gs['GS_SetReadMode']
		message_send = Message(longargs=(funcCode,mode),dblargs=(scaling,))
		message_recv = Message(longargs=(0,))
		self.ExchangeMessages(message_send, message_recv)

	def SetShutterNormallyClosed(self, camera, shutter):
		funcCode = enum_gs['GS_SetShutterNormallyClosed']
		message_send = Message(longargs=(funcCode,camera, shutter))
		message_recv = Message(longargs=(0,))
		self.ExchangeMessages(message_send, message_recv)

	@logwrap
	def SetK2Parameters(self, readMode, scaling, hardwareProc, doseFrac, frameTime, alignFrames, saveFrames, filt=''):
		funcCode = enum_gs['GS_SetK2Parameters']

		self.save_frames = saveFrames

		# filter name
		filt_str = filt + '\0'
		extra = len(filt_str) % 4
		if extra:
			npad = 4 - extra
			filt_str = filt_str + npad * '\0'
		longarray = numpy.frombuffer(filt_str, dtype=numpy.int_)

		longs = [
			funcCode,
			readMode,
			hardwareProc,
		]
		bools = [
			doseFrac,
			alignFrames,
			saveFrames,
		]
		doubles = [
			scaling,
			frameTime,
		]

		message_send = Message(longargs=longs, boolargs=bools, dblargs=doubles, longarray=longarray)
		message_recv = Message(longargs=(0,)) # just return code
		self.ExchangeMessages(message_send, message_recv)

	@logwrap
	def SetupFileSaving(self, rotationFlip, dirname, rootname, filePerImage, earlyReturnFrameCount=0):
		pixelSize = 1.0
		if self.save_frames and earlyReturnFrameCount > 0:
			# early return flag
			flag = 128
			longs = [enum_gs['GS_SetupFileSaving2'], rotationFlip, flag,]
			dbls = [pixelSize,earlyReturnFrameCount,0.,0.,0.,]
		else:
			longs = [enum_gs['GS_SetupFileSaving'], rotationFlip,]
			dbls = [pixelSize,]
		bools = [filePerImage,]
		names_str = dirname + '\0' + rootname + '\0'
		extra = len(names_str) % 4
		if extra:
			npad = 4 - extra
			names_str = names_str + npad * '\0'
		longarray = numpy.frombuffer(names_str, dtype=numpy.int_)
		message_send = Message(longargs=longs, boolargs=bools, dblargs=dbls, longarray=longarray)
		message_recv = Message(longargs=(0,0))
		self.ExchangeMessages(message_send, message_recv)

	def GetFileSaveResult(self):
		longs = [enum_gs['GS_GetFileSaveResult'], rotationFlip]
		message_send = Message(longargs=longs, boolargs=bools, dblargs=dbls, longarray=longarray)
		message_recv = Message(longargs=(0,0,0))
		self.ExchangeMessages(message_send, message_recv)
		args = message_recv.array['longargs']
		numsaved = args[1]
		error = args[2]

	def SelectCamera(self, cameraid):
		funcCode = enum_gs['GS_SelectCamera']
		message_send = Message(longargs=(funcCode,cameraid))
		message_recv = Message(longargs=(0,))
		self.ExchangeMessages(message_send, message_recv)
		
	def GetEnergyFilter(self):
		if 'GetEnergyFilter' not in self.filter_functions.keys():
			return -1.0
		script = 'if ( %s() ) { Exit(1.0); } else { Exit(-1.0); }' % (self.filter_functions['GetEnergyFilter'],)
		return self.ExecuteGetDoubleScript(script)

	def SetEnergyFilter(self, value):
		if 'SetEnergyFilter' not in self.filter_functions.keys():
			return -1.0
		if value:
			i = 1
		else:
			i = 0
		script = '%s(%d); %s' % (self.filter_functions['SetEnergyFilter'], i, self.wait_for_filter)
		return self.ExecuteSendScript(script)

	def GetEnergyFilterWidth(self):
		if 'GetEnergyFilterWidth' not in self.filter_functions.keys():
			return -1.0
		script = 'Exit(%s())' % (self.filter_functions['GetEnergyFilterWidth'],)
		return self.ExecuteGetDoubleScript(script)

	def SetEnergyFilterWidth(self, value):
		if 'SetEnergyFilterWidth' not in self.filter_functions.keys():
			return -1.0
		script = 'if ( %s(%f) ) { Exit(1.0); } else { Exit(-1.0); }' % (self.filter_functions['SetEnergyFilterWidth'], value)
		return self.ExecuteSendScript(script)

	def AlignEnergyFilterZeroLossPeak(self):
		script = ' if ( %s() ) { %s Exit(1.0); } else { Exit(-1.0); }' % (self.filter_functions['AlignEnergyFilterZeroLossPeak'], self.wait_for_filter)
		return self.ExecuteGetDoubleScript(script)

	@logwrap
	def GetImage(self, processing, height, width, binning, top, left, bottom, right, exposure, shutterDelay):

		arrSize = width * height

		# TODO: need to figure out what these should be
		shutter = 0
		divideBy2 = 0
		corrections = 0
		settling = 0.0

		# prepare args for message
		if processing == 'dark':
			longargs = [enum_gs['GS_GetDarkReference']]
		else:
			longargs = [enum_gs['GS_GetAcquiredImage']]
		longargs.extend([
			arrSize,  # pixels in the image
			width, height,
		])
		if processing == 'unprocessed':
			longargs.append(0)
		elif processing == 'dark subtracted':
			longargs.append(1)
		elif processing == 'gain normalized':
			longargs.append(2)
		longargs.extend([
			binning,
			top, left, bottom, right,
			shutter,
		])
		if processing != 'dark':
			longargs.append(shutterDelay)
		longargs.extend([
			divideBy2,
			corrections,
		])
		dblargs = [
			exposure,
			settling,
		]

		message_send = Message(longargs=longargs,dblargs=dblargs)
		message_recv = Message(longargs=(0,0,0,0,0))

		# attempt to solve UCLA problem by reconnecting
		#if self.save_frames:
			#self.reconnect()

		self.ExchangeMessages(message_send, message_recv)

		longargs = message_recv.array['longargs']
		if longargs[0] < 0:
			return 1
		arrSize = longargs[1]
		width = longargs[2]
		height = longargs[3]
		numChunks = longargs[4]
		bytesPerPixel = 2
		numBytes = arrSize * bytesPerPixel
		chunkSize = (numBytes + numChunks - 1) / numChunks
		imArray = numpy.zeros((height,width), numpy.ushort)
		received = 0
		remain = numBytes
		for chunk in range(numChunks):
			# send chunk handshake for all but the first chunk
			if chunk:
				message_send = Message(longargs=(enum_gs['GS_ChunkHandshake'],))
				self.ExchangeMessages(message_send)
			thisChunkSize = min(remain, chunkSize)
			chunkReceived = 0
			chunkRemain = thisChunkSize
			while chunkRemain:
				new_recv = self.recv_data(chunkRemain)
				len_recv = len(new_recv)
				imArray.data[received:received+len_recv] = new_recv
				chunkReceived += len_recv
				chunkRemain -= len_recv
				remain -= len_recv
				received += len_recv
		return imArray

	def ExecuteSendScript(self, command_line, select_camera=0):
		recv_longargs_init = (0,)
		result = self.ExecuteScript(command_line,select_camera,recv_longargs_init)
		# first longargs is error code. Error if > 0
		return result.array['longargs'][0]

	def ExecuteGetLongScript(self,command_line, select_camera=0):
		'''
		Execute DM script and return the result as integer
		'''
		# SerialEMCCD DM TemplatePlugIn::ExecuteScript retval is a double
		return int(self.ExecuteGetDoubleScript(command_line,select_camera))

	def ExecuteGetDoubleScript(self,command_line, select_camera=0):
		'''
		Execute DM script that gets one double float number
		'''
		recv_dblargs_init = (0.0,)
		result = self.ExecuteScript(command_line,select_camera,recv_dblargs_init=recv_dblargs_init)
		return result.array['dblargs'][0]

	def ExecuteScript(self,command_line, select_camera=0, recv_longargs_init=(0,), recv_dblargs_init=(0.0,), recv_longarray_init=[]):
		funcCode = enum_gs['GS_ExecuteScript']
		cmd_str = command_line + '\0'
		extra = len(cmd_str) % 4
		if extra:
			npad = 4 - extra
			cmd_str = cmd_str + (npad) * '\0'
		# send the command string as 1D longarray
		longarray = numpy.frombuffer(cmd_str, dtype=numpy.int_)
		message_send = Message(longargs=(funcCode,), boolargs=(select_camera,), longarray=longarray)
		message_recv = Message(longargs=recv_longargs_init, dblargs=recv_dblargs_init, longarray=recv_longarray_init)
		self.ExchangeMessages(message_send, message_recv)
		return message_recv

def test1():
	g = GatanSocket()
	print g
	ver = g.GetDMVersion()
	print 'Version', ver
	raw_input('enter to quit.')

if __name__ == '__main__':
	test1()
