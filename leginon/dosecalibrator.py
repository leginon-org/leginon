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

		## screen controls
		controlcont = uidata.Container('Manual Screen Controls (Dose Measurement and Sensitivity Calibration Control automatically control screen)')
		upmeth = uidata.Method('Screen Up', self.screenUp)
		downmeth = uidata.Method('Screen Down', self.screenDown)
		controlcont.addObjects((upmeth, downmeth))


		## dose measurement
		dosecont = uidata.Container('Dose Measurement')
		self.beamdia = uidata.Float('Beam Diameter (m)', 160e-3, 'rw', persist=True)
		self.beamscale = uidata.Float('Screen Current->Beam Current Scale Factor', 0.88, 'rw', persist=True)
		dosemeth = uidata.Method('Measure Dose Rate', self.uiMeasureDoseRate)
		self.ui_beamcurrent = uidata.Float('Beam Current (Amps)', 0.0, 'r')
		self.ui_screenmag = uidata.Float('Screen Magnification', 0.0, 'r')
		self.ui_doserate = uidata.Float('Dose Rate (electrons / m^2 / s)', 0.0, 'r')
		dosecont.addObjects((self.beamdia, self.beamscale, dosemeth, self.ui_beamcurrent, self.ui_screenmag, self.ui_doserate))

		### camera calibration
		camcont = uidata.Container('Camera Sensitivity Calibration (Do Dose Measurement First)')
		camsetup = self.cam.uiSetupContainer()
		calcam = uidata.Method('Calibrate Camera Sensitivity', self.uiCalibrateCamera)
		self.ui_sens = uidata.Float('Sensitivity (counts/electron)', 0.0, 'r')
		self.ui_image = uidata.Image('Calibration Image', None, 'r')
		camcont.addObjects((camsetup, calcam, self.ui_sens, self.ui_image))

		mycontainer = uidata.LargeContainer('Dose Calibrator')
		mycontainer.addObjects((controlcont, dosecont, camcont))
		self.uicontainer.addObject(mycontainer)

	def uiMeasureDoseRate(self):
		self.screenDown()
		status = self.getCurrentAndMag()
		if status == 'ok':
			self.ui_screenmag.set(self.results['screen magnification'])
			self.ui_beamcurrent.set(self.results['beam current'])
		elif status == 'screen':
			self.logger.error('Cannot measure current with main screen down')

		screen_mag = self.results['screen magnification']
		beam_current = self.results['beam current']
		beam_diameter = self.beamdia.get()
		doserate = self.calclient.dose_from_screen(screen_mag, beam_current, beam_diameter)
		self.ui_doserate.set(doserate)
		self.results['dose rate'] = doserate

	def screenDown(self):
		# check if screen is down
		scope = data.ScopeEMData(id=('scope',))
		scope['screen position'] = 'down'
		self.publishRemote(scope)

	def screenUp(self):
		# check if screen is down
		scope = data.ScopeEMData(id=('scope',))
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

	def acquireImage(self):
		self.screenUp()
		self.cam.uiApplyAsNeeded()
		imdata = self.cam.acquireCameraImageData(correction=True)
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
