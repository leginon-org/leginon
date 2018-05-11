#!/usr/bin/env python
import unittest
import pyami.moduleconfig
import socket

class TestDB(unittest.TestCase):
	def testConnection(self):
		from leginon import project
		self.assertTrue(project.ProjectData())

	def runTest(self):
		self.testConnection()

def runTestCases():
	'''
	method to be called from module that need to catch and handle the exception.
	'''
	t=TestDB()
	t.runTest()

if __name__ == '__main__':
	unittest.main()
