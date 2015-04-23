#
# COPYRIGHT:
#	   The Leginon software is Copyright 2003
#	   The Scripps Research Institute, La Jolla, CA
#	   For terms of the license agreement
#	   see  http://ami.scripps.edu/software/leginon-license
#
import acquisition
import node, leginondata
import calibrationclient
import threading
import event
import time
import math
from pyami import imagefun, fftfun, ordereddict
import numpy
import copy
import gui.wx.Focuser
import player

class ManualFocusChecker(acquisition.Acquisition):
	panelclass = gui.wx.Focuser.Panel
	settingsclass = leginondata.AcquisitionSettingsData
	defaultsettings = acquisition.Acquisition.defaultsettings

	eventinputs = acquisition.Acquisition.eventinputs
	eventoutputs = acquisition.Acquisition.eventoutputs

	def __init__(self, id, session, managerlocation, **kwargs):

		self.manualchecklock = threading.Lock()
		self.parameter_choice= 'Defocus'
		self.maskradius = 1.0
		self.increment = 5e-7
		self.man_power = None
		self.man_image = None
		self.manualplayer = player.Player(callback=self.onManualPlayer)
		acquisition.Acquisition.__init__(self, id, session, managerlocation, **kwargs)
		self.deltaz = 0.0

	def eucentricFocusToScope(self):
		errstr = 'Eucentric focus to instrument failed: %s'
		try:
			ht = self.instrument.tem.HighTension
			mag = self.instrument.tem.Magnification
			probe = self.instrument.tem.ProbeMode
		except:
			self.logger.error(errstr % 'unable to access instrument')
			return
		eufocdata = self.euclient.researchEucentricFocus(ht, mag, probe)
		if eufocdata is None:
			self.logger.error('No eucentric focus found for HT: %s , Mag.: %s, and %s probe' % (ht, mag, probe))
		else:
			eufoc = eufocdata['focus']
			self.logger.info('set focus to %s' % (eufoc,))
			self.instrument.tem.Focus = eufoc

	def eucentricFocusFromScope(self):
		errstr = 'Eucentric focus from instrument failed: %s'
		try:
			ht = self.instrument.tem.HighTension
			mag = self.instrument.tem.Magnification
			probe = self.instrument.tem.ProbeMode
			foc = self.instrument.tem.Focus
		except:
			self.logger.error(errstr % 'unable to access instrument')
			return
		try:
			self.euclient.publishEucentricFocus(ht, mag, probe, foc)
		except node.PublishError, e:
			self.logger.error(errstr % 'unable to save')
			return
		self.logger.info('Eucentric focus saved to database, HT: %s, Mag.: %s, Focus: %s' % (ht, mag, foc))

	def manualNow(self):
		errstr = 'Manual focus failed: %s'
		presetname = self.settings['manual focus preset']
		if not presetname:
			message = 'no presets specified for manual focus'
			self.logger.error(errstr % message)
			return
		istr = 'Using preset \'%s\' for manual focus check' % (presetname,)
		self.logger.info(istr)
		### Warning:  no target is being used, you are exposing
		### whatever happens to be under the beam
		setting = {'preset name': presetname}
		t = threading.Thread(target=self.manualCheckLoop, args=(setting,None))
		t.setDaemon(1)
		t.start()

	def onManualCheck(self):
		evt = gui.wx.Focuser.ManualCheckEvent(self.panel)
		self.panel.GetEventHandler().AddPendingEvent(evt)

	def onManualCheckDone(self):
		evt = gui.wx.Focuser.ManualCheckDoneEvent(self.panel)
		self.panel.GetEventHandler().AddPendingEvent(evt)

	def acquireManualFocusImage(self):
		t0 = time.time()
		correction = self.settings['correct image']
		self.manualchecklock.acquire()
		if correction:
			imdata = self.acquireCorrectedCameraImageData()
		else:
			imdata = self.acquireCameraImageData()
		imarray = imdata['image']
		self.manualchecklock.release()
		pow = imagefun.power(imarray, self.maskradius)
		self.man_power = pow.astype(numpy.float32)
		self.man_image = imarray.astype(numpy.float32)
		self.panel.setManualImage(self.man_image, 'Image')
		self.panel.setManualImage(self.man_power, 'Power')
		#sleep if too fast in simulation
		safetime = 1.0
		t1 = time.time()
		if t1-t0 < safetime:
			time.sleep(safetime-(t1-t0))

	def getTEMCsValue(self):
		scopedata = self.instrument.getData(leginondata.ScopeEMData)
		cs = scopedata['tem']['cs']
		return cs

	def manualCheckLoop(self, setting, emtarget=None, focusresult=None):
		## go to preset and target
		presetname = setting['preset name']
		if presetname is not None:
			self.presetsclient.toScope(presetname, emtarget)
		pixelsize,center = self.getReciprocalPixelSizeFromPreset(presetname)
		self.ht = self.instrument.tem.HighTension
		self.cs = self.getTEMCsValue()
		self.panel.onNewPixelSize(pixelsize,center,self.ht,self.cs)
		self.logger.info('Starting manual focus loop, please confirm defocus...')
		self.beep()
		self.manualplayer.play()
		self.onManualCheck()
		while True:
			state = self.manualplayer.state()
			if state == 'stop':
				break
			elif state == 'pause':
				if self.manualplayer.wait() == 'stop':
					break
				if presetname is not None:
					self.logger.info('Reseting preset and target after pause')
					self.logger.debug('preset %s' % (presetname,))
					self.presetsclient.toScope(presetname, emtarget)
			# acquire image, show image and power spectrum
			# allow user to adjust defocus and stig
			try:
				self.setTEMState()
			except:
				raise
				self.manualchecklock.release()
				self.manualplayer.stop()
				self.logger.error('Failed to set TEM state, stoping...')
				continue

			try:
				self.acquireManualFocusImage()
			except:
				self.resetTEMState()
				raise
				self.manualchecklock.release()
				self.manualplayer.pause()
				self.logger.error('Failed to acquire image, pausing...')
				continue

		self.onManualCheckDone()
		self.logger.info('Manual focus check completed')
		return 'ok'

	def getReciprocalPixelSizeFromPreset(self,presetname):
		if presetname is None:
			return None, None
		q = leginondata.PresetData(session=self.session,name=presetname)
		results = q.query(results=1)
		if not results:
			return None, None
		presetdata = results[0]
		scope = presetdata['tem']
		ccd = presetdata['ccdcamera']
		mag = presetdata['magnification']
		unbinned_rpixelsize = self.btcalclient.getPixelSize(mag,tem=scope, ccdcamera=ccd)
		if unbinned_rpixelsize is None:
			return None, None
		binning = presetdata['binning']
		dimension = presetdata['dimension']
		rpixelsize = {'x':1.0/(unbinned_rpixelsize*binning['x']*dimension['x']),'y':1.0/(unbinned_rpixelsize*binning['y']*dimension['y'])}
		# This will not work for non-square image
		self.rpixelsize = rpixelsize['x']
		center = {'x':dimension['x'] / 2, 'y':dimension['y'] / 2}
		return rpixelsize, center

	def estimateAstigmation(self,params):
		z0, zast, ast_ratio, angle = fftfun.getAstigmaticDefocii(params,self.rpixelsize,self.ht)
		self.logger.info('z0 %.2f um, zast %.2f um (%.0f %%), angle= %.0f deg' % (z0*1e6,zast*1e6,ast_ratio*100, angle*180.0/math.pi))

	def setParameterChoice(self,parameter):
		self.parameter_choice = parameter

	def onFocusUp(self, parameter):
		self.changeFocus(parameter, 'up')
		self.panel.manualUpdated()

	def onFocusDown(self, parameter):
		self.changeFocus(parameter, 'down')
		self.panel.manualUpdated()

	def onResetDefocus(self):
		self.manualchecklock.acquire()
		self.logger.info('Reseting defocus...')
		if self.deltaz:
			self.logger.info('temporarily applying defocus offset due to z offset %.3e of image shifted target' % (self.deltaz,))
			origdefocus = self.instrument.tem.Defocus
			tempdefocus = origdefocus - self.deltaz
			self.instrument.tem.Defocus = tempdefocus
		try:
			self.resetDefocus()
			self.logger.info('Defocus reset')
		finally:
			if self.deltaz:
				self.instrument.tem.Defocus = self.deltaz
				self.logger.info('returned to defocus offset for image shifted target')
			self.manualchecklock.release()
			self.panel.manualUpdated()

	def resetDefocus(self):
		errstr = 'Reset defocus failed: %s'
		try:
			self.instrument.tem.resetDefocus()
		except:
			self.logger.error(errstr % 'unable to access instrument')

	def onChangeToEucentric(self):
		self.manualchecklock.acquire()
		self.logger.info('Changing to eucentric focus')
		try:
			self.eucentricFocusToScope()
		finally:
			self.manualchecklock.release()
			self.panel.manualUpdated()

	def onEucentricFromScope(self):
		self.eucentricFocusFromScope()
		self.panel.manualUpdated()

	def setFocus(self, value):
		self.manualchecklock.acquire()
		if self.deltaz:
			final = value + self.deltaz
			self.logger.info('Setting defocus to %.3e + z offset %.3e = %.3e' % (value,self.deltaz, final))
		else:
			final = value
			self.logger.info('Setting defocus to %.3e' % (value,))
		try:
			self.instrument.tem.Defocus = final
		finally:
			self.manualchecklock.release()
			self.panel.manualUpdated()

	def changeFocus(self, parameter, direction):
		delta = self.increment
		self.manualchecklock.acquire()
		self.logger.info('Changing %s %s %s' % (parameter, direction, delta))
		try:
			if parameter == 'Stage Z':
				value = self.instrument.tem.StagePosition['z']
			elif parameter == 'Defocus':
				value = self.instrument.tem.Defocus
			if direction == 'up':
				value += delta
			elif direction == 'down':
				value -= delta
			
			if parameter == 'Stage Z':
				self.instrument.tem.StagePosition = {'z': value}
			elif parameter == 'Defocus':
				self.instrument.tem.Defocus = value
		except Exception, e:
			self.logger.exception('Change focus failed: %s' % e)
			self.manualchecklock.release()
			return

		self.manualchecklock.release()

	def onManualPlayer(self, state):
		self.panel.playerEvent(state, self.panel.manualdialog)

	def setTEMState(self):
		pass

	def resetTEMState(self):
		pass
