import node
import data
import event
import cPickle
import datahandler
import dbdatakeeper
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
			self.calnode.setCalibration(idata)

	# borrowed from NodeDataHandler
	def setBinding(self, eventclass, func):
		if issubclass(eventclass, event.Event):
			datahandler.DataBinder.setBinding(self, eventclass, func)
		else:
			raise event.InvalidEventError('eventclass must be Event subclass')


class CalibrationLibrary(node.Node):
	def __init__(self, id, nodelocations, **kwargs):
		node.Node.__init__(self, id, nodelocations,
					[(DataHandler, (self,)), (dbdatakeeper.DBDataKeeper, ())], **kwargs)
		self.storagedict = {
			'pickle': PickleStorage(),
			'db': DBStorage()
		}
		self.storagelist = [
			'db',
			'pickle'
		]
		self.publishDataIDList()

	def publishDataIDList(self):
		# publish the ids that this node manages
		ids = [('calibration',)]
		for value in self.storagedict.values():
			storageids = value.getIDs()
			for id in storageids:
				if id not in ids:
					ids.append(id)

		e = event.ListPublishEvent(self.ID(), ids)
		self.outputEvent(e)

	def setCalibration(self, idata):
		'''
		should call self.publishDataIDList() if updated
		'''
		## chose where to store data
		for key,value in self.storagedict.items():
			print 'storing in %s' % (key,)
			value.set(idata)
		self.publishDataIDList()

	def getCalibration(self, id, storage=None):
		if storage is not None:
			caldata = self.storagedict[storage].get(id)
		else:
			for key in self.storagelist:
				caldata = self.storagedict[key].get(id)
				if caldata is not None:
					break


class CalibrationStorage(object):
	def __init__(self):
		pass

class PickleStorage(CalibrationStorage):
	def __init__(self):
		CalibrationStorage.__init__(self)

	def getIDs(self):
		try:
			f = open('CAL', 'rb')
			cal = cPickle.load(f)
			f.close()
			return cal.keys()
		except:
			self.printerror('cannot open calibration file')
			return ()

	def set(self, idata):
		cal = self.get()

		newitem = idata.content
		key = idata.id

		cal[key] = newitem
		## should make a backup before doing this
		f = open('CAL', 'wb')
		cPickle.dump(cal, f, 1)
		f.close()

	def get(self, id=None):
		try:
			f = open('CAL', 'rb')
			cal = cPickle.load(f)
			f.close()
		except IOError:
			cal = {}

		if id is None:
			# return whole thing
			content = cal
		else:
			# return just the specified key
			try:
				content = cal[id]
			except KeyError:
				content = None
		return data.CalibrationData(id, content)


class BinaryDBStorage(CalibrationStorage):
	def __init__(self):
		CalibrationStorage.__init__(self)
		self.cal = sqlbindict.SQLBinDict('CAL')

	def getIDs(self):
		try:
			return self.cal.keys()
		except:
			return ()

	def set(self, idata):
		newitem = idata.content
		id = idata.id
		self.cal[id] = newitem

	def get(self, id=None):
		if id is None:
			# return whole table as a dictionary
			content = cal
		else:
			# return just the specified key
			try:
				content = cal[id]
			except KeyError:
				content = None


class DBStorage(CalibrationStorage):
	def __init__(self):
		CalibrationStorage.__init__(self)
		#self.cal = sqlbindict.SQLBinDict('CAL')

	def getIDs(self):
		try:
			return self.cal.keys()
		except:
			return ()

	def set(self, idata):
		newitem = idata.content
		id = idata.id
		self.cal[id] = newitem

	def get(self, id=None):
		if id is None:
			# return whole table as a dictionary
			content = cal
		else:
			# return just the specified key
			try:
				content = cal[id]
			except KeyError:
				content = None
