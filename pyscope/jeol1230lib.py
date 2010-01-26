# joel1230lib.py is base Library for jeol 1230 microscope
# Author: Minghui Hu, mhu@nysbc.org, New York Structural Biology Center

# import serial
# ser = serial.Serial(port='COM1', baudrate=9600, bytesize=8, parity='N', stopbits=1, timeout=10, xonxoff=1, rtscts=0)
# from pyscope import jeol1230lib ; j = jeol1230lib.jeol1230lib(); j.getDefocus()

import time
import serial
from ctypes import *
from pyscope import jeol1230cal									#	define maginication

Debug = False

class jeol1230lib(object):
	name = 'jeol1230 library'

	def __init__(self):											# initialize the serial port communication
		self.ser = serial.Serial(port='COM1', baudrate=9600, bytesize=8, parity='N', stopbits=1, xonxoff = 0, timeout=10, rtscts=0)
		self.equipmentAvailable()
		self.defocusFile = "C:\Python25\Lib\site-packages\pyscope\defocus.cfg"		
		self.zeroDefocus = {'zero_time': None, 'zero_oml': None, 'zero_omh': None,'zero_oll': None, 'zero_olh': None}
		self.zeroDefocus = self.readZeroDefocus()
		if (time.time()- float(self.zeroDefocus['zero_time']))/(3600.0 * 24) >= 1:
			print "Defocus value is over one day, and it is better to reset defocus values"
		else:
			print "Defocus value is new"
		self.zero_oml = int(self.zeroDefocus['zero_oml'])
		self.zero_omh = int(self.zeroDefocus['zero_omh'])
		self.zero_oll = int(self.zeroDefocus['zero_oll'])									# specific to jeol1230
		self.zero_olh = int(self.zeroDefocus['zero_olh'])		
		self.wait_time = 0.1


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


	def equipmentAvailable(self):								# check communication to microscope
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
				print "    Serial port can not be initialized by pyscope"
			return False


	def getHighTensionState(self):
		if Debug == True:
			print 'from jeol1230lib.py getHighTensionStatus'
		highTensionStatus = 'unknown'
		while True:
			self.ser.flushInput()
			self.ser.flushOutput()
			ss = '050' + '\r'						# I found this hidden command
			self.ser.write(ss)
			c = ''
			while True:
				newc = self.ser.read()
				if newc == '\r':
					break
				c = c + newc
			words = c.split()
			print words[2]
			if words[0] == '050' and words[1] == '000':
				if words[2] == '1':
					highTensionStatus = 'on'
				else:
					highTensionStatus = 'off'
				break
			time.sleep(self.wait_time)
		return highTensionStatus


	def getHighTension(self):
		if Debug == True:
			print 'from jeol1230lib.py getHighTension'
		while True:
			self.ser.flushInput()
			self.ser.flushOutput()
			ss = '050' + '\r'						# I found this hidden command
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


	def setHighTension(self, value=0):						# 0 is Off, 1 is On
		if Debug == True:
			print 'from jeol1230lib.py setHighTension'
		self.ser.flushInput()
		self.ser.flushOutput()
		ss = '001' + '\t' + str(value) + '\r'						# get high tension infor
		self.ser.write(ss)			
		return True

	def setTurboPump(self, mode):  # Added by Minghui
##		if Debug == True:
##			print 'from jeol1230lib.py setTurboPump--setBeamOnOff'
##		if mode == 'on':
##			value = 1
##		elif mode == 'off':
##			value = 0
##		else:
##			return False
##		self.ser.flushInput()
##		self.ser.flushOutput()
##		ss = '003' + '\t' + str(value) + '\r'
##		self.ser.write(ss)
		return True

	def setBeamState(self, mode):	# Added by Minghui
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

	def getBeamState(self):							# Newly added, mag is a string, not a number
		if Debug == True:
			print 'from jeol1230lib.py getBeamState'
		beamState = 'unknown'
		while True:
			self.ser.flushInput()
			self.ser.flushOutput()
			ss = '050' + '\r'						# I found this hidden command
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


	def getMagnification(self):							        # mag is a string, not a number
		if Debug == True:
			print 'from jeol1230lib.py getMagnification'
		Magn = 0
		while True:
			self.ser.flushInput()									# get Magnification
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


	def setMagnification(self, mag):							# Newly added, mag is a string, not a number
		if Debug == True:
			print 'from jeol1230lib.py setMagnification'
		magRange = 40
		for i in range(0,magRange):
			if int(mag) <= jeol1230cal.screenup_mag[i]:
				break
		if i > magRange:
			print '    Magnification out of range'
			return False
		while True:
			self.ser.flushInput()
			self.ser.flushOutput()
			if i < 13:
				self.ser.write ('106\t0\r')							# use low mag mode
			else:
				i = i - 13
				self.ser.write ('106\t1\r')							# use mag1 mode
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
			ss = '107' + '\t' + str(i) + '\r'						# set magnification uner low or mag1 mode
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
		Magn = self.getMagnification()							# get cl1 value
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
			time.sleep(self.wait_time)											# give 1s break for response
		return True


##	def _getStagePosition(self):								# Reads the current x, y position in micrometer
##		if Debug == True:
##			print 'from jeol1230lib.py _getStagePosition'
##		self.ser.flushInput()
##		self.ser.flushOutput()
##		self.ser.write ('250\r')								# Imaging mode acquisition commond
##		c = ''
##		while True:
##			newc = self.ser.read()
##			if newc == '\r':
##				break
##			c = c + newc
##		words = c.split()
##		position = {'x': None, 'y': None}
##		position['x'] = float(words[2])/1000					# convert from nanometer to micrometer
##		position['y'] = float(words[4])/1000
##		return position


	def getStagePosition(self):									# Reads the current x,y,z in micrometer, a in degree
		if Debug == True:
			print 'from jeol1230lib.py getStagePosition'
		position = {'x': None, 'y': None, 'z': None, 'a': None}		
		while True:
			self.ser.flushInput()
			self.ser.flushOutput()
			self.ser.write ('250\r')								# Imaging mode acquisition commond
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
		if (Debug == True):
			print position
		return position


	def setStagePosition(self,axis,coord,mode):					# Move one position in um or deg
		if Debug == True:
			print 'from jeol1230lib.py setStagePosition'
			print "Received axis, coord, mode is: ", axis, coord, mode
		if mode == 'fine':										# distance is 3, 50um
			dm = '1'											# driving mode: 0(fine), 1(medium), 2(coarse)
			sc = '25'											# speed coefficient: 1-100
		else:
			dm = '2'		
			sc = '100'		
		ml = '0'
		ct = '\t'		
		minimum_stage = {'x': 0.05, 'y': 0.05, 'z': 0.05, 'a': 0.1}		
		maximum_stage = {'x': 1000.0, 'y': 1000.0, 'z': 120.0, 'a': 60.0}		
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
			ss = '203' + ct + str(c_coord) + ct + dm + ct + sc + '\r'
		elif axis == 'a':
			c_axis = '0'
			c_coord = int(coord * 10.0)
			ss = '205' + ct + c_axis + ct + str(c_coord) + ct + dm + ct + sc + '\r'
		else:
			return False
		self.ser.flushInput()
		self.ser.flushOutput()
		self.ser.write(ss)										# start the movement
		time.sleep(1)											# give 1s waiting time
		i = 0													#check stage status to determine return or not
		while True:
			i = i + 1
			self.ser.flushInput()
			self.ser.flushOutput()
			if axis == 'x' or axis == 'y':						# x, y are in 3rd place, and z and a in 5th place
				ss = '250' + '\r'
			else:
				ss = '251' + '\r'
			self.ser.write(ss)
			time.sleep(self.wait_time*2)
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
			if db2 == 0:
				if Debug == True:
					print "    Stage movement in %s mode was sucessfull" % mode
				break
			if (i > 15 and mode == 'coarse') or (i > 30 and mode == 'fine'):						# give 60s to move in coarse mode
				if Debug == True:				
					print "    Too long and terminate the movement"
				self.ser.flushInput()
				self.ser.flushOutput()
				self.ser.write('206\r')							# terminate stage movement
				break							# terminate stage movement
			time.sleep(self.wait_time + 4)						# set check interval as 5s
		return True


	def getIntensity(self):										# get condenser lens-2,3
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


	def setIntensity(self, intensity):							# using relative value
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

	def getObjectiveCurrent(self):								# get objective lens-8,9
		if Debug == True:
			print 'from jeol1230lib.py getObjectiveCurrent'
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
		oll = words[8]
		olh = words[9]
		oml = words[10]
		omh = words[11]
		if Debug == True:
			print 'oll %x, olh %x' % (int(oll,16), int(olh,16))
			print 'oml %x, omh %x' % (int(oml,16), int(omh,16))
		if self.getMagnification() >= 1000:
			current = int(oll,16)*1e5 + int(olh,16)
		else:
			current = int(oml,16)*1e5 + int(omh,16)
		return int(current)


	def setObjectiveCurrent(self,current):						# using relative values
		if Debug == True:
			print 'from jeol1230lib.py setObjectiveCurrent'
		if self.getMagnification() >= 1000:
			code_1 = '9'
			code_2 = '10'
		else:
			code_1 = '11'
			code_2 = '12'
		c_current = self.getObjectiveCurrent()
		l = int(int(current)//1e5) - int(int(c_current)//1e5)
		h = int(int(current)%1e5) - int(int(c_current)%1e5)
		ss_l = '102' + '\t' + code_1 + '\t' + str(l) + '\r'		# set l
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
		ss_h = '102' + '\t' + code_2 + '\t' + str(h) + '\r'		# set h
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


	def getDefocus(self):
		if Debug == True:
			print 'from jeol1230lib.py getDefocus'
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
		oll = words[8]
		olh = words[9]
		oml = words[10]
		omh = words[11]
		if Debug == True:
			print '    oll %d, olh %d' % (int(oll,16), int(olh,16))
			print '    oml %d, omh %d' % (int(oml,16), int(omh,16))
		if self.getMagnification() >= 1000:
			defocus = (int(oll,16)-self.zero_oll)*0.0048/1e6
		else:
			defocus = (int(oml,16)-self.zero_oml)*0.0048/1e6
		return float(defocus)


	def setDefocus(self,defocus):							# arg is not received correctly, float and int
		if Debug == True:
			print 'from jeol1230lib.py setDefocus'
		rel_defocus = float(defocus) - self.getDefocus()
		
		
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
			
		current_oll = words[8]
		current_olh = words[9]
		current_oml = words[10]
		current_omh = words[11]		
		
		diff_olh = self.zero_olh - int(current_olh, 16)
		diff_omh = self.zero_omh - int(current_omh, 16)
		
		print "diff_olh is %d, diff_omh is %d" %(diff_olh, diff_omh)

		flag = False
		
		if self.getMagnification() >= 1000:
			code_1 = '9'
			code_2 = '10'
			diff_oll = int(rel_defocus*1e6*210)
			ss_l = '102' + '\t' + code_1 + '\t' + str(diff_oll) + '\r'		# set l
			ss_h = '102' + '\t' + code_2 + '\t' + str(diff_olh) + '\r'
			if diff_olh != 0:
				flag = True
		else:
			code_1 = '11'
			code_2 = '12'
			diff_oml = int(rel_defocus*1e6*210)
			ss_l = '102' + '\t' + code_1 + '\t' + str(diff_oml) + '\r'		# set l
			ss_h = '102' + '\t' + code_2 + '\t' + str(diff_omh) + '\r'		
			if diff_omh != 0:
				flag = True
		
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

		return True


	def resetDefocus(self, value = 0):
		if Debug == True:
			print 'from jeol1230lib.py resetDefocus'
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
		oll = words[8]
		olh = words[9]
		oml = words[10]
		omh = words[11]		
		if self.getMagnification() > 1000:
			self.zero_oll = int(oll,16)
			self.zero_olh = int(olh,16)
			self.saveZeroDefocus('zero_oll', self.zero_oll)
			self.saveZeroDefocus('zero_olh', self.zero_olh)
		else:
			self.zero_oml = int(oml,16)
			self.zero_omh = int(omh,16)
			self.saveZeroDefocus('zero_oml', self.zero_oml)
			self.saveZeroDefocus('zero_omh', self.zero_omh)
		self.saveZeroDefocus('zero_time', time.time())		
		return True


	def getBeamShift(self):										# get Beamshift X and Y
		if Debug == True:
			print 'from jeol1230lib.py getBeamShift'		
		while True:
			self.ser.flushInput()
			self.ser.flushOutput()
			self.ser.write('151\t3\r')								# beamshift is code 3
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


	def setBeamShift(self,axis,value):							# set Beamshift X and Y
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


	def getBeamTilt(self):										# get Beamtilt X and Y
		if Debug == True:
			print 'from jeol1230lib.py getBeamTilt'		
		while True:
			self.ser.flushInput()
			self.ser.flushOutput()
			self.ser.write('151\t4\r')								# beamtilt is code 4
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
		beamtilt['x'] = int(words[2],16)
		beamtilt['y'] = int(words[3],16)
		return beamtilt


	def setBeamTilt(self,axis,value):							# set Beamtilt X and Y
		if Debug == True:
			print 'from jeol1230lib.py setBeamTilt'
		if Debug == True:
			print "    Image tilt will be %d in %s direction" % (value, axis)
		if axis == 'x':
			code = '7'
		else:
			code = '8'
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


	def getImageShift(self):									# get Imageshift X and Y
		if Debug == True:
			print 'from jeol1230lib.py getImageShift'
		
		while True:
			self.ser.flushInput()
			self.ser.flushOutput()
			self.ser.write('151\t5\r')								# imageshift is code 5
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
			imageshift['x'] = int(words[2],16)*4.375e-9 - 32768*4.375e-9
			imageshift['y'] = int(words[3],16)*4.375e-9 - 32768*4.375e-9
		return imageshift


	def setImageShift(self,axis,value):							# set Imageshift X and Y
		if Debug == True:
			print 'from jeol1230lib.py setImageShift'
		if axis == 'x':
			code = '9'
		else:
			code = '10'
		if self.getMagnification() >= 1000:
			sh = "%x" % int((float(value) + 32768*3.057e-10)/3.057e-10)
		else:
			sh = "%x" % int((float(value) + 32768*4.375e-9)/4.375e-9)
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


	def getStigmator(self):										# Retrieve all the stigmators setting as a single block
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


	def PressureReadout(self):
		if Debug == True:
			print 'from jeol1230lib.py PressureReadout'
		pressures = {'P1': 1, 'P2': 1,'P3': 1,'IGP': 1}
		return pressures


	def GetRotationAlignment(self):								# Retrieves the rotation alignment: need to change!
		if Debug == True:
			print 'from jeol1230lib.py GetRotationAlignment'
		ra = {'x': 1, 'y': 1}
		return ra


	def ScreenCurrent(self):									# not work
		if Debug == True:
			print 'from jeol1230lib.py ScreenCurrent'
		return 1


	def EmissionCurrent(self):
		if Debug == True:
			print 'from jeol1230lib.py EmissionCurrent'
		self.ser.flushInput()
		self.ser.flushOutput()
		self.ser.write('005\r')									# Imaging mode acquisition commond
		c = ''
		while True:
			newc = self.ser.read()
			if newc == '\r':
				break
			c = c + newc
		words = c.split()										# seperate it into words
		beamcurr = float(words[7]) / 1e9						# take the beam current in A information out
		return beamcurr


	def RetrHTCond(self):										# Determine whether high tension may be switched on or not.: NOT WORKING!!!
		return 1


	def ChangeFreeHT(self,deltaht):								# Changes the high tension by the deltaht value specified. NOT WORKING, Free HT must be on for this function to work.dangerous, is blocked now
		return 1


	def SetRotationAlignment(self,RotAl):
		return 1


	def SwitchFreeHT(self,value = 0):								# Switches Free HT CONTROL (1=on;0=off))
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


	def getAlignment(self):
		return 1


	def getCurrents(self):
		return 1


	def __del__(self):											# close connection between computer and tem
		print 'close connection to JEOL1230 through COM1 port'
		self.ser.close()
