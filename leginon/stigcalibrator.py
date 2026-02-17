# The Leginon software is Copyright under
# Apache License, Version 2.0
# For terms of the license agreement
# see http://leginon.org
#
# $Source: /ami/sw/cvsroot/pyleginon/beamtiltcalibrator.py,v $
# $Revision: 1.82 $
# $Name: not supported by cvs2svn $
# $Date: 2007-08-13 23:58:28 $
# $Author: pulokas $
# $State: Exp $
# $Locker:  $


import numpy
import math
import threading
from leginon import calibrator
from leginon import calibrationclient
from leginon import leginondata
from pyami import imagefun
from leginon import tableau
from leginon import player
import leginon.gui.wx.StigCalibrator
import time
from datetime import datetime
import json

class Abort(Exception):
	pass

class StigCalibrator(calibrator.Calibrator):
	panelclass = leginon.gui.wx.StigCalibrator.Panel
	settingsclass = leginondata.StigCalibratorSettingsData
	defaultsettings = dict(calibrator.Calibrator.defaultsettings)
	defaultsettings.update({
		'measure defocus': 1e-6,
		'correct tilt': True,
		'settling time': 0.5,
	})

	def __init__(self, *args, **kwargs):
		calibrator.Calibrator.__init__(self, *args, **kwargs)

		self.abort = threading.Event()

		self.measurement = {}
		self.parameter = 'objective'
		self.dialog_done = threading.Event()
		self.ab_types = ['stigmator','stig','defocus']
		self.sites = 4
		self.manualplayer = player.Player()

		self.calibration_clients = {
			'objective stigmator': calibrationclient.ObjectiveStigCalibrationClient(self),
			'ctf': calibrationclient.CtfCalibrationClient(self),
			'eucentric focus': calibrationclient.EucentricFocusClient(self),
		}
		self.stgcalclient = self.calibration_clients['objective stigmator']

		self.start()

	def stigmatorCenterToScope(self):
		self.calibration_clients['%s stigmator' % self.parameter].stigmatorCenterToScope()
		self.panel.setInstrumentDone()

	def stigmatorCenterFromScope(self):
		self.calibration_clients['%s stigmator' % self.parameter].stigmatorCenterFromScope()
		self.panel.setInstrumentDone()

	def getFakeValues(self, axis, index):
		'''
		get fake values for testing. Set shift to -10e-6 and number of steps to 1.
		'''
		newstate = {}
		fake = {}
		fake['stigmator'] = {'x':[(0.00355495,-0.0236784),(0.00590004,-0.0213854),(0.00808952,-0.0189389)],'y':[(0.00329904,-0.0192235),(0.00585431,-0.0213466),(0.00822038,-0.023757)]}
		fake['stig'] = {'x':[(-0.0047448,-0.0031997),(-0.012963,-0.0113492),(-0.0225249,-0.0163792)],'y':[(-0.0111456, -0.0247119),(-0.0131071,-0.0115893),(-0.0147681, 0.00236871)]}
		fake['defocus'] = {'x':[3.14407e-6*2.429,2.358393e-6*2.429,1.64571e-6*2.429],'y':[2.00239e-6*2.429,2.33574e-6*2.429,2.90392e-6*2.429]}
		for ab_type in list(fake.keys()):
			if type(fake[ab_type][axis][index]) == type(()):
				newstate[ab_type] = {'x':fake[ab_type][axis][index][0],'y':fake[ab_type][axis][index][1]}
			else:
				newstate[ab_type] = fake[ab_type][axis][index]
		return newstate

	def getState(self):
		state = {}
		state['defocus'] = self.instrument.tem.Defocus
		state['stig'] = self.instrument.tem.Stigmator[self.parameter]
		return state

	def readState(self):
		state = self.getState()
		self.panel.readStateDone(state)
		return

	def resetState(self):
		self.instrument.tem.Defocus = self.state0['defocus']
		self.instrument.tem.Stigmator = {self.parameter:self.state0['stig']}
		self.logger.info('Reset to uncorrected state')
		self.readState()

	def setPreMeasureState(self):
		self.state0 = self.getState().copy()
			
	def _correctComaTilt(self):
		bt = self.comameasurement
		oldbt = self.instrument.tem.Stigmator[self.parameter]
		self.logger.info('Old stigmator: %.4f, %.4f' % (oldbt['x'],oldbt['y'],))
		newbt = {'x': oldbt['x'] + bt['x'], 'y': oldbt['y'] + bt['y']}
		self.instrument.tem.Stigmator = {self.parameter: newbt}
		self.logger.info('New stigmator: %.4f, %.4f' % (newbt['x'],newbt['y'],))

	def correctComaTilt(self):
		self.logger.info('Correcting stigmator...')
		try:
			self._correctComaTilt()
		except Exception as e:
			self.logger.exception('Correction failed: %s' % e)
		else:
			self.logger.info('Correction completed')

		self.panel.setInstrumentDone()

	def __calibrateStigmator(self, beam_tilt, delta, stigmator):
		if self.initInstruments():
			raise RuntimeError('cannot initialize instrument')

		calibration_client = self.calibration_clients['%s stigmator' % self.parameter]

		magnification = self.instrument.tem.Magnification
		high_tension = self.instrument.tem.HighTension
		probe = self.instrument.tem.ProbeMode

		# set up the stigmator states
		axes = ('x', 'y')
		deltas = (delta/2.0, -delta/2.0)
		for stig_axis in axes:
			self.logger.info('Calibrating stig. %s-axis...' % stig_axis)
			parameters = []
			states = []
			for delta in deltas:
				v = dict(stigmator)
				v[stig_axis] += delta
				parameters.append(v[stig_axis])
				s = leginondata.ScopeEMData(stigmator={self.parameter: v})
				states.append(s)

			matrix = numpy.identity(2, numpy.float64)
			for i, tilt_axis in enumerate(axes):
				self.logger.info('Calibrating on %s-axis...' % tilt_axis)
				args = (tilt_axis, beam_tilt, states)
				kwargs = {
					'correct_tilt': self.settings['correct tilt'],
					'settle': self.settings['settling time'],
				}
				shifts = calibration_client.measureDisplacements(*args, **kwargs)
				args = (shifts, parameters, beam_tilt)
				matrix[:, i] = calibration_client.eq11(*args)
				self.checkAbort()

			# store calibration
			type = 'stig' + stig_axis
			args = (high_tension, magnification, type, matrix)
			kwargs = {'probe':probe}
			calibration_client.storeMatrix(*args,**kwargs)

	def _calibrateStigmator(self, beam_tilt, delta):
		rotation_center = self.instrument.tem.Stigmator
		stigmator = self.instrument.tem.Stigmator['objective']
		try:
			self.__calibrateStigmator(beam_tilt, delta, stigmator)
		finally:
			self.instrument.tem.Stigmator = rotation_center
			self.instrument.tem.Stigmator = {'objective': stigmator}

	def calibrateStigmator(self):
		beam_tilt = self.settings['stig stigmator']
		delta = self.settings['stig delta']

		self.logger.info('Calibrating objective stigmator...')
		try:
			self._calibrateStigmator(beam_tilt, delta)
		except Exception as e:
			self.logger.error('Calibration failed: %s' % e)
		else:
			self.logger.info('Calibration completed')

		self.panel.calibrationDone()

	def _measure(self, measure_defocus, correct_tilt, settling_time=0.5):
		if self.initInstruments():
			raise RuntimeError('cannot initialize instrument')

		calibration_client = self.calibration_clients['%s stigmator' % self.parameter]

		args = (measure_defocus, self.calibration_clients['ctf'])
		kwargs = {
			'correct_tilt': correct_tilt,
			'settle': settling_time,
		}
		result = calibration_client.measureDefocusStig(*args, **kwargs)
		self.measurement = {}

		try:
			defocus = result['defocus']
			self.measurement['defocus'] = result['defocus']
		except KeyError:
			defocus = None

		stig = {}
		for axis in ('x', 'y'):
			try:
				stig[axis] = result['stig' + axis]
				self.measurement[axis] = result['stig' + axis]
			except KeyError:
				pass

		return defocus, stig

	def measure(self):
		measure_defocus = self.settings['measure defocus']
		if abs(measure_defocus) < 1e-7:
			self.logger.error('defocus for measure astig must not be 0...')
			args = (None, {})
			self.panel.measurementDone(*args)
			return

		correct_tilt = self.settings['correct tilt']

		self.logger.info('Measuring defocus and objective stigmator...')
		try:
			args = self._measure(measure_defocus, correct_tilt)
		except Exception as e:
			args = (None, {})
			self.logger.exception('Measurement failed: %s' % e)
		else:
			self.logger.info('Measurement completed')
		self.panel.measurementDone(*args)

	def _correctDefocus(self):
		try:
			measurement = self.measurement['defocus']
		except:
			raise RuntimeError('no measurement')
		defocus = self.instrument.tem.Defocus
		self.instrument.tem.Defocus = defocus + measurement

	def correctDefocus(self):
		self.logger.info('Correcting defocus...')
		try:
			self._correctDefocus()
		except Exception as e:
			self.logger.exception('Correction failed: %s' % e)
		else:
			self.logger.info('Correction completed')
		self.panel.setInstrumentDone()

	def _correctStigmator(self):
		stigmator = self.instrument.tem.Stigmator['objective']
		try:
			for axis in ('x', 'y'):
				stigmator[axis] += self.measurement[axis]
		except:
			raise RuntimeError('no measurement')
		self.instrument.tem.Stigmator = {'objective': stigmator}

	def correctStigmator(self):
		self.logger.info('Correcting objective stigmator...')
		try:
			self._correctStigmator()
		except Exception as e:
			self.logger.exception('Correction failed: %s' % e)
		else:
			self.logger.info('Correction completed')

		self.panel.setInstrumentDone()

	def resetDefocus(self):
		try:
			self.instrument.tem.resetDefocus()
		except Exception as e:
			self.logger.error('Reset defocus failed: %s' % e)
		else:
			self.logger.info('Defocus reset')

		self.panel.setInstrumentDone()

	def _eucentricFocusToScope(self):
		ht = self.instrument.tem.HighTension
		mag = self.instrument.tem.Magnification
		probe = self.instrument.tem.ProbeMode
		
		calibration_client = self.calibration_clients['eucentric focus']
		eucentric = calibration_client.researchEucentricFocus(ht, mag, probe)
		if not eucentric:
			raise RuntimeError('no eucentric focus for %geV, %gX' % (ht, mag))

		self.instrument.tem.Focus = eucentric['focus']

	def eucentricFocusToScope(self):
		try:
			self._eucentricFocusToScope()
		except Exception as e:
			self.logger.error('Set eucentric focus failed: %s' % e)
		else:
			self.logger.info('Set eucentric focus')

		self.panel.setInstrumentDone()

	def _eucentricFocusFromScope(self):
		ht = self.instrument.tem.HighTension
		mag = self.instrument.tem.Magnification
		probe = self.instrument.tem.ProbeMode
		focus = self.instrument.tem.Focus

		calibration_client = self.calibration_clients['eucentric focus']
		calibration_client.publishEucentricFocus(ht, mag, probe, focus)

	def eucentricFocusFromScope(self):
		try:
			self._eucentricFocusFromScope()
		except Exception as e:
			self.logger.error('Unable to get eucentric focus: %s' % e)
		else:
			self.logger.info('Saved eucentric focus')

		self.panel.getInstrumentDone()

	def checkAbort(self):
		if not self.abort.isSet():
			return
		self.abort.clear()
		raise Abort('operation aborted')

	def abortCalibration(self):
		self.abort.set()

	def editCurrentCalibration(self):
		'''
		Edit calibration of the gui-selected matrix without magnification.  Similar to the function in MatrixCalibrator.
		'''
		try:
			calibrationdata = self.getCurrentStigCalibration()
		except calibrationclient.NoMatrixCalibrationError as e:
			if e.state is None:
				raise e
			else:
				self.logger.warning('No calibration found for current state: %s' % e)
				calibrationdata = e.state
		except Exception as e:
			self.logger.error('Calibration edit failed: %s' % e)
			return
		self.panel.editCalibration(calibrationdata)

	def editCurrentFocusCalibration(self):
		try:
			kwargs = self.getCurrentStigCalibration()
			self.panel.editFocusCalibration(**kwargs)
		except Exception as e:
			self.logger.error('Calibration edit failed: %s' % e)
			return

	def getCurrentStigCalibration(self):
		if self.instrument.tem is None:
			raise RuntimeError('cannot access TEM')
		tem = self.instrument.getTEMData()
		cam = self.instrument.getCCDCameraData()
		par = self.parameter
		return self.stgcalclient.researchCalibration(tem, cam, par)

	def getCurrentFocusCalibration(self):
		tem = self.instrument.getTEMData()
		if tem is None:
			raise RuntimerError('no TEM selected')
		ccd_camera = self.instrument.getCCDCameraData()
		if ccd_camera is None:
			raise RuntimerError('no CCD camera selected')
		high_tension = self.instrument.tem.HighTension
		if high_tension is None:
			raise RuntimerError('cannot get high tension')
		magnification = self.instrument.tem.Magnification
		if magnification is None:
			raise RuntimerError('cannot get magnification')
		probe = self.instrument.tem.ProbeMode
		if probe is None:
			raise RuntimerError('cannot get beam probe mode')
		parameter = 'defocus'
		client = self.calibration_clients['%s stigmator' % self.parameter]
		m = 'Get %s calibration failed: %s'
		try:
			matrix_data = client.researchMatrix(tem, ccd_camera, parameter, high_tension, magnification, probe)
			matrix = matrix_data['matrix']
		except Exception as e:
			self.logger.warning(m % ('focus', e))
			matrix = None
		try:
			rotation_center = client.retrieveRotationCenter(tem, high_tension, magnification, probe)
		except Exception as e:
			self.logger.warning(m % ('rotation center', e))
			rotation_center = None
		client = self.calibration_clients['eucentric focus']
		try:
			eucentric_focus_data = client.researchEucentricFocus(high_tension, magnification, probe, tem=tem, ccdcamera=ccd_camera)
			eucentric_focus = eucentric_focus_data['focus']
		except Exception as e:
			self.logger.warning(m % ('eucentric focus', e))
			eucentric_focus = None
		kwargs = {
			'tem': tem,
			'ccd_camera': ccd_camera,
			'high_tension': high_tension,
			'magnification': magnification,
			'probe': probe,
			'parameter': parameter,
			'matrix': matrix,
			'rotation_center': rotation_center,
			'eucentric_focus': eucentric_focus,
		}
		return kwargs

	def saveCalibration(self, rotation, coeff, parameter):		
		self.stgcalclient.saveStigCalibration(rotation, coeff, parameter)
		self.logger.info('%s calibration is saved' % (parameter))

	def saveFocusCalibration(self, calibration, parameter, high_tension, magnification, tem, ccd_camera, probe):
		matrix, rotation_center, eucentric_focus = calibration
		client = self.calibration_clients['%s stigmator' % self.parameter]
		client.storeMatrix(high_tension, magnification, parameter, matrix, tem, ccd_camera, probe)

#--------manual coma-free dialog
	def getStigmatorList(self):
		tiltlist = []
		anglelist = []
		radlist = []

		tiltlist.append({'x':0.0,'y':0.0})
		anglelist.append(None)

		self.sites = 4
		angleinc = 2*3.14159/self.sites
		startangle = 0
		for i in range(0,self.sites):
			tilt = self.settings['imageshift coma tilt']
			angle = i * angleinc + startangle
			anglelist.append(angle)
			bt = {}
			bt['x']=math.cos(angle)*tilt
			bt['y']=math.sin(angle)*tilt
			tiltlist.append(bt)
		return tiltlist, anglelist

	def initTableau(self):
		self.tableauimages = []
		self.tableauangles = []
		self.tableaurads = []
		self.tabimage = None

	def binPower(self, image, binning=1):
		pow = imagefun.power(image)
		binned = imagefun.bin(pow, binning)
		return binned

	def acquireTableauImages(self):
		oldbt = self.instrument.tem.Stigmator
		oldstig = self.instrument.tem.Stigmator[self.parameter]
		tiltlist,anglelist = self.getStigmatorList()
		rad = 1 #radius step.  Fixed at 1 for this

		## initialize a new tableau
		self.initTableau()
		ht = self.instrument.tem.HighTension
		scope = leginondata.ScopeEMData(tem=self.instrument.getTEMData())
		for i, bt in enumerate(tiltlist):
			newbt = {'x': oldbt['x'] + bt['x'], 'y': oldbt['y'] + bt['y']}
			scope['stigmator'][self.parameter] = newbt
			# acquire image with scope state but not display in node image panel
			imagedata = self.stgcalclient.acquireImage(scope, settle=0.0, correct_tilt=False, corchannel=0, display=False)
			self.setManualComaFreeImage(imagedata['image'])
			self.insertTableau(imagedata, anglelist[i], rad)
			self.renderTableau()
		self.instrument.tem.Stigmator[self.parameter] = oldbt

	def setManualComaFreeImage(self,imagearray):
		self.panel.setManualComaFreeImage(imagearray, 'Image')

	def insertTableau(self, imagedata, angle, rad):
		image = imagedata['image']
		binning = 4
		binned = self.binPower(image, binning)
		self.tableauimages.append(binned)
		self.tableauangles.append(angle)
		self.tableaurads.append(rad)

	def renderTableau(self):
		if not self.tableauimages:
			return
		size = self.tableauimages[0].shape[0]
		radinc = numpy.sqrt(2 * size * size)
		tab = tableau.Tableau()
		for i,im in enumerate(self.tableauimages):
			ang = self.tableauangles[i]
			rad = radinc * self.tableaurads[i]
			tab.insertImage(im, angle=ang, radius=rad)
		self.tabimage,self.tabscale = tab.render()
		self.displayTableau()

	def displayTableau(self):
		self.panel.setManualComaFreeImage(self.tabimage, 'Tableau')

	def applyTiltChange(self, deltabt):
			oldbt = self.instrument.tem.Stigmator
			self.logger.info('Old stigmator: %.4f, %.4f' % (oldbt['x'],oldbt['y'],))
			newbt = {'x': oldbt['x'] + deltabt['x'], 'y': oldbt['y'] + deltabt['y']}
			self.instrument.tem.Stigmator = newbt
			self.logger.info('New stigmator: %.4f, %.4f' % (newbt['x'],newbt['y'],))

	def applyTiltChangeAndReacquireTableau(self,deltabt):
			self.applyTiltChange(deltabt)
			self.acquireTableauImages()
			newbt = self.instrument.tem.Stigmator
			self.logger.info('Final stigmator: %.4f, %.4f' % (newbt['x'],newbt['y'],))

	def navigate(self, xy):
		'''
		Calculate the new stigmator center and then aquire new tableau images.
		This is triggered by clicking at a position in  ManualComaFree_Dialog Tableau Image.
		'''
		clickrow = xy[1]
		clickcol = xy[0]
		try:
			clickshape = self.tabimage.shape
		except:
			self.logger.warning('Can not navigate without a tableau image')
			return
		# calculate delta from image center
		centerr = clickshape[0] / 2.0 - 0.5
		centerc = clickshape[1] / 2.0 - 0.5
		deltarow = clickrow - centerr
		deltacol = clickcol - centerc
		bt = {}
		if self.tabscale is not None:
			bt['x'] = deltacol * self.settings['imageshift coma tilt']/self.tabscale
			bt['y'] = -deltarow * self.settings['imageshift coma tilt']/self.tabscale
			self.applyTiltChangeAndReacquireTableau(bt)
		else:
			self.logger.warning('need more than one stigmator images in tableau to navigate')

	#--------------Manual Focus---------------
	def acquireManualFocusImage(self):
		scope={}
		# acquire image but not display in node image panel
		imagedata = self.stgcalclient.acquireImage(scope, settle=0.0, correct_tilt=False, corchannel=0, display=False)
		# thread to make it possible to acquire the next image before this one is displayed.
		threading.Thread(target=self.setManualFocusImage(imagedata['image'])).start()

	def setManualFocusImage(self,imagearray):
		self.maskradius = 0.01
		self.panel.setManualFocusImage(imagearray, 'Image')
		power = imagefun.power(imagearray, self.maskradius)
		self.man_power = power.astype(numpy.float32)
		self.panel.setManualFocusImage(self.man_power, 'Power')

	def manualFocusLoop(self):
		## go to preset and target
		#pixelsize,center = self.getReciprocalPixelSizeFromPreset(presetname)
		#self.ht = self.instrument.tem.HighTension
		#self.cs = self.getTEMCsValue()
		#self.panel.onNewPixelSize(pixelsize,center,self.ht,self.cs)
		self.logger.info('Starting manual focus loop...')
		self.beep()
		self.manualplayer.play()
		#self.onManualCheck()
		while True:
			state = self.manualplayer.state()
			if state == 'stop':
				break
			elif state == 'pause':
				if self.manualplayer.wait() == 'stop':
					break
			# acquire image, show image and power spectrum
			# allow user to adjust defocus and stig
			self.acquireManualFocusImage()
