#!/usr/bin/env python

class Logger(object):

	def info(self,txt):
		print 'info',txt

	def warning(self,txt):
		print 'WARNING:',txt

	def error(self,txt):
		print 'ERROR:',txt
