#!/usr/bin/env python

class Logger(object):
	def __init__(self, is_debug=False):
		self.is_debug = is_debug

	def info(self,txt):
		print 'info',txt

	def warning(self,txt):
		print 'WARNING:',txt

	def error(self,txt):
		print 'ERROR:',txt

	def debug(self,txt):
		if self.is_debug:
			print 'DEBUG:',txt
