import logging
import logging.handlers
import os
import sys
import time
import uidata

class Logger(object):
	def __init__(self, name, parentname=None):
		name = name
		if parentname is not None:
			name = parentname + '.' + name
		self.logger = logging.getLogger(name)
		self.name = name

		self.formatter = logging.Formatter(
				'%(asctime)s %(name)s %(module)s:%(lineno)d %(levelname)s %(message)s',
				'%H:%M:%S')
		self.formatter.converter = time.localtime

		self.handlers = {}
		self.handlers['Print'] = logging.StreamHandler(sys.stdout)
		self.handlers['Print'].setFormatter(self.formatter)

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
		level = logging._levelNames[value]
		self.logger.setLevel(level)
		return index

	def onPropagate(self, value):
		self.logger.propagate = value
		return value

	def onPrintLog(self, value):
		if value:
			self.logger.addHandler(self.handlers['Print'])
		else:
			self.logger.removeHandler(self.handlers['Print'])
		return value

	def addRotatingFileHandler(self, filename=None):
		if filename is None:
			filename = self.filename.get()
		elif filename == self.filename.get():
			return
		self.handlers['File'] = logging.handlers.RotatingFileHandler(filename,
																																backupCount=32)
		self.handlers['File'].setFormatter(self.formatter)
		self.logger.addHandler(self.handlers['File'])
		self.handlers['File'].doRollover()

	def onFileLog(self, value):
		if value:
			self.addRotatingFileHandler()
		else:
			try:
				self.logger.removeHandler(self.handlers['File'])
				self.handlers['File'].close()
				del self.handlers['File']
			except KeyError:
				pass
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
															position={'position': (0, 0), 'span': (2, 1)})

		self.propagate = uidata.Boolean('Propagate', False, 'rw',
																		callback=self.onPropagate, persist=True,
																		tooltip='If the log event is not handled,'
																			+ ' propagate it up to the parent logger')
		self.container.addObject(self.propagate, position={'position': (0, 1)})

		self.printlog = uidata.Boolean('Print', False, 'rw',
																		callback=self.onPrintLog, persist=True,
															tooltip='Print log events to the standard output')
		self.container.addObject(self.printlog, position={'position': (1, 1)})

		filename = os.path.join('log', self.name + '.log')
		self.filename = uidata.String('Filename', filename, 'rw', persist=True,
																	tooltip='Filename to write log events to')
		self.filelog = uidata.Boolean('File', False, 'rw', persist=True,
																	tooltip='Write log events to a file')
		self.filename.setCallback(self.onFilename)
		self.filelog.setCallback(self.onFileLog)
		self.container.addObject(self.filelog, position={'position': (2, 1)})
		self.container.addObject(self.filename, position={'position': (3, 1)})


# oops
	def setLevel(self, level):
		self.logger.setLevel(level)

	def debug(self, msg, *args, **kwargs):
		self.logger.debug(msg, *args, **kwargs)

	def info(self, msg, *args, **kwargs):
		self.logger.info(msg, *args, **kwargs)

	def warning(self, msg, *args, **kwargs):
		self.logger.warning(msg, *args, **kwargs)

	warn = warning

	def error(self, msg, *args, **kwargs):
		self.logger.error(msg, *args, **kwargs)

	def exception(self, msg, *args):
		self.logger.exception(msg, *args)

	def critical(self, msg, *args, **kwargs):
		self.logger.critical(msg, *args, **kwargs)

	fatal = critical

	def log(self, level, msg, *args, **kwargs):
		self.logger.log(level, msg, *args, **kwargs)

	def findCaller(self):
		self.logger.findCaller(self)

	def makeRecord(self, name, level, fn, lno, msg, args, exc_info):
		self.logger.makeRecord(name, level, fn, lno, msg, args, exc_info)

	def _log(self, level, msg, args, exc_info=None):
		self.logger._log(level, msg, args, exc_info=None)

	def handle(self, record):
		self.logger.handle(record)

	def addHandler(self, hdlr):
		self.logger.addHandler(hdlr)

	def removeHandler(self, hdlr):
		self.logger.removeHandler(hdlr)

	def callHandlers(self, record):
		self.logger.callHandlers(record)

	def getEffectiveLevel(self):
		self.logger.getEffectiveLevel()

	def isEnabledFor(self, level):
		self.logger.isEnabledFor(level)

