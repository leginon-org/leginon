#
# COPYRIGHT:
#	   The Leginon software is Copyright 2003
#	   The Scripps Research Institute, La Jolla, CA
#	   For terms of the license agreement
#	   see  http://ami.scripps.edu/software/leginon-license
#
import acquisition
import node, data
import calibrationclient
import corrector
import threading
import event
import time
import math
from pyami import correlator, peakfinder, imagefun
import numpy
import copy
import gui.wx.BeamTiltImager
import player

class BeamTiltImager(acquisition.Acquisition):
	panelclass = gui.wx.BeamTiltImager.Panel
	settingsclass = data.BeamTiltImagerSettingsData
	defaultsettings = {
		'pause time': 2.5,
		'move type': 'image shift',
		'preset order': [],
		'correct image': True,
		'display image': True,
		'save image': True,
		'wait for process': False,
		'wait for rejects': False,
		#'duplicate targets': False,
		#'duplicate target type': 'focus',
		'iterations': 1,
		'wait time': 0,
		'process target type': 'focus',
		'adjust for drift': False,
		'beam tilt': 0.01,
		'sites': 0,
		'startangle': 0,
		'correlation type': 'phase',
	}

	eventinputs = acquisition.Acquisition.eventinputs
	eventoutputs = acquisition.Acquisition.eventoutputs

	def __init__(self, id, session, managerlocation, **kwargs):

		self.correlator = correlator.Correlator()
		self.correlation_types = ['cross', 'phase']
		self.maskradius = 1.0
		self.increment = 5e-7
		acquisition.Acquisition.__init__(self, id, session, managerlocation, **kwargs)
		self.btcalclient = calibrationclient.BeamTiltCalibrationClient(self)
		self.imageshiftcalclient = calibrationclient.ImageShiftCalibrationClient(self)
		self.euclient = calibrationclient.EucentricFocusClient(self)
		self.corclient = corrector.CorrectorClient(self)

	def alignRotationCenter(self, defocus1, defocus2):
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

	def getBeamTiltList(self):
		tiltlist = []
		tiltlist.append({'x':0.0,'y':0.0})
		if self.settings['sites'] == 0:
			return tiltlist
		angle = 2*3.14159/self.settings['sites']
		startangle = self.settings['startangle'] * numpy.pi / 180.0
		for i in range(0,self.settings['sites']):
			bt = {}
			tilt = self.settings['beam tilt']
			bt['x']=math.cos(i*angle+startangle)*tilt
			bt['y']=math.sin(i*angle+startangle)*tilt
			tiltlist.append(bt)
		return tiltlist

	def acquire(self, presetdata, emtarget=None, attempt=None, target=None):
		'''
		this replaces Acquisition.acquire()
		Instead of acquiring an image, we do autofocus
		'''
		## sometimes have to apply or un-apply deltaz if image shifted on
		## tilted specimen
		if emtarget is None:
			self.deltaz = 0
		else:
			self.deltaz = emtarget['delta z']

		# aquire and save the focus image
		oldbt = self.instrument.tem.BeamTilt
		tiltlist = self.getBeamTiltList()

		## first target is the one given, the remaining are created now
		targetlist = []
		targetlist.append(target)
		for i in range(len(tiltlist)-1):
			## check if target is simulated or not
			if target['type'] == 'simulated':
				targetdata = self.newSimulatedTarget(preset=currentpreset)
			else:
				lastnumber = self.lastTargetNumber(image=target['image'], session=self.session)
				newnumber = lastnumber+1
				newtarget = leginondata.AcquisitionImageTargetData(initializer=target, number=newnumber)
			targetlist.append(newtarget)

		displace = []
		for i,bt in enumerate(tiltlist):
			target = targetlist[i]
			if i == 0:
				channel = 0
			else:
				channel = 1
			self.logger.info('Old beam tilt: %.4f, %.4f' % (oldbt['x'],oldbt['y'],))
			newbt = {'x': oldbt['x'] + bt['x'], 'y': oldbt['y'] + bt['y']}
			self.instrument.tem.BeamTilt = newbt
			self.logger.info('New beam tilt: %.4f, %.4f' % (newbt['x'],newbt['y'],))
			status,imagedata = acquisition.Acquisition.acquire(self, presetdata, emtarget, channel= channel)
			self.instrument.tem.BeamTilt = oldbt
			try:
				shiftinfo = self.correlateOriginal(i,imagedata)
			except Exception, e:
				self.logger.error('Failed correlation: %s' % e)
				return 'error'
			pixelshift = shiftinfo['pixel shift']
			displace.append((pixelshift['row'],pixelshift['col']))
		print displace
		return status

	def alreadyAcquired(self, targetdata, presetname):
		## for now, always do acquire
		return False
	
	def correlateOriginal(self,index,imagedata):
		if index == 0:
			self.originalimage = imagedata['image']
			unbinned = {'row':0.0, 'col': 0.0}
		else:
			## correlate
			self.startTimer('scope change correlation')
			try:
				correlation_type = self.settings['correlation type']
			except KeyError:
				correlation_type = 'phase'
			if correlation_type == 'cross':
				cor = correlator.cross_correlate(self.originalimage,imagedata['image'])
			elif correlation_type == 'phase':
				cor = correlator.phase_correlate(self.originalimage,imagedata['image'],False,wiener=True)
			else:
				raise RuntimeError('invalid correlation type')
			self.stopTimer('scope change correlation')
			self.displayCorrelation(cor)

			## find peak
			self.startTimer('shift peak')
			peak = peakfinder.findSubpixelPeak(cor)
			self.stopTimer('shift peak')

			self.logger.debug('Peak %s' % (peak,))

			pixelpeak = peak['subpixel peak']
			self.startTimer('shift display')
			self.displayPeak(pixelpeak)
			self.stopTimer('shift display')

			peakvalue = peak['subpixel peak value']
			shift = correlator.wrap_coord(peak['subpixel peak'], cor.shape)
			self.logger.debug('pixel shift (row,col): %s' % (shift,))

			## need unbinned result
			binx = imagedata['camera']['binning']['x']
			biny = imagedata['camera']['binning']['y']
			unbinned = {'row':shift[0] * biny, 'col': shift[1] * binx}

		shiftinfo = {'previous': self.originalimage, 'next': imagedata, 'pixel shift': unbinned}
		return shiftinfo

	def displayCorrelation(self, im):
		try:
			self.setImage(im, 'Correlation')
		except:
			pass

	def displayPeak(self, rowcol=None):
		if rowcol is None:
			targets = []
		else:
			# target display requires x,y order not row,col
			targets = [(rowcol[1], rowcol[0])]
		try:
			self.setTargets(targets, 'Peak')
		except:
			pass

	def initSameCorrection(self):
		self.samecorrection = True
		self.correctargs = None

	def endSameCorrection(self):
		self.samecorrection = False

	def acquireCorrectedImage(self):
		if not self.samecorrection or (self.samecorrection and not self.correctargs):
			## acquire image and scope/camera params
			imagedata = self.instrument.getData(data.CameraImageData)
			imarray = imagedata['image']
			self.correctargs = {}
			camdata = imagedata['camera']
			self.correctargs['ccdcamera'] = camdata['ccdcamera']
			corstate = data.CorrectorCamstateData()
			corstate['dimension'] = camdata['dimension']
			corstate['offset'] = camdata['offset']
			corstate['binning'] = camdata['binning']
			self.correctargs['camstate'] = corstate
			self.correctargs['scopedata'] = imagedata['scope']
		else:
			## acquire only raw image
			imarray = self.instrument.ccdcamera.Image

		corrected = self.corclient.correct(original=imarray, **self.correctargs)
		return corrected

