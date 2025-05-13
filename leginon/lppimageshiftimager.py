#
# COPYRIGHT:
#	   The Leginon software is Copyright under
#	   Apache License, Version 2.0
#	   For terms of the license agreement
#	   see  http://leginon.org
#
from leginon import manualfocuschecker
from leginon import node
from leginon import leginondata
from leginon import calibrationclient
from leginon import lppfit
import threading
from leginon import event
import time
import math
from pyami import correlator, peakfinder, imagefun, numpil,arraystats,fftfun
import numpy
from scipy import ndimage
import copy
import leginon.gui.wx.LppImageShiftImager
from leginon import player
from leginon import tableau
import subprocess
import re
import os

from pyami import aberration

hide_incomplete = False
TESTING = False

class LppImageShiftImager(manualfocuschecker.ManualFocusChecker):
	panelclass = leginon.gui.wx.LppImageShiftImager.Panel
	settingsclass = leginondata.LppImageShiftImagerSettingsData
	defaultsettings = dict(manualfocuschecker.ManualFocusChecker.defaultsettings)
	defaultsettings.update({
		'process target type': 'focus',
		'image shift': 0.005,
		'image shift count': 1,
		'sites': 1,
		'startangle': 0,
		'tableau type': 'image shift series-lpp defocused',
		'tableau binning': 2,
		'fringe rotation': 3, # degrees
	})

	eventinputs = manualfocuschecker.ManualFocusChecker.eventinputs
	eventoutputs = manualfocuschecker.ManualFocusChecker.eventoutputs

	def __init__(self, id, session, managerlocation, **kwargs):

		self.tableau_types = ['image shift series-lpp defocused','image shift series-lpp infocus']
		self.shiftdelta = 5e-3
		self.tabscale = None
		manualfocuschecker.ManualFocusChecker.__init__(self, id, session, managerlocation, **kwargs)
		self.parameter_choice= 'Beam Tilt X'
		self.increment = 5e-4
		self.btcalclient = calibrationclient.BeamTiltCalibrationClient(self)
		self.ctfcalclient = calibrationclient.CtfCalibrationClient(self)
		self.cs = None
		# ace2 is not used for now.
		self.ace = None
		self.auto_count = 0

	def getImageShiftList(self):
		shiftlist = []
		anglelist = []
		radlist = []

		shiftlist.append({'x':0.0,'y':0.0})
		anglelist.append(None)
		radlist.append(0)

		angleinc = 2*3.14159/self.settings['sites']
		startangle = self.settings['startangle'] * numpy.pi / 180.0
		for i in range(0,self.settings['sites']):
			for n in range(1, 1 + self.settings['image shift count']):
				radlist.append(n)	
				shift = n * self.settings['image shift']
				angle = i * angleinc + startangle
				anglelist.append(angle)
				bt = {}
				bt['x']=math.cos(angle)*shift
				bt['y']=math.sin(angle)*shift
				shiftlist.append(bt)
		return shiftlist, anglelist, radlist

	def initTableau(self):
		self.tableauimages = []
		self.tableauangles = []
		self.tableaurads = []
		self.tabimage = None
		self.ctfdata = []

	def insertTableau(self, imagedata, angle, rad, result):
		image = imagedata['image']
		binning = self.settings['tableau binning']
		if self.settings['tableau type'] == 'image shift series-lpp infocus':
			binned = self.makeBinnedImageAndAddCTFlabel(image, result, binning)
		else:
			binned = imagefun.bin(image, binning)
			binned = self.makeBinnedImageAndAddFringeFitlabel(image, result, binning)
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
		if self.settings['tableau type'] == 'image shift series-lpp infocus':
			mean = self.tabimage.mean()
			std = self.tabimage.std()
			a = numpy.where(self.tabimage >= mean + 5*std, 0, self.tabimage)
			self.tabimage = numpy.clip(a, 0, mean*1.5)
		self.displayTableau()
		self.saveTableau()

	def catchBadSettings(self,presetdata):
		if 'image shift' in self.settings['tableau type']:
			if (presetdata['dimension']['x'] > 2048 or presetdata['dimension']['y'] > 2048):
				self.logger.error('Analysis will be too slow: Reduce preset image dimension')
				return 'error'
		# Bad image binning will cause error
			if presetdata['dimension']['x'] % self.settings['tableau binning'] != 0 or presetdata['dimension']['y'] % self.settings['tableau binning'] != 0:
				self.logger.error('Preset dimension not dividable by binning. Correct Settings or preset dimension')
				return 'error'
		if 'split image' in self.settings['tableau type']:
			if presetdata['dimension']['x'] % self.settings['tableau split'] != 0 or presetdata['dimension']['y'] % self.settings['tableau split'] != 0:
				self.logger.error('Preset dimension can not be split evenly. Correct Settings or preset dimension')
				return 'error'

	def acquire(self, presetdata, emtarget=None, attempt=None, target=None):
		'''
		this replaces Acquisition.acquire()
		Instead of acquiring an image, we acquire a series of image shift images
		'''
		if self.catchBadSettings(presetdata) == 'error':
			return 'error'

		self.defocus = presetdata['defocus']
		## sometimes have to apply or un-apply deltaz if image shifted on
		## shifted specimen
		if emtarget is None:
			self.deltaz = 0
		else:
			self.deltaz = emtarget['delta z']

		# aquire and save the image
		# Need to set Magnification of the preset first so that beam and stig is valid
		self.setPresetMagProbeMode(presetdata, emtarget)

		oldbt = self.instrument.tem.ImageShift
		oldstig = self.instrument.tem.Stigmator['objective']
		shiftlist,anglelist,radlist = self.getImageShiftList()

		## initialize a new tableau
		self.initTableau()
		ht = self.instrument.tem.HighTension

		## first target is the one given, the remaining are created now
		emtargetlist = []
		emtargetlist.append(emtarget)
		for i in range(len(shiftlist)-1):
			## check if target is simulated or not
			if target['type'] == 'simulated':
				newtarget = self.newSimulatedTarget(preset=presetdata)
				newemtarget = leginondata.EMTargetData(initializer=emtarget, target=newtarget)
			else:
				lastnumber = self.lastTargetNumber(image=target['image'], session=self.session)
				newnumber = lastnumber+1
				newtarget = leginondata.AcquisitionImageTargetData(initializer=target, number=newnumber)
				newemtarget = leginondata.EMTargetData(initializer=emtarget, target=newtarget)

			bt = shiftlist[i+1]
			oldbt = emtarget['image shift']
			newbt = {'x': oldbt['x'] + bt['x'], 'y': oldbt['y'] + bt['y']}
			newemtarget['image shift'] = newbt
			newemtarget.insert(force=True)
			emtargetlist.append(newemtarget)

		displace = []
		for i,bt in enumerate(shiftlist):
			emtarget = emtargetlist[i]
			if i == 0:
				channel = 0
			else:
				channel = 1
			# image shift is set by emtarget
			newbt = emtarget['image shift']
			self.logger.info('New image shift um: %.4f, %.4f' % (newbt['x']*1e6,newbt['y']*1e6,))
			self.x1focus = self.instrument.tem.PhasePlateFocus
			if self.settings['tableau type'] == 'image shift series-lpp defocused':
				self.instrument.tem.PhasePlateFocus = self.x1focus - 0.005
			# actual move by emtarget/preset and acquire
			try:
				status = manualfocuschecker.ManualFocusChecker.acquire(self, presetdata, emtarget, channel= channel)
			except Exception as e:
				self.instrument.tem.PhasePlateFocus = self.x1focus
				self.logger.error('Failed acquiring image: %s' % e)
				self.setComaStig0()
				return 'error'
			if self.settings['tableau type'] == 'image shift series-lpp defocused':
				self.instrument.tem.PhasePlateFocus = self.x1focus
			imagedata = self.imagedata
			# get these values once
			self.setImage(imagedata['image'], 'Image')
			self.instrument.tem.ImageShift = oldbt
			angle = anglelist[i]
			rad = radlist[i]

			if self.settings['tableau type'] == 'image shift series-lpp infocus':
				ctfresult = self.getImageCtfResult(imagedata)
				if ctfresult:
					if ctfresult['confidence'] < 0.01:
						self.logger.error('gctffind fitting bad score=%.1f score' % ctfresult['confidence'])
						self.ctfdata.append(ctfresult)
				self.insertTableau(imagedata, angle, rad, ctfresult)
			if self.settings['tableau type'] == 'image shift series-lpp defocused':
				try:
					fringeresult = self.fitLppFringes(imagedata)
				except Exception as e:
					self.logger.error('Failed lpp fringe fitting: %s' % e)
					return 'error'
				self.insertTableau(imagedata, angle, rad, fringeresult)
		if 'image shift series' in self.settings['tableau type']:
			self.renderTableau()
			self.instrument.tem.ImageShift = oldbt
			self.logger.info('Final image shift: %.5f, %.5f' % (oldbt['x'],oldbt['y'],))
			# image shift series modifies self.beamshift0 and self.stig0 at each shift
			# when it calls moveAndPreset. Need to reset them back to the value before
			# the series.
			self.setComaStig0()
		return status

	def simulateTarget(self):
		self._parentSimulateTarget()
		return

	def _parentSimulateTarget(self):
		# Doing the parent simulateTarget action.
		# See redmine issue #16176
		return super(LppImageShiftImager,self).simulateTarget()

	def alreadyAcquired(self, targetdata, presetname):
		## for now, always do acquire
		return False
	
	def fitLppFringes(self,imagedata):
		myimage = imagedata['image']
		try:
			amp_fit, freq_fit, phase_fit, offset_fit, period_fit, phase_shift_needed = lppfit.run_fringe_fit(myimage, self.settings['fringe rotation'])
			shiftinfo = {'period': period_fit, 'phase_shift': phase_shift_needed}
			return shiftinfo
		except Exception as e:
			raise RuntimeError('failed fitting: %s' % e)

	def displayTableau(self):
		try:
			self.setImage(self.tabimage, 'Tableau')
		except:
			pass

	def applyTiltChange(self, deltabt):
			oldbt = self.instrument.tem.ImageShift
			self.logger.info('Old image shift: %.4f, %.4f' % (oldbt['x'],oldbt['y'],))
			newbt = {'x': oldbt['x'] + deltabt['x'], 'y': oldbt['y'] + deltabt['y']}
			self.instrument.tem.ImageShift = newbt
			self.logger.info('New image shift: %.4f, %.4f' % (newbt['x'],newbt['y'],))

	def applyTiltChangeAndReacquireTableau(self,deltabt):
			self.applyTiltChange(deltabt)
			self.simulateTarget()
			newbt = self.instrument.tem.ImageShift
			self.logger.info('Final image shift: %.4f, %.4f' % (newbt['x'],newbt['y'],))

	def navigate(self, xy):
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
			bt['x'] = deltacol * self.settings['image shift']/self.tabscale
			bt['y'] = -deltarow * self.settings['image shift']/self.tabscale
			self.applyTiltChangeAndReacquireTableau(bt)
		else:
			self.logger.warning('need more than one image shift images in tableau to navigate')


	def getImageCtfResult(self, imagedata):
		phase_search = (0,15)
		try:
			defocus_avg, ctfvalues = self.ctfcalclient.measureImageCtf(imagedata, phase_search)
		except Exception as e:
			self.logger.error('Error estimating ctf: %s' % e)
		return ctfvalues

	def getSimulatedImageCtfResult(self, imagedata):
		'''
		return simulate ctf result with this function call instead of getImageCtfResult
		'''
		phase_search = (0,15)
		defocus_avg, ctfvalues = self.ctfcalclient.measureImageCtf(imagedata, phase_search)
		return ctfvalues

	def _addTextToImageArray(self, image, s):
		if s:
			t = numpil.textArray(s)
			min_axis_index = (image.shape).index(min(image.shape))
			zoom_factor = (min(image.shape)-40.0)*0.08/(t.shape)[0]
			if (zoom_factor * t.shape[1])+40 > image.shape[1]:
				zoom_factor = (image.shape[1]-40.0)/t.shape[1]
			t = ndimage.zoom(t, zoom_factor)
			minvalue = arraystats.min(image)
			maxvalue = arraystats.max(image)
			t = minvalue + t * (maxvalue-minvalue)
			imagefun.pasteInto(t, image, (20,20))
		return image

	def makeBinnedImageAndAddFringeFitlabel(self, image, fitresult, binning):
		binned = imagefun.bin(image, binning)
		try:
			s = 'p-p=%.1f, phi=%.1f deg' % (fitresult['period'], fitresult['phase_shift'])
		except:
			s = 'failed'
		return self._addTextToImageArray(binned, s)

	def makeBinnedImageAndAddCTFlabel(self, image, ctfresult, binning=1, defocus=None):
		binned = imagefun.bin(image, binning)
		try:
			s = 'def=%.2f um, phi=%.1f deg' % ((ctfresult['defocus1']+ctfresult['defocus2'])*1e-4/2, ctfresult['extra_phase_shift'])
		except:
			s = 'failed'
		return self._addTextToImageArray(binned, s)

	def saveTableau(self):
		init = self.imagedata
		tabim = self.tabimage
		filename = init['filename'] + '_tableau'
		cam = leginondata.CameraEMData(initializer=init['camera'])
		tab_bin = self.settings['tableau binning']
		new_bin = {'x':tab_bin*cam['binning']['x'], 'y':tab_bin*cam['binning']['y']}
		cam['dimension'] = {'x':tabim.shape[1],'y':tabim.shape[0]}
		cam['binning'] = new_bin

		tabimdata = leginondata.AcquisitionImageData(initializer=self.imagedata, image=self.tabimage, filename=filename, camera=cam)
		tabimdata.insert(force=True)
		self.logger.info('Saved tableau.')

