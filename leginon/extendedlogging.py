import logging
import logging.handlers
import os
import sys
import time
import uidata

logging.Logger.manager.emittedNoHandlerWarning = 1

class Logger(logging.Logger):
	def __init__(self, name):
		logging.Logger.__init__(self, name)
		self.format = '%(asctime)s' \
									' %(name)s' \
									' %(module)s:%(lineno)d' \
									' %(levelname)s' \
									' %(message)s'
		self.dateformat = '%H:%M:%S'
		self.formatter = logging.Formatter('%(asctime)s'\
																				' %(name)s'\
																				' %(module)s:%(lineno)d'\
																				' %(levelname)s'\
																				' %(message)s',
																				'%H:%M:%S')
		self.formatter.converter = time.localtime

		self.printhandler = None

	def hasPrintHandler(self):
		if self.printhandler is None:
			return False
		else:
			return True

	def setPrintFormatter(self):
		if self.hasPrintHandler():
			formatter = logging.Formatter(self.format, self.dateformat)
			self.printhandler.setFormatter(formatter)

	def addPrintHandler(self):
		if not self.hasPrintHandler():
			self.printhandler = logging.StreamHandler(sys.stdout)
			self.setPrintFormatter()
			self.addHandler(self.printhandler)

	def removePrintHandler(self):
		if self.hasPrintHandler():
			self.removeHandler(self.printhandler)
			self.printhandler = None

	def getLevelNames(self):
		levelnames = []
		for i in logging._levelNames:
			if type(i) is int:
				levelnames.append(i)
		levelnames.sort()
		levelnames = map(lambda n: logging._levelNames[n], levelnames)
		return levelnames

	def onLevelSelect(self, index):
		value = self.loglevelselect.getSelectedValue(index)
		level = logging.getLevelName(value)
		self.setLevel(level)
		return index

	def onPropagate(self, value):
		self.propagate = value
		return value

	def onPrintLog(self, value):
		if value:
			self.printhandler = logging.StreamHandler(sys.stdout)
			self.printhandler.setFormatter(self.formatter)
			self.addHandler(self.printhandler)
		elif self.printhandler is not None:
			self.removeHandler(self.printhandler)
			self.printhandler = None
		return value

logging.setLoggerClass(Logger)

def getLogger(name, parentname=None):
	if parentname is not None:
		name = parentname + '.' + name
	return logging.getLogger(name)

