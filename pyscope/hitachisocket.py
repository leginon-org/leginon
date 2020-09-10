#!/usr/bin/env python
'''
This defines a client class to interface with the socket based HT7800 interface.
'''

import os
import socket
import time
import numpy

## set this to a file name to log some socket debug messages.
## Set to None to avoid saving a log.
## for example:
debug_log = None
#debug_log = 'hitachisocket.log'
def log(msg):
        pass

def logwrap(func):
	def newfunc(*args, **kwargs):
		log('%s\t%s\t%s' % (func,args,kwargs))
		try:
			result = func(*args, **kwargs)
		except Exception, exc:
			log('EXCEPTION: %s' % (exc,))
			#raise
		return result
	return newfunc


SET_GET_REPLACEMENTS = {'Move':'Position'}

class HitachiSocket(object):
	eof_marker = "\r"
	def __init__(self, host='', port=None):
		self.host = host
		if port is not None:
			self.port = port
		else:
			raise ValueError('need to specify a port to HitachiSocket instance')
		self.connect()

	def connect(self):
		# recommended by Gatan to use localhost IP to avoid using tcp
		self.sock = socket.create_connection((self.host,self.port))

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
	def recv_data(self, min_length):
		data = self.sock.recv(min_length)
		return data

	def sendMessage(self, text):
		self.send_data(text+self.eof_marker)

	def recvMessage(self, min_length):
		new_recv = self.recv_data(min_length)
		recv_text = ''
		while 1:
			one_recv = self.recv_data(1)
			if one_recv == self.eof_marker:
				break
			else:
				recv_text += one_recv
		#print recv_text
		return recv_text

	def runSetCommand(self, sub_code, ext_code, args=[], data_types=[],hex_lengths=[6,]):
		'''
		common class of function that sets data. Specify data types
		for each value that returned
		'''
		if len(args) != len(data_types):
			raise ValueError('args and data_types not at the same length')
		main_code = 'Set'
		cmd = ' '.join([main_code, sub_code, ext_code])
		recv_min_length = len(cmd)+1 # set command will be repeated in the recv'd message
		hex_count = 0
		for i,t in enumerate(data_types):
			if t == 'int':
				args[i] = '%d' % args[i]
			elif t == 'float':
				args[i] = '%.1f' % args[i]
			elif t == 'bool':
				args[i] = '%d' % int(args[i])
			elif t == 'hexdec':
				# use the last value if count is larger than number of input hex_lengths
				hex_length = hex_lengths[min(hex_count, len(hex_lengths)-1)]
				args[i] = "{0:0{1}X}".format(int(args[i],16),hex_length) # format to 000FFF, for example
				hex_count += 1
			else:
				# string type
				pass
		arg_string = ','.join(args)
		print 'send', arg_string, recv_min_length
		self.sendMessage(cmd+' '+arg_string)
		# Special case without message coming back.
		if sub_code == 'Stage' and ext_code == 'SpecimenNo':
			data_string = '8000' # This does not have message coming back.
			return
		# expect any data to include '8001, "NG."'
		data_string = self.recvMessage(recv_min_length)
		data = data_string.split(',')
		status_code = int(data[0])
		if status_code != 8000:
			if status_code == 8001:
				raise ValueError('cmd "%s"is not valid' % cmd)
			else:
				raise RuntimeError('Other error %s' % data[1])
		return

	def runGetCommand(self, sub_code, ext_code, data_types=[]):
		'''
		common class of function that gets data. Specify data types
		for each value that returned
		'''
		main_code = 'Get'
		cmd = ' '.join([main_code, sub_code, ext_code])
		self.sendMessage(cmd)
		# expect any data to include '8001, "NG."'
		data_string = self.recvMessage(0)
		if '8001,"NG."' in data_string:
			raise ValueError('cmd is not valid')
		data = data_string[len(cmd):].split(',')
		for i,t in enumerate(data_types):
			if t == 'int':
				data[i] = int(data[i])
			elif t == 'float':
				data[i] = float(data[i])
			elif t == 'bool':
				data[i] = bool(data[i])
			elif t == 'hexdec':
				data[i] = hex(int(data[i],16)) #hexdec string without 0x
			else: #str
				pass
		if len(data) == 1:
			return data[0]
		else:
			return data

	def runSetAndWait(self, sub_code, ext_code, value_list, type_list, timeout=60, hex_lengths=[6,]):
		# create a copy of value_list since args get modified in runSetComand and causes wait comparison fails
		self.runSetCommand(sub_code,ext_code,list(value_list),type_list, hex_lengths)
		t0 = time.time()
		get_ext_code = ext_code
		if get_ext_code in SET_GET_REPLACEMENTS.keys():
			get_ext_code = SET_GET_REPLACEMENTS[get_ext_code]
		while True:
			result_list = self.runGetCommand(sub_code,get_ext_code,type_list)
			if type(result_list) != type([]):
				result_list = [result_list,]
			if len(result_list) != len(value_list):
				raise RuntimeError('get values not the same length as input')
			is_done = True
			for i in range(len(value_list)):
				# FF keeps the same value.  Does not work, though
				if sub_code == 'Column' and ext_code == 'Mode' and int(value_list[i],16) == int('FF',16):
					is_done = True
					continue
				is_done =  is_done and value_list[i] == result_list[i]
			if is_done is True:
				break
			if time.time() - t0 > timeout:
				raise RuntimeError('set %s.%s not reached requested value in %d seconds' % (sub_code, ext_code, timeout))
		return

	def runSetFloatAndWait(self, sub_code, ext_code, value_list, precision=0.1, timeout=60):
		type_list = []
		for v in value_list:
			if type(v) != type(1.0):
				raise ValueError('input must be integer type')
			type_list.append('float')
		# create a copy of value_list since args get modified in runSetComand and causes wait comparison fails
		self.runSetCommand(sub_code,ext_code,list(value_list),type_list)
		t0 = time.time()
		get_ext_code = ext_code
		if get_ext_code in SET_GET_REPLACEMENTS.keys():
			get_ext_code = SET_GET_REPLACEMENTS[get_ext_code]
		while True:
			result_list = self.runGetCommand(sub_code,get_ext_code,type_list)
			if type(result_list) != type([]):
				result_list = [result_list,]
			if len(result_list) != len(value_list):
				raise RuntimeError('get values not the same length as input')
			is_done = True
			for i in range(len(value_list)):
				is_done =  is_done and abs(value_list[i] - result_list[i]) <= precision
			if is_done is True:
				break
			if time.time() - t0 > timeout:
				raise RuntimeError('set %s.%s not reached requested value in %d seconds' % (sub_code, ext_code, timeout))
		return

	def runSetIntAndWait(self, sub_code, ext_code, value_list, timeout=10):
		type_list = []
		for v in value_list:
			if type(v) != type(1):
				raise ValueError('input must be integer type')
			type_list.append('int')
		return self.runSetAndWait(sub_code, ext_code, value_list, type_list, timeout)

	def runSetBoolAndWait(self, sub_code, ext_code, value_list, timeout=60):
		type_list = []
		for v in value_list:
			if type(v) != type(True):
				raise ValueError('input must be boolean type')
			type_list.append('bool')
		return self.runSetAndWait(sub_code, ext_code, value_list, type_list, timeout)

	def runSetHexdecAndWait(self, sub_code, ext_code, value_list, timeout=60, hex_lengths=[6,]):
		type_list = []
		for v in value_list:
			if type(v) != type(hex(17)): #hexdec string without 0x
				raise ValueError('input must be hexdec type')
			type_list.append('hexdec')
		return self.runSetAndWait(sub_code, ext_code, value_list, type_list, timeout, hex_lengths)

def test1(h):
		# Stage get in submicron
		print h.runGetCommand('StageXY', 'Position',['int','int'])
		# Stage set, non-blocking.  need to monitor for done
		h.runSetCommand('StageXY', 'Move',[0,0],['int','int'])
		# Example for getting hexdec numbers and convert to decimal
		hexdecs = h.runGetCommand('Coil', 'IS',['hexdec','hexdec'])
		print 'result item0 in decimal:%d' % (int(hexdecs[0],16),)
		print 'result itme1 in hexdec %s' % (hexdecs[1],)
		# Example for sending a hexdec pair with FF as ID for expansion
		h.runSetCommand('Coil','IS',['FF',hexdecs[1],hexdecs[0]],['str','hexdec','hexdec'])

def test2(h):
	print h.runSetIntAndWait('Column', 'Magnification', [100000,]) 
	time.sleep(2)
	print h.runSetIntAndWait('Column', 'Magnification', [2000,]) 
	time.sleep(2)
	h.runSetIntAndWait('StageXY', 'Move',[2000,2000])
	print h.runGetCommand('StageXY', 'Position',['int','int'])
	time.sleep(2)
	h.runSetIntAndWait('StageXY', 'Move',[0,0])
	print h.runGetCommand('StageXY', 'Position',['int','int'])
	print h.runGetCommand('Column','Mode',['hexdec',])

if __name__=='__main__':
	try:
		make_it_fail
		h = HitachiSocket('192.168.10.1',12068)
		test2(h)
	except Exception as e:
		print e
		h = HitachiSocket('127.0.0.1',12068)
		test2(h)
	finally:
		raw_input('wait to exit')
