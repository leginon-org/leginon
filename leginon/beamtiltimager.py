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
import gui.wx.BeamTiltImager
import player
import tableau
import subprocess
import re
import os

class BeamTiltImager(acquisition.Acquisition):
	panelclass = gui.wx.BeamTiltImager.Panel
	settingsclass = leginondata.BeamTiltImagerSettingsData
	defaultsettings = acquisition.Acquisition.defaultsettings
	defaultsettings.update({
		'process target type': 'focus',
		'beam tilt': 0.01,
		'beam tilt count': 1,
		'sites': 0,
		'startangle': 0,
		'correlation type': 'phase',
		'tableau type': 'split image-power',
		'tableau binning': 2,
		'tableau split': 8,
	})

	eventinputs = acquisition.Acquisition.eventinputs
	eventoutputs = acquisition.Acquisition.eventoutputs

	def __init__(self, id, session, managerlocation, **kwargs):

		self.correlator = correlator.Correlator()
		self.correlation_types = ['cross', 'phase']
		self.tableau_types = ['beam tilt series-power', 'beam tilt series-image','split image-power']
		self.maskradius = 1.0
		self.increment = 5e-7
		self.tabscale = None
		acquisition.Acquisition.__init__(self, id, session, managerlocation, **kwargs)
		self.btcalclient = calibrationclient.BeamTiltCalibrationClient(self)
		self.imageshiftcalclient = calibrationclient.ImageShiftCalibrationClient(self)
		self.euclient = calibrationclient.EucentricFocusClient(self)
		self.ace2exe = self.getACE2Path()

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

	def splitTableau(self, image):
		split = self.settings['tableau split']
		self.tabimage = tableau.splitTableau(image, split)
		self.tabscale = None
		self.displayTableau()
		self.saveTableau()

	def insertTableau(self, imagedata, angle, rad):
		image = imagedata['image']
		binning = self.settings['tableau binning']
		if self.settings['tableau type'] != 'beam tilt series-image':
			pow = imagefun.power(image)
			binned = imagefun.bin(pow, binning)
			s = None
			self.ht = imagedata['scope']['high tension']
			if not self.rpixelsize:
				self.rpixelsize = self.btcalclient.getReciprocalPixelSize(imagedata)
			ctfdata = fftfun.fitFirstCTFNode(pow,self.rpixelsize['x'], self.defocus, self.ht)
			self.ctfdata.append(ctfdata)
			if ctfdata:
				s = '%d' % int(ctfdata[0]*1e9)
			#elif self.ace2exe:
			elif False:
				ctfdata = self.estimateCTF(imagedata)
				z0 = (ctfdata['defocus1'] + ctfdata['defocus2']) / 2
				s = '%d' % (int(z0*1e9),)
			if s:
				t = numpil.textArray(s)
				min = arraystats.min(binned)
				max = arraystats.max(binned)
				t = min + t * (max-min)
				imagefun.pasteInto(t, binned, (20,20))
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

	def acquire(self, presetdata, emtarget=None, attempt=None, target=None):
		'''
		this replaces Acquisition.acquire()
		Instead of acquiring an image, we do autofocus
		'''
		## sometimes have to apply or un-apply deltaz if image shifted on
		## tilted specimen
		self.rpixelsize = None
		self.defocus = presetdata['defocus']
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
			status = acquisition.Acquisition.acquire(self, presetdata, emtarget, channel= channel)
			imagedata = self.imagedata
			self.instrument.tem.BeamTilt = oldbt
			angle = anglelist[i]
			rad = radlist[i]

			if self.settings['tableau type'] == 'split image-power':
				self.splitTableau(imagedata['image'])
			elif 'beam tilt series' in self.settings['tableau type']:
				print 'beam tilt', bt['x'] - tiltlist[0]['x'], bt['y'] - tiltlist[0]['y']
				self.insertTableau(imagedata, angle, rad)
			try:
				shiftinfo = self.correlateOriginal(i,imagedata)
			except Exception, e:
				self.logger.error('Failed correlation: %s' % e)
				return 'error'
			pixelshift = shiftinfo['pixel shift']
			displace.append((pixelshift['row'],pixelshift['col']))
		if 'beam tilt series' in self.settings['tableau type']:
			self.renderTableau()
		self.calculateAxialComa(self.ctfdata)
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

	def initSameCorrection(self):
		self.samecorrection = True
		self.correctargs = None

	def endSameCorrection(self):
		self.samecorrection = False

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
