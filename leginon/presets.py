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

	def getPresetsFromDB(self, session=None):
		'''
		get list of presets for this session from DB
		and use them to create self.presets list
		'''
		if session is None:
			session = self.session
		### get presets from database
		print 'SESSION'
		print session
		pdata = data.PresetData(session=session)
		print 'PDATA'
		print pdata
		presets = self.research(datainstance=pdata)
		print 'PRESETS'
		print presets

		### only want most recent of each name
		mostrecent = []
		names = []
		for preset in presets:
			if preset['name'] not in names:
				mostrecent.append(preset)
				names.append(preset['name'])
		print 'NAMES'
		print names
		self.setPresets(mostrecent)

	def presetToDB(self, presetdata):
		'''
		stores a preset in the DB under the current session name
		'''
		pdata = copy.copy(presetdata)
		pdata['session'] = self.session
		print 'PDATA'
		print pdata
		self.publish(pdata, database=True)

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
		p is either the index or item to insert at
		'''
		if type(p) is int:
			i = p
		else:
			i = self.index(p)
		self.presets.insert(i, newpreset)

	def removePreset(self, p):
		'''
		remove a preset by index or reference
		p is either a preset, or index of the preset
		'''
		if type(p) is int:
			del self.presets[p]
		else:
			self.presets.remove(p)

	def toScope(self, p):
		'''
		p is either index, preset, or name
		'''
		presetdata = None
		if type(p) is int:
			presetdata = self.presets[p]
		elif type(p) is str:
			for preset in self.presets:
				if p == preset['name']:
					presetdata = preset
					break
		elif isinstance(p, data.PresetData):
			presetdata = p
		else:
			print 'Bad arg for toScope'
			return

		if presetdata is None:
			print 'no such preset'
			return

		## should use AllEMData, but that is not working yet
		scopedata = data.ScopeEMData()
		cameradata = data.CameraEMData()
		scopedata.friendly_update(presetdata)
		cameradata.friendly_update(presetdata)
		scopedata['id'] = ('scope',)
		cameradata['id'] = ('camera',)
		self.publishRemote(scopedata)
		self.publishRemote(cameradata)

	def fromScope(self, name):
		'''
		create a new preset with name
		if a preset by this name already exists in my 
		list of managed presets, it will be replaced by the new one
		also returns the new preset object
		'''
		scopedata = self.researchByDataID(('scope',))
		cameradata = self.researchByDataID(('camera no image data',))
		newpreset = data.PresetData()
		newpreset.friendly_update(scopedata)
		newpreset.friendly_update(cameradata)
		newpreset['id'] = None
		newpreset['session'] = self.session
		newpreset['name'] = name

		for p in self.presets:
			if p['name'] == name:
				self.presets.remove(p)
				break
		self.presets.append(newpreset)

		print 'NEWPRESET'
		print newpreset
		self.presetToDB(newpreset)
		print 'inDB'
		pnames = self.presetNames()
		print 'PNAMES'
		print pnames
		self.uiselectpreset.set(pnames,[0])
		return newpreset

	def presetNames(self):
		print 'presetNames, presets'
		print self.presets
		names = [p['name'] for p in self.presets]
		return names

	def uiGetPresets(self):
		self.getPresetsFromDB()
		pnames = self.presetNames()
		print 'uiGetP PNAMES'
		print pnames
		self.uiselectpreset.set(pnames, [0])

	def uiToScope(self):
		sel = self.uiselectpreset.getSelectedValue()
		if sel:
			self.toScope(sel[0])
		else:
			print 'Select a preset name!'

	def uiSelectedFromScope(self):
		sel = self.uiselectpreset.getSelectedValue()
		if sel:
			newpreset = self.fromScope(sel[0])
		else:
			print 'Select a preset name!'

	def uiNewFromScope(self):
		newname = self.enteredname.get()
		if newname:
			newpreset = self.fromScope(newname)
		else:
			print 'Enter a preset name!'

	def uiSelectCallback(self, value):
		print 'VALUE'
		print value
		if value:
			index = value[0]
			self.current = self.presets[index]
			d = self.current.toDict(noNone=True)
			print 'D', d
			self.presetparams.set(d, callback=False)
		return value

	def uiParamsCallback(self, value):
		for key in value:
			self.current[key] = value[key]
		if self.current is None:
			return {}
		else:
			self.presetToDB(self.current)
			return self.current.toDict(noNone=True)

	def defineUserInterface(self):
		node.Node.defineUserInterface(self)

		self.uiselectpreset = uidata.UISelectFromList('Preset', [], [], 'r', callback=self.uiSelectCallback)

		getpresetsmethod = uidata.UIMethod('Get Presets', self.uiGetPresets)

		toscopemethod = uidata.UIMethod('To Scope', self.uiToScope)
		fromscopemethod = uidata.UIMethod('Selected From Scope', self.uiSelectedFromScope)

		self.enteredname = uidata.UIString('New Name', '', 'rw')
		newfromscopemethod = uidata.UIMethod('New From Scope', self.uiNewFromScope)

		self.presetparams = uidata.UIStruct('Parameters', {}, 'rw', self.uiParamsCallback)
		#self.presetparams.set(self.current, callback=False)


		container = uidata.UIMediumContainer('Presets Manager')
		container.addUIObjects((self.uiselectpreset, getpresetsmethod, toscopemethod, fromscopemethod, self.enteredname, newfromscopemethod, self.presetparams))
		self.uiserver.addUIObject(container)

		return



		toscopemethod = uidata.UIMethod('To Scope', self.uiRestore)
		toscopecontainer = uidata.UIContainer('Apply Preset')
		toscopecontainer.addUIObjects((self.uiselectpreset, getpresetsmethod, toscopemethod))



		self.selecteditpreset = uidata.UISelectFromList('Preset', self.managedPresets(), [], 'r')
		self.editpresetstruct = uidata.UIStruct('Preset Parameters', {}, 'rw')
		editcontainer = uidata.UIContainer('Edit Preset')
		editcontainer.addUIObjects((self.selecteditpreset,self.editpresetstruct))


		self.enteredname = uidata.UIString('Name', '', 'rw')
		self.enteredpos = uidata.UIInteger('Position', 0, 'rw')
		fromscope = uidata.UIMethod('Set Params From Scope', self.uiStoreCurrent)
		setpos = uidata.UIMethod('Set Position', self.uiStoreCurrent)

		updatecontainer = uidata.UIContainer('Update Preset')
		updatecontainer.addUIObjects((self.enteredname, self.enteredpos, fromscope, setpos))

		container = uidata.UIMediumContainer('Presets Manager')
		container.addUIObjects((toscopecontainer, fromscopecontainer))
		self.uiserver.addUIObject(container)


