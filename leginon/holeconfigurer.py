#!/usr/bin/env python
'''
Common holefinder configuration
'''
class Configurer(object):
	def __init__(self):
		self.configs = {}

	def setDefaults(self, default_configs):
		self.configs = default_configs

	def configure(self, new_configs):
		'''
		Set items in configs according to the input dictionary.  If the input
		value is None, no change is made.
		'''
		for k in new_configs.keys():
			if new_configs[k] is not None:
				self.configs[k] = new_configs[k]

