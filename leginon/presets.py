import node
import data
import event
import datahandler
import dbdatakeeper
import cPickle
import copy

class PresetsClient(object):
	def __init__(self, node):
		self.node = node

	def getPreset(self, key):
		try:
			# needs to research new style
			presetdata = self.node.researchByDataID('presets')
		except:
			print 'PresetClient unable to use presets.  Is a PresetsManager node running?'
			raise
		try:
			## make a new PresetData from the stored version
			dictcopy = copy.deepcopy(presetdata)
			presetdata = data.PresetData(self.ID())
			presetdata.update(dictcopy)
		except KeyError:
			print '%s is not in presets' % (key,)
			raise
		return presetdata

	def setPreset(self, key, presetdict):
		dictcopy = copy.deepcopy(dict(presetdict))
		newdict = {key: dictcopy}
		# should work
		dat = data.PresetData('presets', newdict)
		self.node.publishRemote(dat)

	def toScope(self, presetdict):
		d = dict(presetdict)
		### this seems to work even if the preset contains camera keys
		emdata = data.EMData('scope', em=d)
		self.node.publishRemote(emdata)

	def fromScope(self):
		'''
		return a new preset 
		'''
		p = PresetData(self.ID())
		scope = self.node.researchByDataID('scope')
		camera = self.node.researchByDataID('camera no image data')
		#p.update(scope)
		#p.update(camera)
		for key in p:
			try:
				p[key] = scope[key]
			except KeyError:
				pass
			try:
				p[key] = camera[key]
			except KeyError:
				pass
		return p


class DataHandler(datahandler.DataBinder):
	def __init__(self, id, node):
		datahandler.DataBinder.__init__(self, id)
		self.node = node

	def query(self, id):
		cal = self.node.getPresets()
		# assume this is a dict
		result = data.PresetData(self.ID(), cal)
		return result

	def insert(self, idata):
		if isinstance(idata, event.Event):
			datahandler.DataBinder.insert(self, idata)
		else:
			self.node.setPresets(idata)

	# borrowed from NodeDataHandler
	def setBinding(self, eventclass, func):
		if issubclass(eventclass, event.Event):
			datahandler.DataBinder.setBinding(self, eventclass, func)
		else:
			raise event.InvalidEventError('eventclass must be Event subclass')


class PresetsManager(node.Node):
	def __init__(self, id, session, nodelocations, **kwargs):
		node.Node.__init__(self, id, session, nodelocations,
												[(DataHandler, (self,)),
													(dbdatakeeper.DBDataKeeper, ())], **kwargs)

		ids = ['presets',]
		e = event.ListPublishEvent(self.ID(), idlist=ids)
		self.outputEvent(e)
		
		self.presetsclient = PresetsClient(self)
		self.current = None

		self.defineUserInterface()
		self.start()

	def getPresets(self):
		try:
			f = open('PRESETS', 'rb')
			presetdict = cPickle.load(f)
			presetdict = copy.deepcopy(presetdict)
			f.close()
		except IOError:
			print 'unable to open PRESETS'
			presetdict = {}
		except EOFError:
			print 'bad pickle in PRESETS'
			presetdict = {}
		return presetdict

	def getPreset(self, name):
		presets = self.getPresets()
		return copy.deepcopy(presets[name])

	def setPreset(self, name, preset):
		newdict = {name: preset}
		self.setPresets(newdict)

	def setPresets(self, preset):
		presets = self.getPresets()
		presets.update(preset)
		## should make a backup before doing this
		f = open('PRESETS', 'wb')
		cPickle.dump(presets, f, 1)
		f.close()

	def defineUserInterface(self):
		nodespec = node.Node.defineUserInterface(self)

		presetname = self.registerUIData('Name', 'string')
		store = self.registerUIMethod(self.uiStoreCurrent, 'From Scope', (presetname,))
		restore = self.registerUIMethod(self.uiRestore, 'To Scope', (presetname,))

		test = self.registerUIContainer('Test', (store, restore))

		myspec = self.registerUISpec('Presets Manager', (test,))
		myspec += nodespec
		return myspec

	def uiStoreCurrent(self, name):
		preset = self.presetsclient.fromScope()
		## is this the problem
		presetdict = dict(preset)
		self.setPreset(name, presetdict)
		return ''

	def uiRestore(self, name):
		preset = self.getPreset(name)
		self.presetsclient.toScope(preset)
		return ''
