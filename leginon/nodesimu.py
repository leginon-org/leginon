#!/usr/bin/env python
'''
This is a gui-free node that is good for development.
'''
from leginon import leginondata

class Logger(object):
	def info(self,msg):
		print 'INFO: %s' % msg
	def warning(self,msg):
		print 'WARNING: %s' % msg
	def error(self,msg):
		print 'ERROR: %s' % msg
	def debug(self,msg):
		print('DEBUG: %s' % msg)

class NodeSimulator(object):
	def __init__(self, session):
		self.logger = Logger()
		self.session = session
		self.event_input = []
		self.event_output = []

	def addEventInput(self,evt,handler):
		self.event_input.append((evt,handler))

	def addEventOutput(self,evt):
		self.event_output.append(evt)

	def research(self, datainstance, results=None, readimages=True, timelimit=None):
		'''
		find instances in the database that match the given datainstance
		'''
		try:
			resultlist = datainstance.query(results=results, readimages=readimages, timelimit=timelimit)
		except (IOError, OSError) as e:
			raise ResearchError(e)
		return resultlist

if __name__ == '__main__':
	# Use Example
	from leginon import presets
	session = leginondata.SessionData().query()[0]
	# Node allows session information to pass through
	test_node = NodeSimulator(session) 
	# Presets Client need to know which node it is from.
	pclient = presets.PresetsClient(test_node)
	# The function in the class instance had now access to session info.
	print pclient.getPresetsFromDB().keys()
