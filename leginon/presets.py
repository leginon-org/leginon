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
		print 'XXXXXXXXXXXX'
		self.pchanged[presetname] = threading.Event()
		print 'YYYYYYYYYYYYY'
		evt = event.ChangePresetEvent()
		print 'ZZZZZZZZZZZZ'
		evt['name'] = presetname
		print 'WWWWWWWWWWWWW'
		evt['emtarget'] = emtarget
		print 'ouputEvent', evt
		self.node.outputEvent(evt, wait=True, timeout=10)
		print 'outputEvent done'
		#print 'waiting for preset %s to be set' % (presetname,)
		#self.pchanged[presetname].wait(10)

	def presetchanged(self, ievent):
		print 'IEVENT', ievent
		name = ievent['name']
		if name in self.pchanged:
			self.pchanged[name].set()
		self.node.confirmEvent(ievent)

	def getPresets(self):
		seqdata = self.node.researchByDataID(('presets',))
		if seqdata is None:
			return []
		else:
			return seqdata['sequence']

	def getCurrentPreset(self):
		pdata = self.node.researchByDataID(('current preset',))
		return pdata


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


class DataHandler(node.DataHandler):
	def query(self, id):
		if id == ('presets',):
			self.lock.acquire()
			result = data.PresetSequenceData()
			result['sequence'] = self.node.presets
			self.lock.release()
		elif id == ('current preset',):
			self.lock.acquire()
			result = self.currentpreset
			self.lock.release()
		else:
			result = node.DataHandler.query(self, id)
		return result


class PresetsManager(node.Node):
	def __init__(self, id, session, nodelocations, **kwargs):
		node.Node.__init__(self, id, session, nodelocations, datahandler=DataHandler, **kwargs)

		self.addEventInput(event.ChangePresetEvent, self.changePreset)
		self.addEventOutput(event.PresetChangedEvent)

		ids = [('presets',)]
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
			self.toScope(pname)
		else:
			self.targetToScope(pname, emtarget)
		self.confirmEvent(ievent)

	def getPresetsFromDB(self, session=None):
		'''
		get list of presets for this session from DB
		and use them to create self.presets list
		'''
		if session is None:
			session = self.session
		### get presets from database
		pdata = data.PresetData(session=session)
		presets = self.research(datainstance=pdata)

		### only want most recent of each name
		mostrecent = []
		names = []
		for preset in presets:
			if preset['name'] not in names:
				mostrecent.append(preset)
				names.append(preset['name'])
		self.presets[:] = mostrecent

	def presetToDB(self, presetdata):
		'''
		stores a preset in the DB under the current session name
		'''
		pdata = copy.copy(presetdata)
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
		try:
			self.publishRemote(scopedata)
			self.publishRemote(cameradata)
		except node.PublishError:
			self.printException()
			print '** Maybe EM is not running?'
		else:
			name = presetdata['name']
			self.currentpreset = presetdata
			self.outputEvent(event.PresetChangedEvent(name=name))

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
		self.uiselectpreset.set(pnames,[0])
		return newpreset

	def presetNames(self):
		names = [p['name'] for p in self.presets]
		return names

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
			d = newpreset.toDict(noNone=True)
			self.presetparams.set(d, callback=False)
		else:
			print 'Enter a preset name!'

	def uiSelectCallback(self, value):
		if value:
			try:
				index = value[0]
			except IndexError:
				self.currentselection = None
			else:
				try:
					self.currentselection = self.presets[index]
				except IndexError:
					self.currentselection = None
				else:
					d = self.currentselection.toDict(noNone=True)
					self.presetparams.set(d, callback=False)
		return value

	def uiParamsCallback(self, value):
		for key in value:
			self.currentselection[key] = value[key]
		if self.currentselection is None:
			return {}
		else:
			self.presetToDB(self.currentselection)
			d = self.currentselection.toDict(noNone=True)
			del d['session']
			return d

	def defineUserInterface(self):
		node.Node.defineUserInterface(self)

		self.presetparams = uidata.UIStruct('Parameters', {}, 'rw', self.uiParamsCallback)
		self.uiselectpreset = uidata.UISelectFromList('Preset', [], [], 'r', callback=self.uiSelectCallback)
		pnames = self.presetNames()
		self.uiselectpreset.set(pnames,[0])

		toscopemethod = uidata.UIMethod('To Scope', self.uiToScope)
		fromscopemethod = uidata.UIMethod('Selected From Scope', self.uiSelectedFromScope)

		self.enteredname = uidata.UIString('New Name', '', 'rw')
		newfromscopemethod = uidata.UIMethod('New From Scope', self.uiNewFromScope)

		container = uidata.UIMediumContainer('Presets Manager')
		container.addUIObjects((self.uiselectpreset, toscopemethod, fromscopemethod, self.enteredname, newfromscopemethod, self.presetparams))
		self.uiserver.addUIObject(container)

		return

	def targetToScope(self, newpresetname, emtargetdata):
		'''
		This is like toScope, but this one is mainly called
		by client nodes which request that presets and targets
		be tightly coupled.
		'''
		emdata = emtargetdata['scope']
		oldpreset = self.presetFromName(emtargetdata['preset'])
		newpreset = self.presetFromName(newpresetname)

		newemdata = data.ScopeEMData(id=('scope',), initializer=emdata)

		# remove influence of old preset from emdata
		newemdata['image shift']['x'] -= oldpreset['image shift']['x']
		newemdata['image shift']['y'] -= oldpreset['image shift']['y']

		# add influence of new preset
		newishift = {}
		newishift['x'] = newemdata['image shift']['x'] + newpreset['image shift']['x']
		newishift['y'] = newemdata['image shift']['y'] + newpreset['image shift']['y']

		newemdata.update(newpreset)
		newemdata['image shift'] = newishift

		## should use AllEMData, but that is not working yet
		cameradata = data.CameraEMData()
		cameradata.friendly_update(presetdata)
		cameradata['id'] = ('camera',)

		try:
			self.publishRemote(newemdata)
			self.publishRemote(cameradata)
		except node.PublishError:
			self.printException()
			print '** Maybe EM is not running?'
		else:
			name = presetdata['name']
			self.currentpreset = newpreset
			self.outputEvent(event.PresetChangedEvent(name=name))
