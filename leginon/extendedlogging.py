import logging
import logging.handlers
import os
import sys
import time
import uidata

class Logger(logging.Logger):
	def __init__(self, name):
		logging.Logger.__init__(self, name)
		self.formatter = logging.Formatter(
				'%(asctime)s %(name)s %(module)s:%(lineno)d %(levelname)s %(message)s',
				'%H:%M:%S')
		self.formatter.converter = time.localtime

		self.printhandler = None
		self.filehandler = None

		self.defineUserInterface()

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

	def addRotatingFileHandler(self, filename=None):
		if filename is None:
			filename = self.filename.get()
		elif filename == self.filename.get():
			return
		try:
			self.filehandler = logging.handlers.RotatingFileHandler(filename,
																																backupCount=32)
		except IOError, e:
			i = 0
			format = 'Message %d'
			while format % i in self.container:
				i += 1
			self.container.addObject(uidata.Message(format % i, 'error',
																					'Error logging to file: %s' % str(e)))
		self.filehandler.setFormatter(self.formatter)
		self.addHandler(self.filehandler)
		self.filehandler.doRollover()

	def onFileLog(self, value):
		if value:
			self.addRotatingFileHandler()
		elif self.filehandler is not None:
			self.removeHandler(self.filehandler)
			self.filehandler.close()
			self.filehandler = None
		return value

	def onFilename(self, value):
		if filelog.get():
			self.addRotatingFileHandler(value)
		return value

	def defineUserInterface(self):
		self.container = uidata.Container(self.name.split('.')[-1] + ' Logging')

		levelnames = self.getLevelNames()
		self.loglevelselect = uidata.SingleSelectFromList('Level', levelnames, 0,
													persist=True, tooltip='Level at which to log events')
		self.loglevelselect.setCallback(self.onLevelSelect)
		self.onLevelSelect(0)
		self.container.addObject(self.loglevelselect,
															position={'position': (0, 1), 'span': (2, 1)})

		self.propagateflag = uidata.Boolean('Propagate', False, 'rw',
																		callback=self.onPropagate, persist=True,
																		tooltip='If the log event is not handled,'
																			+ ' propagate it up to the parent logger')
		self.container.addObject(self.propagateflag, position={'position': (0, 0)})

		self.printlog = uidata.Boolean('Print', False, 'rw',
																		callback=self.onPrintLog, persist=True,
															tooltip='Print log events to the standard output')
		self.container.addObject(self.printlog, position={'position': (1, 0)})

		filename = os.path.join('log', self.name + '.log')
		self.filename = uidata.String('Filename', filename, 'rw', persist=True,
																	tooltip='Filename to write log events to')
		self.filelog = uidata.Boolean('File', False, 'rw', persist=True,
																	tooltip='Write log events to a file')
		self.filename.setCallback(self.onFilename)
		self.filelog.setCallback(self.onFileLog)
		self.container.addObject(self.filelog, position={'position': (2, 0)})
		self.container.addObject(self.filename, position={'position': (2, 1)})

logging.setLoggerClass(Logger)

def getLogger(name, parentname=None):
	if parentname is not None:
		name = parentname + '.' + name
	return logging.getLogger(name)

