import node
import data
import event
import dbdatakeeper
import cPickle
import copy
import uidata
import camerafuncs
import strictdict
import threading


class PresetsClient(object):
	'''
	client functions for nodes to access PresetsManager
	'''
	def __init__(self, node):
		self.node = node
		self.node.addEventInput(event.PresetChangedEvent, self.presetchanged)
		self.pchanged = {}

	def toScope(self, presetname, emtarget=None):
		'''
		send the named preset to the scope
		optionally send a target to the scope as well
		'''
		self.pchanged[presetname] = threading.Event()
		evt = event.ChangePresetEvent()
		evt['name'] = presetname
		evt['emtarget'] = emtarget
		try:
			self.node.outputEvent(evt, wait=True, timeout=10)
		except node.ConfirmationTimeout:
			print 'no response from PresetsManager after 10s'

	def presetchanged(self, ievent):
		name = ievent['name']
		if name in self.pchanged:
			self.pchanged[name].set()
		self.node.confirmEvent(ievent)

	def getPresets(self):
		try:
			seqdata = self.node.researchByDataID(('presets',))
		except node.ResearchError:
			return []
		if seqdata is None:
			return []
		else:
			return seqdata['sequence']

	def getCurrentPreset(self):
		pdata = self.node.researchByDataID(('current preset',))
		return pdata

	def getPresetByName(self, pname):
		ps = self.getPresets()
		for p in ps:
			if p['name'] == pname:
				return p

	def uiPresetSelector(self):
		getpresets = uidata.Method('Get Names', self.uiGetPresetNames)
		self.uiselectpreset = uidata.SingleSelectFromList('Select Preset', [], 0)
		container = uidata.Container('Preset Selection')
		container.addObjects((getpresets, self.uiselectpreset))
		return container

	def uiGetPresetNames(self):
		presetlist = self.getPresets()
		pnames = [p['name'] for p in presetlist]
		self.uiselectpreset.set(pnames, 0) 

	def uiGetSelectedName(self):
		presetname = self.uiselectpreset.getSelectedValue()
		return presetname


class OLDPresetsClient(object):
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


class DataHandler(node.DataHandler):
	def query(self, id):
		if id == ('presets',):
			result = data.PresetSequenceData()
			result['sequence'] = self.node.presets
		elif id == ('current preset',):
			result = self.node.currentpreset
		else:
			result = node.DataHandler.query(self, id)
		return result


class PresetsManager(node.Node):
	def __init__(self, id, session, nodelocations, **kwargs):
		node.Node.__init__(self, id, session, nodelocations, datahandler=DataHandler, **kwargs)

		self.addEventInput(event.ChangePresetEvent, self.changePreset)
		self.addEventOutput(event.PresetChangedEvent)

		ids = [('presets',), ('current preset',)]
		e = event.ListPublishEvent(idlist=ids)
		self.outputEvent(e)

		self.currentselection = None
		self.currentpreset = None
		self.presets = []
		self.circle = CircularIter(self.presets)
		self.getPresetsFromDB()

		self.defineUserInterface()
		self.start()

	def changePreset(self, ievent):
		'''
		callback for received PresetChangeEvent from client
		'''
		pname = ievent['name']
		emtarget = ievent['emtarget']
		if emtarget is None:
			print 'ToScope'
			self.toScope(pname)
		else:
			print 'targetToScope'
			self.targetToScope(pname, emtarget)
		self.confirmEvent(ievent)
		print 'Preset changed to %s' % (pname,)

	def getPresetsFromDB(self, session=None):
		'''
		get list of presets for this session from DB
		and use them to create self.presets list
		'''
		if session is None:
			session = self.session
			diffsession = False
		else:
			## importing another sessions presets
			diffsession = True

		### get presets from database
		pdata = data.PresetData(session=session)
		presets = self.research(datainstance=pdata)

		### only want most recent of each name
		mostrecent = []
		names = []
		for preset in presets:
			if preset['name'] not in names:
				names.append(preset['name'])
				if preset['removed'] != 1:
					preset['session'] = self.session
					mostrecent.append(preset)
		self.presets[:] = mostrecent

		### if using another session's presets, now save them
		### as this sessions presets
		if diffsession:
			self.presetToDB()

	def presetToDB(self, presetdata=None):
		'''
		stores a preset in the DB under the current session name
		if no preset is specified, store all self.presets
		'''
		if presetdata is None:
			tostore = self.presets
		else:
			tostore = [presetdata]
		for p in tostore:
			pdata = copy.copy(p)
			pdata['session'] = self.session
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
		premove = None
		if type(p) is int:
			premove = self.presets[p]
			del self.presets[p]
		elif type(p) is str:
			pcopy = list(self.presets)
			for preset in pcopy:
				if preset['name'] == p:
					premove = preset
					self.presets.remove(preset)
		else:
			premove = p
			self.presets.remove(p)
		if premove is not None:
			premove['removed'] = 1
			self.presetToDB(premove)
		pnames = self.presetNames()
		self.uiselectpreset.set(pnames, 0)

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

		name = presetdata['name']

		print 'changing to preset %s' % (name,)

		## should use AllEMData, but that is not working yet
		scopedata = data.ScopeEMData()
		cameradata = data.CameraEMData()
		scopedata.friendly_update(presetdata)
		cameradata.friendly_update(presetdata)
		scopedata['id'] = ('scope',)
		cameradata['id'] = ('camera',)
		try:
			self.publishRemote(scopedata)
			self.publishRemote(cameradata)
		except node.PublishError:
			self.printException()
			print '** Maybe EM is not running?'
		else:
			self.currentpreset = presetdata
			self.outputEvent(event.PresetChangedEvent(name=name))
			print 'preset changed to %s' % (name,)

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

		self.presetToDB(newpreset)
		pnames = self.presetNames()
		self.uiselectpreset.set(pnames, len(pnames)-1)
		return newpreset



	def presetNames(self):
		names = [p['name'] for p in self.presets]
		return names

	def uiGetPresetsFromDB(self):
		othersession = self.othersession.get()
		self.getPresetsFromDB(othersession)
		names = self.presetNames()
		self.uiselectpreset.set(names, 0)

	def uiToScope(self):
		sel = self.uiselectpreset.getSelectedValue()
		self.toScope(sel)

	def uiSelectedFromScope(self):
		sel = self.uiselectpreset.getSelectedValue()
		newpreset = self.fromScope(sel)

	def uiSelectedRemove(self):
		sel = self.uiselectpreset.getSelectedValue()
		self.removePreset(sel)

	def uiNewFromScope(self):
		newname = self.enteredname.get()
		if newname:
			newpreset = self.fromScope(newname)
			d = newpreset.toDict(noNone=True)
			self.presetparams.set(d, callback=False)
		else:
			print 'Enter a preset name!'

	def uiSelectCallback(self, index):
		print 'INDEX', index
		try:
			self.currentselection = self.presets[index]
		except IndexError:
			self.currentselection = None
		else:
			d = self.currentselection.toDict(noNone=True)
			self.presetparams.set(d, callback=False)
		return index

	def uiParamsCallback(self, value):
		if (self.currentselection is None) or (not value):
			return {}
		else:
			if self.autosquare.get():
				for autokey in ('dimension','binning','offset'):
					self.square(value[autokey])
			for key in value:
				self.currentselection[key] = value[key]
			self.presetToDB(self.currentselection)
			d = self.currentselection.toDict(noNone=True)
			del d['session']
		return d

	def square(self, xydict):
		xydict['y'] = xydict['x']

	def defineUserInterface(self):
		node.Node.defineUserInterface(self)

		self.othersession = uidata.String('Session', '', 'rw')
		fromdb = uidata.Method('Import', self.uiGetPresetsFromDB)

		self.autosquare = uidata.Boolean('Auto Square', True, 'rw')
		self.presetparams = uidata.Struct('Parameters', {}, 'rw', self.uiParamsCallback)
		self.uiselectpreset = uidata.SingleSelectFromList('Preset', [], 0, callback=self.uiSelectCallback)
		pnames = self.presetNames()
		self.uiselectpreset.set(pnames, 0)

		toscopemethod = uidata.Method('To Scope', self.uiToScope)
		fromscopemethod = uidata.Method('Selected From Scope', self.uiSelectedFromScope)
		removemethod = uidata.Method('Remove Selected', self.uiSelectedRemove)

		self.enteredname = uidata.String('New Name', '', 'rw')
		newfromscopemethod = uidata.Method('New From Scope', self.uiNewFromScope)

		container = uidata.MediumContainer('Presets Manager')
		container.addObjects((self.othersession, fromdb, self.uiselectpreset, toscopemethod, fromscopemethod, removemethod, self.enteredname, newfromscopemethod, self.autosquare, self.presetparams))
		self.uiserver.addObject(container)

		return

	def targetToScope(self, newpresetname, emtargetdata):
		'''
		This is like toScope, but this one is mainly called
		by client nodes which request that presets and targets
		be tightly coupled.
		'''
		emdata = emtargetdata['scope']
		## XXX this might be dangerous:  I'm taking the original target
		## preset and using it's name to get the PresetManager's preset
		## by that same name
		oldpreset = self.presetByName(emtargetdata['preset']['name'])
		newpreset = self.presetByName(newpresetname)

		scopedata = data.ScopeEMData(id=('scope',), initializer=emdata)

		# remove influence of old preset from emdata
		scopedata['image shift']['x'] -= oldpreset['image shift']['x']
		scopedata['image shift']['y'] -= oldpreset['image shift']['y']

		# add influence of new preset
		newishift = {}
		newishift['x'] = scopedata['image shift']['x'] + newpreset['image shift']['x']
		newishift['y'] = scopedata['image shift']['y'] + newpreset['image shift']['y']

		## should use AllEMData, but that is not working yet
		scopedata.friendly_update(newpreset)
		scopedata['image shift'] = newishift
		cameradata = data.CameraEMData()
		cameradata.friendly_update(newpreset)

		cameradata['id'] = ('camera',)
		scopedata['id'] = ('scope',)

		try:
			self.publishRemote(scopedata)
			self.publishRemote(cameradata)
		except node.PublishError:
			self.printException()
			print '** Maybe EM is not running?'
		else:
			name = newpreset['name']
			self.currentpreset = newpreset
			self.outputEvent(event.PresetChangedEvent(name=name))
