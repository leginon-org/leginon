#!/usr/bin/env python

import data

class DataStorage(object):
	def __init__(self):
		pass

	def classname(self, idata):
		dataclass = idata.__class__
		dataclassname = dataclass.__name__
		return dataclassname

	def retrieve(self, dataclass, dataid):
		raise NotImplementedError()

	def store(self, datainstance):
		raise NotImplementedError()
	

class PickleStorage(Storage):
	def __init__(self):
		Storage.__init__(self)
		self.filename = None

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
		self.filename = self.classname(idata)
		cal = self.get()

		newitem = idata.content
		key = idata.id

		cal[key] = newitem
		## should make a backup before doing this
		f = open(self.filename, 'wb')
		cPickle.dump(cal, f, 1)
		f.close()

	def get(self, idata):
		try:
			f = open(self.filename, 'rb')
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

	def getIDs(self):
		try:
			return self.cal.keys()
		except:
			return ()

	def set(self, idata):
		newitem = idata.content
		id = idata.id
		cal = sqlbindict.SQLBinDict('CAL')
		self.cal[id] = newitem

	def get(self, id=None):
		if id is None:
			# return whole table as a dictionary
			content = cal
		else:
			# return just the specified key
			try:
				cal = sqlbindict.SQLBinDict('CAL')
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


if __name__ == '__main__':
	ps = PickleStorage()
	
	## how to store some data
	example = data.MatrixCalibrationData.EXAMPLE
	d = data.MatrixCalibrationData((mag, type), **example)
	ps.set(d)

	## how to retrieve some data
	dclass = data.MatrixCalibrationData
	id = (mag, type)
	ps.get(dclass, id)
