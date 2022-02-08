#!/usr/bin/env python
import unittest
import pyami.mysocket
import socket

class TestIpMapping(unittest.TestCase):
	def setUp(self):
		self.host_maps = {}
		self.setHostMappings()

	def setHostMappings(self):
		host_maps = pyami.mysocket.getHostMappings()
		self.host_maps = host_maps

	def testHostname(self):
		for name in self.host_maps.keys():
			msg = 'pyami.cfg hostname %s does not exist.' % name
			self.assertEqual(type(self._getHostByName(name)),str,msg=msg)

	def _getHostByName(self,name):
		'''
		Catch socket.gaierror so that it does not display as exception.
		'''
		try:
			address = socket.gethostbyname(name)
		except socket.gaierror:
			return None
		return address
		
	def testMapping(self):
		'''
		Test that the address in pyami.cfg is mapped to the assigned hostname.
		'''
		for name in self.host_maps.keys():
			addr = self.host_maps[name]
			msg = 'Incorrect pyami.cfg host mapping for %s' % (addr)
			self.longMessage = True
			socket_address = self._getHostByName(name)
			self.assertEqual(socket_address,addr,msg=msg)

	def runTest(self):
		'''
		Run test and output result to standard out
		'''
		self.setUp()
		self.testHostname()
		#self.testMapping()

def runTestCases():
	'''
	method to be called from module that need to catch and handle the exception.
	'''
	t=TestIpMapping()
	t.runTest()

if __name__ == '__main__':
	unittest.main()
