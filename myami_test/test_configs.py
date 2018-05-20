#!/usr/bin/env python
import unittest
import pyami.moduleconfig
import socket

class TestConfigs(unittest.TestCase):
	def testSinedon(self):
		self.assertTrue(pyami.moduleconfig.getConfigured('sinedon.cfg', package='sinedon'))

	def testLeginon(self):
		self.assertTrue(pyami.moduleconfig.getConfigured('leginon.cfg', package='leginon'))

	def testInstruments(self):
		self.instrument_error = 'No'
		self.assertTrue(self._testInstruments(),msg=self.instrument_error)

	def _testInstruments(self):
		try:
			config = pyami.moduleconfig.getConfigured('instruments.cfg', package='pyscope')
			return type(config) == type({})
		except IOError, e:
			self.instrument_error = e
			return False

	def runTest(self):
		self.testSinedon()
		self.testLeginon()
		self.testInstruments()

def runTestCases():
	'''
	method to be called from module that need to catch and handle the exception.
	'''
	t=TestConfigs()
	t.runTest()

if __name__ == '__main__':
	unittest.main()
