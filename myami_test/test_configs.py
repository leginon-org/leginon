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

	def testSession(self):
		self.session_error = 'No'
		self.assertTrue(self._testSession(), msg=self.session_error)

	def _testSession(self):
		try:
			pyami.moduleconfig.getConfigured('leginon_session.cfg', package='leginon')['name']['prefix']
		except IOError:
			# optional config file
			return True
		except KeyError, e:
			self.session_error = 'Existing leginon_session.cfg does not have "prefix" item in "name" section'
			return False
		return True

	def testRemote(self):
		self.remote_error = 'No'
		self.assertTrue(self._testRemote(), msg=self.remote_error)

	def _testRemote(self):
		try:
			configs = pyami.moduleconfig.getConfigured('remote.cfg', package='leginon')
			import json
			import requests
			response = requests.get('%sapi/microscopes/' %(configs['web server']['url'],),auth=(configs['leginon auth']['username'],configs['leginon auth']['password']))
			if not response.ok:
				self.remote_error = 'REST request error: %s' %(response.reason)
				return False
		except IOError:
			# optional config file
			return True
		except ImportError, e:
			self.remote_error = 'Could not import required module. %s' %(e)
			return False
		except KeyError, e:
			self.remote_error = 'Existing remote.cfg does not have required key: %s' %(e)
			return False
		return True

	def runTest(self):
		self.testSinedon()
		self.testLeginon()
		self.testInstruments()
		self.testSession()
		self.testRemote()

def runTestCases():
	'''
	method to be called from module that need to catch and handle the exception.
	'''
	t=TestConfigs()
	t.runTest()

if __name__ == '__main__':
	unittest.main()
