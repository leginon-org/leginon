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

	def retrievePresets(self, presetname=None, session=None):
		'''
		Returns a list of PresetData instances.
		if session is not specified, use this node's session
		if presetname is not specified, return all.
		'''
		query = {}
		if presetname is not None:
			query['name'] = presetname
		if session is not None:
			query['session'] = session
		# now default will be get all sessions
		#else:
		#	query['session'] = self.node.session
			
		presetdatalist = self.node.research(dataclass=data.PresetData, **query)
		return presetdatalist

	def storePreset(self, presetdata):
		# should work
		print 'PRESETDATA'
		print presetdata
		self.node.publish(presetdata, database=True)

	def toScope(self, presetdata):
		'''
		push a PresetData object to the scope/camera
		'''
		d = dict(presetdata)
		### this seems to work even if the preset contains camera keys
		emdata = data.EMData(('scope',), em=d)
		self.node.publishRemote(emdata)

	def fromScope(self, presetname):
		'''
		return a new PresetData object using the current scope/camera
		settings
		'''
		scope = self.node.researchByDataID(('scope',))
		camera = self.node.researchByDataID(('camera no image data',))
		scopedict = scope['em']
		cameradict = camera['em']

		## create new preset data
		p = data.PresetData(self.node.ID(), name=presetname)
		p.friendly_update(scopedict)
		p.friendly_update(cameradict)
		return p


class DataHandler(datahandler.DataBinder):
	def __init__(self, id, session, node):
		datahandler.DataBinder.__init__(self, id, session)
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

	_insert = insert

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

		ids = [('presets',),]
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

	def getSessionPresetNames(self, value=None):
		presets = self.presetsclient.retrievePresets()
		names = []
		for preset in presets:
			names.append(preset['name'])
		return names

	def defineUserInterface(self):
		nodespec = node.Node.defineUserInterface(self)

		presetchoices = self.registerUIData('presetchoices', 'array', callback=self.getSessionPresetNames, permissions='r')
		presetname = self.registerUIData('Name', 'string', choices=presetchoices)
		store = self.registerUIMethod(self.uiStoreCurrent, 'From Scope', (presetname,))
		restore = self.registerUIMethod(self.uiRestore, 'To Scope', (presetname,))

		test = self.registerUIContainer('Test', (store, restore))

		myspec = self.registerUISpec('Presets Manager', (test,))
		myspec += nodespec
		return myspec

	def uiStoreCurrent(self, presetname):
		presetdata = self.presetsclient.fromScope(presetname)
		self.presetsclient.storePreset(presetdata)
		return ''

	def uiRestore(self, presetname):
		presetlist = self.presetsclient.retrievePresets(presetname)
		presetdata = presetlist[0]
		self.presetsclient.toScope(presetdata)
		return ''
