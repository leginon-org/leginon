# joel1230lib.py is base Library for jeol 1230 microscope
# Copyright by New York Structural Biology Center
# import serial
# ser = serial.Serial(port='COM1', baudrate=9600, bytesize=8, parity='N', stopbits=1, timeout=10, xonxoff=1, rtscts=0)
# from pyScope import jeol1230lib ; j = jeol1230lib.jeol1230lib(); j.getStagePosition()

import os
import inspect
import time
import serial
from ctypes import *

Debug = False

# constants for Jeol Hex value
MAX = 65535
# coarse-fine ratio for OL and OM
COARSE_SCALE = 32


class jeol1230lib(object):
	name = 'jeol1230 library'
	
	# initialize serial port communication, magnification and eucentric focus
	def __init__(self):
		self.ser = serial.Serial(port='COM1', baudrate=9600, bytesize=8, parity='N', stopbits=1, xonxoff = 0, timeout=10, rtscts=0)
		self.lowMag = [50, 60, 80, 100, 120, 150, 200, 250, 300, 400, 500, 600, 800]
		self.highMag = [1000, 1200, 1500, 2000, 2500, 3000, 4000, 5000, 6000, 8000, 10000, 12000, 15000, 20000, 25000, 30000, 40000, 50000, 60000, 80000, 100000, 120000, 150000, 200000, 250000, 300000, 400000, 500000]									# 28 SA mags
		self.magnification = self.lowMag + self.highMag
		self.equipmentAvailable()
		this_file = inspect.currentframe().f_code.co_filename
		fullmod = os.path.abspath(this_file)
		self.defocusFile = os.path.join(os.path.dirname(fullmod),'defocus.cfg')
		self.zeroDefocus = {'zero_time': None, 'zero_oml': None, 'zero_omh': None,'zero_oll': None, 'zero_olh': None}
		self.zeroDefocus = self.readZeroDefocus()
		self.zero_oml = int(self.zeroDefocus['zero_oml'])
		self.zero_omh = int(self.zeroDefocus['zero_omh'])
		self.zero_oll = int(self.zeroDefocus['zero_oll'])									# specific to jeol1230
		self.zero_olh = int(self.zeroDefocus['zero_olh'])
		self.wait_time = 0.1

	# read four lens currents correspondint to eucentric focus, two for lowMag, two for highMag
	def readZeroDefocus(self):
		zeroDefocus = {'zero_time': None, 'zero_oml': None, 'zero_omh': None,'zero_oll': None,'zero_olh': None}
		infile = open(self.defocusFile,"r")
		lines = infile.readlines()
		line = lines[0]
		zeroDefocus['zero_time'] = line[:-1]
		line = lines[1]
		zeroDefocus['zero_oml'] = line[:-1]
		line = lines[2]
		zeroDefocus['zero_omh'] = line[:-1]
		line = lines[3]
		zeroDefocus['zero_oll'] = line[:-1]
		line = lines[4]
		zeroDefocus['zero_olh'] = line[:-1]
		infile.close()
		return zeroDefocus

	# save four lens currents correspondint to eucentric focus, two for lowMag, two for highMag
	def saveZeroDefocus(self, zeroDefocusType, value):
		zeroDefocus = {'zero_time': None,'zero_oml': None, 'zero_omh': None, 'zero_oll': None, 'zero_olh': None}
		zeroDefocus = self.readZeroDefocus()
		zeroDefocus['zero_time'] = time.time()
		if zeroDefocusType == 'zero_time':
			zeroDefocus['zero_time'] = value
		elif zeroDefocusType == 'zero_oml':
			zeroDefocus['zero_oml'] = value
		elif zeroDefocusType == 'zero_omh':
			zeroDefocus['zero_omh'] = value
		elif zeroDefocusType == 'zero_oll':
			zeroDefocus['zero_oll'] = value
		else:
			zeroDefocus['zero_olh'] = value
		outfile = open(self.defocusFile,"w")
		outfile.write(str(zeroDefocus['zero_time']) + '\n')
		outfile.write(str(zeroDefocus['zero_oml']) + '\n')
		outfile.write(str(zeroDefocus['zero_omh']) + '\n')
		outfile.write(str(zeroDefocus['zero_oll']) + '\n')
		outfile.write(str(zeroDefocus['zero_olh']) + '\n')
		outfile.close()
		return True

	# check serial port communication to microscope
	def equipmentAvailable(self):
		if Debug == True:
			print 'from jeol1230lib.py equipmentAvailable'
		model   = "jeol"
		version = "1230"
		if self.ser.portstr == 'COM1' and self.ser.isOpen():
			if Debug == True:
				print "    Microscope Model: %s  Version: %s" % (model, version)
			return True
		else:
			if Debug == True:
				print "    Serial port can not be initialized by pyScope"
			return False

	# check if high tension is on or off
	def getHighTensionState(self):
		if Debug == True:
			print 'from jeol1230lib.py getHighTensionStatus'
		highTensionStatus = 'unknown'
		while True:
			self.ser.flushInput()
			self.ser.flushOutput()
			ss = '050' + '\r'
			self.ser.write(ss)
			c = ''
			while True:
				newc = self.ser.read()
				if newc == '\r':
					break
				c = c + newc
			words = c.split()
			if words[0] == '050' and words[1] == '000':
				if words[2] == '1':
					highTensionStatus = 'on'
				else:
					highTensionStatus = 'off'
				break
			time.sleep(self.wait_time)
		return highTensionStatus

	# get the high tension voltage value
	def getHighTension(self):
		if Debug == True:
			print 'from jeol1230lib.py getHighTension'
		while True:
			self.ser.flushInput()
			self.ser.flushOutput()
			ss = '050' + '\r'
			self.ser.write(ss)
			c = ''
			while True:
				newc = self.ser.read()
				if newc == '\r':
					break
				c = c + newc
			words = c.split()
			if words[0] == '050' and words[1] == '000':
				highTension = words[4]
				break
			time.sleep(self.wait_time)
		return int(highTension)

	# set high tension on or off
	def setHighTension(self, mode='off'):
		if Debug == True:
			print 'from jeol1230lib.py setHighTension'
		if mode == 'off':
			value = '0'
		elif mode == 'on':
			value = '1'
		else:
			return False
		self.ser.flushInput()
		self.ser.flushOutput()
		ss = '001' + '\t' + str(value) + '\r'
		self.ser.write(ss)
		return True

	# even doesn't do anything, leginon needs this
	def setTurboPump(self, mode):
		return True

	# set beam on or off
	def setBeamState(self, mode):
		if Debug == True:
			print 'from jeol1230lib.py setBeamState'
		if mode == 'on':
			value = '1'
		elif mode == 'off':
			value = '0'
		else:
			return False
		timesTried = 0
		while True:
			self.ser.flushInput()
			self.ser.flushOutput()
			ss = '003' + '\t' + value + '\r'
			self.ser.write(ss)
			c = ''
			while True:
				newc = self.ser.read()
				if newc == '\r':
					break
				c = c + newc
			words = c.split()
			if words[0] == '003' and words[2] == '000':
				break
				if timesTried >= 3:
					return False
			++timesTried
			time.sleep(self.wait_time)
		return True

	# check if beam is on or off
	def getBeamState(self):
		if Debug == True:
			print 'from jeol1230lib.py getBeamState'
		beamState = 'unknown'
		while True:
			self.ser.flushInput()
			self.ser.flushOutput()
			ss = '050' + '\r'
			self.ser.write(ss)
			c = ''
			while True:
				newc = self.ser.read()
				if newc == '\r':
					break
				c = c + newc
			words = c.split()
			if words[0] == '050' and words[1] == '000':
				if words[5] == '1':
					beamState = 'on'
				else:
					beamState = 'off'
				break
			time.sleep(self.wait_time)
		return beamState

	# get current magnification
	def getMagnification(self):
		if Debug == True:
			print 'from jeol1230lib.py getMagnification'
		Magn = 0
		while True:
			self.ser.flushInput()
			self.ser.flushOutput()
			self.ser.write('152\r')
			c = ''
			while True:
				newc = self.ser.read()
				if newc == '\r':
					break
				c = c + newc
			words = c.split()
			if words[0] == '152' and words[1] == '000':
				magWithX = words[len(words)-2]
				length = len(magWithX)
				if magWithX[0] == '*':
					start = 2
				else:
					start = 1
				if magWithX[length-1:] == 'k':
					end = length - 1
					mul = 1000
				else:
					end = length
					mul = 1
				Magn = int(magWithX[start:end])*mul
				break
			time.sleep(self.wait_time)
		return int(Magn)

	# set magnification to EM, here mag is a string, not a number
	def setMagnification(self, mag):
		if Debug == True:
			print 'from jeol1230lib.py setMagnification'
		magRange = 40
		for i in range(0,magRange):
			if int(mag) <= self.magnification[i]:
				break
		if i > magRange:
			print '    Magnification out of range'
			return False
		while True:
			self.ser.flushInput()
			self.ser.flushOutput()
			if i < 13:
				self.ser.write ('106\t0\r')	# use low mag mode
			else:
				i = i - 13
				self.ser.write ('106\t1\r')	# use high mag mode
			c = ''
			while True:
				newc = self.ser.read()
				if newc == '\r':
					break
				c = c + newc
			words = c.split()
			if words[0] == '106' and words[1] == '000':
				break
			time.sleep(self.wait_time)
		while True:
			self.ser.flushInput()
			self.ser.flushOutput()
			ss = '107' + '\t' + str(i) + '\r'
			self.ser.write(ss)
			c = ''
			while True:
				newc = self.ser.read()
				if newc == '\r':
					break
				c = c + newc
			words = c.split()
			if words[0] == '107' and words[1] == '000':
				break
			time.sleep(self.wait_time)
		return True

	# get current spot size
	def getSpotSize(self):
		if Debug == True:
			print 'from jeol1230lib.py getSpotSize'
		while True:
			self.ser.flushInput()
			self.ser.flushOutput()
			self.ser.write('150\t0\r')
			c = ''
			while True:
				newc = self.ser.read()
				if newc == '\r':
					break
				c = c + newc
			words = c.split()
			if words[0] == '150' and words[1] == '000':
				break
			time.sleep(self.wait_time)
		cl1 = words[2]
		Magn = self.getMagnification()		# get cl1 value
		if Magn >= 1000:
			if int(cl1,16) < 11520:
				spotsize = 1
			elif int(cl1,16) < 13312:
				spotsize = 2
			elif int(cl1,16) < 20736:
				spotsize = 3
			elif int(cl1,16) < 35072:
				spotsize = 4
			else:
				spotsize = 5
		else:
			if int(cl1,16) < 13040:
				spotsize = 1
			elif int(cl1,16) < 14920:
				spotsize = 2
			elif int(cl1,16) < 20240:
				spotsize = 3
			elif int(cl1,16) < 29744:
				spotsize = 4
			else:
				spotsize = 5
		return int(spotsize)

	# set spot size to EM
	def setSpotSize(self, size):
		if Debug == True:
			print 'from jeol1230lib.py setSpotSize'
		if int(size) > 5 or int(size) < 0:
			print '    Spotsize is out of range'
			return False
		ssize = int(size) - 1
		ss = '109' + '\t' + str(ssize) + '\r'
		while True:
			self.ser.flushInput()
			self.ser.flushOutput()
			self.ser.write(ss)
			c = ''
			while True:
				newc = self.ser.read()
				if newc == '\r':
					break
				c = c + newc
			words = c.split()
			if words[0] == '109' and words[1] == '000':
				break
			time.sleep(self.wait_time)
		return True

	# reads the current x,y,z in micrometer, a (tilt) in degree
	def getStagePosition(self):
		if Debug == True:
			print 'from jeol1230lib.py getStagePosition'
		position = {'x': None, 'y': None, 'z': None, 'a': None}
		while True:
			self.ser.flushInput()
			self.ser.flushOutput()
			self.ser.write ('250\r')
			c = ''
			while True:
				newc = self.ser.read()
				if newc == '\r':
					break
				c = c + newc
			words = c.split()
			if words[0] == '250' and words[1] == '000':
				position['x'] = float(words[2])/1000.0
				position['y'] = float(words[4])/1000.0
				break
			time.sleep(self.wait_time)
		while True:
			self.ser.flushInput()
			self.ser.flushOutput()
			self.ser.write ('251\r')
			c = ''
			while True:
				newc = self.ser.read()
				if newc == '\r':
					break
				c = c + newc
			words = c.split()
			if words[0] == '251' and words[1] == '000':
				position['z'] = float(words[2])/1000.0
				position['a'] = float(words[4])/10.0
				break
			time.sleep(self.wait_time)
		return position

	# move/rotate the stage only in one direction by micrometer or deg
	def setStagePosition(self,axis,coord,mode):
		if Debug == True:
			print 'from jeol1230lib.py setStagePosition'
		if mode == 'fine':
			dm = '1'		# driving mode: 0(fine), 1(medium), 2(coarse)
			sc = '50'		# speed coefficient: 1-100
		else:
			dm = '2'
			sc = '100'
		ml = '0'
		ct = '\t'
		minimum_stage = {'x': 0.1, 'y': 0.1, 'z': 0.1, 'a': 0.1}
		maximum_stage = {'x': 1000.0, 'y': 1000.0, 'z': 400.0, 'a': 20.0}
		stagenow = {'x': None, 'y': None, 'z': None, 'a': None}
		stagenow = self.getStagePosition()
		if abs(coord - stagenow[axis]) < minimum_stage[axis]:
			if Debug == True:
				print '   %s Move is too small: %d' %(axis, abs(coord - stagenow[axis]))
			return	False
		if abs(coord) > maximum_stage[axis]:
			if Debug == True:
				print '    %s Move is too large: %d' %(axis, abs(coord))
			return	False
		if axis == 'x':
			c_axis = '0'
			c_coord = int(coord * 1000.0)
			ss = '201' + ct + c_axis + ct + str(c_coord) + ct + dm + ct + sc + ct + ml + '\r'
		elif axis == 'y':
			c_axis = '1'
			c_coord = int(coord * 1000.0)
			ss = '201' + ct + c_axis + ct + str(c_coord) + ct + dm + ct + sc + ct + ml + '\r'
		elif axis == 'z':
			c_coord =  int(coord * 1000.0)
			dm = '1'
			sc = '50'
			ss = '203' + ct + str(c_coord) + ct + dm + ct + sc + '\r'
		elif axis == 'a':
			c_axis = '0'
			c_coord = int(coord * 10.0)
			dm = '2'
			sc = '50'
			ss = '205' + ct + c_axis + ct + str(c_coord) + ct + dm + ct + sc + '\r'
		else:
			return False
		self.ser.flushInput()
		self.ser.flushOutput()
		self.ser.write(ss)
		time.sleep(1)
		i = 0
		while True:
			i = i + 1
			self.ser.flushInput()
			self.ser.flushOutput()
			if axis == 'x' or axis == 'y':
				ss = '250' + '\r'
			elif axis == 'z' or axis == 'a':
				ss = '251' + '\r'
			else:
				return False
			self.ser.write(ss)
			c = ''
			while True:
				newc = self.ser.read()
				if newc == '\r':
					break
				c = c + newc
				words = c.split()
			if axis == 'x' or axis == 'z':
				r = words[3]
			else:
				r = words[5]
			db1 = (int(r) >> 1) & 1
			db2 = (int(r) >> 2) & 1
			if Debug == True:
				print "    Stage is moving, please wait"
			if db2 == 0:
				if Debug == True:
					print "    Stage movement in %s mode was sucessfull" % mode
				break
			if i > 15:
				if Debug == True:
					print "    Too long and terminate the movement"
				self.ser.flushInput()
				self.ser.flushOutput()
				self.ser.write('206\r')	# terminate stage movement
				break
			time.sleep(self.wait_time + 4)
		return True

	# read beam intensity from condenser lens
	def getIntensity(self):
		if Debug == True:
			print 'from jeol1230lib.py getIntensity'
		while True:
			self.ser.flushInput()
			self.ser.flushOutput()
			self.ser.write('150\t0\r')
			c = ''
			while True:
				newc = self.ser.read()
				if newc == '\r':
					break
				c = c + newc
			words = c.split()
			if words[0] == '150' and words[1] == '000':
				break
			time.sleep(self.wait_time)
		cl3 = words[3]
		intensity = int(cl3,16)
		return int(intensity)

	# set beam intensity by condenser lens using relative value
	def setIntensity(self, intensity):
		if Debug == True:
			print 'from jeol1230lib.py setIntenstiy'
		cl3 = int(intensity) - self.getIntensity()
		while True:
			self.ser.flushInput()
			self.ser.flushOutput()
			ss_cl3 = '102' + '\t' + '3' + '\t' + str(cl3) + '\r'	# set cl3
			self.ser.write(ss_cl3)
			c = ''
			while True:
				newc = self.ser.read()
				if newc == '\r':
					break
				c = c + newc
			words = c.split()
			if words[0] == '102' and words[1] == '000':
				break
			time.sleep(self.wait_time)
		return True

	def toOLcOLf(self,ticks):
		'''
		relative value conversion only, works for both ol and om
		'''
		coarse_ticks = ticks / COARSE_SCALE
		fine_ticks = ticks % COARSE_SCALE
		return coarse_ticks, fine_ticks

	def fromOLcOLf(self,OLc, OLf):
		'''
		Convert to current
		'''
		return OLc * COARSE_SCALE + OLf

	# get objective lens input raw values
	def getRawObjectiveInputs(self):
		if Debug == True:
			print 'from jeol1230lib.py getRawObjectiveInputs'
		while True:
			self.ser.flushInput()
			self.ser.flushOutput()
			self.ser.write('150\t0\r')
			c = ''
			while True:
				newc = self.ser.read()
				if newc == '\r':
					break
				c = c + newc
			words = c.split()
			if words[0] == '150' and words[1] == '000':
				break
			time.sleep(self.wait_time)
		# convert from hex
		oll = int(words[8],16)
		olh = int(words[9],16)
		oml = int(words[10],16)
		omh = int(words[11],16)
		if Debug == True:
			print 'oll %x, olh %x' % (oll, olh)
			print 'oml %x, omh %x' % (oml, omh)
		return oll,olh,oml,omh

	# get objective lens currents
	def getObjectiveCurrent(self):
		'''
		Get objective lens absolute current as a combination of
		high gain (coarse) and low gain (fine) knobs
		'''
		oll,olh,oml,omh = self.getRawObjectiveInputs()
		if self.getMagnification() >= 1000:
			current = self.fromOLcOLf(olh, oll)
		else:
			current = self.fromOLcOLf(omh, oml)
		return int(current)

	# set obj len currents using relative values; direct lens control is bad
	def setObjectiveCurrent(self,current):
		'''
		Set objective lens absolute current as a combination of
		high gain (coarse) and low gain (fine) knobs.
		'''
		if Debug == True:
			print 'from jeol1230lib.py setObjectiveCurrent'
		# get current input values
		oll,olh,oml,omh = self.getRawObjectiveInputs()
		if self.getMagnification() >= 1000:
			code_1 = '9'
			code_2 = '10'
			low_gain_ticks = oll
			high_gain_ticks = olh
		else:
			code_1 = '11'
			code_2 = '12'
			low_gain_ticks = oml
			high_gain_ticks = omh
		c_current = self.getObjectiveCurrent()
		# The adjustment is relative
		diff_current = current - c_current
		h,l = self.toOLcOLf(int(diff_current))

		# Change only low_gain_ticks if the new value can be
		# in the middle range of the knob.
		expected_new_low_gain_ticks = h*COARSE_SCALE+low_gain_ticks+l
		if abs(expected_new_low_gain_ticks) < MAX*3/4 and abs(expected_new_low_gain_ticks) > MAX/4:
			h = 0
			l = diff_current

		# The adjustment is relative
		ss_l = '102' + '\t' + code_1 + '\t' + str(l) + '\r'
		while True:
			self.ser.flushInput()
			self.ser.flushOutput()
			self.ser.write(ss_l)
			c = ''
			while True:
				newc = self.ser.read()
				if newc == '\r':
					break
				c = c + newc
			words = c.split()
			if words[0] == '102' and words[1] == '000':
				break
			time.sleep(self.wait_time)
		time.sleep(1)
		ss_h = '102' + '\t' + code_2 + '\t' + str(h) + '\r'
		while True:
			self.ser.flushInput()
			self.ser.flushOutput()
			self.ser.write(ss_h)
			c = ''
			while True:
				newc = self.ser.read()
				if newc == '\r':
					break
				c = c + newc
			words = c.split()
			if words[0] == '102' and words[1] == '000':
				break
			time.sleep(self.wait_time)
		return True

	# get defocus value in meter
	def getDefocus(self):
		# BUG? getDefocus is based on oll/oml only
		if Debug == True:
			print 'from jeol1230lib.py getDefocus'
		focus = self.getRawFocus()
		if self.getMagnification() >= 1000:
			defocus = ((focus-self.zero_oll)*0.0048)/1e6
		else:
			defocus = ((focus-self.zero_oml)*0.0048)/1e6
		return float(defocus)
	
	def getRawFocus(self):
		'''
		Get unscaled focus value
		'''
		# BUG? getRwFocus is based on oll/oml only

		oll,olh,oml,omh = self.getRawObjectiveInputs()

		if self.getMagnification() >= 1000:
			# BUG? This assumes that olh is never changed
			focus = oll
		else:
			# BUG? This assumes that omh is never changed
			focus = oml
		return focus

	# set defocus value in meter
	def setDefocus(self,defocus):
		if Debug == True:
			print 'from jeol1230lib.py setDefocus'
		# getDefocus is based on oll/oml only
		rel_focus = float(defocus) - self.getDefocus()
		state = self.setRelativeFocus(rel_focus)
		return state

	def setRelativeFocus(self,rel_focus):
		# read current ol and om values from register 150
		currnt_oll,current_olh,current_oml,current_omh = self.getRawObjectiveInputs()
		# difference between current olh/omh and zerodefocus is used to change olh/omh
		diff_olh = self.zero_olh - current_olh
		diff_omh = self.zero_omh - current_omh
		flag = False
		# First set relative to current
		if self.getMagnification() >= 1000:
			code_1 = '9'
			code_2 = '10'
			# rel_defocus is handled by oll
			# BUG ? If rel_focus is large, this will be over limit
			diff_oll = int(rel_focus*1e6*210)
			ss_l = '102' + '\t' + code_1 + '\t' + str(diff_oll) + '\r'
			ss_h = '102' + '\t' + code_2 + '\t' + str(diff_olh) + '\r'
			if diff_olh != 0:
				# set olh, too
				flag = True
		else:
			code_1 = '11'
			code_2 = '12'
			# rel_focus is expected to be small enough to be handled by oml
			diff_oml = int(rel_focus*1e6*210)
			ss_l = '102' + '\t' + code_1 + '\t' + str(diff_oml) + '\r'
			ss_h = '102' + '\t' + code_2 + '\t' + str(diff_omh) + '\r'
			if diff_omh != 0:
				flag = True
		# Then set difference between zerodefocus and current
		# flag is true if olh or omh need to be set
		if flag == True:
			while True:
				self.ser.flushInput()
				self.ser.flushOutput()
				self.ser.write(ss_h)
				c = ''
				while True:
					newc = self.ser.read()
					if newc == '\r':
						break
					c = c + newc
				words = c.split()
				if words[0] == '102' and words[1] == '000':
					break
				time.sleep(self.wait_time)
		# set oll and oml values
		while True:
			self.ser.flushInput()
			self.ser.flushOutput()
			self.ser.write(ss_l)
			c = ''
			while True:
				newc = self.ser.read()
				if newc == '\r':
					break
				c = c + newc
			words = c.split()
			if words[0] == '102' and words[1] == '000':
				break
			time.sleep(self.wait_time)
		### NOTE from Anchi ####
		### setting of focus value is slow.  If getRawFocus right away
		### it shows that the value is not reached
		return True

	# set obj lens currents (defocus value) to eucentric focus
	def resetDefocus(self, value = 0):
		if Debug == True:
			print 'from jeol1230lib.py resetDefocus'
		oll,olh,oml,omh = self.getRawObjectiveInputs()
		if self.getMagnification() > 1000:
			self.zero_oll = oll
			self.zero_olh = olh
			self.saveZeroDefocus('zero_oll', self.zero_oll)
			self.saveZeroDefocus('zero_olh', self.zero_olh)
		else:
			self.zero_oml = oml
			self.zero_omh = omh
			self.saveZeroDefocus('zero_oml', self.zero_oml)
			self.saveZeroDefocus('zero_omh', self.zero_omh)
		self.saveZeroDefocus('zero_time', time.time())
		return True

	# get beam shift X and Y
	def getBeamShift(self):
		if Debug == True:
			print 'from jeol1230lib.py getBeamShift'
		while True:
			self.ser.flushInput()
			self.ser.flushOutput()
			self.ser.write('151\t3\r')
			c = ''
			while True:
				newc = self.ser.read()
				if newc == '\r':
					break
				c = c + newc
			words = c.split()
			if words[0] == '151' and words[1] == '000':
				break
			time.sleep(self.wait_time)
		beamshift = {'x': None, 'y': None}
		beamshift['x'] = int(words[2],16)*1.20e-8 - 32768*1.20e-8
		beamshift['y'] = int(words[3],16)*1.20e-8 - 32768*1.20e-8
		return beamshift

	# set beam shift X and Y
	def setBeamShift(self,axis,value):
		if Debug == True:
			print 'from jeol1230lib.py setBeamShift'
		if axis == 'x':
			code = '5'
		else:
			code = '6'
		sh = "%x" % int((float(value) + 32768*1.20e-8)/1.20e-8)
		ss = '104' + '\t' + code + '\t' + str(sh) + '\r'
		while True:
			self.ser.flushInput()
			self.ser.flushOutput()
			self.ser.write(ss)
			c = ''
			while True:
				newc = self.ser.read()
				if newc == '\r':
					break
				c = c + newc
			words = c.split()
			if words[0] == '104' and words[1] == '000':
				break
			time.sleep(self.wait_time)
		return True

	# get beam tilt X and Y
	def getBeamTilt(self):
		if Debug == True:
			print 'from jeol1230lib.py getBeamTilt'
		while True:
			self.ser.flushInput()
			self.ser.flushOutput()
			self.ser.write('151\t4\r')
			c = ''
			while True:
				newc = self.ser.read()
				if newc == '\r':
					break
				c = c + newc
			words = c.split()
			if words[0] == '151' and words[1] == '000':
				break
			time.sleep(self.wait_time)
		beamtilt = {'x': None, 'y': None}
		beamtilt['x'] = int(words[2],16)*1.25e-6 - 32858*1.25e-6
		beamtilt['y'] = int(words[3],16)*1.25e-6 - 32858*1.25e-6
		return beamtilt

	# set beam tilt X or Y
	def setBeamTilt(self,axis,value):
		if Debug == True:
			print 'from jeol1230lib.py setBeamTilt'
		sh = "%x" % int((float(value) + 32858*1.25e-6)/1.25e-6)
		if Debug == True:
			print "    Image tilt will be %d in %s direction" % (sh, axis)
		if axis == 'x':
			code = '7'
		else:
			code = '8'
		ss = '104' + '\t' + code + '\t' + str(sh) + '\r'
		while True:
			self.ser.flushInput()
			self.ser.flushOutput()
			self.ser.write(ss)
			c = ''
			while True:
				newc = self.ser.read()
				if newc == '\r':
					break
				c = c + newc
			words = c.split()
			if words[0] == '104' and words[1] == '000':
				break
			time.sleep(self.wait_time)
		return True

	# get image shift X and Y
	def getImageShift(self):
		if Debug == True:
			print 'from jeol1230lib.py getImageShift'
		while True:
			self.ser.flushInput()
			self.ser.flushOutput()
			self.ser.write('151\t5\r')
			c = ''
			while True:
				newc = self.ser.read()
				if newc == '\r':
					break
				c = c + newc
			words = c.split()
			if words[0] == '151' and words[1] == '000':
				break
			time.sleep(self.wait_time)
		imageshift = {'x': None, 'y': None}
		if self.getMagnification() >= 1000:
			imageshift['x'] = int(words[2],16)*3.057e-10 - 32768*3.057e-10
			imageshift['y'] = int(words[3],16)*3.057e-10 - 32768*3.057e-10
		else:
			#good for 200x
			#imageshift['x'] = int(words[2],16)*4.375e-9 - 32768*4.375e-9
			#imageshift['y'] = int(words[3],16)*4.375e-9 - 32768*4.375e-9
			#good for 120x
			imageshift['x'] = int(words[2],16)*2.82e-9 - 32768*2.82e-9
			imageshift['y'] = int(words[3],16)*2.82e-9 - 32768*2.82e-9
		return imageshift

	# set Imageshift X and Y
	def setImageShift(self,axis,value):
		if Debug == True:
			print 'from jeol1230lib.py setImageShift'
		if axis == 'x':
			code = '9'
		else:
			code = '10'
		if self.getMagnification() >= 1000:
			sh = "%x" % int((float(value) + 32768*3.057e-10)/3.057e-10)
		else:
			sh = "%x" % int((float(value) + 32768*2.82e-9)/2.82e-9)
		ss = '104' + '\t' + code + '\t' + str(sh) + '\r'
		itr = 0
		while True:
			self.ser.flushInput()
			self.ser.flushOutput()
			self.ser.write(ss)
			c = ''
			while True:
				newc = self.ser.read()
				if newc == '\r':
					break
				c = c + newc
			words = c.split()
			if words[0] == '104' and words[1] == '000':
				break
			itr += 1
			time.sleep(self.wait_time)
			if itr > 5:
				print 'setImageShift failed', value
				break
		return True

	# retrieve all the stigmators setting as a single block
	def getStigmator(self):
		if Debug == True:
			print 'from jeol1230lib.py getStigmator'
		while True:
			self.ser.flushInput()
			self.ser.flushOutput()
			self.ser.write('151\t0\r')
			c = ''
			while True:
				newc = self.ser.read()
				if newc == '\r':
					break
				c = c + newc
			words = c.split()
			if words[0] == '151' and words[1] == '000':
				break
			time.sleep(self.wait_time)
		stigs = {'condenser': {'x': None, 'y': None},
					'objective': {'x': None, 'y': None},
					'diffraction': {'x': None, 'y': None}}
		stigs['condenser']['x'] = int(words[16],16)
		stigs['condenser']['y'] = int(words[17],16)
		stigs['objective']['x'] = int(words[18],16)
		stigs['objective']['y'] = int(words[19],16)
		stigs['diffraction']['x'] = int(words[20],16)
		stigs['diffraction']['y'] = int(words[21],16)
		return stigs

	# set all the stigmators setting as a single block
	def setStigmator(self, key, axis, value):
		if Debug == True:
			print 'from jeol1230lib.py setStigmator'
		if self.getMagnification() <= 1000:
			print "stigmator doesn't work in low mag mode"
			return False
		if key == 'condenser':
			if axis == 'x':
				code = '15'
			else:
				code = '16'
		elif key == 'objective':
			if axis == 'x':
				code = '17'
			else:
				code = '18'
		else:
			if axis == 'x':
				code = '19'
			else:
				code = '20'
		sh = "%x" % int(value)
		ss = '104' + '\t' + code + '\t' + str(sh) + '\r'
		while True:
			self.ser.flushInput()
			self.ser.flushOutput()
			self.ser.write(ss)
			c = ''
			while True:
				newc = self.ser.read()
				if newc == '\r':
					break
				c = c + newc
			words = c.split()
			if words[0] == '104' and words[1] == '000':
				break
			time.sleep(self.wait_time)
		return True

	# read presure, it requires such a data structure
	def PressureReadout(self):
		if Debug == True:
			print 'from jeol1230lib.py PressureReadout'
		pressures = {'P1': 1, 'P2': 1,'P3': 1,'IGP': 1}
		return pressures

	# read voltage center, it required such a data structure
	def GetRotationAlignment(self):
		if Debug == True:
			print 'from jeol1230lib.py GetRotationAlignment'
		ra = {'x': 1, 'y': 1}
		return ra

	# doesn't work, but required
	def ScreenCurrent(self):	
		if Debug == True:
			print 'from jeol1230lib.py ScreenCurrent'
		return 1

	# read the beam current in A (ampire)
	def EmissionCurrent(self):
		if Debug == True:
			print 'from jeol1230lib.py EmissionCurrent'
		self.ser.flushInput()
		self.ser.flushOutput()
		self.ser.write('005\r')
		c = ''
		while True:
			newc = self.ser.read()
			if newc == '\r':
				break
			c = c + newc
		words = c.split()
		beamcurr = float(words[7]) / 1e9
		return beamcurr

	# doesn't work, but required for data structure
	def RetrHTCond(self):
		return 1

	# doesn't work, but required for data structure
	def ChangeFreeHT(self,deltaht):
		return 1

	# doesn't work, but required for data structure
	def SetRotationAlignment(self,RotAl):
		return 1

	# turn FreeHT on or off
	def SwitchFreeHT(self,value = 0):
		self.ser.flushInput()
		self.ser.flushOutput()
		ss = '001' + '\t' + str(value)+'\r'
		self.ser.write(ss)
		c = ''
		while True:
			newc = self.ser.read()
			if newc == '\r':
				break
			c = c + newc
		words = c.split()
		r0 = words[0]
		r2 = words[2]
		if r0 == '001' and r2 == '000':
			print "    HT is Set Succesfully"
			return True
		else:
			print "    HT set is Failed"
			return False

	# doesn't work, but required for data structure
	def getAlignment(self):
		return 1

	# doesn't work, but required for data structure
	def getCurrents(self):
		return 1

	# close connection between computer and tem
	def __del__(self):
		print 'close connection to JEOL1230 through COM1 port'
		self.ser.close()
