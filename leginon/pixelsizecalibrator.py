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
import math
import EM
import camerafuncs

class PixelSizeCalibrator(calibrator.Calibrator):
	'''
	calibrate the pixel size for different mags
	'''
	def __init__(self, id, session, managerlocation, **kwargs):
		calibrator.Calibrator.__init__(self, id, session, managerlocation, **kwargs)
		self.calclient = calibrationclient.PixelSizeCalibrationClient(self)

		self.defineUserInterface()
		self.start()

	def defineUserInterface(self):
		node.Node.defineUserInterface(self)
#		calibrator.Calibrator.defineUserInterface(self)

		listcont = uidata.Container('Pixel Size List')
		self.uilisting = uidata.Sequence('Pixel Size Calibrations', [])
		listmethod = uidata.Method('List All For This Instrument', self.uiGetCalibrations)
		listcont.addObject(listmethod, position={'position':(0,0)})
		listcont.addObject(self.uilisting, position={'position':(0,1)})

		# store container
		self.uimag = uidata.Integer('Magnification', 62000, 'rw')
		self.uipixsize = uidata.Float('Meters/Pixel', 1e-9, 'rw')
		self.comment = uidata.String('Comment', '', 'rw')
		storemethod = uidata.Method('Store', self.uiStore)
		storecont = uidata.Container('Direct Entry')
		storecont.addObject(self.uimag, position={'position':(0,0)})
		storecont.addObject(self.uipixsize, position={'position':(0,1)})
		storecont.addObject(self.comment, position={'position':(0,2)})
		storecont.addObject(storemethod, position={'position':(0,3)})

		# extrapolate container
		self.extrapfrommags = uidata.Sequence('Known Mags', [], 'rw')
		self.extraptomags = uidata.Sequence('Mags to Extrapolate', [], 'rw')
		extrapmeth = uidata.Method('Extrapolate', self.extrapolate)
		extrapcont = uidata.Container('Extrapolate')
		extrapcont.addObject(self.extrapfrommags,position={'position':(0,0)})
		extrapcont.addObject(self.extraptomags, position={'position':(0,1)})
		extrapcont.addObject(extrapmeth, position={'position':(1,0), 'span':(1,2)})

		# Measure from an image
		measurecont = uidata.Container('Measure From Image')
		cameraconfigure = self.cam.uiSetupContainer()
		acquiremeth = uidata.Method('Acquire', self.acquireImage)
		self.lastclick = None
		self.pixeldistance = uidata.Float('Pixel Distance', None, 'r')
		self.realdistance = uidata.Float('Real Distance', None, 'rw', persist=True)
		self.binning = uidata.Integer('Binning', None, 'r')
		self.magnification = uidata.Integer('Magnification', None, 'r')
		self.calculatedsize = uidata.Float('Pixel Size', None, 'r')
		self.measuredcomment = uidata.String('Comment', '', 'rw')
		storemeasured = uidata.Method('Store', self.uiStoreMeasured)

		measurecont.addObject(cameraconfigure, position={'position':(0,0), 'span':(1,4)})
		measurecont.addObject(acquiremeth, position={'position':(1,0), 'span':(1,4)})
		measurecont.addObject(self.realdistance, position={'position':(3,0)})
		measurecont.addObject(self.pixeldistance, position={'position':(3,1)})
		measurecont.addObject(self.binning, position={'position':(3,2)})
		measurecont.addObject(self.magnification, position={'position':(4,0)})
		measurecont.addObject(self.calculatedsize, position={'position':(4,1)})
		measurecont.addObject(self.measuredcomment, position={'position':(4,2)})
		measurecont.addObject(storemeasured, position={'position':(4,3)})

		mycontainer = uidata.LargeContainer('Pixel Size Calibrator')
		mycontainer.addObjects((listcont, storecont, extrapcont, measurecont))
		self.uicontainer.addObject(mycontainer)

	def acquireImage(self):
		self.cam.setCameraDict(self.settings['camera settings'])
		try:
			imagedata = self.cam.acquireCameraImageData()
		except camerafuncs.NoCorrectorError:
			self.messagelog.error('No Corrector node, acquisition failed')
			return

		if imagedata is None:
			self.messagelog.error('acquisition failed')
			return

		scope = imagedata['scope']
		camera = imagedata['camera']
		self.mag = scope['magnification']
		self.bin = camera['binning']['x']
		newimage = imagedata['image']
		self.shape = newimage.shape
		self.updateImage('Image', newimage)
		self.magnification.set(self.mag)
		self.binning.set(self.bin)

	def handleImageClick(self, xy):
		print 'XY', xy
		if self.lastclick is not None:
			## calculate distance
			dist = math.hypot(xy[0]-self.lastclick[0], xy[1]-self.lastclick[1])
			self.pixeldistance.set(dist)
			realdist = self.realdistance.get()
			if realdist is None:
				raise RuntimeError('no real distance')
			self.measured = self.realdistance.get() / (self.bin * dist)
			self.calculatedsize.set(self.measured)
		self.lastclick = xy

	def uiStoreMeasured(self):
		self._store(self.mag, self.measured, self.measuredcomment.get())

	def extrapolate(self):
		fmags = self.extrapfrommags.get()
		tmags = self.extraptomags.get()
		
		## get pixel size of known mags from DB to calculate scale
		scales = []
		for fmag in fmags:
			psize = self.calclient.retrievePixelSize(fmag)
			scales.append(psize*fmag)
		scale = sum(scales) / len(scales)

		## calculate new pixel sizes
		for tmag in tmags:
			psize = scale / tmag
			self.logger.info('Magnification: %sx, pixel size: %s' % (tmag, psize))
			comment = 'extrapolated from %s' % (fmags,)
			self._store(tmag, psize, comment)

	def uiGetCalibrations(self):
		calibrations = self.calclient.retrieveAllPixelSizes()
		calibrationstrings = []
		for calibration in calibrations:
			calibrationstrings.append('Magnification: %.1f Pixel size: %e Comment: %s, Session: %s Instrument: %s' %(calibration['magnification'], calibration['pixelsize'], calibration['comment'], calibration['session']['name'], calibration['session']['instrument']['name']))
		self.uilisting.set(calibrationstrings)

	def uiStore(self):
		mag = self.uimag.get()
		psize = self.uipixsize.get()
		comment = self.comment.get()
		self._store(mag, psize, comment)

	def _store(self, mag, psize, comment):
		caldata = data.PixelSizeCalibrationData()
		caldata['magnification'] = mag
		caldata['pixelsize'] = psize
		caldata['comment'] = comment
		caldata['session'] = self.session
		self.publish(caldata, database=True)
