#!/usr/bin/env python

import time
import sys
import SocketServer
import socket

#### Choose either numarray or numpy

################ numarray ##################
if True:
	import numarray
	import numarray.random_array as rand
	int32 = numarray.Int32
	float32 = numarray.Float32
	num = numarray
################ numpy ##################
else:
	import numpy
	rand = numpy.random
	int32 = numpy.int32
	float32 = numpy.float32
	num = numpy

def timefunc(n, func, args):
	t0 = time.time()
	for i in range(n):
		t00 = time.time()
		func(*args)
		t11 = time.time()
		print '        %7.3f' % (t11-t00,)
	t1 = time.time()
	total = t1 - t0
	percall = total / n
	print ''
	print '%7.3f %7.3f' % (total, percall)

def randomData(mb):
	'Generate mb megabytes of random data'
	## will create array with 4 byte integers
	n = 1024 * 1024 * mb / 4
	a = rand.randint(-2147483648, 2147483648, n)
	a = num.asarray(a, int32)
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
	def handle(self):
		request = self.rfile.readline()
		mb = int(request)
		if mb not in self.server.data:
			print 'received bad request:', mb
			return
		print 'writing %d MB to socket...' % (mb,)

		t0 = time.time()
		self.server.data[mb].tofile(self.wfile)
		t1 = time.time()

		t = t1-t0
		rate = mb/t
		print 'sent %d MB in %.3f sec... %.3f MB/sec' % (mb, t, rate)

class Server(SocketServer.TCPServer):
	def __init__(self, port):
		print 'creating random data'
		self.data = {}
		for mb in (1,32,64):
			self.data[mb] = randomData(mb)
		SocketServer.TCPServer.__init__(self, ('',port), Handler)

def serveData(port):
	serv = Server(port)
	#serv.handle_request()
	print 'server waiting for requests'
	serv.serve_forever()

def getData(host, port, mb):
	print 'connecting to ', host, port
	sock = socket.socket()
	sock.connect((host, port))
	f = sock.makefile('rwb')

	print 'requesting', mb
	f.write('%d\n' % (mb,))
	print 'flush'
	f.flush()
	print 'receiving data'

	t0 = time.time()
	data = f.read()
	#data = num.fromfile(f, int32)
	t1 = time.time()

	m = len(data) / 1024.0 / 1024.0
	t = t1-t0
	rate = m/t
	print 'received %d MB in %.3f sec... %.3f MB/sec' % (m, t, rate)
	f.close()
	sock.close()

def timeGetData(n, host, port, mb):
	timefunc(n, getData, (host, port, mb))


if __name__ == '__main__':
	'''
	filename = sys.argv[1]
	n = int(sys.argv[2])
	mb = int(sys.argv[3])
	timeSaveData(n, mb, filename)
	'''

	if len(sys.argv) == 5:
		# client
		host = sys.argv[1]
		port = int(sys.argv[2])
		mb = int(sys.argv[3])
		n = int(sys.argv[4])
		timeGetData(n, host, port, mb)
	elif len(sys.argv) == 2:
		# server
		port = int(sys.argv[1])
		serveData(port)

