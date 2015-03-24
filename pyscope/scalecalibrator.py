#from pyscope import simtem
import math
from pyscope import jeolcom

class Logger(object):
	def input(self, msg):
		return raw_input(msg)

	def output(self, prefix, msg):
		print '%s: %s' % (prefix, msg)

	def inputInt(self, msg):
		answer = self.input(msg)
		try:
			answer = int(answer)
		except:
			self.outputError('Not an Integer')
			self.inputInt(msg)
		return answer

	def inputBoolean(self, msg):
		hint = ' (Y/N or y/n)'
		answer = self.input(msg + hint)
		if answer.lower() == 'y':
			return True
		else:
			return False

	def error(self,msg):
		raise
		self.output('Error',msg)

	def info(self,msg):
		self.output('Info',msg)

class ScaleCalibrator(object):
	def __init__(self):
		self.logger = Logger()
		self.mag_scale = 1.0
		self.done_submodes = []
		self.initializeTEM()
		self.defineOptions()
		self.last_standard_focus = None

	def initializeTEM(self):
		self.is_cap_prefix = False
		self.tem = simtem.SimTEM()
		self.tem.findMagnifications()
		self.move_class_instance = self.tem

	def defineOptions(self):
		pass

	def confirmMainScreenMagnification(self):
		mag = self.tem.getMagnification()
		screen_mag = self.tem.getMainScreenMagnification()
		answer = self.logger.inputBoolean('Is the magnification at the main screen %d ?' % int(screen_mag))
		if not answer:
			screen_mag = self.logger.inputInt('Enter the magnification on the main screen appoximately as integer: ')

		if not screen_mag:
			raise ValueError('invalid main screen magnification')
		self.mag_scale = float(mag) / screen_mag

	def getScreenMag(self):
		mag = self.tem.getMagnification()
		return mag / self.mag_scale

	def getAttrNamePrefix(self, is_get):
		if is_get:
			prefix = 'get'
		else:
			prefix = 'set'
		if self.is_cap_prefix:
			prefix = prefix[0].upper()+prefix[1:]
		return prefix

	def getCurrentValue(self):
		if not self.move_property:
			self.logger.error('Move property not set')

		if self.move_property in ('OL','OM'):
			attr_name = 'getRawFocus%s' % (self.move_property)
			value = [getattr(self.tem,attr_name)(),]
		else:
			attr_name = self.getAttrNamePrefix(is_get=True)+self.move_property
			value = getattr(self.move_class_instance,attr_name)()
		return value

	def setValue(self,value):
		'''
		move to the value
		'''
		if not self.move_property:
			self.logger.error('Move property not set')
		if self.move_property in ('OL','OM'):
			attr_name = 'setRawFocus%s' % (self.move_property)
			getattr(self.tem,attr_name)(value)
		else:
			attr_name = self.getAttrNamePrefix(is_get=False)+self.move_property
			self._setValue(attr_name,value)

	def _setValue(self,attr_name,value):
		getattr(self.move_class_instance,attr_name)(value)

	def setMoveProperty(self, property_name):
		self.move_property = None
		attr_name = self.getAttrNamePrefix(is_get=True)+property_name
		if property_name == 'OL':
			# NEED OLc and OLf instead
			attr_name = 'SetOLc'
		if not hasattr(self.move_class_instance,attr_name):
			raise ValueError('%s attribute not found' % (attr_name))
		self.move_property = property_name

	def setPhysicalShift(self,value):
		'''
		Set physical shift of the movement in SI unit (meters, radians)
		'''
		self.physical_shift = value

	def getPhysicalShift(self):
		return self.physical_shift

	def setAxes(self,value_list):
		self.axes = value_list

	def getAxes(self):
		self.axes.sort()
		return self.axes

	def applyMovement(self,axis=None):
		if axis:
			if self.move_property != 'Pos':
				raw_input('Move %s by %.1f cm on Main Screen in %s direction' %
						(self.move_property,self.physical_shift*100, axis))
			else:
				if axis in ('a','b'):
					raw_input('Move %s %s axis by %d degrees ' %
							(self.move_property,axis,math.degrees(self.physical_shift)))
				else:
					raw_input('Move %s %s axis by %d um ' %
							(self.move_property,axis,self.physical_shift / 1e-6))
		else:
			raw_input('Move %s by %d um ' %
					(self.move_property,self.physical_shift*1e6))
		attr_name = self.getAttrNamePrefix(is_get=False)+self.move_property
		value = self.getCurrentValue()
  
	def measureStageShift(self, property_name,xy_shift,z_shift,tiltangle_degrees):
		try:
			self.setMoveProperty(property_name)
		except Exception, e:
			self.logger.error(e.__str__())
			return
		physical_shifts = {
				'x': xy_shift,
				'y': xy_shift,
				'z': z_shift,
				'a': math.radians(tiltangle_degrees),
				'b': math.radians(tiltangle_degrees),
		}
		pos0 = self.getCurrentValue()
		self.setAxes(pos0.keys())
		for axis in self.getAxes():
			if axis in ('a','b'):
				continue
			self.setPhysicalShift(physical_shifts[axis])
			self.applyMovement(axis)
			pos1 = self.getCurrentValue()
			# return to the original value
			self.setValue(pos0)
			self.calculateScaleAtAxis(pos0, pos1, axis)

	def isStageMovement(self):
		if self.move_property == 'Pos':
			return True
		return False

	def isFocus(self):
		if self.move_property in ('OM','OL'):
			return True
		return False

	def calculateScaleAtAxis(self, pos0, pos1, axis=None):
		if axis is None:
			shift = pos1 - pos0 + 1e-20
		else:
			shift = pos1[axis] - pos0[axis] + 1e-20
		self.logger.info('physical shift effect = %.2e' % (self.getPhysicalShift()))
		self.logger.info('measured digital shift = %d' % (shift))
		if self.isStageMovement():
			# stage clicks / scale = effect
			self.logger.info('measured shift scale = %.1f' % (float(shift) / self.getPhysicalShift()))
		elif self.isFocus():
			# others clicks * scale = effect
			self.logger.info('measured shift scale = %.3e' % (float(self.getPhysicalShift() / shift)))
		else:
			# others clicks * scale = effect
			self.logger.info('measured shift scale = %.3e' % (float(self.getPhysicalShift() / (self.getScreenMag() * shift))))

	def measureShift(self, property_name, physical_shift):
		try:
			self.setPhysicalShift(physical_shift)
			self.setMoveProperty(property_name)
		except Exception, e:
			self.logger.error(e.__str__())
			return
		print 'Prepare to calibrate %s:' % (property_name)
		raw_input('Waiting for you to setup the initial condition... (hit any key to continue. ')
		pos0 = self.getCurrentValue()
		if type(pos0) == type({}):
			self.setAxes(pos0.keys())
		else:
			self.setAxes([None,])
		for axis in self.getAxes():
			self.applyMovement(axis)
			pos1 = self.getCurrentValue()
			# return to the original value
			self.setValue(pos0)
			self.calculateScaleAtAxis(pos0, pos1, axis)

	def getCalibrationRequired(self):
		return {
				'imageshift': ('','ImageShift'),
				'beamshift': ('','BeamShift'),
		}

	def setMoveClassInstance(self,effect_type):
		self.move_class_instance = self.tem

	def getPhysicalStageShiftAtMag(self,mag):
		screen_mag = mag / self.mag_scale
		stage_shift = 10e-6 # 10 um
		return stage_shift

	def displayStandardFocus(self, mag):
		raw_input('Push Standard Focus button on your TEM panel... (hit any key to continue. ')
		# current_calibration should be set to focus by now
		self.setMoveProperty(self.current_calibration[1])
		raw_focus_value = self.getCurrentValue()
		print raw_focus_value, mag
		if self.last_standard_focus is None or self.last_standard_focus != raw_focus_value:
			self.logger.info('New Standard Focus at %d = %d' % (mag, raw_focus_value))

	def calibrateAll(self):
		#for i, mag in enumerate(self.tem.getMagnifications()):
		for i, mag in enumerate([500, 5000,]):
			self.tem.setMagnification(mag)
			self.logger.info('Current magnification = %d' % (int(mag)))
			if i == 0:
				self.confirmMainScreenMagnification()
			self.calibrations = self.getCalibrationRequired()
			for effect_type in self.calibrations.keys():
				self.current_calibration = self.calibrations[effect_type]
				self.setMoveClassInstance(effect_type)
				if effect_type == 'stage':
					xy_shift = self.getPhysicalStageShiftAtMag(mag)
					self.measureStageShift(self.calibrations[effect_type][1],xy_shift,10e-6,20.0)
					continue
				elif effect_type == 'focus':
					self.displayStandardFocus(mag)
					screen_shift = 1e-5
				else:
					screen_shift = 0.01 # 1 cm
				self.measureShift(self.calibrations[effect_type][1],screen_shift)
		raw_input('hit any key to end')

class JeolScaleCalibrator(ScaleCalibrator):
	def initializeTEM(self):
		# scope model independent
		self.modes = ['MAG1','LOWMAG']
		self.all_axes = {'def3':['x','y'],'stage3':['x','y','z','a','b']}
		self.projection_submode_dependent = ['CLA1','CLA2']
		self.is_cap_prefix = True
		self.tem = jeolcom.Jeol()
		self.tem.findMagnifications()

	def defineOptions(self):
		self.use_pla = self.logger.inputBoolean('Using PLA for image shift?')

	def getEffectPropertyDict(self):
		'''
		Choose from TEM module the move property.
		Projection submode must be set first.
		'''
		# tem_module->effect_type->move_property
		self.all_configs = {
				'lens': {
						'intensity': 'CL3',
						'focus':		{'MAG1':'OL', 'LOWMAG':'OM'},
				},
				'def':	{
						'beamshift': 'CLA1',
						'beamtilt': 'CLA2',
						'imageshift': {False:'IS1',True:'PLA'},
				},
				'stage': {
						'stage': 'Pos',
				}
		}
		self.configs = self.all_configs.copy()
		if 'imageshift' in self.configs['def'].keys():
			self.configs['def']['imageshift'] = self.chooseImageShiftMoveProperty()
		if 'focus' in self.configs['lens'].keys():
			self.configs['lens']['focus'] = self.chooseFocusMoveProperty()

	def getCalibrationRequired(self):
		self.mag = self.tem.getMagnification()
		self.submode = self.tem.getProjectionSubModeName().upper()
		self.getEffectPropertyDict()
		set_attrs = self.constructAttributeNames()
		for effect_type in set_attrs.keys():
			attrname = set_attrs[effect_type][1]
			if self.isCalibrated(attrname):
				del set_attrs[effect_type]
		print 'required', set_attrs
		return set_attrs

	def chooseFocusMoveProperty(self):
		return self.all_configs['lens']['focus'][self.submode]

	def chooseImageShiftMoveProperty(self):
		return self.all_configs['def']['imageshift'][self.isUsePLA()]

	def getSetAttributes(self):
		return self.constructAttributeNames()

	def isUsePLA(self):
		return self.use_pla

	def isNewSubMode(self):
		if self.done_submodes and self.submode in self.done_submodes:
			return False
		self.done_submodes.append(self.submode)
		return True

	def isCalibrated(self,move_property):
		if move_property in self.projection_submode_dependent and not self.isNewSubMode():
			return True
		#default, recalibration
		return False

	def constructAttributeNames(self):
		results = {}
		for tem_module in self.configs.keys():
			for effect_type in self.configs[tem_module].keys():
				effect_type_item = self.configs[tem_module][effect_type]
				results[effect_type] = tem_module+'3', effect_type_item
		return results

	def setMoveClassInstance(self,effect_type):
		self.move_class_instance = getattr(self.tem,self.calibrations[effect_type][0])

	def getCurrentValue(self):
		results = super(JeolScaleCalibrator,self).getCurrentValue()
		tem_module = self.current_calibration[0]
		if tem_module not in self.all_axes.keys():
			return results[0]
		else:
			return dict(zip(self.all_axes[tem_module],results[:-1]))

	def _setValue(self,attr_name,value):
		tem_module = self.current_calibration[0]
		if 'stage' in tem_module:
			self._setStage(value)
		elif tem_module not in self.all_axes.keys():
			getattr(self.move_class_instance,attr_name)(value)
		else:
			args = map((lambda x: value[x]), self.all_axes[tem_module])
			getattr(self.move_class_instance,attr_name)(*args)

	def _setStage(self, value):
		axis_attrs = {'x':'X','y':'Y','z':'Z','a':'TiltXAngle','b':'TiltYAngle'}
		for axis in value.keys():
			attr_name = 'Set'+axis_attrs[axis]
			getattr(self.move_class_instance,attr_name)(value[axis])
			
if __name__ == "__main__":
	app = JeolScaleCalibrator()
	app.calibrateAll()
