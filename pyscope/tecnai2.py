#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#
import sys
sys.coinit_flags = 0
import pythoncom
import win32com.client
import pywintypes
import tecnaicom
import ldcom
import adacom
import math

magnificationtable = [
	(0, 0), # place holder for index 0
	(21, 18.5),
	(28, 25),
	(38, 34),
	(56, 50),
	(75, 66),
	(97, 86),
	(120, 105),
	(170, 150),
	(220, 195),
	(330, 290),
	(420, 370),
	(550, 490),
	(800, 710),
	(1100, 970),
	(1500, 1350),
	(2100, 1850),
	(1700, 1500),
	(2500, 2200),
	(3500, 3100),
	(5000, 4400),
	(6500, 5800),
	(7800, 6900),
	(9600, 8500),
	(11500, 10000),
	(14500, 13000),
	(19000, 17000),
	(25000, 22000),
	(29000, 25500),
	(50000, 44000),
	(62000, 55000),
	(80000, 71000),
	(100000, 89000),
	(150000, 135000),
	(200000, 175000),
	(240000, 210000),
	(280000, 250000),
	(390000, 350000),
	(490000, 430000),
	(700000, 620000),
]

class Attribute(object):
	def __init__(self, name, type=None, ranges=[], values=[], unit=None,
								length=None):
		self.name = name
		self.type = type
		self.ranges = ranges
		self.values = values
		self.unit = unit
		self.length = length

		if self.hasGet():
			self.get = self._typeGet
		if self.hasSet():
			self.set = self._validateSet
		if self.hasCall():
			self.call = self._call

	def hasGet(self):
		return False

	def hasSet(self):
		return False

	def hasCall(self):
		return False

	def _typeGet(self, **kwargs):
		value = self._get(**kwargs)
		if self.type is not None:
			try:
				value = self.type(value)
			except:
				raise RuntimeError('Unable to convert internal get value to type %s' %
														self.type.__name__)
		return value

	def _validate(self, value, unit=None):
		if self.type is not None and not isinstance(value, self.type):
			raise TypeError('Type must be %s, type of value given is %s' %
											(self.type.__name__, value.__class__.__name__))

		for r in self.ranges:
			if value < r[0] or value > r[1]:
				raise ValueError('%s not in range' % (value,))

		if self.values and value not in self.values:
			raise ValueError('%s not a valid value' % (value,))

		if self.length is not None and len(value) > self.length:
			raise ValueError('Value exceeds maximun length')

	def _validateSet(self, value, **kwargs):
		self._validate(value, **kwargs)
		self._set(value, **kwargs)

	def _get(self, unit=None):
		raise NotImplementedError

	def _set(self, value, unit=None):
		raise NotImplementedError

	def _call(self, args=(), unit=None):
		raise NotImplementedError

class ValueAttribute(Attribute):
	def __init__(self, name, value, **kwargs):
		self.value = value
		Attribute.__init__(self, name, **kwargs)

	def hasGet(self):
		return True

	def hasSet(self):
		return True

	def _get(self):
		return self.value

	def _set(self, value):
		self.value = value

class COMAttribute(Attribute):
	def __init__(self, name, comobject, attribute, **kwargs):
		self.comobject = comobject
		self.attribute = attribute
		Attribute.__init__(self, name, **kwargs)

	def hasGet(self):
		return self.attribute in self.comobject._prop_map_get_

	def hasSet(self):
		return self.attribute in self.comobject._prop_map_put_

	def hasCall(self):
		if not self.hasGet() and not self.hasSet():
			if hasattr(self.comobject, self.attribute):
				return True
		return False

	def _get(self):
		return getattr(self.comobject, self.attribute)

	def _set(self, value):
		return setattr(self.comobject, self.attribute, value)

	def _call(self, args=()):
		if args is False:
			return
		if args is True:
			args = ()
		return getattr(self.comobject, self.attribute)(*args)

class MappedCOMAttribute(COMAttribute):
	def __init__(self, name, comobject, attribute, mapping, **kwargs):
		self.getmap = {}
		self.setmap = {}
		for key, value in mapping:
			self.getmap[key] = value
			self.setmap[value] = key
		COMAttribute.__init__(self, name, comobject, attribute, **kwargs)

	def _get(self):
		try:
			return self.getmap[COMAttribute._get(self)]
		except KeyError:
			#raise RuntimeError('Constant does not map to known value')
			return 'unknown'

	def _set(self, value):
		try:
			COMAttribute._set(self, self.setmap[value])
		except KeyError:
			raise ValueError('Invalid value %s' % value)

	def _call(self, args=()):
		if type(args) is not tuple:
			args = (args,)
		try:
			return COMAttribute._call(self, map(lambda v: self.setmap[v], args))
		except KeyError:
			raise ValueError('Invalid args %s' % (args,))

class ConstantMappedCOMAttribute(MappedCOMAttribute):
	def __init__(self, name, comobject, attribute, mapping,
								constants=win32com.client.constants, values=None):
		mapping = map(lambda (k, v): (getattr(constants, k), v), mapping)
		if values is None:
			values = map(lambda l: l[1], mapping)
		MappedCOMAttribute.__init__(self, name, comobject, attribute, mapping,
																type=str, values=values)

class MappedBooleanCOMAttribute(MappedCOMAttribute):
	def __init__(self, name, comobject, attribute, true, false):
		mapping = [(True, true), (False, false)]
		MappedCOMAttribute.__init__(self, name, comobject, attribute, mapping,
																type=bool)

class AttributeContainer(Attribute, dict):
	def __init__(self, name, attributes=[]):
		self.mapping = {}
		for attribute in attributes:
			self.add(attribute)
		Attribute.__init__(self, name)

	def add(self, attribute):
		self.mapping[attribute.name] = attribute
		attributename = attribute.name.replace(' ', '')
		setattr(self, attributename, attribute)

	def remove(self, name):
		try:
			del self.mapping[name]
			attributename = name.replace(' ', '')
			delattr(self, attributename)
		except KeyError:
			raise AttributeError('no attribute \'%s\'' % name)

	def hasGet(self):
		return True

	def hasSet(self):
		return True

	def _get(self):
		value = {}
		for name, attribute in self.mapping.items():
			if hasattr(attribute, 'get'):
				value[name] = attribute.get()
		return value

	def _set(self, value):
		for k, v in value.items():
			try:
				if hasattr(attribute, 'set'):
					self.mapping[k].set(v)
				else:
					raise ValueError('Cannot set name %s' % k)
			except KeyError:
				raise ValueError('Invalid name %s' % k)

	def __getitem__(self, key):
		attribute = self.mapping[key]
		if isinstance(attribute, AttributeContainer):
			return attribute
		else:
			return attribute.get()

	def __setitem__(self, key, value):
		attribute = self.mapping[key]
		if hasattr(attribute, 'set'):
			return attribute.set(value)
		elif hasattr(attribute, 'call'):
			return attribute.call(value)
		else:
			raise AttributeError('Cannot set item %s' % key)

	def keys(self):
		return self.mapping.keys()

	def values(self):
		return self.get().values()

	def items(self):
		return self.get().items()

	def update(self, other):
		for key in other:
			self[key] = other[key]

	def __str__(self):
		return str(self.get())

	def __repr__(self):
		return repr(self.get())

	def copy(self):
		return self.get()

class COMAttributeContainer(AttributeContainer):
	def __init__(self, name, comobject, mapping, attributes=[], **kwargs):
		self.comobject = comobject
		self.commapping = mapping
		for key, value in mapping.items():
			attributes.append(COMAttribute(key, comobject, value, **kwargs))
		AttributeContainer.__init__(self, name, attributes)

class XYCOMAttributeContainer(COMAttributeContainer):
	def __init__(self, name, comobject, **kwargs):
		mapping = {'x': 'X', 'y': 'Y'}
		COMAttributeContainer.__init__(self, name, comobject, mapping, **kwargs)

class MagnificationAttribute(COMAttribute):
	def __init__(self, comobject, mainscreenattribute):
		self.mainscreenattribute = mainscreenattribute
		self.indexvalues = []
		self.indexvalues.append(map(lambda m: m[0], magnificationtable))
		self.indexvalues.append(map(lambda m: m[1], magnificationtable))
		values = self.indexvalues[0] + self.indexvalues[1]
		COMAttribute.__init__(self, 'magnification', comobject,
													'MagnificationIndex', type=float, values=values)

	def _getValues(self, value, index=None):
		if index is None:
			index = self._getTableIndex()
		if index == 0:
			return self.upvalues
		elif index == 1:
			return self.downvalues
		else:
			raise RuntimeError('Unknown magnification table index')

	def _getTableIndex(self):
		mainscreen = self.mainscreenattribute.get()
		if mainscreen == 'up':
			index = 0
		elif mainscreen == 'down':
			index = 1
		else:
			raise RuntimeError('Unable to determine screen position')

		return index

	def _get(self):
		index = self._getTableIndex()

		magnificationindex = COMAttribute._get(self)

		try:
			magnification = magnificationtable[magnificationindex][index]
		except IndexError:
			raise RuntimeError('Unknown magnification value')

		return float(magnification)

	def _set(self, value, index=None):
		if index is None:
			index = self._getTableIndex()

		if value not in self.indexvalues[index]:
			if index == 0 and value in self.indexvalues[1]:
				values = self.indexvalues[1]
			elif index == 1 and value in self.indexvalues[0]:
				values = self.indexvalues[1]
			else:
				values = self.indexvalues[index]
		else:
			values = self.indexvalues[index]

		for i, magnification in enumerate(values):
			if value == magnification:
				return COMAttribute._set(self, i)

		maxindex = len(values) - 1
		for i in range(maxindex):
			if (value > values[i] and value < values[i + 1]):
				return COMAttribute._set(self, i)

		return COMAttribute._set(self, maxindex)

class LowDoseStatusAttribute(ConstantMappedCOMAttribute):
	def __init__(self, comobject):
		ConstantMappedCOMAttribute.__init__(self, 'status', comobject,
																				'LowDoseActive',
																				[('IsOn', 'on'), ('IsOff', 'off')])

	def hasGet(self):
		return True

	def hasSet(self):
		return True

	def _get(self):
		try:
			if not getattr(self.comobject, 'IsInitialized'):
				return 'uninitialized'
			return ConstantMappedCOMAttribute._get(self)
		except pythoncom.com_error:
			return 'disabled'

	def _set(self, value):
		try:
			if value != 'off' and not getattr(self.comobject, 'IsInitialized'):
				raise RuntimeError('Low dose is not initialized')
			return ConstantMappedCOMAttribute._set(self, value)
		except pythoncom.com_error:
			raise RuntimeError('Low dose is not enabled')

class LowDoseModeAttribute(ConstantMappedCOMAttribute):
	def __init__(self, comobject):
		mapping = [('eExposure', 'exposure'),
								('eFocus1', 'focus1'),
								('eFocus2', 'focus2'),
								('eSearch', 'search')]
		ConstantMappedCOMAttribute.__init__(self, 'mode', comobject,
																				'LowDoseState', mapping)

	def _get(self):
		try:
			return ConstantMappedCOMAttribute._get(self)
		except pythoncom.com_error:
			return 'disabled'

	def _set(self, value):
		try:
			return ConstantMappedCOMAttribute._set(self, value)
		except pythoncom.com_error:
			raise RuntimeError('Low dose is not enabled')

class TurboPumpAttribute(ConstantMappedCOMAttribute):
	def __init__(self, comobject):
		name = 'turbo pump'
		mapping = [('eOn', 'on'), ('eOff', 'off')]
		self.getattribute = 'GetTmpStatus'
		self.callattribute = 'SetTmp'
		ConstantMappedCOMAttribute.__init__(self, name, comobject,
																				self.getattribute, mapping)

	def hasSet(self):
		return True

	def _get(self):
		self.attribute = self.getattribute
		return ConstantMappedCOMAttribute._get(self)

	def _set(self, value):
		self.attribute = self.callattribute
		return ConstantMappedCOMAttribute._call(self, value)

class HolderTypeAttribute(MappedCOMAttribute):
	def __init__(self, comobject):
		name = 'type'
		mapping = [(u'No Specimen Holder', 'no holder'),
								(u'Single Tilt', 'single tilt'),
								(u'ST Cryo Holder', 'cryo'),
								(u'Error', 'error')]
		attribute = 'CurrentSpecimenHolderName'
		MappedCOMAttribute.__init__(self, name, comobject, attribute, mapping)

	def hasSet(self):
		return True

	def _set(self, value):
		try:
			holdername = self.setmap[value]
		except KeyError:
			raise ValueError('Invalid value %s' % value)

		for i in range(10):
			if getattr(self.comobject, 'SpecimenHolderName')(i) == holdername:
				getattr(self.comobject, 'SetCurrentSpecimenHolder')(i)
				return

		raise RuntimeError('Cannot set holder type to %s' % value)

class VacuumGaugeAttributeContainer(COMAttributeContainer):
	def __init__(self, name, comobject, gauge):
		comobject = comobject.Gauges(gauge)
		mapping = {'pressure': 'Pressure',
								'label': 'Name'}
		attributes = [ConstantMappedCOMAttribute('status', comobject, 'Status',
																						[('gsValid', 'valid'),
																							('gsUnderflow', 'underflow'),
																							('gsOverflow', 'overflow'),
																							('gsInvalid', 'invalid')]),
									ConstantMappedCOMAttribute('level', comobject,
																							'PressureLevel',
														[('plGaugePressurelevelLow', 'low'),
															('plGaugePressurelevelLowMedium', 'low medium'),
															('plGaugePressurelevelMediumHigh', 'medium low'),
															('plGaugePressurelevelHigh', 'high'),
															('plGaugePressurelevelUndefined', 'inactive')])]
		COMAttributeContainer.__init__(self, name, comobject, mapping, attributes)

class StagePositionAttribute(Attribute):
	def __init__(self, name, attribute, container, **kwargs):
		self.container = container
		self.attribute = attribute
		Attribute.__init__(self, name, type=float, **kwargs)

	def hasGet(self):
		return True

	def hasSet(self):
		return True

	def _get(self):
		return getattr(getattr(self.container.comobject, 'Position'),
										self.attribute)

	def _set(self, value):
		self.container.position({self.name: value})

class StagePositionAttributeContainer(AttributeContainer):
	def __init__(self, comobject):
		self.comobject = comobject
		self.correctionattribute = ValueAttribute('correction', True, type=bool)
		self.typeattribute = ValueAttribute('type', 'go',
																				type=str, values=['go', 'move'])
		# not really
		self.delta = 2e-6
		self.xylimit = 1e-3
		self.zlimit = 3.75e-4
		# a + b should be dynamic by holder
		self.alimit = math.pi * 80.0/180.0

		self.stageranges = {}
		self.stageranges['x'] = (-self.xylimit + self.delta, self.xylimit)
		self.stageranges['y'] = (-self.xylimit + self.delta, self.xylimit)
		self.stageranges['z'] = (-self.zlimit, self.zlimit)
		self.stageranges['a'] = (-self.alimit, self.alimit)
		self.stageranges['b'] = (-self.alimit, self.alimit)

		name = 'position'
		mapping = {'x': 'X', 'y': 'Y', 'z': 'Z', 'a': 'A', 'b': 'B'}
		attributes = [self.correctionattribute, self.typeattribute]
		self.axesmapping = {}
		for key, value in mapping.items():
			self.axesmapping[key] = getattr(win32com.client.constants, 'axis' + value)
			attributes.append(StagePositionAttribute(key, value, self,
																							ranges=(self.stageranges[key],)))
		AttributeContainer.__init__(self, name, attributes)

	def _set(self, value):
		value = dict(value)
		if 'correction' in value:
			self.correction.set(value['correction'])
			del value['correction']
		if 'type' in value:
			self.type.set(value['type'])
			del value['type']
		self.position(value)

	def _position(self, position):
		for key, value in position.items():
			if value < self.stageranges[key][0] or value > self.stageranges[key][1]:
				raise ValueError('Stage position %s for %s out of range' % (value, key))

		composition = getattr(self.comobject, 'Position')
		axes = 0
		for key, value in position.items():
			setattr(composition, self.mapping[key].attribute, value)
			axes |= self.axesmapping[key]

		positiontype = self.typeattribute.get()
		if positiontype == 'go':
			method = getattr(self.comobject, 'Goto')
		elif positiontype == 'move':
			method = getattr(self.comobject, 'MoveTo')
		else:
			raise RuntimeError('Invalid position type %s' % positiontype)

		try:
			method(composition, axes)
		except pywintypes.com_error, e:
			raise RuntimeError('Error positioning stage')

	def position(self, value):
		# pre-position x and y (maybe others later)
		if self.correctionattribute.get() and ('x' in value or 'y' in value):
			currentposition = self.get()
			preposition = {}
			if 'x' in value:
				preposition['x'] = value['x'] - self.delta
			else:
				preposition['x'] = currentposition['x'] - self.delta
			if 'y' in value:
				preposition['y'] = value['y'] - self.delta
			else:
				preposition['y'] = currentposition['y'] - self.delta
			self._position(preposition)
		return self._position(value)

class FilmExposureNumberAttribute(COMAttribute):
	def __init__(self, comobject):
		COMAttribute.__init__(self, 'exposure number', comobject, 'ExposureNumber',
													type=int, ranges=((0, 99999),))

	def _get(self):
		return COMAttribute._get(self) % 100000

	def _set(self, value):
		return COMAttribute._set(self, (COMAttribute._get(self) / 100000)
																		* 100000 + value)

class FilmExposeAttribute(COMAttribute):
	def __init__(self, cameracomobject, exposureadaptorcomobject, stockattribute):
		self.exposureadaptorcomobject = exposureadaptorcomobject
		self.stockattribute = stockattribute
		COMAttribute.__init__(self, 'expose', cameracomobject, 'TakeExposure')

	def _call(self, args=()):
		if self.stockattribute.get() < 1:
			raise RuntimeError('No film to take exposure')

		if self.exposureadaptorcomobject.CloseShutter != 0:
			raise RuntimeError('Close shutter (pre-exposure) failed')
		if self.exposureadaptorcomobject.DisconnectExternalShutter != 0:
			raise RuntimeError('Disconnect external shutter failed')
		if self.exposureadaptorcomobject.LoadPlate != 0:
			raise RuntimeError('Load plate failed')
		if self.exposureadaptorcomobject.ExposePlateLabel != 0:
			raise RuntimeError('Expose plate label failed')
		if self.exposureadaptorcomobject.OpenShutter != 0:
			raise RuntimeError('Open (pre-exposure) shutter failed')
		
		COMAttribute._call(self, args)
		
		if self.exposureadaptorcomobject.CloseShutter != 0:
			raise RuntimeError('Close shutter (post-exposure) failed')
		if self.exposureadaptorcomobject.UnloadPlate != 0:
			raise RuntimeError('Unload plate failed')
		if self.exposureadaptorcomobject.UpdateExposureNumber != 0:
			raise RuntimeError('Update exposure number failed')
		if self.exposureadaptorcomobject.ConnectExternalShutter != 0:
			raise RuntimeError('Connect external shutter failed')
		if self.exposureadaptorcomobject.OpenShutter != 0:
			raise RuntimeError('Open shutter (post-exposure) failed')

class Tecnai(AttributeContainer):
	def __init__(self):
		pythoncom.CoInitializeEx(pythoncom.COINIT_MULTITHREADED)
		self.comobjects = {}
		args = {'tecnai': ('Tecnai.Instrument',),
						'low dose': ('LDServer.LdSrv',),
						'exposure adaptor': ('adaExp.TAdaExp', None, None, None, False,
																	pythoncom.CLSCTX_LOCAL_SERVER)}
		for name, args in args.items():
			try:
				self.comobjects[name] = win32com.client.Dispatch(*args)
			except pywintypes.com_error:
				pass

		hightension = AttributeContainer('high tension',
			(
				ConstantMappedCOMAttribute('status', self.comobjects['tecnai'].Gun,
																		'HTState',
																		[('htOff', 'off'),
																			('htOn', 'on'),
																			('htDisabled', 'disabled')]),
				COMAttribute('max value', self.comobjects['tecnai'].Gun, 'HTMaxValue',
											type=float),
			)
		)
		hightensionvalue = COMAttribute('value', self.comobjects['tecnai'].Gun,
																	'HTValue', type=float,
																	ranges=((0.0, hightension.maxvalue.get()),))
		hightension.add(hightensionvalue)
		
		gun = AttributeContainer('gun',
			(
				XYCOMAttributeContainer('tilt', self.comobjects['tecnai'].Gun.Tilt,
																type=float, ranges=((-1.0, 1.0),)),
				XYCOMAttributeContainer('shift', self.comobjects['tecnai'].Gun.Shift,
																type=float, ranges=((-1.0, 1.0),)),
				hightension,
			)
		)
		
		beam = AttributeContainer('beam',
			(
				ConstantMappedCOMAttribute('mode',
																		self.comobjects['tecnai'].Illumination,
																		'Mode',
																		[('imMicroProbe', 'microprobe'),
																			('imNanoProbe', 'nanoprobe')]),
				ConstantMappedCOMAttribute('dark field mode',
																		self.comobjects['tecnai'].Illumination,
																		'DFMode',
																		[('dfOff', 'off'),
																			('dfCartesian', 'cartesian'),
																			('dfConical', 'conical')]),
				MappedBooleanCOMAttribute('blank',
																	self.comobjects['tecnai'].Illumination,
																	'BeamBlanked', 'on', 'off'),
				COMAttribute('spot size', self.comobjects['tecnai'].Illumination,
											'SpotsizeIndex', type=int, ranges=((1, 11),)),
				AttributeContainer('stigmator',
					(
						XYCOMAttributeContainer('condensor',
										self.comobjects['tecnai'].Illumination.CondenserStigmator,
										type=float, ranges=((-1.0, 1.0),)),
					)
				),
				COMAttribute('intensity', self.comobjects['tecnai'].Illumination,
											'Intensity', type=float, ranges=((0.0, 1.0),)),
				XYCOMAttributeContainer('tilt',
																self.comobjects['tecnai'].Illumination.Tilt,
																type=float),
																#, ranges=((-0.3, -0.2), (0.2, 0.3))),
				XYCOMAttributeContainer('shift',
																self.comobjects['tecnai'].Illumination.Shift,
																type=float),
				ConstantMappedCOMAttribute('normalize',
																		self.comobjects['tecnai'].Illumination,
																		'Normalize',
																		[('nmSpotsize', 'spot size'),
																			('nmIntensity', 'intensity'),
																			('nmCondenser', 'condenser'),
																			('nmMiniCondenser', 'minicondenser'),
																			('nmObjectivePole', 'objective pole'),
																			('nmAll', 'all')]),
			)
		)
		
		screen = AttributeContainer('screen',
			(
				ConstantMappedCOMAttribute('main position',
																		self.comobjects['tecnai'].Camera,
																		'MainScreen',
																		[('spUp', 'up'), ('spDown', 'down')]),
				MappedBooleanCOMAttribute('small position',
																	self.comobjects['tecnai'].Camera,
																	'IsSmallScreenDown', 'down', 'up'),
				COMAttribute('current', self.comobjects['tecnai'].Camera,
											'ScreenCurrent', type=float),
			)
		)
		
		image = AttributeContainer('image',
			(
				ConstantMappedCOMAttribute('mode', self.comobjects['tecnai'].Projection,
																		'Mode',
																		[('pmImaging', 'imaging'),
																			('pmDiffraction', 'diffraction')]),
				ConstantMappedCOMAttribute('submode',
																		self.comobjects['tecnai'].Projection,
																		'SubMode',
																		[('psmLM', 'LM'),
																			('psmMi', 'Mi'),
																			('psmSA', 'SA'),
																			('psmMh', 'Mh'),
																			('psmLAD', 'LAD'),
																			('psmD', 'D')]),
				MagnificationAttribute(self.comobjects['tecnai'].Projection,
																screen.mainposition),
				COMAttribute('rotation', self.comobjects['tecnai'].Projection,
											'ImageRotation', type=float),
				COMAttribute('focus', self.comobjects['tecnai'].Projection, 'Focus',
											type=float, ranges=((-1.0, 1.0),)),
				COMAttribute('defocus', self.comobjects['tecnai'].Projection,
											'Defocus', type=float),
				COMAttribute('objective excitation',
											self.comobjects['tecnai'].Projection,
											'ObjectiveExcitation', type=float),
				XYCOMAttributeContainer('shift',
															self.comobjects['tecnai'].Projection.ImageShift,
															type=float),
				XYCOMAttributeContainer('beam shift',
													self.comobjects['tecnai'].Projection.ImageBeamShift,
													type=float),
				COMAttribute('reset defocus', self.comobjects['tecnai'].Projection,
											'ResetDefocus'),
				AttributeContainer('stigmator',
					(
						XYCOMAttributeContainer('objective',
											self.comobjects['tecnai'].Projection.ObjectiveStigmator,
											type=float, ranges=((-1.0, 1.0),)),
						XYCOMAttributeContainer('diffraction',
										self.comobjects['tecnai'].Projection.DiffractionStigmator,
										type=float, ranges=((-1.0, 1.0),)),
					)
				),
				ConstantMappedCOMAttribute('normalize',
																		self.comobjects['tecnai'].Projection,
																		'Normalize',
																		[('pnmObjective', 'objective'),
																			('pnmProjector', 'projector'),
																			('pnmAll', 'all')]),
			)
		)
		
		stage = AttributeContainer('stage',
			(
				ConstantMappedCOMAttribute('status', self.comobjects['tecnai'].Stage,
																		'Status',
																		[('stReady', 'ready'),
																			('stDisabled', 'disabled'),
																			('stGoing', 'going'),
																			('stMoving', 'moving'),
																			('stWobbling', 'wobbling'),
																			('stNotReady', 'not ready')]),
				StagePositionAttributeContainer(self.comobjects['tecnai'].Stage),
			)
		)
		try:
			stageled = ConstantMappedCOMAttribute('LED',
																						self.comobjects['exposure adaptor'],
																						'GonioLedStatus',
																						[('eOn', 'on'), ('eOff', 'off')])
			stage.add(stageled)
		except KeyError:
			pass
		
		vacuum = AttributeContainer('vacuum',
			(
				ConstantMappedCOMAttribute('status', self.comobjects['tecnai'].Vacuum,
																		'Status',
																		[('vsOff', 'off'),
																			('vsCameraAir', 'camera air'),
																			('vsBusy', 'busy'),
																			('vsReady', 'ready'),
																			('vsUnknown', 'unknown'),
																			('vsElse', 'else')]),
				MappedBooleanCOMAttribute('prevacuum pump',
																	self.comobjects['tecnai'].Vacuum,
																	'PVPRunning', 'on', 'off'),
				AttributeContainer('column',
					(
						VacuumGaugeAttributeContainer('condition',
																					self.comobjects['tecnai'].Vacuum,
																					'P4'),
						MappedBooleanCOMAttribute('valves',
																			self.comobjects['tecnai'].Vacuum,
																			'ColumnValvesOpen', 'open', 'closed'),
					)
				),
				AttributeContainer('buffer',
					(
						VacuumGaugeAttributeContainer('condition',
																					self.comobjects['tecnai'].Vacuum,
																					'P1'),
						COMAttribute('cycle', self.comobjects['tecnai'].Vacuum,
													'RunBufferCycle'),
					)
				),
				AttributeContainer('backing line',
					(
						VacuumGaugeAttributeContainer('condition',
																					self.comobjects['tecnai'].Vacuum,
																					 'P2'),
					)
				),
				AttributeContainer('camera',
					(
						VacuumGaugeAttributeContainer('condition',
																					self.comobjects['tecnai'].Vacuum,
																					 'P3'),
					)
				),
				AttributeContainer('gun',
					(
						VacuumGaugeAttributeContainer('condition',
																					 self.comobjects['tecnai'].Vacuum,
																					 'P6'),
					)
				),
				AttributeContainer('condensor',
					(
						VacuumGaugeAttributeContainer('condition',
																					 self.comobjects['tecnai'].Vacuum,
																					 'P8'),
					)
				),
				AttributeContainer('IGP backing lines',
					(
						VacuumGaugeAttributeContainer('condition',
																					 self.comobjects['tecnai'].Vacuum,
																					 'P15'),
					)
				),
			)
		)
		try:
			vacuumturbopump = TurboPumpAttribute(self.comobjects['exposure adaptor'])
			vacuum.add(vacuumturbopump)
		except KeyError:
			pass
		
		filmstock = COMAttribute('stock', self.comobjects['tecnai'].Camera, 'Stock',
															type=int)
		film = AttributeContainer('film',
			(
				filmstock,
				MappedBooleanCOMAttribute('exposure type',
																	 self.comobjects['tecnai'].Camera,
																	'ManualExposure', 'manual', 'automatic'),
				COMAttribute('manual exposure time', self.comobjects['tecnai'].Camera,
											'ManualExposureTime', type=float),
				COMAttribute('automatic exposure time',
											self.comobjects['tecnai'].Camera,
											'MeasuredExposureTime', type=float),
				COMAttribute('text', self.comobjects['tecnai'].Camera, 'FilmText',
											type=str, length=96),
				COMAttribute('user code', self.comobjects['tecnai'].Camera, 'Usercode',
											type=str, length=3),
				ConstantMappedCOMAttribute('date type',
																		self.comobjects['tecnai'].Camera,
																		'PlateLabelDateType',
																		[('dtNoDate', 'no date'),
																			('dtDDMMYY', 'DD-MM-YY'),
																			('dtMMDDYY', 'MM/DD/YY'),
																			('dtYYMMDD', 'YY.MM.DD')]),
				FilmExposureNumberAttribute(self.comobjects['tecnai'].Camera)
			)
		)
		try:
			filmexpose = FilmExposeAttribute(self.comobjects['tecnai'].Camera,
																				self.comobjects['exposure adaptor'],
																				filmstock)
			film.add(filmexpose)
		except KeyError:
			pass
		
		attributes = [
			COMAttribute('automatic normalization', self.comobjects['tecnai'],
										'AutoNormalizeEnabled', type=bool),
			COMAttribute('normalize', self.comobjects['tecnai'], 'NormalizeAll'),
			gun,
			beam,
			image,
			stage,
			screen,
			vacuum,
			film,
		]

		try:
			lowdose = AttributeContainer('low dose',
				(
					LowDoseStatusAttribute(self.comobjects['low dose']),
					LowDoseModeAttribute(self.comobjects['low dose']),
				)
			)
			attributes.append(lowdose)
		except KeyError:
			pass
		
		try:
			holder = AttributeContainer('holder',
				(
					ConstantMappedCOMAttribute('status',
																			self.comobjects['exposure adaptor'],
																			'SpecimenHolderInserted',
																			[('eInserted', 'inserted'),
																				('eNotInserted', 'not inserted')]),
					HolderTypeAttribute(self.comobjects['exposure adaptor']),
				)
			)
			attributes.append(holder)
		except KeyError:
			pass

		AttributeContainer.__init__(self, 'tecnai', attributes)

'''

map = {
	'gun': {
			# volts
			'value': 
			# volts
			'max value'
		},
	},
	'beam': {
		# radians 
		'tilt': {
			'x':
			'y':
		},
		# meters
		'shift': {
			'x':
			'y':
		},
	},
	'image': {
		# radians
		'rotation':
		# meters
		'defocus':
		# meters
		'shift': {
			'x':
			'y':
		},
		# meters
		'beam shift': {
			'x':
			'y':
		},
	},
	'stage': {
		'position': {
			# meters
			'x':
			'y':
			'z':
			'a':
			'b':
		}
	},
		# Amps
		'current':
	},
	'vacuum': {
		'column':
			# r
			# double
			# pascal
			'pressure':
		},
	},
}
'''

