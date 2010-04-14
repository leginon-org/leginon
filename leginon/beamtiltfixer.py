#
# COPYRIGHT:
#	   The Leginon software is Copyright 2003
#	   The Scripps Research Institute, La Jolla, CA
#	   For terms of the license agreement
#	   see  http://ami.scripps.edu/software/leginon-license
#
import acquisition
import node
import leginondata
import calibrationclient
import threading
import event
import time
import math
from pyami import correlator, peakfinder, imagefun, numpil,arraystats,fftfun
import numpy
from scipy import ndimage
import copy
import gui.wx.BeamTiltFixer
import player
import tableau
import subprocess
import re
import os

class BeamTiltFixer(acquisition.Acquisition):
	panelclass = gui.wx.BeamTiltFixer.Panel
	settingsclass = leginondata.BeamTiltFixerSettingsData
	defaultsettings = acquisition.Acquisition.defaultsettings
	defaultsettings.update({
		'process target type': 'acquisition',
		'beam tilt': 0.01,
		'min threshold': 0.00015,
		'max threshold': 0.0015,
	})

	eventinputs = acquisition.Acquisition.eventinputs
	eventoutputs = acquisition.Acquisition.eventoutputs

	def __init__(self, id, session, managerlocation, **kwargs):

		acquisition.Acquisition.__init__(self, id, session, managerlocation, **kwargs)
		self.btcalclient = calibrationclient.BeamTiltCalibrationClient(self)

	def alignRotationCenter(self, defocus1, defocus2):
		# use preset order preset if not set
		if not self.presetsclient.currentpreset:
			presetnames = self.settings['preset order']
			self.presetsclient.toScope(presetnames[0], None, keep_shift=False)
		try:
			bt = self.btcalclient.measureRotationCenter(defocus1, defocus2, correlation_type=None, settle=0.5)
		except Exception, e:
			estr = str(e)
			self.logger.error(estr)
			return
		self.logger.info('Misalignment correction: %.4f, %.4f' % (bt['x'],bt['y'],))
		oldbt = self.instrument.tem.BeamTilt
		self.logger.info('Old beam tilt: %.4f, %.4f' % (oldbt['x'],oldbt['y'],))
		newbt = {'x': oldbt['x'] + bt['x'], 'y': oldbt['y'] + bt['y']}
		self.instrument.tem.BeamTilt = newbt
		self.logger.info('New beam tilt: %.4f, %.4f' % (newbt['x'],newbt['y'],))

	def acquireCCD(self, presetdata, emtarget=None,channel=None):
		targetdata = emtarget['target']
		## set correction channel
		## in the future, may want this based on preset or something
		imagedata = self.acquireCameraImageData()
		tabimage, is_corrected = self.measureBeamTiltAndCorrect()
		imagedata['image'] = tabimage
		self.reportStatus('acquisition', 'image acquired')
		self.stopTimer('acquire getData')
		if imagedata is None:
			return 'fail'

		if self.settings['bad stats response'] != 'Continue':
			self.evaluateStats(imagedata['image'])

		## convert float to uint16
		if self.settings['save integer']:
			imagedata['image'] = numpy.clip(imagedata['image'], 0, 2**16-1)
			imagedata['image'] = numpy.asarray(imagedata['image'], numpy.uint16)

		## convert CameraImageData to AcquisitionImageData
		dim = imagedata['camera']['dimension']
		pixels = dim['x'] * dim['y']
		pixeltype = str(imagedata['image'].dtype)
		imagedata = leginondata.AcquisitionImageData(initializer=imagedata, preset=presetdata, label=self.name, target=targetdata, list=self.imagelistdata, emtarget=emtarget, pixels=pixels, pixeltype=pixeltype)
		imagedata['version'] = 0
		## store EMData to DB to prevent referencing errors
		self.publish(imagedata['scope'], database=True)
		self.publish(imagedata['camera'], database=True)
		# publish results only if not simulated
		if targetdata['image'] is not None:
			self.publishBeamTiltMeasurement(presetdata,targetdata,is_corrected)
		return imagedata
	
	def measureBeamTiltAndCorrect(self):
		is_corrected = False
		tilt_value = self.settings['beam tilt']
		calibration_client = self.btcalclient
		btilt0 = calibration_client.getBeamTilt()
		# measure axial coma beam tilt
		self.logger.info('Measuring axial coma beam tilt....')
		try:
			cftilt = calibration_client.repeatMeasureComaFree(tilt_value, settle=self.settings['pause time'],repeat=1)
			comatilt = {'x':cftilt[0].mean(),'y':cftilt[1].mean()}
			self.comameasurement = comatilt
			self.logger.info('Measured beam tilt x:%8.5f, y:%8.5f' % (comatilt['x'],comatilt['y']))
		except Exception, e:
			comatilt = None
			raise
			self.logger.error('Measurement failed: %s' % e)
		if comatilt:
			btilt_offset = math.hypot(comatilt['x'],comatilt['y'])
			if self.settings['min threshold'] < btilt_offset < self.settings['max threshold']:
				try:
					calibration_client.setBeamTilt({'x':-comatilt['x']+btilt0['x'],'y':-comatilt['y']+btilt0['y']})
					is_corrected = True
					self.logger.info('Beam Tilt Corrected')
				except Exception, e:
					self.logger.error('Beam Tilt Correction failed: %s' % e)
		return calibration_client.tabimage,is_corrected
	
	def publishBeamTiltMeasurement(self,presetdata,target,is_corrected=False):
		beamtiltdata = leginondata.BeamTiltMeasurementData()
		beamtiltdata['session'] = self.session
		beamtiltdata['preset'] = presetdata
		beamtiltdata['target'] = target
		beamtiltdata['beam tilt'] = self.comameasurement
		beamtiltdata['correction'] = is_corrected
		defocusarray = numpy.array(self.btcalclient.getMeasured_Defocii())
		beamtiltdata['mean defocus'] = defocusarray.mean()
		self.publish(beamtiltdata, database=True)
		self.logger.info('Measurement saved')

	def saveTableau(self,imagedata):
		init = imagedata
		tabim = self.tabimage
		filename = init['filename'] + '_tableau'
		cam = leginondata.CameraEMData(initializer=init['camera'])
		tab_bin = self.settings['tableau binning']
		new_bin = {'x':tab_bin*cam['binning']['x'], 'y':tab_bin*cam['binning']['y']}
		cam['dimension'] = {'x':tabim.shape[1],'y':tabim.shape[0]}
		cam['binning'] = new_bin

		tabimdata = leginondata.AcquisitionImageData(initializer=imagedata, image=self.tabimage, filename=filename, camera=cam)
		tabimdata.insert(force=True)
		self.logger.info('Saved tableau.')
