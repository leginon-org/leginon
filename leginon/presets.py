import node
import data
import event
import dbdatakeeper
import cPickle
import copy
import uidata
import camerafuncs
import strictdict

class PresetsClient(object):
	'''
	methods for accessing presets in the database
	and using presets manager
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
		emdata = data.ScopeEMData(('scope',), initializer=d)
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
		self.setPresets([])

		self.defineUserInterface()
		self.start()

	def setPresets(self, presetlist):
		'''
		initializes my current list of presets, in proper order
		also initializes my circular iterator
		'''
		self.presets = list(presetlist)
		self.circle = CircularIter(self.presets)

	def getSessionPresets(self):
		'''
		get list of presets for this session
		'''
		### get presets from database
		pdata = data.PresetData(('dummy',), session=self['session'])
		pdata['id'] = None
		presets = self.research(pdata)

		### only want most recent of each name
		recent = strictdict.OrderedDict()
		for preset in presets:
			if preset['name'] not in recent:
				recent[preset['name'] = preset
		return recent

	def presetByName(self, name):
		for p in self.presets:
			if p['name'] == name:
				return p
		return None

	def indexByName(self, name):
		i = 0
		for p in self.presets:
			if p['name'] == name:
				return i
			i += 1
		return None

	def indexByPreset(self, preset):
		return self.presets.index(preset)

	def insertPreset(self, p, newpreset):
		'''
		insert new preset into my set of managed presets
		'''
		if type(p) is int:
			i = p
		else:
			i = self.index
		self.presets.insert(position, newpreset)

	def removePreset(self, p):
		'''
		remove a preset by index or reference
		'''
		if type(p) is int:
			del self.presets[p]
		else:
			self.presets.remove(p)

	def presetNames(self):
		names = [p['name'] for p in self.presets]
		return names

	def newPreset(self, name, position):
		

	def defineUserInterface(self):
		node.Node.defineUserInterface(self)
		self.uiselectpreset = uidata.UISelectFromList('Preset', [], [], 'r')
		self.uiGetPresets()
		getpresetsmethod = uidata.UIMethod('Get Presets', self.uiGetPresets)
		toscopemethod = uidata.UIMethod('To Scope', self.uiRestore)
		toscopecontainer = uidata.UIContainer('Apply Preset')
		toscopecontainer.addUIObjects((self.uiselectpreset, getpresetsmethod, toscopemethod))



		self.selecteditpreset = uidata.UISelectFromList('Preset', self.managedPresets(), [], 'r')
		self.editpresetstruct = uidata.UIStruct('Preset Parameters', {}, 'rw')
		editcontainer = uidata.UIContainer('Edit Preset')
		editcontainer.addUIObjects((,))


		self.enteredname = uidata.UIString('Name', '', 'rw')
		self.enteredpos = uidata.UIInteger('Position', 0, 'rw')
		fromscope = uidata.UIMethod('Set Params From Scope', self.uiStoreCurrent)
		setpos = uidata.UIMethod('Set Position', self.uiStoreCurrent)

		updatecontainer = uidata.UIContainer('Update Preset')
		updatecontainer.addUIObjects((self.enteredname, self.enteredpos, fromscope, setpos))

		container = uidata.UIMediumContainer('Presets Manager')
		container.addUIObjects((toscopecontainer, fromscopecontainer))
		self.uiserver.addUIObject(container)

	def NEWdefineUserInterface(self):
		node.Node.defineUserInterface(self)
		self.statestruct = uidata.UIStruct('Instrument State', {}, 'rw', self.uiCallback)
		self.statestruct.set(self.uistate, callback=False)
		unlockmethod = uidata.UIMethod('Unlock', self.uiUnlock)
		container = uidata.UIMediumContainer('EM')
		container.addUIObjects((self.statestruct, unlockmethod))
		self.uiserver.addUIObject(container)

	def managedPresets(self, value=None):
		'''
		get and set the list of managed presets for this session
		'''
		if value is not None:
			self.managedpresets = value
		return self.managedpresets

	def uiGetPresets(self):
		presetsnames = self.getPresetNames()
		if presetsnames:
			presetsnames.sort()
			selected = [0]
		else:
			selected = []
		self.uiselectpreset.set(presetsnames, selected)

	def uiStoreCurrent(self):
		presetname = self.uipresetname.get()
		presetdata = self.presetsclient.fromScope(presetname)
		self.presetsclient.storePreset(presetdata)
		self.uiGetPresets()

	def uiRestore(self):
		try:
			presetname = self.uiselectpreset.getSelectedValue()[0]
		except IndexError:
			self.printerror('no preset to send to instrument')
			return
		presetlist = self.presetsclient.retrievePresets(presetname)
		presetdata = presetlist[0]
		self.presetsclient.toScope(presetdata)

