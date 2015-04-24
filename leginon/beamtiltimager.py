#
# COPYRIGHT:
#	   The Leginon software is Copyright 2003
#	   The Scripps Research Institute, La Jolla, CA
#	   For terms of the license agreement
#	   see  http://ami.scripps.edu/software/leginon-license
#
import manualfocuschecker
import node
from leginon import leginondata
import calibrationclient
import threading
import event
import time
import math
from pyami import correlator, peakfinder, imagefun, numpil,arraystats,fftfun
import numpy
from scipy import ndimage
import copy
import gui.wx.BeamTiltImager
import player
import tableau
import subprocess
import re
import os

hide_incomplete = False

class BeamTiltImager(manualfocuschecker.ManualFocusChecker):
	panelclass = gui.wx.BeamTiltImager.Panel
	settingsclass = leginondata.BeamTiltImagerSettingsData
	defaultsettings = manualfocuschecker.ManualFocusChecker.defaultsettings
	defaultsettings.update({
		'process target type': 'focus',
		'beam tilt': 0.005,
		'beam tilt count': 1,
		'sites': 0,
		'startangle': 0,
		'correlation type': 'phase',
		'tableau type': 'split image-power',
		'tableau binning': 2,
		'tableau split': 8,
	})

	eventinputs = manualfocuschecker.ManualFocusChecker.eventinputs
	eventoutputs = manualfocuschecker.ManualFocusChecker.eventoutputs

	def __init__(self, id, session, managerlocation, **kwargs):

		self.correlator = correlator.Correlator()
		self.correlation_types = ['cross', 'phase']
		self.tableau_types = ['beam tilt series-power','split image-power']
		if not hide_incomplete:
			self.tableau_types.append('beam tilt series-image')
		self.tiltdelta = 5e-3
		self.tabscale = None
		manualfocuschecker.ManualFocusChecker.__init__(self, id, session, managerlocation, **kwargs)
		self.parameter_choice= 'Beam Tilt X'
		self.increment = 5e-4
		self.btcalclient = calibrationclient.BeamTiltCalibrationClient(self)
		self.imageshiftcalclient = calibrationclient.ImageShiftCalibrationClient(self)
		self.euclient = calibrationclient.EucentricFocusClient(self)
		self.rpixelsize = None
		self.ht = None
		self.cs = None
		# ace2 is not used for now.
		#self.ace2exe = self.getACE2Path()

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
		anglelist = []
		radlist = []

		tiltlist.append({'x':0.0,'y':0.0})
		anglelist.append(None)
		radlist.append(0)

		if self.settings['sites'] == 0 or self.settings['tableau type'] == 'split image-power':
			return tiltlist, anglelist, radlist
		angleinc = 2*3.14159/self.settings['sites']
		startangle = self.settings['startangle'] * numpy.pi / 180.0
		for i in range(0,self.settings['sites']):
			for n in range(1, 1 + self.settings['beam tilt count']):
				radlist.append(n)	
				tilt = n * self.settings['beam tilt']
				angle = i * angleinc + startangle
				anglelist.append(angle)
				bt = {}
				bt['x']=math.cos(angle)*tilt
				bt['y']=math.sin(angle)*tilt
				tiltlist.append(bt)
		return tiltlist, anglelist, radlist

	def initTableau(self):
		self.tableauimages = []
		self.tableauangles = []
		self.tableaurads = []
		self.tabimage = None
		self.ctfdata = []

	def splitTableau(self, imagedata):
		image = imagedata['image']
		split = self.settings['tableau split']
		self.tabimage = tableau.splitTableau(image, split)
		#self.addCornerCTFlabels(imagedata, split)
		self.tabscale = None
		self.displayTableau()
		self.saveTableau()

	def addCornerCTFlabels(self, imagedata, split):
		self.ht = imagedata['scope']['high tension']
		self.cs = imagedata['scope']['tem']['cs']
		image = imagedata['image']
		if not self.rpixelsize:
			self.rpixelsize = self.btcalclient.getImageReciprocalPixelSize(imagedata)
			self.rpixelsize['x'] *= split
			self.rpixelsize['y'] *= split
		splitsize = int(math.floor(image.shape[0]*0.5/int(split)))*2, int(math.floor(image.shape[1]*0.5/int(split)))*2
		for row in (0,(split/2)*splitsize[0],(split-1)*splitsize[0]):
			rowslice = slice(row,row+splitsize[0])
			for col in (0,(split/2)*splitsize[1],(split-1)*splitsize[1]):
				colslice = slice(col,col+splitsize[1])
				splitimage = image[rowslice,colslice]
				labeled, ctfdata = self.binAndAddCTFlabel(splitimage, self.ht, self.cs, self.rpixelsize, 1, self.defocus)
				self.tabimage[rowslice,colslice] = labeled

	def insertTableau(self, imagedata, angle, rad):
		image = imagedata['image']
		binning = self.settings['tableau binning']
		if self.settings['tableau type'] != 'beam tilt series-image':
			binned, ctfdata = self.binAndAddCTFlabel(image, self.ht, self.cs, self.rpixelsize, binning, self.defocus)
			self.ctfdata.append(ctfdata)
		else:
			binned = imagefun.bin(image, binning)
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
		if self.settings['tableau type'] == 'beam tilt series-image':
			mean = self.tabimage.mean()
			std = self.tabimage.std()
			a = numpy.where(self.tabimage >= mean + 5*std, 0, self.tabimage)
			self.tabimage = numpy.clip(a, 0, mean*1.5)
		self.displayTableau()
		self.saveTableau()

	def catchBadSettings(self,presetdata):
		if 'beam tilt' in self.settings['tableau type']:
			if (presetdata['dimension']['x'] > 1024 or presetdata['dimension']['y'] > 1024):
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
		Instead of acquiring an image, we acquire a series of beam tilt images
		'''
		if self.catchBadSettings(presetdata) == 'error':
			return 'error'

		self.rpixelsize = None
		self.defocus = presetdata['defocus']
		## sometimes have to apply or un-apply deltaz if image shifted on
		## tilted specimen
		if emtarget is None:
			self.deltaz = 0
		else:
			self.deltaz = emtarget['delta z']

		# aquire and save the focus image
		oldbt = self.instrument.tem.BeamTilt
		tiltlist,anglelist,radlist = self.getBeamTiltList()

		## initialize a new tableau
		self.initTableau()

		## first target is the one given, the remaining are created now
		emtargetlist = []
		emtargetlist.append(emtarget)
		for i in range(len(tiltlist)-1):
			## check if target is simulated or not
			if target['type'] == 'simulated':
				newtarget = self.newSimulatedTarget(preset=presetdata)
				newemtarget = leginondata.EMTargetData(initializer=emtarget, target=newtarget)
			else:
				lastnumber = self.lastTargetNumber(image=target['image'], session=self.session)
				newnumber = lastnumber+1
				newtarget = leginondata.AcquisitionImageTargetData(initializer=target, number=newnumber)
				newemtarget = leginondata.EMTargetData(initializer=emtarget, target=newtarget)

			newemtarget.insert(force=True)
			emtargetlist.append(newemtarget)

		displace = []
		for i,bt in enumerate(tiltlist):
			emtarget = emtargetlist[i]
			if i == 0:
				channel = 0
			else:
				channel = 1
			self.logger.info('Old beam tilt: %.4f, %.4f' % (oldbt['x'],oldbt['y'],))
			newbt = {'x': oldbt['x'] + bt['x'], 'y': oldbt['y'] + bt['y']}
			self.instrument.tem.BeamTilt = newbt
			self.logger.info('New beam tilt: %.4f, %.4f' % (newbt['x'],newbt['y'],))
			status = manualfocuschecker.ManualFocusChecker.acquire(self, presetdata, emtarget, channel= channel)
			imagedata = self.imagedata
			# get these values once
			if not self.rpixelsize or not self.ht or not self.cs:
				self.rpixelsize = self.btcalclient.getImageReciprocalPixelSize(imagedata)
				self.ht = imagedata['scope']['high tension']
				self.cs = imagedata['scope']['tem']['cs']
			self.setImage(imagedata['image'], 'Image')
			self.instrument.tem.BeamTilt = oldbt
			angle = anglelist[i]
			rad = radlist[i]

			if self.settings['tableau type'] == 'split image-power':
				self.splitTableau(imagedata)
			elif 'beam tilt series' in self.settings['tableau type']:
				self.insertTableau(imagedata, angle, rad)
			if self.settings['tableau type'] == 'beam tilt series-image':
				try:
					shiftinfo = self.correlateOriginal(i,imagedata)
				except Exception, e:
					self.logger.error('Failed correlation: %s' % e)
					return 'error'
				pixelshift = shiftinfo['pixel shift']
				displace.append((pixelshift['row'],pixelshift['col']))
		if 'beam tilt series' in self.settings['tableau type']:
			self.renderTableau()
			# not to calculate Axial Coma to save time for now
			#if 'power' in self.settings['tableau type']:
			#	self.calculateAxialComa(self.ctfdata)
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

	def displayTableau(self):
		try:
			self.setImage(self.tabimage, 'Tableau')
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
			bt['x'] = deltacol * self.settings['beam tilt']/self.tabscale
			bt['y'] = -deltarow * self.settings['beam tilt']/self.tabscale
			oldbt = self.instrument.tem.BeamTilt
			self.logger.info('Old beam tilt: %.4f, %.4f' % (oldbt['x'],oldbt['y'],))
			newbt = {'x': oldbt['x'] + bt['x'], 'y': oldbt['y'] + bt['y']}
			self.instrument.tem.BeamTilt = newbt
			self.logger.info('New beam tilt: %.4f, %.4f' % (newbt['x'],newbt['y'],))
			self.simulateTarget()
			self.logger.info('New beam tilt: %.4f, %.4f' % (newbt['x'],newbt['y'],))
		else:
			self.logger.warning('need more than one beam tilt images in tableau to navigate')

	def getACE2Path(self):
		exename = 'ace2.exe'
		ace2exe = subprocess.Popen("which "+exename, shell=True, stdout=subprocess.PIPE).stdout.read().strip()
		if not os.path.isfile(ace2exe):
			self.logger.warning(exename+" was not found in path. No ctf estimation")
			return None
		return ace2exe

	def binAndAddCTFlabel(self, image, ht, cs, rpixelsize, binning=1, defocus=None):
		pow = imagefun.power(image)
		binned = imagefun.bin(pow, binning)
		# No ctf estimation until it works better so that this node does not
		# depend on coma beam-tilt calibration
		s = None
		ctfdata = None
		'''
		try:
			ctfdata = fftfun.fitFirstCTFNode(pow,rpixelsize['x'], defocus, ht, cs)
		except Exception, e:
			self.logger.error("ctf fitting failed: %s" % e)
			ctfdata = None
		if ctfdata:
			self.logger.info('z0 %.3f um, zast %.3f um (%.0f ), angle= %.1f deg' % (ctfdata[0]*1e6,ctfdata[1]*1e6,ctfdata[2]*100, ctfdata[3]*180.0/math.pi))
			s = '%d' % int(ctfdata[0]*1e9)
		#elif self.ace2exe:
		elif False:
			ctfdata = self.estimateCTF(imagedata)
			z0 = (ctfdata['defocus1'] + ctfdata['defocus2']) / 2
			s = '%d' % (int(z0*1e9),)
		'''
		if s:
			t = numpil.textArray(s)
			t = ndimage.zoom(t, (min(binned.shape)-40.0)*0.08/(t.shape)[0])
			minvalue = arraystats.min(binned)
			maxvalue = arraystats.max(binned)
			t = minvalue + t * (maxvalue-minvalue)
			imagefun.pasteInto(t, binned, (20,20))
		return binned, ctfdata

	def estimateCTF(self, imagedata):
		mag = imagedata['scope']['magnification']
		tem = imagedata['scope']['tem']
		cam = imagedata['camera']['ccdcamera']
		pixelsize = self.btcalclient.getPixelSize(mag, tem, cam)
		inputparams = {
			'input': os.path.join(imagedata['session']['image path'],imagedata['filename']+".mrc"),
			'cs': 2.0,
			'kv': imagedata['scope']['high tension']/1000.0,
			'apix': pixelsize*1e10,
			'binby': 1,
		}

		### make standard input for ACE 2
		commandline = ( self.ace2exe
			+ " -i " + str(inputparams['input'])
			+ " -b " + str(inputparams['binby'])
			+ " -c " + str(inputparams['cs'])
			+ " -k " + str(inputparams['kv'])
			+ " -a " + str(inputparams['apix']) + "\n" )

		### run ace2
		self.logger.info("run ace2 on %s" % (imagedata['filename']))
		#aceoutf = open("ace2.out", "a")
		#aceerrf = open("ace2.err", "a")
		t0 = time.time()
		#ace2proc = subprocess.Popen(commandline, shell=True, stdout=aceoutf, stderr=aceerrf)
		ace2proc = subprocess.Popen(commandline, shell=True)
		ace2proc.wait()

		### check if ace2 worked
		imagelog = imagedata['filename']+".mrc"+".ctf.txt"
		if not os.path.isfile(imagelog):
			### ace2 always crashes on first image??? .fft_wisdom file??
			time.sleep(1)
			#ace2proc = subprocess.Popen(commandline, shell=True, stdout=aceoutf, stderr=aceerrf)
			ace2proc = subprocess.Popen(commandline, shell=True)
			ace2proc.wait()
		#aceoutf.close()
		#aceerrf.close()
		if not os.path.isfile(imagelog):
			self.logger.warning("ace2 did not run")

		### parse log file
		self.ctfvalues = {}
		logf = open(imagelog, "r")
		for line in logf:
			sline = line.strip()
			if re.search("^Final Defocus:", sline):
				parts = sline.split()
				self.ctfvalues['defocus1'] = float(parts[2])
				self.ctfvalues['defocus2'] = float(parts[3])
				### convert to degrees
				self.ctfvalues['angle_astigmatism'] = math.degrees(float(parts[4]))
			elif re.search("^Amplitude Contrast:",sline):
				parts = sline.split()
				self.ctfvalues['amplitude_contrast'] = float(parts[2])
			elif re.search("^Confidence:",sline):
				parts = sline.split()
				self.ctfvalues['confidence'] = float(parts[1])
				self.ctfvalues['confidence_d'] = float(parts[1])
		logf.close()

		### summary stats
		avgdf = (self.ctfvalues['defocus1']+self.ctfvalues['defocus2'])/2.0
		ampconst = 100.0*self.ctfvalues['amplitude_contrast']
		pererror = 100.0 * (self.ctfvalues['defocus1']-self.ctfvalues['defocus2']) / avgdf
		self.ctfvalues['astig'] = pererror
		self.logger.info("Amplitude contrast: %.2f percent"%(ampconst))
		self.logger.info("Final confidence: %.3f"%(self.ctfvalues['confidence']))
		self.logger.info("Defocus: %.3f x %.3f um, angle %.2f degress (%.2f %% astigmatism)"%
			(self.ctfvalues['defocus1']*1.0e6, self.ctfvalues['defocus2']*1.0e6, self.ctfvalues['angle_astigmatism'],pererror ))

		return self.ctfvalues

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


	def	calculateAxialComa(self,ctfdata):
		sites = self.settings['sites']
		b2 = [0,0]
		if 4 * (sites / 4) !=  sites or self.settings['startangle']:
			return
		skipangle = sites / 4
		for n in range(1, 1 + self.settings['beam tilt count']):
			tiltangle = self.settings['beam tilt'] * n
			for i in (0,1):
				index1 = n + i * skipangle
				index2 = n + (i+2) * skipangle
				if ctfdata[index1] is None or ctfdata[index2] is None:
					continue
				b2[i] = (3 / (8*tiltangle)) * (ctfdata[index1][0] - ctfdata[index2][0])
			self.logger.info('Axial Coma(um)= (%.2f,%.2f) at %.2f mrad tilt' % (b2[0]*1e6,b2[1]*1e6,tiltangle*1e3))
			mcal = (6.4,-7.0)
			tshape = self.tabimage.shape
			self.logger.info('Axial Coma(pixels)= (%.2f,%.2f)' % (mcal[0]*b2[0]*1e6+tshape[0]/2,mcal[1]*b2[1]*1e6+tshape[1]/2))

	def getTilt(self):
		newtilt = self.coma_free_tilt.copy()
		new_tilt_direction = (-1) * self.tiltdirection
		newtilt[self.axis] = self.coma_free_tilt[self.axis] + new_tilt_direction * self.tiltdelta
		self.tiltdirection = new_tilt_direction
		return newtilt

	def rotationCenterToScope(self):
		self.btcalclient.rotationCenterToScope()
		self.coma_free_tilt = self.instrument.tem.BeamTilt


	def rotationCenterFromScope(self):
		self.btcalclient.rotationCenterFromScope()

	
