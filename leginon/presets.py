import node
import data
import event
import datahandler
import cPickle

class PresetDict(dict):
	'''
	PresetDict(keys)
	   keys - sequence of keys that are allowed in the dict

	Subclassed from dict, with the following differences:
	   - restricted to only keys specified at initialization
	   - keys() method returns keys in same order as initialized
	   - new method allowed_keys() returns all the allowed keys
	'''
	def __init__(self, keys):
		dict.__init__(self)
		self.__allowed = tuple(keys)

	def __setitem__(self, key, value):
		if key in self.__allowed:
			dict.__setitem__(self, key, value)

	def allowed_keys(self):
		return self.__allowed

	def keys(self):
		ordered = []
		actualkeys = dict.keys(self)
		for key in self.__allowed:
			if key in actualkeys:
				ordered.append(key)
		return ordered

	def update(self, obj):
		for key in obj.keys(): self[key] = obj[key]


### most common allowed keys for PresetDict
STANDARD_KEYS = (
	'spot size',
	'magnification',
	'image shift',
	'beam shift',
	'intensity',
	'defocus',
	'dimension',
	'binning',
	'exposure time'
)


class PresetsClient(object):
	def __init__(self, node, allowed_keys):
		self.node = node
		self.allowed_keys = allowed_keys

	def getPreset(self, key):
		try:
			presetdata = self.node.researchByDataID('presets')
		except:
			print 'PresetClient unable to use presets.  Is a PresetsManager node running?'
			raise
		try:
			presetvalue = presetdata.content[key]
		except KeyError:
			print '%s is not in presets' % (key,)
			raise
		return presetvalue

	def setPreset(self, key, presetdict):
		newdict = {key: presetdict}
		dat = data.PresetData('presets', newdict)
		self.node.publishRemote(dat)

	def toScope(self, presetdict):
		d = dict(presetdict)
		### this seems to work event if the preset contains camera keys
		emdata = data.EMData('scope', d)
		self.node.publishRemote(emdata)

	def fromScope(self):
		'''
		return a new preset 
		'''
		p = PresetDict(self.allowed_keys)
		scope = self.node.researchByDataID('scope')
		camera = self.node.researchByDataID('camera no image data')
		p.update(scope.content)
		p.update(camera.content)
		return p


class DataHandler(datahandler.DataBinder):
	def __init__(self, id, node):
		datahandler.DataBinder.__init__(self, id)
		self.node = node

	def query(self, id):
		cal = self.node.getPresets()
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
			raise InvalidEventError('eventclass must be Event subclass')


class PresetsManager(node.Node):
	def __init__(self, id, nodelocations, **kwargs):
		node.Node.__init__(self, id, nodelocations, DataHandler, (self,), **kwargs)

		ids = ['presets',]
		e = event.ListPublishEvent(self.ID(), ids)
		self.outputEvent(e)

		
		self.presetsclient = PresetsClient(self, STANDARD_KEYS)

		self.defineUserInterface()
		self.start()

	def getPresets(self):
		try:
			f = open('PRESETS', 'r')
			presets = cPickle.load(f)
			f.close()
		except IOError:
			print 'unable to open PRESETS'
			presets = {}
		except EOFError:
			print 'bad pickle in PRESETS'
			presets = {}
		return presets

	def setPresets(self, idata):
		presets = self.getPresets()
		newdict = idata.content
		presets.update(newdict)
		## should make a backup before doing this
		f = open('PRESETS', 'w')
		cPickle.dump(presets, f, 1)
		f.close()

	def defineUserInterface(self):
		nodespec = node.Node.defineUserInterface(self)

		presetname = self.registerUIData('Name', 'string')
		store = self.registerUIMethod(self.uiStoreCurrent, 'From Scope', (presetname,))
		restore = self.registerUIMethod(self.uiRestore, 'To Scope', (presetname,))

		test = self.registerUIContainer('Test', (store, restore))

		self.registerUISpec('Presets Manager', (test, nodespec))

	def uiStoreCurrent(self, name):
		preset = self.presetsclient.fromScope()
		self.presetsclient.setPreset(name, preset)
		return ''

	def uiRestore(self, name):
		preset = self.presetsclient.getPreset(name)
		self.presetsclient.toScope(preset)
		return ''
