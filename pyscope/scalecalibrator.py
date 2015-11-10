#from pyscope import simtem
import math
from pyscope import jeolcom

class Logger(object):
	def __init__(self,filename):
		self.cfgdict = {}

	def input(self, msg):
		return raw_input(msg)

	def output(self, prefix, msg):
		print '%s: %s' % (prefix, msg)

	def inputInt(self, msg):
		answer = self.input(msg)
		try:
			answer = int(answer)
		except:
			self.error('Not an Integer')
			self.inputInt(msg)
		return answer

	def inputBoolean(self, msg):
		hint = ' (Y/N or y/n)'
		answer = self.input(msg + hint)
		if answer.lower() == 'y':
			return True
		else:
			return False

	def warning(self,msg):
		self.output('Warning',msg)

	def error(self,msg):
		self.output('Error',msg)

	def info(self,msg):
		self.output('Info',msg)

	def cfg(self,module_name,item,value):
		if 'standard focus' not in module_name:
			sep = '='
		else:
			sep = ':'
		option = '%s%s%s\n' % (item,sep,value)
		print('\n[%s]\n%s\n' % (module_name,option))
		if module_name not in self.cfgdict:
			self.cfgdict[module_name] = [option,]
		else:
			self.cfgdict[module_name].append(option)

	def writeConfig(self):
		filename = raw_input('output calibrated jeol.cfg as: ')
		if not filename:
			return
		self.cfg_outfile = open(filename,'w')
		self.cfg_outfile.write('[tem option]\n')
		options = self.cfgdict['tem option']
		options.sort()
		self.cfg_outfile.write(''.join(options))
		self.cfg_outfile.write('\n')
		self.cfgdict.pop('tem option',None)
		
		for module_name in self.cfgdict.keys():
			self.cfg_outfile.write('[%s]\n' % module_name)
			text = ''.join(self.cfgdict[module_name])
			self.cfg_outfile.write(text)
			self.cfg_outfile.write('\n')
		self.cfg_outfile.close()

class ScaleCalibrator(object):
	def __init__(self,filename):
		self.logger = Logger(filename)
		self.mag_scale = 1.0
		self.done_submodes = []
		self.initializeTEM()
		self.defineOptions()
		self.last_standard_focus = None
		self.effect_type = None
		self.cam_length = None

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

	def isBeamTilt(self):
		if self.move_property == 'CLA2':
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
			self.logger.cfg('stage','STAGE_SCALE%%%s' %axis.upper(), '%.1e' % (float(shift) / self.getPhysicalShift()))
		elif self.isBeamTilt():
			cam_length = self.getCameraLength()
			# beamtilt clicks * scale = math.atan(effect / camera_length)
			scale = math.atan(float(self.getPhysicalShift()) / (self.mag * cam_length)) / shift
			self.logger.cfg('def','%s_SCALE%%%s' % (self.effect_type.upper(),axis.upper()),'%.1e' % (scale))
		elif self.isFocus():
			# others clicks * scale = effect
			self.logger.cfg('lens','%s_SCALE%%%s' % (self.effect_type.upper(),self.getSubModeString()),'%.1e' % (float(self.getPhysicalShift() / shift)))
		else:
			# others clicks * scale = effect
			self.logger.cfg('def',
					'%s_SCALE%%%s%%%s' % (self.effect_type.upper(),self.getSubModeString(),axis.upper()),
					'%.1e' % (float(self.getPhysicalShift() / (self.getScreenMag() * shift)))
			)

	def getSubModeString(self):
		return self.subDivideMode(self.submode,self.mag)

	def subDivideMode(self,mode_name,mag):
		name_lower = mode_name.lower()
		is_lower = (name_lower == mode_name)
		if name_lower == 'mag1':
			if mag > self.max_ls4:
				name_lower = 'ls5'
			elif mag > self.max_ls3:
				name_lower = 'ls4'
			elif mag > self.max_ls2:
				name_lower = 'ls3'
			elif mag > self.max_ls1:
				name_lower = 'ls2'
			else:
				name_lower = 'ls1'
		if not is_lower:
			name_lower = name_lower.upper()
		return name_lower

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

	def selectMagList(self):
		all_mags = self.tem.getMagnifications()
		selected_mags = [None,]
		while not set(selected_mags).issubset(set(all_mags)):
			if selected_mags[0] is not None:
				self.logger.warning('Contains invalid magnification')
				self.logger.info('valid magnification:')
				print all_mags
			try:
				selected_mags = map((lambda x:int(x)),raw_input('Enter mags to calibrate with "," as separator:').split(','))
			except:
				pass
			print selected_mags
		return selected_mags

	def selectMagRange(self):
		all_mags = self.tem.getMagnifications()
		start_mag = None
		end_mag = None
		while start_mag not in all_mags:
			if start_mag is not None:
				self.logger.warning('invalid magnification')
			start_mag = self.logger.inputInt('Enter the lowest mag to calibrate:')
		while end_mag not in all_mags:
			if end_mag is not None:
				self.logger.warning('invalid magnification')
			end_mag = self.logger.inputInt('Enter the highest mag to calibrate:')
		return all_mags[all_mags.index(start_mag):all_mags.index(end_mag)+1]

	def calibrateInImageMode(self):
		mags_to_calibrate = self.selectMagList()
		for i, mag in enumerate(mags_to_calibrate):
			self.tem.setMagnification(mag)
			self.logger.info('Current magnification = %d' % (int(mag)))
			if i == 0:
				self.confirmMainScreenMagnification()
			self.calibrations = self.getCalibrationRequired(first=(i==0))
			for effect_type in self.calibrations.keys():
				self.effect_type = effect_type
				self.current_calibration = self.calibrations[effect_type]
				self.setMoveClassInstance(effect_type)
				if effect_type == 'stage':
					xy_shift = self.getPhysicalStageShiftAtMag(mag)
					self.measureStageShift(self.calibrations[effect_type][1],xy_shift,10e-6,20.0)
					continue
				elif effect_type == 'focus':
					screen_shift = 1e-5
				else:
					screen_shift = 0.01 # 1 cm
				self.measureShift(self.calibrations[effect_type][1],screen_shift)


	def calibrateInDiffractionMode(self):
		while self.tem.getMagnification() < 5000:
			raw_input('Change mag to above 5000 for diffraction mode calibration.\nHit any key to continue')
		self.calibrations = self.getDiffractionCalibrationRequired()
		for effect_type in self.calibrations.keys():
			self.effect_type = effect_type
			self.current_calibration = self.calibrations[effect_type]
			self.setMoveClassInstance(effect_type)
			screen_shift = 0.01 # 1 cm
			self.measureShift(self.calibrations[effect_type][1],screen_shift)
		raw_input('hit any key to return to MAG1')
		self.tem.setDiffractionMode('imaging')

	def calibrateAll(self):
		self.calibrateInImageMode()
		self.calibrateInDiffractionMode()
		self.writeConfig()
		raw_input('hit any key to end')

	def writeConfig(self):
		self.logger.writeConfig()

class JeolScaleCalibrator(ScaleCalibrator):
	def initializeTEM(self):
		# scope model independent
		self.modes = ['MAG1','LOWMAG']
		self.all_axes = {'def3':['x','y'],'stage3':['x','y','z','a','b']}
		# move_property scale that does not depend on submode
		self.projection_submode_independent = ['Pos','CL3']
		self.is_cap_prefix = True
		self.tem = jeolcom.Jeol()
		# set to MAG1 first
		self.tem.setDiffractionMode('imaging')
		self.tem.findMagnifications()
		self.last_mag = 0

	def defineOptions(self):
		# set existing tem options
		tem_options = self.tem.getJeolConfig('tem option')
		for key in tem_options.keys():
			self.logger.cfg('tem option','%s' % key.upper(),tem_options[key])
		self.use_pla = self.tem.getJeolConfig('tem option','use_pla') 
		self.has_efilter = self.tem.getJeolConfig('tem option','energy_filter') 
		self.max_ls1 = self.tem.getJeolConfig('tem option','ls1_mag_max') 
		self.max_ls2 = self.tem.getJeolConfig('tem option','ls2_mag_max') 
		self.max_ls3 = self.tem.getJeolConfig('tem option','ls3_mag_max') 
		self.max_ls4 = self.tem.getJeolConfig('tem option','ls4_mag_max') 
		self.max_lm1 = self.tem.getJeolConfig('tem option','lm1_mag_max')
		# set constant eos values
		self.logger.cfg('eos','USE_MODES','lowmag, mag1')

	def getImagingEffectPropertyDict(self):
		'''
		Choose from TEM module the move property.
		Projection submode must be set first.
		'''
		# tem_module->effect_type->move_property
		self.all_configs = {
				'lens': {
						#'intensity': 'CL3',
						'focus':		{'MAG1':'OL', 'LOWMAG':'OM'},
				},
				'def':	{
						'beamshift': 'CLA1',
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
	def getDiffractionEffectPropertyDict(self):
		self.configs = {
				'def':	{
						'beamtilt': 'CLA2',
				},
		}

	def getCalibrationRequired(self,first=False,accept_all=False):
		self.mag = self.tem.getMagnification()
		self.submode = self.tem.getProjectionSubModeName().upper()
		self.getImagingEffectPropertyDict()
		set_attrs = self.constructAttributeNames()
		for effect_type in set_attrs.keys():
			attrname = set_attrs[effect_type][1]
			# remove calibrated
			if first:
				continue
			if not accept_all and self.isCalibrated(attrname):
				del set_attrs[effect_type]
		print 'required', set_attrs
		return set_attrs

	def getDiffractionCalibrationRequired(self):
		self.logger.info('Switching to Diffraction Mode')
		self.tem.setDiffractionMode('diffraction')
		self.submode = self.tem.getProjectionSubModeName().upper()
		raw_input('Adjust camera length to the desired value >=100 cm, Hit any key when done')
		self.mag = self.tem.getMagnification()
		self.getDiffractionEffectPropertyDict()
		set_attrs = self.constructAttributeNames()
		return set_attrs

	def getCameraLength(self):
		# get cam_length only once in the whole run
		while self.cam_length is None:
				# we do not get camera length from the scope, yet.
				cam_length_str = raw_input('Enter camera length in meters ')
				try:
					self.cam_length = float(cam_length_str)
				except:
					pass
		return self.cam_length

	def chooseFocusMoveProperty(self):
		return self.all_configs['lens']['focus'][self.submode]

	def chooseImageShiftMoveProperty(self):
		return self.all_configs['def']['imageshift'][self.isUsePLA()]

	def getSetAttributes(self):
		return self.constructAttributeNames()

	def isUsePLA(self):
		return self.use_pla

	def isNewSubMode(self):
		print '-------------------------'
		divided_submode = self.getSubModeString()
		if self.done_submodes and divided_submode in self.done_submodes:
			return False
		self.done_submodes.append(divided_submode)
		return True

	def isNewMag(self):
		if self.mag != self.last_mag:
			self.last_mag = self.mag
			return True
		return False

	def isCalibrated(self,move_property):
		if move_property in self.projection_submode_independent:
			return True
		is_new_submode = self.isNewSubMode()
		is_new_mag = self.isNewMag()
		if is_new_mag:
			is_cal = not is_new_submode
		else:
			is_cal = self.last_is_cal
		self.last_is_cal = is_cal
		return is_cal

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
	outputfilename = 'jeol_test.cfg'
	app = JeolScaleCalibrator(outputfilename)
	app.calibrateAll()
