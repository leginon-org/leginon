import node
import data
import event
import cPickle
import datahandler

class DataHandler(datahandler.DataBinder):
	def __init__(self, id, calnode):
		datahandler.DataBinder.__init__(self, id)
		self.calnode = calnode

	def query(self, id):
		cal = self.calnode.getCalibration()
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
			raise InvalidEventError('eventclass must be Event subclass')

class CalibrationLibrary(node.Node):
	def __init__(self, id, nodelocations, **kwargs):
		node.Node.__init__(self, id, nodelocations, DataHandler, (self,), **kwargs)
		ids = ['calibrations',]
		e = event.ListPublishEvent(self.ID(), ids)
		self.outputEvent(e)
		self.defineUserInterface()
		self.start()

	def getCalibration(self):
		try:
			f = open('CAL', 'r')
			cal = cPickle.load(f)
			f.close()
		except IOError:
			cal = {}

		return cal

	def setCalibration(self, idata):
		cal = self.getCalibration()
		newdict = idata.content
		cal.update(newdict)
		## should make a backup before doing this
		f = open('CAL', 'w')
		cPickle.dump(cal, f, 1)
		f.close()

	def defineUserInterface(self):
		nodespec = node.Node.defineUserInterface(self)
		self.registerUISpec('Calibration Library', (nodespec,))


