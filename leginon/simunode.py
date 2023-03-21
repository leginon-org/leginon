#!/usr/bin/env python
'''
This is a gui-free node that is good for development.
'''
from leginon import leginondata
from leginon import calibrationclient
from pyami import simplelogger

class NodeSimulator(object):
	def __init__(self, session):
		self.logger = simplelogger.Logger()
		self.session = session
		self.event_input = []
		self.event_output = []
	def addEventInput(self,evt,handler):
		self.event_input.append((evt,handler))

	def addEventOutput(self,evt):
		self.event_output.append(evt)

	def research(self,datainstance, results=None):
		if results:
			return datainstance.query(results=results)
		return datainstance.query()


if __name__ == '__main__':
	# Use Example of the most recent session
	session = leginondata.SessionData().query()[0]
	# Node allows session information to pass through
	test_node = NodeSimulator(session) 
	# Find the most recent image in this session
	image = leginondata.AcquisitionImageData(session=session).query(results=1)[0]
	# tem instrument instance
	tem = image['scope']['tem']
	# ccdcamera instrument
	ccdcamera = image['camera']['ccdcamera']
	# caltype in this example
	caltype = 'image shift'
	# high tension of the scope
	ht = image['scope']['high tension']
	# nominal magnification
	mag = image['scope']['magnification']
	# We don't care what probe mode is used
	probe = None
	# research matrix needs these to construct the result
	# use the NodeSimulator instance to allow passing of logger and other tasks
	# done by them normally.
	calclient = calibrationclient.ImageShiftCalibrationClient(test_node)
	# Now we can use calclient on any function in there.
	matrix = calclient.researchMatrix(tem, ccdcamera, caltype, ht, mag, probe)
	# Do what you need with the matrix.
	print matrix
