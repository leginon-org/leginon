import node
import data
import event
import dbdatakeeper
import cPickle

class PresetsClient(object):
	'''
	methods for accessing presets in the database
	and for setting/getting a preset to/from the EM node
	'''
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
		emdata = data.EMData(('scope',), initializer=d)
		self.node.publishRemote(emdata)

	def fromScope(self, presetname):
		'''
		return a new PresetData object using the current scope/camera
		settings
		'''
		scopedata = self.node.researchByDataID(('scope',))
		cameradata = self.node.researchByDataID(('camera no image data',))
		## create new preset data
		p = data.PresetData(self.node.ID(), name=presetname)
		p.friendly_update(scopedata)
		p.friendly_update(cameradata)
		return p

	def UI(self):
		### this is just a start
		### will be similar to camerafuncs configUIData
		self.registerUIData()
		self.registerUIMethod()

class CircularIter(object):
	'''
	creates a circular iterator around an object that supports iteration
	'''
	def __init__(self, iterable):
		self.iterable = iterable
		self.iterator = iter(self.iterable)

	def next(self):
		try:
			return self.iterator.next()
		except StopIteration:
			self.iterator = iter(self.iterable)
			return self.iterator.next()

	def __iter__(self):
		return self


class PresetsManager(node.Node):
	def __init__(self, id, session, nodelocations, **kwargs):
		node.Node.__init__(self, id, session, nodelocations, **kwargs)

		self.presetsclient = PresetsClient(self)
		self.current = None
		self.presetdict = OrderedDict()
		self.presetcircle = CircularIter(self.presetdict)

		self.defineUserInterface()
		self.start()

	def getPresetNames(self, value=None):
		presets = self.presetsclient.retrievePresets()
		names = []
		for preset in presets:
			presetname = preset['name']
			if presetname not in names:
				names.append(presetname)
		return names

	def addToPresetList(self, presetdata):
		self.presetlist.append(presetdata)

	def defineUserInterface(self):
		nodespec = node.Node.defineUserInterface(self)

		presetchoices = self.registerUIData('presetchoices', 'array', callback=self.getPresetNames, permissions='r')
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
