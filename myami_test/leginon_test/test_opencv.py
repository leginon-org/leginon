#!/usr/bin/env python
import unittest
import leginon.openCVcaller
import pyami.mrc
import time
import inspect
import os

class TestOpenCV(unittest.TestCase):

	def testMatchImages(self):
		self.match_error = 'No'
		self.assertTrue(self._testMatchImages(),msg=self.match_error)

	def _testMatchImages(self):
		# read mrc files
		thisdir = self.getThisModuleDir()
		arraynew = pyami.mrc.read(os.path.join(thisdir,'data','arraynew.mrc'))
		arrayold = pyami.mrc.read(os.path.join(thisdir,'data','arrayold.mrc'))
		try:
			t0 = time.time()
			blur = 11
			arraynew = leginon.openCVcaller.modifyImage(arraynew, blur,0)
			arrayold = leginon.openCVcaller.modifyImage(arrayold, blur,0)

			result = leginon.openCVcaller.MatchImages(arrayold, arraynew)
			t1 = time.time()
			print 'process time = %.1f seconds' % (t1 - t0)
			return True
		except:
			self.match_error = e
			return False

	def getThisModuleDir(self):
		# full path of this module
		this_file = inspect.currentframe().f_code.co_filename
		fullmod = os.path.abspath(this_file)
		# just the directory
		dirname = os.path.dirname(fullmod)
		return dirname

	def runTest(self):
		self.testMatchImages()

def runTestCases():
	'''
	method to be called from module that need to catch and handle the exception.
	'''
	t=TestOpenCV()
	t.runTest()

if __name__ == '__main__':
	unittest.main()
