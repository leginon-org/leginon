#!/usr/bin/env python

import time
import sys
import SocketServer
import socket
from pyami import correlator

'''
try:
	from pyscope import gatan
except:
	pass
try:
	from pyscope import tietz
except:
	pass
'''

import cPickle
import numextension
import simtime

#### Choose either numarray or numpy

################ numarray ##################
if True:
	import numarray
	import numarray.random_array as rand
	import numarray.nd_image as ndimage
	int32 = numarray.Int32
	float32 = numarray.Float32
	float64 = numarray.Float64
	uint16 = numarray.UInt16
	num = numarray
################ numpy ##################
else:
	import numpy
	#import scipy.ndimage as ndimage
	rand = numpy.random
	int32 = numpy.int32
	float32 = numpy.float32
	float64 = numpy.float64
	uint16 = numpy.uint16
	num = numpy

def timefunc(n, func, args):
	t0 = time.time()
	for i in range(n):
		t00 = time.time()
		result = func(*args)
		t11 = time.time()
		print '        %7.3f' % (t11-t00,)
	t1 = time.time()
	total = t1 - t0
	percall = total / n
	print ''
	print '%7.3f %7.3f' % (total, percall)
	return result

def randomImage(dim):
	n = dim * dim
	a = rand.randint(-2147483648, 2147483648, n)
	a = num.asarray(a, uint16)
	a.shape = dim,dim
	return a

def randomData(mb):
	'Generate mb megabytes of random data'
	## will create array with 4 byte integers
	n = 1024 * 1024 * mb / 2
	a = rand.randint(-2147483648, 2147483648, n)
	a = num.asarray(a, uint16)
	return a

def saveData(a, filename):
	f = open(filename, 'w')
	a.tofile(f)
	f.close()

def saveRandomData(mb, filename):
	a = randomData(mb)
	saveData(a, filename)

def timeRandomData(n, mb):
	timefunc(n, randomData, (mb,))

def timeSaveData(n, mb, filename):
	a = randomData(mb)
	timefunc(n, saveData, (a, filename))

def timeSaveRandomData(n, mb, filename):
	timefunc(n, saveRandomData, (mb, filename))

class Handler(SocketServer.StreamRequestHandler):
	'''
	Handles requests separated by newline.
	Request can either:
	  - integer specifying MB of random data to request
	  - two integers separated by whitespace specifying size and binning
	'''
	def handle(self):
		print 'REQUEST RECEIVED', time.time()
		request = self.rfile.readline()
		config = map(int, request.split())

		t0 = time.time()

		data = self.server.acquire(config)
		if data is None:
			print 'received bad request:', request
			return
		print 'SIZE', data.size()
		print 'ITEMSIZE', data.itemsize()
		mb = int(data.size() * data.itemsize() / 1024.0 / 1024.0)

		t1 = time.time()
		t = t1 - t0
		print 'generated data in %.3f sec' % (t,)

		print 'writing %d MB to socket...' % (mb,)
		print 'DATA', data

		t0 = time.time()
		print 'TTTTTTTTTTT', time.time()

		#s = data.tostring()
		#self.wfile.write(s)
		cPickle.dump(data, self.wfile, cPickle.HIGHEST_PROTOCOL)

		t1 = time.time()
		t = t1-t0
		rate = mb/t
		print 'sent %d MB in %.3f sec... %.3f MB/sec' % (mb, t, rate)

class Server(SocketServer.TCPServer):
	def __init__(self, port):
		try:
			self.ccd = gatan.Gatan()
			print 'Gatan initialized'
		except:
			print '** Gatan initialization failed'
			try:
				self.ccd = tietz.TietzSCX()
				print 'TietzSCX initialized'
			except:
				print '** TietzSCX initialization failed.'
				self.ccd = None
		SocketServer.TCPServer.__init__(self, ('',port), Handler)

	def fake(self, config):
		print 'CONFIG', config
		dim,bin = config
		'''
		tr = simtime.tietzReadout(dim, bin, 0)
		t0 = time.time()
		'''
		im = randomImage(dim)
		'''
		t1 = time.time()
		dt = tr-t1+t0
		time.sleep(dt)
		'''
		return im

	def acquire(self, config):
		if self.ccd is None:
			return self.fake(config)
		dim,bin = config
		try:
			self.ccd.setExposureTime(0)
			self.ccd.setOffset({'x':0, 'y':0})
			self.ccd.setDimension({'x':dim, 'y':dim})
			self.ccd.setBinning({'x':bin, 'y':bin})
		except:
			print '** Exception during camera config'
			return None
		try:
			data = self.ccd.getImage()
			print 'IMAGE', data.shape, data.type()
		except:
			data = None
		return data

def serveData(port):
	serv = Server(port)
	#serv.handle_request()
	print 'server waiting for requests'
	serv.serve_forever()

def getData(host, port, int1, int2=None):
	print 'connecting to ', host, port
	sock = socket.socket()
	sock.connect((host, port))
	f = sock.makefile('rwb')

	if int2 is None:
		request = '%d\n' % (int1,)
	else:
		request = '%d %d\n' % (int1,int2)

	print 'requesting', request
	f.write(request)
	print 'flush'
	f.flush()
	print 'REQUEST SENT', time.time()
	print 'receiving data'

	t0 = time.time()

	#data = f.read()
	data = cPickle.load(f)
	print 'DATA', data

	t1 = time.time()

	#data = num.fromfile(f, uint16)
	#print 'fromstring 0', time.time()
	#data = num.fromstring(data, uint16)
	#print 'fromstring 1', time.time()
	print 'TTTTTTTTTTT', time.time()
	#data = num.fromfile(f, int32)

	m = len(data) / 1024.0 / 1024.0
	t = t1-t0
	rate = m/t
	print 'received data %.3f sec after request' % (t,)
	f.close()
	sock.close()
	return data

def timeGetData(n, host, port, int1, int2=None):
	return timefunc(n, getData, (host, port, int1, int2))

def timeGetSaveData(n, host, port, int1, int2, prefix):
	for i in range(n):
		t0 = time.time()
		data = getData(host, port, int1, int2)
		filename = '%s%05d' % (prefix, i)
		saveData(data, filename)
		t1 = time.time()
		print 'GetSave', t1-t0

def stats(a):
	ndimage.mean(a)
	ndimage.standard_deviation(a)
	ndimage.minimum(a)
	ndimage.maximum(a)

def stats2(a):
	ndimage.mean(a)
	ndimage.standard_deviation(a)
	numextension.minmax(a)

def timeStats(n, a):
	timefunc(n, stats, (a,))

def randomStats(shape):
	a = rand.random(shape)
	stats(a)

def timeRandomStats(n, shape):
	a = rand.random(shape)
	a = num.array(a, float32)
	timefunc(n, stats, (a,))

def correct(a, d, n):
	return (a - d) * n

def timeRandomCorrect(n, size):
	s = size*size
	a = rand.randint(0,2**16, s)
	a = num.array(a, uint16)
	d = rand.random(s)
	d = num.array(d, float64)
	b = rand.random(s)
	b = num.array(b, float64)
	timefunc(n, correct, (a,d,b))

def correlate(im1, im2):
	c = correlator.Correlator()
	c.insertImage(im1)
	c.insertImage(im2)
	pc = c.phaseCorrelate()

def timeRandomCorrelate(n, size):
	im1 = randomImage(size)
	im2 = randomImage(size)
	timefunc(n, correlate, (im1,im2))

if __name__ == '__main__':
	'''
	filename = sys.argv[1]
	n = int(sys.argv[2])
	mb = int(sys.argv[3])
	timeSaveData(n, mb, filename)
	'''

	if len(sys.argv) in (6,7):
		# client
		host = sys.argv[1]
		port = int(sys.argv[2])
		n = int(sys.argv[3])
		prefix = sys.argv[4]
		int1 = int(sys.argv[5])
		if len(sys.argv) == 7:
			int2 = int(sys.argv[6])
		else:
			int2 = None
		#timeGetSaveData(n, host, port, int1, int2, prefix)
		timeGetData(n, host, port, int1, int2)
	elif len(sys.argv) == 2:
		# server
		port = int(sys.argv[1])
		serveData(port)

