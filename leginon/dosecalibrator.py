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

		downmeth = uidata.Method('Screen Down', self.screenDown)
		self.beamdia = uidata.Float('Beam Diameter', 160e-3, 'rw', persist=True)
		self.beamscale = uidata.Float('Screen Current->Beam Current Scale Factor', 0.88, 'rw', persist=True)
		bcmeth = uidata.Method('Measure Beam Current', self.uiGetCurrentAndMag)
		self.ui_beamcurrent = uidata.Float('Beam Current (Amps)', 0.0, 'r')
		self.ui_screenmag = uidata.Float('Screen Magnification', 0.0, 'r')
		doseratemeth = uidata.Method('Calculate Dose Rate', self.uiCalculateDoseRate)
		self.ui_doserate = uidata.Float('Dose Rate (electons / m^2 / s)', 0.0, 'r')
		upmeth = uidata.Method('Screen Up', self.screenUp)

		calcam = uidata.Method('Calibrate Camera Sensitivity', self.uiCalibrateCamera)
		self.ui_sens = uidata.Float('Sensitivity (counts/electron)', 0.0, 'r')
		self.ui_image = uidata.Image('Calibration Image', None, 'r')
		

		mycontainer = uidata.LargeContainer('Dose Calibrator')
		mycontainer.addObjects((downmeth, self.beamdia, self.beamscale, bcmeth, self.ui_beamcurrent, self.ui_screenmag, doseratemeth, self.ui_doserate, upmeth, calcam, self.ui_sens, self.ui_image))
		self.uiserver.addObject(mycontainer)

	def uiCalculateDoseRate(self):
		screen_mag = self.results['screen magnification']
		beam_current = self.results['beam current']
		beam_diameter = self.beamdia.get()
		doserate = self.calclient.dose_from_screen(screen_mag, beam_current, beam_diameter)
		self.results['dose rate'] = doserate

	def screenDown(self):
		# check if screen is down
		scope = data.ScopeEMData(id=('scope',))
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
			scale = self.beamscale.get()
			self.results['screen magnification'] = mag
			self.results['beam current'] = current * scale
			return 'ok'
		else:
			return 'screen'

	def uiGetCurrentAndMag(self):
		self.screenDown()
		status = self.getCurrentAndMag()
		self.screenUp()
		if status == 'ok':
			self.ui_screenmag.set(self.results['screen magnification'])
			self.ui_beamcurrent.set(self.results['beam current'])
		elif status == 'screen':
			self.outputMessage('Screen is up', 'Screen is up.  You must have screen down to measure the current')

	def acquireImage(self):
		conf = {'auto square':True, 'auto offset':True, 'dimension':{'x':512}, 'binnning':{'x':1}, 'offset':{'x':0}}
		camconfig = self.cam.cameraConfig(conf)
		imdata = self.cam.acquireCameraImageData(camconfig, correction=True)
		self.ui_image.set(imdata['image'])
		return imdata

	def uiCalibrateCamera(self):
		imdata = self.acquireImage()
		screen_mag = self.results['screen magnification']
		beam_current = self.results['beam current']
		beam_diameter = self.beamdia.get()
		dose_rate = self.results['dose rate']
		sens = self.calclient.sensitivity_from_imagedata(imdata, dose_rate)
		self.ui_sens.set(sens)
		ht = imdata['scope']['high tension']
		self.calclient.storeSensitivity(ht, sens)
