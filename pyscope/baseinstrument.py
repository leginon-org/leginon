import time
import loggedmethods

class BaseInstrument(object):
	logged_methods_on = False
	capabilities = (
		{'name': 'SystemTime', 'type': 'property'},
	)
	debug = False

	def __init__(self):
		pass

	def initConfig(self):
		# This import can not be at the module level due to circulated argument
		import config
		self.config_name = config.getNameByClass(self.__class__)
		if self.config_name is None:
			raise RuntimeError('%s was not found in your instruments.cfg' % (self.__class__.__name__,))
		self.conf = config.getConfigured()[self.config_name]

	def getSystemTime(self):
		return time.time()

	def getCapabilities(self):
		implemented = []
		for cap in self.capabilities:
			found = {'name': cap['name'], 'implemented': []}
			if cap['type'] == 'property':
				for op in ('set','get'):
					attr = op + cap['name']
					if hasattr(self, attr):
						found['implemented'].append(op)
			elif cap['type'] == 'method':
				if hasattr(self, cap['name']):
					found['implemented'].append('call')
			if found['implemented']:
				implemented.append(found)
		return implemented

	def debug_print(self,message):
		if self.debug:
			print 'DEBUG: %s' % (message,)
