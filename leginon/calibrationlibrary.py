import node
import data
import event
import cPickle
import datahandler
import sqlbindict

class DataHandler(datahandler.DataBinder):
	def __init__(self, id, calnode):
		datahandler.DataBinder.__init__(self, id)
		self.calnode = calnode

	def query(self, id):
#		print 'query ID', id
		if type(id) is str:
			key = None
		else:
			key = id[1]
		cal = self.calnode.getCalibration(key)
#		print 'CAL', cal
		result = data.CalibrationData(self.ID(), cal)
		return result

	def insert(self, idata):
		if isinstance(idata, event.Event):
			datahandler.DataBinder.insert(self, idata)
		else:
			key = idata.id[1]
			self.calnode.setCalibration(key, idata)

	# borrowed from NodeDataHandler
	def setBinding(self, eventclass, func):
		if issubclass(eventclass, event.Event):
			datahandler.DataBinder.setBinding(self, eventclass, func)
		else:
			raise InvalidEventError('eventclass must be Event subclass')

class CalibrationLibrary(node.Node):
	def __init__(self, id, nodelocations, **kwargs):
		node.Node.__init__(self, id, nodelocations, DataHandler, (self,), **kwargs)
		self.publishDataIDList()

	def publishDataIDList(self):
		# publish the ids that this node manages
		ids = [('calibrations',)]
		keys = self.getKeys()
		for key in keys:
			id = ('calibrations',key)
			ids.append(id)
		e = event.ListPublishEvent(self.ID(), ids)
		self.outputEvent(e)

	def getKeys(self):
		raise NotImplementedError()

	def setCalibration(self, key, idata):
		'''
		should call self.publishDataIDList() if updated
		'''
		raise NotImplementedError()

	def getCalibration(self, key=None):
		raise NotImplementedError()


class PickleCalibrationLibrary(CalibrationLibrary):
	def __init__(self, id, nodelocations, **kwargs):
		CalibrationLibrary.__init__(self, id, nodelocations, **kwargs)
		self.defineUserInterface()


		self.start()

	def getKeys(self):
		try:
			f = open('CAL', 'rb')
			cal = cPickle.load(f)
			f.close()
			return cal.keys()
		except:
			self.printerror('cannot open calibration file')
			return ()

	def setCalibration(self, key, idata):
		cal = self.getCalibration()
		newitem = idata.content
		cal[key] = newitem
		## should make a backup before doing this
		f = open('CAL', 'wb')
		cPickle.dump(cal, f, 1)
		f.close()
		self.publishDataIDList()

	def getCalibration(self, key=None):
		try:
			f = open('CAL', 'rb')
			cal = cPickle.load(f)
			f.close()
		except IOError:
			cal = {}

		if key is None:
			# return whole thing
			return cal
		else:
			# return just the specified key
			try:
				return cal[key]
			except KeyError:
				return None

	def defineUserInterface(self):
		nodespec = CalibrationLibrary.defineUserInterface(self)
		self.registerUISpec('Pickle Calibration Library', (nodespec,))

class DBCalibrationLibrary(CalibrationLibrary):
	def __init__(self, id, nodelocation, **kwargs):
		CalibrationLibrary.__init__(self, id, nodelocations, **kwargs)
		self.defineUserInterface()


		self.start()

	def getKeys(self):
		try:
			cal = sqlbindict.SQLBinDict('CAL')
			return cal.keys()
		except:
			return ()

	def setCalibration(self, key, idata):
		cal = self.getCalibration()
		newitem = idata.content
		cal[key] = newitem
		self.publishDataIDList()

	def getCalibration(self, key=None):
		try:
			cal = sqlbindict.SQLBinDict('CAL')
		except:
			cal = {}

		if key is None:
			# return whole table as a dictionary
			return cal
		else:
			# return just the specified key
			try:
				return cal[key]
			except KeyError:
				return None

	def defineUserInterface(self):
		nodespec = CalibrationLibrary.defineUserInterface(self)
		self.registerUISpec('DB Calibration Library', (nodespec,))
