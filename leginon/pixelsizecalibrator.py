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

class PixelSizeCalibrator(calibrator.Calibrator):
	'''
	calibrate the pixel size for different mags
	'''
	def __init__(self, id, session, nodelocations, **kwargs):
		calibrator.Calibrator.__init__(self, id, session, nodelocations, **kwargs)
		self.calclient = calibrationclient.PixelSizeCalibrationClient(self)

		self.defineUserInterface()
		self.start()

	def defineUserInterface(self):
		node.Node.defineUserInterface(self)
#		calibrator.Calibrator.defineUserInterface(self)

		self.uilisting = uidata.Sequence('Pixel Size Calibrations', [])
		testmethod = uidata.Method('List All For This Instrument', self.uiGetCalibrations)

		# store container
		self.uimag = uidata.Integer('Magnification', 62000, 'rw')
		self.uipixsize = uidata.Float('Meters/Pixel', 1e-9, 'rw')
		self.comment = uidata.String('Comment', '', 'rw')
		storemethod = uidata.Method('Store', self.uiStore)
		storecont = uidata.Container('Store')
		storecont.addObjects((self.uimag,self.uipixsize,self.comment,storemethod))

		# extrapolate container
		self.extrapfrommags = uidata.Sequence('Known Mags', [], 'rw')
		self.extraptomags = uidata.Sequence('Mags to Extrapolate', [], 'rw')
		extrapmeth = uidata.Method('Extrapolate', self.extrapolate)
		extrapcont = uidata.Container('Extrapolate')
		extrapcont.addObjects((self.extrapfrommags,self.extraptomags,extrapmeth))


		mycontainer = uidata.LargeContainer('Pixel Size Calibrator')
		mycontainer.addObjects((self.uilisting, testmethod, storecont, extrapcont))
		self.uiserver.addObject(mycontainer)

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
			print 'Mag:  %s,  psize: %s' % (tmag, psize)
			comment = 'extrapolated from %s' % (fmags,)
			self._store(tmag, psize, comment)

	def uiGetCalibrations(self):
		calibrations = self.calclient.retrieveAllPixelSizes()
		calibrationstrings = []
		for calibration in calibrations:
			calibrationstrings.append('Magnification: %.1f Pixel size: %e Comment: %s, Session: %s Instrument: %s' %(calibration['magnification'], calibration['pixelsize'], calibration['comment'], calibration['session']['name'], calibration['session']['instrument']['name']))
		self.uilisting.set(calibrationstrings)

	def uiStore(self):
		self.store()
		return ''

	def store(self):
		mag = self.uimag.get()
		psize = self.uipixsize.get()
		comment = self.comment.get()
		self._store(mag, psize, comment)
		
	def _store(self, mag, psize, comment):
		caldata = data.PixelSizeCalibrationData()
		caldata['magnification'] = mag
		caldata['pixelsize'] = psize
		caldata['comment'] = comment
		self.publish(caldata, database=True)
