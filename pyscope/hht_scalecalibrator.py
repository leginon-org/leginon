#from pyscope import simtem
import math
from pyscope import hitachi
from pyami import fftfun

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

	def cfg(self,module_name,item,value,value2=None):
		if 'standard focus' not in module_name:
			sep = '='
		else:
			sep = ':'
		option = '%s%s%s' % (item,sep,value)
		if value2 is not None:
			option += ',%s' % (value2,)
		option += '\n'
		print('\n[%s]\n%s\n' % (module_name,option))
		if module_name not in self.cfgdict:
			self.cfgdict[module_name] = [option,]
		else:
			self.cfgdict[module_name].append(option)

	def writeConfig(self):
		filename = raw_input('output calibrated cfg file as: ')
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
	'''
	Scale calibration from digital clicks to meters or radians.
	These are saved in a config file defined by logger.
	'''
	def __init__(self,filename):
		self.logger = Logger(filename)
		self.mag_scale = 1.0
		self.done_submodes = []
		self.focus_move_properties = ('OM','OL')
		self.beam_tilt_move_properties = ('BT',)
		self.last_standard_focus = None
		self.effect_type = None
		self.cam_length = None
		self.initializeTEM()
		self.defineOptions()

	def initializeTEM(self):
		'''
		ScaleCalibrator base class initialize SimTEM.
		'''
		self.is_cap_prefix = False
		self.tem = simtem.SimTEM()
		self.tem.findMagnifications()
		self.set_move_class_instance = self.tem
		self.get_move_class_instance = self.tem

	def defineOptions(self):
		pass

	def confirmMainScreenMagnification(self):
		'''
		Calibrations are done on main screen.
		'''
		mag = self.tem.getMagnification()
		print mag
		screen_mag = self.tem.getMainScreenMagnification()
		print 'screen',screen_mag
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

		if self.move_property in self.focus_move_properties:
			attr_name = 'getRawFocus%s' % (self.move_property)
			value = [getattr(self.tem,attr_name)(),]
		else:
			attr_name = self.getAttrNamePrefix(is_get=True)+self.move_property
			value = getattr(self.get_move_class_instance,attr_name)()
		return value

	def setValue(self,value):
		'''
		ScaleCalibrator move to the value.
		'''
		if not self.move_property:
			self.logger.error('Move property not set')
		if self.move_property in self.focus_move_properties:
			attr_name = 'setRawFocus%s' % (self.move_property)
			getattr(self.tem,attr_name)(value)
		else:
			attr_name = self.getAttrNamePrefix(is_get=False)+self.move_property
			self._setValue(attr_name,value)

	def _setValue(self,attr_name,value):
		getattr(self.set_move_class_instance,attr_name)(value)

	def setMoveProperty(self, property_name):
		self.move_property = None
		attr_name = self.getAttrNamePrefix(is_get=True)+property_name
		if property_name == 'OL':
			# NEED OLc and OLf instead
			attr_name = 'SetOLc'
		if not hasattr(self.set_move_class_instance,attr_name):
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
				raw_input('Move %s by %.2f um on Main Screen in %s direction based on specimen image' %
						(self.move_property,self.physical_shift*1e6, axis))
			else:
				if axis in ('a','b'):
					raw_input('Move %s %s axis by %d degrees ' %
							(self.move_property,axis,math.degrees(self.physical_shift)))
				else:
					raw_input('Move %s %s axis by %d um ' %
							(self.move_property,axis,self.physical_shift*1e6))
		else:
			raw_input('Move %s with %s by %d um ' %
					(self.move_property, self.effect_type,self.physical_shift*1e6))
  
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
		if self.move_property in self.focus_move_properties:
			return True
		return False

	def isBeamTilt(self):
		if self.move_property == self.beam_tilt_move_properties:
			return True
		return False

	def calculateScaleAtAxis(self, pos0, pos1, axis=None):
		if axis is None:
			shift = pos1 - pos0
		else:
			shift = pos1[axis] - pos0[axis]
		if abs(shift) < 1e-10:
			self.logger.info('add 1 for simulated result....')
			shift += 1
		self.logger.info('physical shift effect = %.2e' % (self.getPhysicalShift()))
		self.logger.info('measured digital shift = %d' % (shift))
		if self.isBeamTilt():
			cam_length = self.getCameraLength()
			physicalshift_radians = self.getPhysicalShift()
			half_scale = physicalshift_radians*int('3FFC00',16)/2.0/shift
			item_type = 'COIL'
			item_name = '%s_%s_SCALE%%%s%%%s' % (item_type,self.move_property.upper(),self.getSubModeString(),axis.upper())
		elif self.isFocus():
			# others clicks * scale = effect
			half_scale = self.getPhysicalShift()*int('3FFC00',16)/2.0/shift
			item_type = 'LENS'
			item_name = '%s_%s_SCALE%%%s' % (item_type,self.move_property.upper(),self.getSubModeString())
		else:
			# others clicks * scale = effect
			half_scale = self.getPhysicalShift()*int('3FFC00',16)/2.0/shift
			item_type = 'COIL'
			coil_name = self.move_property.upper()
			if coil_name in ('BH','BT','CS'):
				item_name = '%s_%s_%d_SCALE%%%s%%%s' % (item_type,self.move_property.upper(),self.mag,self.getProbeModeString(),axis.upper())
			else:
				item_name = '%s_%s_SCALE%%%s%%%s' % (item_type,self.move_property.upper(),self.getSubModeString(),axis.upper())
		self.logger.cfg('optic',
				item_name,
				'%.2e' % (-half_scale),
				'%.2e' % (half_scale)
		)

	def getProbeModeString(self):
		return self.tem.getProbeMode().upper()

	def getSubModeString(self):
		return self.tem.getProjectionSubModeName().upper()

	def measureShift(self, property_name, physical_shift):
		try:
			self.setPhysicalShift(physical_shift)
			self.setMoveProperty(property_name)
		except Exception, e:
			raise
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
		self.set_move_class_instance = self.tem
		self.get_move_class_instance = self.tem

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

	def setProbeModeForMag(self,mag):
		# default require user to do manually
		raw_input('Set to the probe mode required by mag %d for calibration and then hit return ' % mag)

	def logReferenceMag(self, mag):
		self.logger.cfg('optics','REF_MAGNIFICATION%%%s' % (self.getSubModeString()),'%d' % (int(mag)))

	def calibrateInImageMode(self):
		mags_to_calibrate = self.selectMagList()
		for i, mag in enumerate(mags_to_calibrate):
			# need to set probe mode
			self.setProbeModeForMag(mag)
			self.tem.setMagnification(mag)
			self.logger.info('Current magnification = %d' % (int(mag)))
			if i == 0:
				self.confirmMainScreenMagnification()
			self.calibrations = self.getCalibrationRequired(first=(i==0))
			self.logReferenceMag(mag)
			print 'image mode calibrations', self.calibrations
			for effect_type in self.calibrations.keys():
				# example effect_type: imageshift, beamshift
				self.effect_type = effect_type
				self.current_calibration = self.calibrations[effect_type]
				self.setMoveClassInstance(effect_type)
				if effect_type == 'stage':
					xy_shift = self.getPhysicalStageShiftAtMag(mag)
					self.measureStageShift(self.calibrations[effect_type][1],xy_shift,10e-6,20.0)
					continue
				elif effect_type == 'focus':
					screen_shift = 1e-5
					specimen_shift = screen_shift
				else:
					screen_shift = 0.01 # 1 cm
					specimen_shift = screen_shift / (mag / self.mag_scale) # shift at specimen plane
					self.logger.info('Screeen shift of %.2e cm = Specimen shift of %.2f um' % (screen_shift*100,specimen_shift*1e6))
				self.measureShift(self.calibrations[effect_type][1],specimen_shift)


	def calibrateInDiffractionMode(self):
		while self.tem.getMagnification() < 5000:
			raw_input('Change mag to above 5000 for diffraction mode calibration.\nHit any key to continue')
		self.calibrations = self.getDiffractionCalibrationRequired()
		for effect_type in self.calibrations.keys():
			self.effect_type = effect_type
			self.current_calibration = self.calibrations[effect_type]
			self.setMoveClassInstance(effect_type)
			wavelength = fftfun.getElectronWavelength(self.tem.getHighTension())
			cam_length = self.getCameraLength()
			specimen_shift =  math.tan(wavelength/2.31e-10)*cam_length
			self.logger.info('Move from origin to AuPd (111) reflection in this calibration')
			self.logger.info('Screeen shift = Beam tilt of %.2f mrad' % (specimen_shift*1e3))
			self.measureShift(self.calibrations[effect_type][1],specimen_shift)
		raw_input('hit any key to return to imaging mode')
		self.tem.setProjectionMode('imaging')

	def calibrateAll(self):
		self.calibrateInImageMode()
		self.calibrateInDiffractionMode()
		self.writeConfig()
		raw_input('hit any key to end')

	def writeConfig(self):
		self.logger.writeConfig()

class HitachiScaleCalibrator(ScaleCalibrator):
	def initializeTEM(self):
		# initalize tem
		self.tem = hitachi.HT7800()
		self.tem.setProjectionMode('imaging')
		self.tem.findMagnifications()
		# set default config
		self.is_cap_prefix = True
		self.use_pla = True
		self.focus_move_properties = ('OBJ','I1')
		self.beam_tilt_move_properties = ('BT',)
		# scope model independent
		self.all_axes = {'Coil':['x','y'],'stage':['x','y','z','a','b']}
		# move_property scale that does not depend on submode
		self.projection_submode_independent = ['C2',]
		# set to MAG1 first
		self.last_mag = 0

	def defineOptions(self):
		# set existing tem options
		tem_options = self.tem.getHitachiConfig('tem option')
		for key in tem_options.keys():
			self.logger.cfg('tem option','%s' % key.upper(),tem_options[key])

	def getImageShiftCoil(self):
		return self.tem.getImageShiftCoil()

	def getImagingEffectPropertyDict(self):
		'''
		Choose from TEM module the move property.
		Projection submode must be set first.
		'''
		# tem_module->effect_type->move_property
		self.all_configs = {
				'lens': {
						#'intensity': 'C2',
						# OBJ calibration is known. Don't know how to calibration lowmag
						#'focus':		{'ZOOM1':'OBJ', 'LOWMAG':'I1'},
				},
				'coil':	{
						'beamshift': 'BH',
						'imageshift': {False:'ISF',True:self.getImageShiftCoil()},
				},
		}
		self.configs = self.all_configs.copy()
		if 'imageshift' in self.configs['coil'].keys():
			self.configs['coil']['imageshift'] = self.chooseImageShiftMoveProperty()
		if 'focus' in self.configs['lens'].keys():
			self.configs['lens']['focus'] = self.chooseFocusMoveProperty()

	def getDiffractionEffectPropertyDict(self):
		self.configs = {
				'coil':	{
						'beamtilt': 'BT',
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
		self.tem.setProjectionMode('diffraction')
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
		return self.all_configs['coil']['imageshift'][self.isUsePLA()]

	def getSetAttributes(self):
		return self.constructAttributeNames()

	def isUsePLA(self):
		return self.use_pla

	def setProbeModeForMag(self,mag):
		'''
		Making a guess of the probe mode on Hitachi instrument and set it if correct.
		This is required before setting magnification since not all magnifications are
		accessible in a given probe mode.
		'''
		submodes = self.tem.getProjectionSubModes()
		for submode in submodes:
			if mag in self.tem.submode_mags[submode]:
				answer = raw_input('Is %d mag in submode %s ? (Y/N/y/n)' % (mag, submode))
				if answer.lower() == 'y':
					try:
						# Find the one to one mapping of probe mode and set it.
						probe = self.tem.getProbeModeFromProjectionSubMode(submode)
						self.tem.setProbeMode(probe)
						return
					except ValueError as e:
						print('Error finding matching probe mode. Please set probe mode manually.')
						break
				else:
					# wrong guess.
					break
		# default require user to do manually
		raw_input('Set to the probe mode required by mag %d for calibration and then hit return ' % mag)

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

	def getMoveClassName(self, config_name):
		if config_name == 'lens':
			return 'LensCurrentRaw'
		if config_name == 'coil':
			return 'CoilVectorRaw'
		else:
			return config_name[0].upper()+config_name[1:]

	def constructAttributeNames(self):
		results = {}
		for optic_module in self.configs.keys():
			for effect_type in self.configs[optic_module].keys():
				effect_type_item = self.configs[optic_module][effect_type]
				results[effect_type] = optic_module, effect_type_item
		print 'attribute names', results
		return results

	def setMoveClassInstance(self,effect_type):
		self.set_move_class_instance = getattr(self.tem,'set'+self.getMoveClassName(self.calibrations[effect_type][0]))
		self.get_move_class_instance = getattr(self.tem,'get'+self.getMoveClassName(self.calibrations[effect_type][0]))

	def setMoveProperty(self, property_name):
		self.move_property = property_name

	def getCurrentValue(self):
		'''
		Hitachi class get current value comes from get_move_class_instance
		of the effect_type
		'''
		if not self.move_property:
			self.logger.error('Move property not set')
		item_name = self.calibrations[self.effect_type][1]
		value = self.get_move_class_instance(item_name)
		print value
		return value

	def setValue(self,value):
		'''
		Hitachi moves to the physical value using move_property (e.g. BH) and
		known set_move_class_instance (e.g. setCoilVector)
		'''
		if not self.move_property:
			self.logger.error('Move property not set')
		self._setValue(self.move_property, value)

	def _setValue(self,item_name,value):
		'''
		Hitachi moves to the physical shift value using known set_move_class_instance
		with current scale calibration.
		e.g. setCoilVector('BH',{'x':0.00001,'y':0})
		'''
		self.set_move_class_instance(item_name,value)
			
if __name__ == "__main__":
	outputfilename = 'hht_test.cfg'
	app = HitachiScaleCalibrator(outputfilename)
	app.calibrateAll()
