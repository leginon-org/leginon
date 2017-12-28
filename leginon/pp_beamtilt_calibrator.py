#!/usr/bin/env python
import sys
import math
import threading
import time
import socket

from leginon import leginondata, calibrationclient
from pyscope import config

class Instrument(object):
	def __init__(self,tem,cam):
		self.tem = tem
		self.cccdcamera = cam

	def getCCDCameraData(self):
		return None

class Session(object):
	def __init__(self):
		pass

class Node(object):
	def __init__(self,tem,cam):
		self.instrument = Instrument(tem,cam)
		self.session = None

class BeamTiltRotationCalibrator(object):
	def __init__(self):
		self.tems = config.getTEMClasses()
		if not self.tems:
			raw_input('Must have tem classes to run this. Hit any key to quit.')
			sys.exit()
		self.tem1 = None
		for t in self.tems:
			answer = raw_input('Is %s the current TEM mode ? (Y/N)(y/n) ' % t.name)
			if answer.lower() == 'y':
				self.tem1 = t()
				print 'Set TEM to %s mode' % self.tem1.name
				break
		if self.tem1 is None:
			print 'TEM not set.', self.tem1
			self.finish()

		print self.tem1.getProbeMode()
		# fake node to host calibrationclient
		node = Node(self.tem1, None)
		self.bt0 = self.tem1.getBeamTilt()
		self.calclient = calibrationclient.BeamTiltCalibrationClient(node)

	def printInstruction(self):
		answer = raw_input('''
1. Use cross-grating or other specimen that scatter well.

2. Change TEM to diffraction mode.
 * You should see the phase plate slot as well as the focused beam on screen.

3. Navigate the phase plate with "Next" button in TUI-Aperture dialog
   to learn which direction
   points to patch 1 from the center of the phase plate slot.

4. Activate "Adjust" button in TUI to move the beam to the straight edge of the slot.

5. When you are ready, this program will tilt the beam by 0.01 mrad and
   rotate it around the current center at 10 degree increment.

Hit "Enter" or "Return" key to stop it when the beam is on the edge again, pointing to the direction from patch 2 to 1 relative to the original center.

6. Are you ready ? (Y/N,y/n)
		''')
		if answer.lower() != 'y':
			return False
		return True	

	def rotateXY0(self,xy, rotation):
		'''
		rotate around {'x':0,'y':0}
		'''
		bt = {}
		bt['x'] = xy['x']*math.cos(rotation)-xy['y']*math.sin(rotation)
		bt['y'] = xy['x']*math.sin(rotation)+xy['y']*math.cos(rotation)
		return bt

	def modifyBeamTilt(self,bt0, bt_delta):
		bt1 = dict(bt0)
		bt1['x'] += bt_delta['x']
		bt1['y'] += bt_delta['y']
		return bt1

	def waitForDone(self):
		self.done=False
		raw_input('')
		self.done=True

	def run(self):
		starting_angle = -math.pi/2.0
		thread = threading.Thread(name='wait_thread',target=self.waitForDone)
		thread.start()
		angle = starting_angle
		while not self.done:
			angle += math.pi/18
			bt_delta = self.rotateXY0({'x':0.01,'y':0}, angle)
			print math.degrees(angle)
			bt1 = self.modifyBeamTilt(self.bt0, bt_delta)
			self.tem1.setBeamTilt(bt1)
			time.sleep(0.5)
		print 'final angle', math.degrees(angle)
		print 'pause 10 seconds before continue....'
		time.sleep(10)
		self.tem1.setBeamTilt(self.bt0)
		return angle

	def getYDirection(self, angle):
		answer = raw_input('''
Next to decide the y direction tilt.  The beam will be tilted
by y = 0.01 radians.  Examine the tilt direction relative to
the patch advance direction.

Hit return when ready.
		''')

		try:
			bt_delta = self.rotateXY0({'x':0,'y':0.01}, angle)
			bt1 = self.modifyBeamTilt(self.bt0, bt_delta)
			self.tem1.setBeamTilt(bt1)
		finally:
			self.tem1.setBeamTilt(self.bt0)
		answer = raw_input('''
Type Y if this is pointing to the previous row of phase plate patch. 
Type N if a direction reversal is needed : 
		''')
		return answer.lower() == 'y'

	def confirm(self):
		answer = raw_input('Type Y or y if ready to save, Else repeat : ')
		return answer.lower() == 'y'

	def storeToDatabase(self, anglei, y_is_positive):
		tems = leginondata.InstrumentData(hostname=socket.gethostname(),name=self.tem1.name).query(results=1)
		tem=tems[0]
		cam = None
		probe = self.tem1.getProbeMode()
		if y_is_positive:
			vectors = ((1,0),(0,1))
		else:
			vectors = ((1,0),(0,-1))
		self.calclient.storePhasePlateBeamTiltVectors(tem, cam, vectors, probe)
		self.calclient.storePhasePlateBeamTiltRotation(tem, cam, angle, probe)
		print 'calibration saved for %s at %.1f' % (tem['name'],math.degrees(angle))

	def finish(self):
		raw_input('Hit Enter to quit')

if __name__ == '__main__':
	app = BeamTiltRotationCalibrator()
	if app.printInstruction():
		confirm = False
		while not confirm:
			angle = app.run()
			y_direction = app.getYDirection(angle)
			confirm = app.confirm()
		app.storeToDatabase(angle, y_direction)
		app.finish()
