#
# CM.py is implemented suitable to CM series electron microscope
# Author: Min Su
#         Wen Jiang
# Structure Biology, Purdue University, West Lafayette, IN
#
# Change Log:
# 12-29-2006 Min Su Implementation
# The CM base data structure is defined in CMData module
# The Calibration table is filled in CMCal module
# The base library is defined in cmlib.py, Caching machnism is
# implemented there, but not efficiently used 



import tem
try:
	import pythoncom
except:
	pass
import cmlib
import CMCal
import time
import math

Debug = True

class MagnificationsUninitialized(Exception):
	pass

# if a stage position movement is less than the following, then ignore it
# Note: The movement unit is micro meter in CM, however meter in Tecnai.
minimum_stage = {
	'x': 5e-8,
	'y': 5e-8,
	'z': 5e-8,
	'a': 6e-5,
}

class CM(tem.TEM):
	name = 'CM'
	def __init__(self):
		if Debug == True:
			print 'from CM class'
		
		tem.TEM.__init__(self)
		self.correctedstage = True
		pythoncom.CoInitializeEx(pythoncom.COINIT_MULTITHREADED)
		self.CMLIB = cmlib.CMLIB()
		
		self.magnifications = []
		self.mainscreenscale = 44000.0 / 50000.0


	# return the actual Mag value to film camera, no mather mainscreen up or down
	def getMagnification(self, index=None):
		if Debug == True:
			print "from getMagnification"
		CMvar = self.CMLIB.GetCMVar()
		
		if index is None:
			# find out if mainscreen is up or down */
			if CMvar.MainScrn == 0:
				i = self._emcGetMagPosition(CMvar.Magn, 0)   # MainScreen down
				return CMCal.screenup_mag[i]
			else:
				return int(round(CMvar.Magn))   # MainScreen up
		
		elif not self.getMagnificationsInitialized():
			raise MagnificationsUninitialized
		else:
			try:
				return self.magnifications[index]
			except IndexError:
				raise ValueError('invalid magnification index')


	# return the actual Mag value to mainscreen,no mather mainscreen up or down
	def getMainScreenMagnification(self):
		if Debug == True:
			print 'from getMainScreenMagnification'
		
		CMvar = self.CMLIB.GetCMVar()
		# find out if mainscreen is up or down */
		if CMvar.MainScrn == 0:
			return int(round(CMvar.Magn))
		else:
			i = self._emcGetMagPosition(CMvar.Magn, 1)
			return CMCal.screendown_mag[i]		


	def getMainScreenScale(self):
		if Debug == True:
			print 'from getMainScreenScale'
		return self.mainscreenscale

	def setMainScreenScale(self, mainscreenscale):
		if Debug == True:
			print 'from setMainScreenScale'
		self.mainscreenscale = mainscreenscale

	def getMagnificationsInitialized(self):
		if Debug == True:
			print "from getMagnificationsInitialized"
		if self.magnifications:
			return True
		else:
			return False


	def getMagnifications(self):
		if Debug == True:
			print "from getMagnifications"
		return self.magnifications


	# Mag index is not retrievable from CM. Only the Mag value can be retrieved.
	# Assume Mag index is pre-known and stored in CMCal.
	def findMagnifications(self):
		if Debug == True:
			print 'from findMagnifications'
		self.setMagnifications(CMCal.screenup_mag)


	#  get Mag index position
	def _emcGetMagPosition(self,magnification,screenUp):
		if Debug == True:
			print 'from _emcGetMagPostion'
		if screenUp == 0:
			mags = CMCal.screendown_mag
		else:
			mags = CMCal.screenup_mag
		for i in range(0,39):
			if mags[i] >= int(magnification):
				break
		if i >= 38:
			raise ValueError('magnification out of range')
		return i                


	def setMagnifications(self, magnifications):
		if Debug == True:
			print 'from setMagnifications'
		self.magnifications = magnifications


	# In original tecnai.py, setMagnification() is funtional through
	# setMagnificationIndex(), which maynot be directly called in Legion.
	def setMagnificationIndex(self, value):
		if Debug == True:
			print " from setMagnificationIndex"
			print 'since setMagnificationIndex() is called, it must be implemented. Please do it !!!'
		return NotImplementedError()

		
	def setMagnification(self, mag):
		if Debug == True:
			print "from setMagnification"
		CMvar = self.CMLIB.GetCMVar()
		
		# assume to be setted mag is always to the film, not mainscreen position dependant/
		i = self._emcGetMagPosition(mag, 1)
		if i < 16:
			self.CMLIB.DirectOperation(6,i+1) # set Mag in LM mode
		else:
			self.CMLIB.DirectOperation(3,i+1) # set Mag in HM/SA mode
		time.sleep(1)
		self.CMLIB.DirectOperation(16,0)      # normalize imaging length


	def getStagePosition(self):
		if Debug == True:
			print "from getStagePosition"
		value = {'x': None, 'y': None, 'z': None, 'a': None}
		pos = self.CMLIB.CSAskPos()
		value['x'] = float(pos.x[0]/1e6)      # Leginon requires meter, however micron meter in CM.
		value['y'] = float(pos.y[0]/1e6)
		value['z'] = float(pos.z[0]/1e6)
		value['a'] = float(pos.a[0]/57.3)
		return value


	def setStagePosition(self, value):
		if Debug == True:
			print 'from setStagePosition'
		value_raw = {'x': None, 'y': None, 'z': None, 'a': None}
		# pre-position x and y (maybe others later)
		axes = 0           # 1(X) AND 2(Y) AND 4(Z)	preset moving axes in X,Y,Z,a detections
		
		# Check current stage postion
		stagenow = self.getStagePosition()
		
		bigenough = {}
		for axis in ('x', 'y', 'z', 'a'):
			if axis in value:
				value_raw[axis] = value[axis]
				delta = abs(value[axis] - stagenow[axis])
				if delta > minimum_stage[axis]:
					bigenough[axis] = value[axis]
					if axis == 'x':
						axes = axes | 1
					elif axis == 'y':
						axes = axes | 2
					elif axis == 'z':
						axes = axes | 4
					elif axis == 'a':
						axes = axes | 8
					else:
						axes = axes | 0						
			else:
				value_raw[axis] = stagenow[axis]
						
		if not bigenough:
			return

		if self.correctedstage:
			Backlash = 2e-6
			prevalue = {}
			# calculate pre-position
			for axis in ('x','y','z','a'):
				if axis == 'a':
					prevalue[axis] = stagenow[axis]
				else:
					prevalue[axis] = stagenow[axis] - Backlash
			if axes != 8:
				self.CMLIB.CSGotoPos(prevalue['x']*1e6,prevalue['y']*1e6,prevalue['z']*1e6,prevalue['a']*57.3,0,axes)

		self.CMLIB.CSGotoPos(value_raw['x']*1e6,value_raw['y']*1e6,value_raw['z']*1e6,value_raw['a']*57.3,0,axes)

	def getCorrectedStagePosition(self):
		if Debug == True:
			print 'from getCorrectedStagePosition'
		return self.correctedstage


	def setCorrectedStagePosition(self, value):
		if Debug == True:
			print 'from setCorrectedStagePosition'
		self.correctedstage = bool(value)
		return self.correctedstage


	# The return value(positive) from cmremote32 is in nano meter, however CM console display
	# in micron meter(positive). Leginon requires meter unit(negative).
	def getDefocus(self):
		if Debug == True:
			print 'from getDefocus'
		defocus = self.CMLIB.GetCMVar().defocus*1e-9*CMCal.f_defocus_H_rate
		return float(defocus)


	def setDefocus(self, defocus, relative = 'absolute'):
		if Debug == True:
			print 'from setDefocus'
		CMvar = self.CMLIB.GetCMVar()
		if relative == 'absolute':
			focus_now = float(CMvar.defocus*1e-9*CMCal.f_defocus_H_rate)
			value = (defocus - focus_now) * 1e6
		else:
			value = defocus *1e6
			
		# find out if magnification is low or high setting */
		if CMvar.MainScrn != 0:
			magnum = self._emcGetMagPosition(CMvar.Magn,1)
		else:
			magnum = self._emcGetMagPosition(CMvar.Magn,0)
		if magnum > 15:
			focus = int(round(0.49 + value/CMCal.f_defocus_H))
		if magnum < 15:
			focus = int(0.49 + round(value/CMCal.f_defocus_L))
		if magnum == 15:
			if CMvar.Spotsize == 180:
				focus = int(0.49 + round(value/CMCal.f_defocus_L))
			else:
				focus = int(0.49 + round(value/CMCal.f_defocus_H))

		self.CMLIB.TurnKnob(CMCal.TK_FocusStep,-9)         # enforce stepsize knob back to the initial position, 
													       # which is stepsize 1 no mather its current position.
		self.CMLIB.TurnKnob(CMCal.TK_FocusStep,2)		   # set stepsize to 3, since the defocus calibration was
		                                                   # done in this condition.
		if focus != 0:										       
			self.CMLIB.TurnKnob(CMCal.TK_FocusKnob,focus)

		cmlib.focus += value * 1e-6                        # record focus changing


	# No direct operation can do the job, softkey need to be
	# combined for this implementation. 
	def resetDefocus(self, value):
		if Debug == True:
			print 'from resetDefocus'
		if not value:
			return
		self.CMLIB.PushButton(CMCal.PB_Ready,CMCal.PB_PRESS)  # press Ready button to enter into console main page
		self.CMLIB.Softkey(12,1)    # press softkey 12 (reset defocus) once in console low dose main page
		                            # Be VERY careful to use softkey, it is page dependant, you may
		                            # make BIG mistake by hitting the same softkey in a wrong page

		
	def getResetDefocus(self):
		if Debug == True:
			print 'from getResetDefocus'
		return False


	# No equivalent info from CM
	def getObjectiveExcitation(self):
		if Debug == True:
			print 'from getObjectiveExcitation'
		return NotImplementedError()


	# focus is recoreded as a reference for proceeding Z-height adjustment.
	# The native focus value from Tecnai is normalized to -1 to 1.
	def getFocus(self):
		if Debug == True:
			print 'from getFocus'
		pos = self.CMLIB.CSAskPos()
		return float(pos.z[0]/1e6)


	def setFocus(self, value):
		if Debug == True:
			print 'from setFocus'
		self.CMLIB.CSGotoPos(0,0,value*1e6,9,0,4)   # move stage in Z direction only


	def getHighTensionStates(self):
		if Debug == True:
			print 'from getHighTensionStates'
		return ['off', 'on', 'disabled','unknown']


	# see setHighTension for explanition
	def getHighTensionState(self):
		if Debug == True:
			print 'from getHighTensionState'
		return 'unknown'


	def getHighTension(self):
		if Debug == True:
			print 'from getHighTension'
		HT = self.CMLIB.GetCMVar().HT
		return float(HT)


	# This function sets the high tension by the given value.
	# Free HT must be on for this function to work.
	# Note: There is no retriving info to specify the current Free HT status(on/off).
	# Free HT is switched on within this function, it may need to be switch off out of
	# this function, which depends on the operation purpose.
	def setHighTension(self, ht):
		if Debug == True:
			print 'from setHighTEnsion'
		if (ht > 200) or (ht < 0):
			print "high tension setting out of range"
			return
##		CMvar = self.CMLIB.GetCMVar()
##		deltaht = round(ht - CMvar.HT)
##		self.CMLIB.DirectOperation(CMCal.DO_HTStep,1)   # set high tension stepsize 1
##		self.CMLIB.SwitchFreeHT(1)        # switch on free hightensition. 1 is on, 0 is off  
##		self.CMLIB.ChangeFreeHT(deltaht)  # Free HT must be on for this function to work.

		
	def getIntensity(self):
		if Debug == True:
			print 'from getIntensity'
		Intensity = self.CMLIB.GetCMVar().Intensity
		return float(Intensity)


	def setIntensity(self, intensity, relative = 'absolute'):
		if Debug == True:
			print 'from setIntensity'
		CMvar = self.CMLIB.GetCMVar()
		intensity_max = 100000.0
		intensity_min = 1000.0
				
		if relative == 'relative':
			if (intensity + CMvar.Intensity) >= intensity_max:
				intensity_raw = intensity_max - CMvar.Intensity
			elif (intensity + CMvar.Intensity) <= intensity_min:
				intensity_raw = intensity_min - CMvar.Intensity 
			else:
				intensity_raw = intensity
		
		elif relative == 'absolute':
			if (intensity <= intensity_min):
				intensity_raw = intensity_min
			elif (intensity >= intensity_max):
				intensity_raw = intensity_max
			else:
				intensity_raw = intensity
			intensity_raw = intensity_raw - CMvar.Intensity
			if (CMvar.ButtonState & 0x4000 == 0):
				fineWasOff = 1
			else:
				fineWasOff = 0
				self.CMLIB.PushButton(CMCal.PB_IntFine,CMCal.PB_OFF)    # IntFine off
		else:
			 raise ValueError
		intensity_click = int(round(intensity_raw / CMCal.f_intensity))

		self.CMLIB.TurnKnob(CMCal.TK_Intensity,intensity_click)   # Turn knod to change intensity, intensity must be integer value
		self.CMLIB.PushButton(CMCal.PB_IntFine,fineWasOff)  # recover IntFine status
		

	# The none unit X,Y value is correlated with X,Y physical beamtilt
	# angle in radian.
	# refer to emscope->rcm.c to interprete RotAlgn[]
	def getBeamTilt(self):
		if Debug == True:
			print 'from getBeamTilt'
		value = {'x': None, 'y': None}
		Rot = self.CMLIB.GetRotationAlignment()
		value['x'] = Rot.RotAlgn[0].x
		value['y'] = Rot.RotAlgn[0].y
		return value


	def setBeamTilt(self, vector, relative = 'absolute'):
		if Debug == True:
			print 'from setBeamTilt'
		Rot = self.CMLIB.GetRotationAlignment()
		if relative == 'relative':
			if vector['x'] != None:
				vector['x'] += Rot.RotAlgn[0].x
			if vector['y'] != None:
				vector['y'] += Rot.RotAlgn[0].y
		elif relative == 'absolute':
			pass
		else:
			raise ValueError
		
		if vector['x'] != None:
			Rot.RotAlgn[0].x = vector['x']
			
		if vector['y'] != None:
			Rot.RotAlgn[0].y = vector['y']

		self.CMLIB.SetRotationAlignment(Rot)


	def getBeamShift(self):
		if Debug == True:
			print 'from getBeamShift'
		value = {'x': None, 'y': None}
		CMvar = self.CMLIB.GetCMVar()
		i = self._emcGetMagPosition(CMvar.Magn, CMvar.MainScrn)     # locate Mag index
		value['x'] = float(CMvar.beamx)/CMCal.imgshiftpix[i]['x']
		value['y'] = float(CMvar.beamy)/CMCal.imgshiftpix[i]['y']		
		return value


	# Not used in CM.
	def setBeamShift(self, vector, relative = 'absolute'):
		if Debug == True:
			print 'from setBeamShift'
##		vector_raw = {'x': None, 'y': None}
##		CMvar = self.CMLIB.GetCMVar()
##		i = self._emcGetMagPosition(CMvar.Magn, CMvar.MainScrn)     # locate Mag index
##		try:
##			vector_raw['x'] = vector['x'] * CMCal.beamshiftpix[i]['x']
##		except KeyError:
##			pass
##		try:
##			vector_raw['y'] = vector['y'] * CMCal.beamshiftpix[i]['y']
##		except KeyError:
##			pass
##		
##		FLT_MAX = 2000         # threshold value for beam tilt
##		
##		if relative == 'absolute':
##			if vector_raw['x'] != None:
##				if abs(vector_raw['x']) < FLT_MAX:
##					dox = 1
##				else:
##					dox = 0
##					print 'Beam Shift setting X out of range'
##			if vector_raw['y'] != None:
##				if abs(vector_raw['y']) < FLT_MAX:
##					doy = 1
##				else:
##					doy = 0
##					print 'Beam Shift setting Y out of range'
##
##		if relative == 'reletive':
##			if vector_raw['x'] != None:
##				if abs(CMvar.beamx + vector_raw['x']) < FLT_MAX:
##					dox = 1
##				else:
##					dox = 0
##					print 'Beam Shift setting X out of range'
##			if vector_raw['y'] != None:
##				if abs(CMvar.beamy + vector_raw['y']) < FLT_MAX:
##					doy = 1
##				else:
##					doy = 0
##					print 'Beam Shift setting Y out of range'
##
##		if relative == 'relative':
##			pass
##		elif relative == 'absolute':
##			if vector_raw['x'] != None:
##				vector_raw['x'] -= CMvar.beamx
##			if vector_raw['y'] != None:
##				vector_raw['y'] -= CMvar.beamy
##		else:
##			raise ValueError
##
##		if vector_raw['x'] != None:
##			if (dox):
####				vector_raw['x'] = int(round(vector_raw['x'] / CMCal.f_beamshiftx))
##				vector_raw['x'] = int(round(vector_raw['x']))
##				self.CMLIB.TurnKnob(CMCal.TK_ShiftX,vector_raw['x'])
##		if vector_raw['y'] != None:
##			if (doy):
####				vector_raw['y'] = int(round(vector_raw['y'] / CMCal.f_beamshifty))
##				vector_raw['y'] = int(round(vector_raw['y']))
##				self.CMLIB.TurnKnob(CMCal.TK_ShiftY,vector_raw['y'])


	# ImageShift is for low dose mode, which is different from RawImageShift.
	# Leginon requires meter unit, CM retrieve none unit value (-35,000 -- 35,000),
	def getImageShift(self):
		if Debug == True:
			print 'from getImageShift'
		value = {'x': None, 'y': None}
		CMvar = self.CMLIB.GetCMVar()
		i = self._emcGetMagPosition(CMvar.Magn, CMvar.MainScrn)     # locate Mag index
		if i > 15:
			value['x'] = float(CMvar.ImageShiftX)/CMCal.imgshiftpix[i]['x']
			value['y'] = float(CMvar.ImageShiftY)/CMCal.imgshiftpix[i]['y']
		else:
			value['x'] = float(cmlib.imageshift_LM['x'])/CMCal.imgshiftpix[i]['x']
			value['y'] = float(cmlib.imageshift_LM['y'])/CMCal.imgshiftpix[i]['y']
		return value

	
	def setImageShift(self, vector, relative = 'absolute'):
		if Debug == True:
			print 'from setImageShift'
		vector_raw = {'x': None, 'y': None}
		CMvar = self.CMLIB.GetCMVar()
		i = self._emcGetMagPosition(CMvar.Magn, CMvar.MainScrn)     # locate Mag index
		try:
			vector_raw['x'] = vector['x'] * CMCal.imgshiftpix[i]['x']   # convert vector input from meter to CM none unit value
		except KeyError:
			pass
		try:
			vector_raw['y'] = vector['y'] * CMCal.imgshiftpix[i]['y']
		except KeyError:
			pass

		FLT_MAX = 350000

		if relative == 'absolute':
			if vector_raw['x'] != None:
				if abs(vector_raw['x']) < FLT_MAX:
					dox = 1
				else:
					dox = 0
					print 'Image Shift setting X out of range'
			if vector_raw['y'] != None:
				if abs(vector_raw['y']) < FLT_MAX:
					doy = 1
				else:
					doy = 0
					print 'Image Shift setting Y out of range'

		if relative == 'reletive':
			if vector_raw['x'] != None:
				if abs(CMvar.ImageShiftX + vector_raw['x']) < FLT_MAX:
					dox = 1
				else:
					dox = 0
					print 'Image Shift setting X out of range'
			if vector_raw['y'] != None:
				if abs(CMvar.ImageShiftY + vector_raw['y']) < FLT_MAX:
					doy = 1
				else:
					doy = 0
					print 'Image Shift setting Y out of range'

		if (CMvar.ButtonState & 0x0004 == 1):
			self.CMLIB.PushButton(CMCal.PB_Darkfield,CMCal.PB_OFF)        # push Darkfield button to off

		if relative == 'relative':
			if vector_raw['x'] != None:
				if i <=15:
					cmlib.imageshift_LM['x'] += vector_raw['x']
			if vector_raw['y'] != None:
				if i <=15:
					cmlib.imageshift_LM['y'] += vector_raw['y']
		elif relative == 'absolute':
			if vector_raw['x'] != None:
				if i > 15:
					vector_raw['x'] -= CMvar.ImageShiftX
				else:
					vector_raw['x'] -= cmlib.imageshift_LM['x']
					cmlib.imageshift_LM['x'] += vector_raw['x']
			if vector_raw['y'] != None:
				if i > 15:
					vector_raw['y'] -= CMvar.ImageShiftY
				else:
					vector_raw['y'] -= cmlib.imageshift_LM['y']
					cmlib.imageshift_LM['y'] += vector_raw['y']
		else:
			raise ValueError

		if vector_raw['x'] != None:
			if (dox):
				vector_raw['x'] = int(round(vector_raw['x'] / CMCal.f_imageshiftx))
				self.CMLIB.TurnKnob(CMCal.TK_MultifunctionX,vector_raw['x'])   # The interpretation is from emscope rcm.h. It has been tested and calibrated by Min Su on 09/03/06
		if vector_raw['y'] != None:
			if (doy):
				vector_raw['y'] = int(round(vector_raw['y'] / CMCal.f_imageshifty))
				self.CMLIB.TurnKnob(CMCal.TK_MultifunctionY,vector_raw['y'])

		if (CMvar.ButtonState & 0x0004 == 1):
			self.CMLIB.PushButton(CMCal.PB_Darkfield,CMCal.PB_ON)          # push Darkfield button to ON


	# There is no equivalent info from CM for gunshift
	def getGunShift(self):
		if Debug == True:
			print 'from getGunShift'
		return NotImplementedError()


	# There is no equivalent info from CM for gunshift
	def setGunShift(self, vector, relative = 'absolute'):
		if Debug == True:
			print 'from setGunShift'
		return NotImplementedError()

	# There is no equivalent info from CM for guntilt
	def getGunTilt(self):
		if Debug == True:
			print 'from getGunTilt'
		return NotImplementedError()


	# There is no equivalent info from CM for guntilt
	def setGunTilt(self, vector, relative = 'absolute'):
		if Debug == True:
			print 'from setGunTilt'
		return NotImplementedError()


	def getStigmator(self):
		if Debug == True:
			print 'from getStigmator'
		value = {'condenser': {'x': None, 'y': None},
					'objective': {'x': None, 'y': None},
					'diffraction': {'x': None, 'y': None}}
		StigValue = self.CMLIB.GetStigmators()
		
		if StigValue.s[10] >= 0:       # C2 stigmator
			value['condenser']['x'] = (float(StigValue.s[10]) - 1050000000.0)/150000000.0
		else:
			value['condenser']['x'] = -(float(StigValue.s[10]) + 1100000000.0)/150000000.0
		if StigValue.s[21] >= 0:       # objective stigmator
			value['condenser']['y'] = (float(StigValue.s[21]) - 1050000000.0)/150000000.0
		else:
			value['condenser']['y'] = -(float(StigValue.s[21]) + 1100000000.0)/150000000.0

		if StigValue.s[4] >= 0:        # diffraction stigmator
			value['objective']['x'] = (float(StigValue.s[4]) - 1050000000.0)/150000000.0
		else:
			value['objective']['x'] = -(float(StigValue.s[4]) + 1100000000.0)/150000000.0
		if StigValue.s[6] >= 0:
			value['objective']['y'] = (float(StigValue.s[6]) - 1050000000.0)/150000000.0
		else:
			value['objective']['y'] = -(float(StigValue.s[6]) + 1100000000.0)/150000000.0

		if StigValue.s[140] >= 0:
			value['diffraction']['x'] = (float(StigValue.s[140]) - 1050000000.0)/150000000.0
		else:
			value['diffraction']['x'] = -(float(StigValue.s[140]) + 1100000000.0)/150000000.0
		if StigValue.s[142] >= 0:
			value['diffraction']['y'] = (float(StigValue.s[142]) - 1050000000.0)/150000000.0
		else:
			value['diffraction']['y'] = -(float(StigValue.s[142]) + 1100000000.0)/150000000.0
		
		return value
		
	
	def setStigmator(self, stigs, relative = 'absolute'):
		if Debug == True:
			print 'from setStigmator'
		StigValue = self.CMLIB.GetStigmators()
		for key in stigs.keys():
			if key == 'condenser':
				stigmatorX = StigValue['condenser']['x']
				stigmatorY = StigValue['condenser']['y']
			elif key == 'objective':
				stigmatorX = StigValue['objective']['x']
				stigmatorY = StigValue['objective']['y']
			elif key == 'diffraction':
				stigmatorX = StigValue['diffraction']['x']
				stigmatorY = StigValue['diffraction']['y']
			else:
				raise ValueError

			if relative == 'relative':
				if stigs[key]['x'] != None:
					stigs[key]['x'] += stigmatorX
				if stigs[key]['y'] != None:
					stigs[key]['y'] += stigmatorY

			elif relative == 'absolute':
				pass
			else:
				raise ValueError

			if stigs[key]['x'] != None:
				stigmatorX = stigs[key]['x']
			if stigs[key]['y'] != None:
				stigmatorY = stigs[key]['y']

			if key == 'condenser':
				if stigmatorX > 0:
					cmlib.CacheInfo['stigmators'].s[10] = round(stigmatorX * 150000000.0 + 1050000000.0)
				elif stigmatorX < 0:
					cmlib.CacheInfo['stigmators'].s[10] = round(-stigmatorX * 150000000.0 - 1100000000.0)
				else:
					raise ValueError
				if stigmatorY > 0:
					cmlib.CacheInfo['stigmators'].s[21] = round(stigmatorY * 150000000.0 + 1050000000.0)
				elif stigmatorY < 0:
					cmlib.CacheInfo['stigmators'].s[21] = round(-stigmatorY * 150000000.0 - 1100000000.0)
				else:
					raise ValueError
				self.CMLIB.SetStigmators('C2')
				
			elif key == 'objective':
				if stigmatorX > 0:
					cmlib.CacheInfo['stigmators'].s[4] = round(stigmatorX * 150000000.0 + 1050000000.0)
				elif stigmatorX < 0:
					cmlib.CacheInfo['stigmators'].s[4] = round(-stigmatorX * 150000000.0 - 1100000000.0)
				else:
					raise ValueError
				if stigmatorY > 0:
					cmlib.CacheInfo['stigmators'].s[6] = round(stigmatorY * 150000000.0 + 1050000000.0)
				elif stigmatorY < 0:
					cmlib.CacheInfo['stigmators'].s[6] = round(-stigmatorY * 150000000.0 - 1100000000.0)
				else:
					raise ValueError
				self.CMLIB.SetStigmators('Obj')
				
			elif key == 'diffraction':
				if stigmatorX > 0:
					cmlib.CacheInfo['stigmators'].s[140] = round(stigmatorX * 150000000.0 + 1050000000.0)
				elif stigmatorX < 0:
					cmlib.CacheInfo['stigmators'].s[140] = round(-stigmatorX * 150000000.0 - 1100000000.0)
				else:
					raise ValueError
				if stigmatorY > 0:
					cmlib.CacheInfo['stigmators'].s[142] = round(stigmatorY * 150000000.0 + 1050000000.0)
				elif stigmatorY < 0:
					cmlib.CacheInfo['stigmators'].s[142] = round(-stigmatorY * 150000000.0 - 1100000000.0)
				else:
					raise ValueError
				self.CMLIB.SetStigmators('Diff')
				
			else:
				raise ValueError


	# From what i undertanded, there is no subdivision (cartesian/conical)for darkfield mode,
	# only on/off info can be retrieved, which is different from tecnai.
	def getDarkFieldMode(self):
		if Debug == True:
			print 'from getDarkFieldMode'
		CMvar = self.CMLIB.GetCMVar()
		bool = CMvar.ButtonState & 0x004    # Based upon CM help, it should be 0x0002,however 0x0004 in emscope.
		                                    # It has been tested, 0x0004 is correct, CM help is wrong again.
		if bool == 0:
			return 'off'
		else:
			return 'on'


	def setDarkFieldMode(self, mode):
		if Debug == True:
			print 'from setDarkFieldMode'
		if mode == 'off':
			self.CMLIB.PushButton(CMCal.PB_Darkfield,CMCal.PB_OFF)
		else:
			self.CMLIB.PushButton(CMCal.PB_Darkfield,CMCal.PB_ON)


	# The spotsize index (not the actual value) need to be returned to the Leginon
	# cmremote32 can only return the actual spotsize value
	def getSpotSize(self):
		if Debug == True:
			print 'from getSpotSize'
		CMvar = self.CMLIB.GetCMVar()
		for i in range(0,11):
			if CMCal.LMSS[i] == CMvar.Spotsize:
				return i + 1
			if CMCal.HMSS[i] == CMvar.Spotsize:
				return i + 1


	def setSpotSize(self, ss, relative = 'absolute'):
		if Debug == True:
			print 'from setSpotSize'
		if relative == 'relative':
			pass
		elif relative == 'absolute':
			ss -= self.getSpotSize()	
		else:
			raise ValueError
		
		self.CMLIB.TurnKnob(CMCal.TK_SpotSize,ss)


	# From what I understand, RawImageShift and Imageshift is mode dependent,
	# Imageshift is for lowdose mode (beam/image shift), RawImageShift is for
	# HRTEM mode. the actual return variable should be the same.
	# Note, this is none unit from CM, however meter in Tecnai
	def getRawImageShift(self):
		if Debug == True:
			print 'from getRawImageShift'
		value = {'x': None, 'y': None}
		CMvar = self.CMLIB.GetCMVar()
		value['x'] = CMvar.ImageShiftX
		value['y'] = CMvar.ImageShiftY
		return value


	# From what I understand, this function is for HREM, low dose
	# is taken care of by setImagShit()
	def setRawImageShift(self, vector, relative = 'absolute'):
		if Debug == True:
			print 'setRawImageShift'
		return NotImplementedError()


	# This function maybe implemented by combinding P1-4. Not fully
	# implemented here.
	def getVacuumStatus(self):
		if Debug == True:
			print "from getVacuumStatus"
		return 'N/A for CM'

	
	# columnpressure in Tecnai is the same as P4 in CM
	def getColumnPressure(self):
		if Debug == True:
			print 'from getColumnPressure'
		IGP = self.CMLIB.PressureReadout().IGP
		return float(IGP)                      # IGP is P4


	# No corresponding retrieving info can be found from CMREMOTE
	def getColumnValvePositions(self):
		if Debug == True:
			print "from getColumnValvePositions"
		return ['open', 'closed','unknown']

	
	def getColumnValvePosition(self):
		if Debug == True:
			print 'from getColumnValvePostion'
		return 'unknown'


	def setColumnValvePosition(self, state):
		if Debug == True:
			print 'from setColumnValvePosition'
		return 'unknown'


	# No corresponding retrieving info can be found from CM
	def getTurboPump(self):
		if Debug == True:
			print "from getTurboPump"
		return 'N/A for CM'


	def setTurboPump(self, mode):
		if Debug == True:
			print "from setTurboPump"
		return NotImplementedError()


	def getFilmStock(self):
		if Debug == True:
			print 'from getFilmStock'
		stock = self.CMLIB.GetCmCamValues().stock
		return stock


	# The meaning of exposurenumber is confusing at this moment,
	# this function was not implemented yet.
	def getFilmExposureNumber(self):
		if Debug == True:
			print 'from getFilmExposureNumber'
		nr = self.cmremote32.CM_GetCmCamValues().exposure_nr
		return nr
		return NotImplementedError()


	def setFilmExposureNumber(self, value):
		if Debug == True:
			print 'from setFilmExposureNumber'
		return NotImplementedError()


	def getFilmExposureTime(self):
		if Debug == True:
			print 'from getFilmExposureTime'
		exptimemanual = self.CMLIB.GetCmCamValues().exptimemanual
		if exptimemanual:
			return self.getFilmManualExposureTime()
		else:
			return self.getFilmAutomaticExposureTime()


	def getFilmExposureTypes(self):
		if Debug == True:
			print 'from getFilmExposureTypes'
		return ['manual', 'automatic']


	def getFilmExposureType(self):
		if Debug == True:
			print 'from getFilmExposureType'
		exptimemanual = self.CMLIB.GetCmCamValues().exptimemanual
		if exptimemanual:
			return 'manual'
		else:
			return 'automatic'


	# Manual setting is expected in CM.
	def setFilmExposureType(self, value):
		if Debug == True:
			print 'from setFilmExposureType'
		return NotImplementedError()


	def getFilmAutomaticExposureTime(self):
		if Debug == True:
			print 'from getFilmAutomaticExposureTime'
		measuredexptime = self.CMLIB.GetCmCamValues().measuredexptime
		return measuredexptime


	def getFilmManualExposureTime(self):
		if Debug == True:
			print 'from getFilmManualExposureTime'
		manualsetexptime = self.CMLIB.GetCmCamValues().manualsetexptime
		return manualsetexptime


	def setFilmManualExposureTime(self, value):
		if Debug == True:
			print 'from setFilmManualExposureTime'
		return NotImplementedError()


	# This feature is not supported by cmremote, a seperate software
	# called FilmText can provide this function. By calling its functions
	# in the dll, this feature should be able to implemented.
	def getFilmUserCode(self):
		if Debug == True:
			print 'from getFilmUserCode'
		return str('Min')


	def setFilmUserCode(self, value):
		if Debug == True:
			print 'from setFilmUserCode'
		return NotImplementedError()


	def getFilmDateTypes(self):
		if Debug == True:
			print 'from getFilmDateTypes'
		return ['no date', 'DD-MM-YY', 'MM/DD/YY', 'YY.MM.DD', 'unknown']


	def getFilmDateType(self):
		if Debug == True:
			print 'from getFilmDateType'
		return 'unknown'
##		return NotImplementedError()


	def setFilmDateType(self, value):
		if Debug == True:
			print 'from setFilmDateType'
		return NotImplementedError()

	
	def getFilmText(self):
		if Debug == True:
			print 'from getFilmText'
		return str('Min Su implemented')


	# This function should be able to be implemented
	# refer to Tutor for detail, not critical at this moment
	def setFilmText(self, value):
		if Debug == True:
			print 'from setFilmText'
		return NotImplementedError()

	
	def getShutter(self):
		if Debug == True:
			print 'from getShutter'
		return 'unknown'


	def setShutter(self, state):
		if Debug == True:
			print 'from setShutter'
		return NotImplementedError()


	def getShutterPositions(self):
		if Debug == True:
			print 'from getShutterPositions'
		return ['open', 'closed','unknown']


	def getExternalShutterStates(self):
		if Debug == True:
			print 'from getExternalShutterStates'
		return ['connected', 'disconnected','unknown']

	def getExternalShutter(self):     # no external shutter available from CM
		if Debug == True:
			print 'from getExternalShutter'
		return 'unknown'


	def setExternalShutter(self, state):
		if Debug == True:
			print 'from setExternalShutter'
		return NotImplementedError()


	def normalizeLens(self, lens = 'all'):
		if Debug == True:
			print 'from normalizeLens'
		return NotImplementedError()


	# small screen must be down, unit in Ampire
	def getScreenCurrent(self):
		if Debug == True:
			print 'from getScreenCurrent'
		ScreenCurrent = self.CMLIB.ScreenCurrent()
		return float(ScreenCurrent)


	def getMainScreenPositions(self):
		if Debug == True:
			print 'from getMainScreenPositions'
		return ['up', 'down', 'unknown']


	def setMainScreenPosition(self, mode):
		if Debug == True:
			print 'from setMainScreenPositions'
		return NotImplementedError()


	def getMainScreenPosition(self):
		if Debug == True:
			print 'from getManinScreenPostion'
		CMvar = self.CMLIB.GetCMVar()
		if CMvar.MainScrn == 255:
			return 'up'
		elif CMvar.MainScrn == 0:
			return 'down'
		else:
			return 'unknown'


	# NO direct retrieval info to test smallscreen position.
	# It could be done by checking the dose reading compare with Mainscreen,
	# but it seems not worth to make this effort here.
	def getSmallScreenPosition(self):
		if Debug == True:
			print 'from getSmallScreenPosition' 
		return 'unknown'                
			                            

	# This is not critical for Leginon, it could be supported by CM.
	def getHolderStatus(self):
		if Debug == True:
			print 'from getHolderStatus'
		HolderInserted = self.CMLIB.GetCMInfo().HolderInserted
		if HolderInserted == 1:
			return 'Inserted'
		else:
			return 'Not Inserted'


	def getHolderTypes(self):
		if Debug == True:
			print 'from getHolderTypes'
		return ['no holder', 'single tilt', 'cryo', 'unknown','N/A']


	def getHolderType(self):
		if Debug == True:
			print 'from getHolderType'
		return 'cryo'

	# not critical for Leginon runing
	def setHolderType(self, holdertype):
		if Debug == True:
			print 'from setHolderType'
		return NotImplementedError()


	# low dose functions don't have to be implemented,
	# Leginon PresetManager node will take care of it internally.
	def getLowDoseModes(self):
		if Debug == True:
			print 'from getLowDoseModes'
		return ['exposure', 'focus1', 'focus2', 'search', 'unknown', 'disabled']


	def getLowDoseMode(self):
		if Debug == True:
			print 'from getLowDoseMode'
		return 'unknown'


	def setLowDoseMode(self, mode):
		if Debug == True:
			print 'setLowDoseMode'
		return NotImplementedError()


	def getLowDoseStates(self):
		if Debug == True:
			print 'from getLowDoseStates'
		return ['on', 'off', 'disabled','unknown']


	def getLowDose(self):
		if Debug == True:
			print 'from getLowDose'
		return 'unknown'


	def setLowDose(self, ld):
		if Debug == True:
			print 'from setLowDose'
		return NotImplementedError()


	def getStageStatus(self):
		if Debug == True:
			print 'from getStageStatus'
		return 'unknown'		# This info is not availabe from CM	


	# some pressure values can be retrieved from CM,
	# however they are not equivalent to tecnai in the function.
	def getVacuumStatus(self):
		if Debug == True:
			print 'from getVacuumStatus'
		return 'unknown'


	def preFilmExposure(self, value):
		if Debug == True:
			print 'from preFilmExposure'
		return NotImplementedError()


	def postFilmExposure(self, value):
		if Debug == True:
			print 'from postFilmExposure'
		return NotImplementedError()


	def filmExposure(self, value):
		if Debug == True:
			print 'from filmExposure'
		return NotImplementedError()


	# This is no retrieving info to show the status of beamblank
	def getBeamBlank(self):
		if Debug == True:
			print 'from getBeamBlank'
		return 'unknown'

		
	def setBeamBlank(self, bb):
		if Debug == True:
			print 'from setBeamBlank'
		if bb == 'off' :
			self.CMLIB.DirectOperation(CMCal.DO_BeamBlankOFF,0)   # the second arg is no function here
		elif bb == 'on':
			self.CMLIB.DirectOperation(CMCal.DO_BeamBlankON,0)    # the second arg is no function here
		else:
			raise ValueError

	# get/setDiffractionMode is not critical for low dose purpose,
	# they should be able to be implemented with cmlib.CMLIB.get/setMode
	# though the meaning of get/setMode is not well documented
	def getDiffractionMode(self):
		if Debug == True:
			print 'from getDiffractionMode'
		return NotImplementedError()
		
		
	def setDiffractionMode(self, mode):
		if Debug == True:
			print 'from setDiffractionMode'
		return NotImplementedError()


	def runBufferCycle(self):
		if Debug == True:
			print 'from runBufferCycle'
		return NotImplementedError()
