#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#
import calibrator
import calibrationclient
import event, data
import uidata
import node

class DoseCalibrator(calibrator.Calibrator):
	'''
	calibrate the camera sensitivity and other dose measurements
	'''
	def __init__(self, id, session, nodelocations, **kwargs):
		calibrator.Calibrator.__init__(self, id, session, nodelocations, **kwargs)
		self.calclient = calibrationclient.DoseCalibrationClient(self)
		self.results = {}

		self.defineUserInterface()
		self.start()

	def defineUserInterface(self):
		node.Node.defineUserInterface(self)

		### dose rate
		self.beamdia.get

		mycontainer = uidata.LargeContainer('Pixel Size Calibrator')
		mycontainer.addObjects(())
		self.uiserver.addObject(mycontainer)

	def dose_from_screen(self, screen_mag, beam_current, beam_diameter):
		## electrons per screen area per second
		beam_area = pi * (beam_diameter/2.0)**2
		screen_electrons = beam_current * coulomb / beam_area
		print 'screen_electrons', screen_electrons

		## electrons per specimen area per second (dose)
		dose = screen_electrons * (screen_mag**2)
		print 'dose', dose
		return dose

	def screenDown(self):
		# check if screen is down
		scope = data.ScopeEMData(('scope',))
		scope['screen position'] = 'down'
		self.publishRemote(scope)

	def screenUp(self):
		# check if screen is down
		scope = data.ScopeEMData(('scope',))
		scope['screen position'] = 'up'
		self.publishRemote(scope)

	def getCurrentAndMag(self):
		scope = self.researchByDataID(('scope',))
		if scope['screen position'] == 'down':
			mag = scope['magnification']
			current = scope['screen current']
			self.results['screen magnification'] = mag
			self.results['screen current'] = current
			return 'ok'
		else:
			return 'screen'

	def uiGetCurrentAndMag(self):
		status = self.getCurrentAndMag()
		if stats == 'ok':
			self.uiscreenmag.set(self.results['screen magnification'])
			self.uiscreencur.set(self.results['screen current'])
		elif status == 'screen':
			self.outputMessage('Screen is up', 'Screen is up.  You must have screen down to measure the current')

	def acquireImage(self):
		conf = {'auto square':True}
		camconfig = self.cam.cameraConfig(conf)
		self.cam.acquireCameraImageData(camconfig, correction=True)

	def calibrateCamera(self):
		print 'screen down'
		self.screenDown()
		curmag = self.getCurrentAndMag()
		self.screenUp()

		screen_mag = curmag['magnification']
		beam_current = curmag['screen current']
		beam_diameter = self.beamdia.get()
		dose_rate = self.dose_from_screen(screen_mag, beam_current, beamdiameter)


	def _store(self, mag, psize, comment):
		caldata = data.PixelSizeCalibrationData()
		caldata['magnification'] = mag
		caldata['pixelsize'] = psize
		caldata['comment'] = comment
		self.publish(caldata, database=True)
