import node
import data
import event
import datahandler
import cPickle
import copy

class StrictDict(dict):
	'''
	StrictDict(keys)
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

	def diff(self, other):
		return self.__diffValues(dict(self), dict(other))

	def __sub__(self, other):
		return self.diff(other)

	def significant(self):
		'''
		return copy of self with only the significant items
		'''
		pass

	def __equalKeys(self, keys1, keys2):
		if len(keys1) != len(keys2):
			return 0
		for key in keys1:
			if key not in keys2:
				return 0
		return 1

	def __nonzeroValues(self, value):
		'''
		return true if at least one nonzero item in value
		'''
		if isinstance(value, dict):
			#### dict objects
			for key, value in value.items():
				if self.__nonzeroValues(value):
					return 1
			return 0
		else:
			#### other objects
			if value:
				return 1
			else:
				return 0

	def __diffValues(self, value1, value2):
		try:
			diff = value1 - value2
		except TypeError:
			if type(value1) == type(value2) == dict:
				## dict subtraction
				if not self.__equalKeys(value1.keys(), value2.keys()):
					raise ValueError('keys are not same')
				diff = {}
				for key in value1:
					diff[key] = self.__diffValues(value1[key], value2[key])
			else:
				## don't know what to do with this type
				raise

		return diff

### most common allowed keys for PresetDict
PRESET_KEYS = (
	'spot size',
	'magnification',
	'image shift',
	'beam shift',
	'intensity',
	'defocus',

	'dimension',
	'binning',
	'offset',
	'exposure time'
)

class PresetDict(StrictDict):
	def __init__(self):
		StrictDict.__init__(self, PRESET_KEYS)


class PresetsClient(object):
	def __init__(self, node):
		self.node = node

	def getPreset(self, key):
		try:
			presetdata = self.node.researchByDataID('presets')
		except:
			print 'PresetClient unable to use presets.  Is a PresetsManager node running?'
			raise
		try:
			presetdict = presetdata.content[key]
			dictcopy = copy.deepcopy(presetdict)
			presetvalue = PresetDict()
			presetvalue.update(dictcopy)
		except KeyError:
			print '%s is not in presets' % (key,)
			raise
		return presetvalue

	def setPreset(self, key, presetdict):
		dictcopy = copy.deepcopy(dict(presetdict))
		newdict = {key: dictcopy}
		dat = data.PresetData('presets', newdict)
		self.node.publishRemote(dat)

	def toScope(self, presetdict):
		d = dict(presetdict)
		### this seems to work even if the preset contains camera keys
		emdata = data.EMData('scope', d)
		self.node.publishRemote(emdata)

	def fromScope(self):
		'''
		return a new preset 
		'''
		p = PresetDict()
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
			self.node.setPresets(idata.content)

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
