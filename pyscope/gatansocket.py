#!/usr/bin/env python
'''
This defines a client class to interface with the socket based DM plugin.
'''

import os
import socket
import numpy

# enum function codes as in GatanSocket.cpp and SocketPathway.cpp
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

class GatanSocket(object):
	def __init__(self, host='', port=None):
		self.host = host
		if port is not None:
			self.port = port
		elif 'SERIALEMCCD_PORT' in os.environ:
			self.port = os.environ['SERIALEMCCD_PORT']
		else:
			raise ValueError('need to specify a port to GatanSocket instance, or set environment variable SERIALEMCCD_PORT')
		self.connect()

	def connect(self):
		self.sock = socket.create_connection((self.host,self.port))

	def ExchangeMessages(self, message_send, message_recv=None):
		self.sock.sendall(message_send.pack())
		if message_recv is None:
			return
		recv_buffer = message_recv.pack()
		recv_len = len(recv_buffer)
		total_recv = 0
		parts = []
		while total_recv < recv_len:
			remain = recv_len - total_recv
			new_recv = self.sock.recv(remain)
			parts.append(new_recv)
			total_recv += len(new_recv)
		buf = ''.join(parts)
		message_recv.unpack(buf)

	def GetLong(self, funcName):
		'''common class of function that gets a single long'''
		funcCode = enum_gs[funcName]
		message_send = Message(longargs=(funcCode,))
		message_recv = Message(longargs=(0,0))
		self.ExchangeMessages(message_send, message_recv)
		result = message_recv.array['longargs'][1]
		return result

	def SendLongGetLong(self, funcName, longarg):
		'''common class of function with one long arg
		that returns a single long'''
		funcCode = enum_gs[funcName]
		message_send = Message(longargs=(funcCode,longarg))
		message_recv = Message(longargs=(0,0))
		self.ExchangeMessages(message_send, message_recv)
		result = message_recv.array['longargs'][1]
		return result

	def GetDMVersion(self):
		return self.GetLong('GS_GetDMVersion')

	def GetNumberOfCameras(self):
		return self.GetLong('GS_GetNumberOfCameras')

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

	def SetK2Parameters(self, readMode, scaling, hardwareProc, doseFrac, frameTime, alignFrames, saveFrames, filt=''):
		funcCode = enum_gs['GS_SetK2Parameters']

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

	def SetupFileSaving(self, rotationFlip, dirname, rootname):
		longs = [enum_gs['GS_SetupFileSaving'], rotationFlip]
		bools = [True,] # filePerImage=True
		pixelSize = 1.0
		dbls = [pixelSize]
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
				new_recv = self.sock.recv(chunkRemain)
				len_recv = len(new_recv)
				imArray.data[received:received+len_recv] = new_recv
				chunkReceived += len_recv
				chunkRemain -= len_recv
				remain -= len_recv
				received += len_recv
		return imArray

def test1():
	g = GatanSocket()
	print g
	ver = g.GetDMVersion()
	print 'Version', ver
	raw_input('enter to quit.')

if __name__ == '__main__':
	test1()
