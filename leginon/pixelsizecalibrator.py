import calibrator
import event, data
import uidata

class PixelSizeCalibrator(calibrator.Calibrator):
	'''
	calibrate the pixel size for different mags
	'''
	def __init__(self, id, session, nodelocations, **kwargs):
		calibrator.Calibrator.__init__(self, id, session, nodelocations, **kwargs)

		self.defineUserInterface()
		self.start()

	def defineUserInterface(self):
		calibrator.Calibrator.defineUserInterface(self)

		self.uimag = uidata.Integer('Magnification', 62000, 'rw')
		self.uipixsize = uidata.Float('Meters/Pixel', 1e-9, 'rw')
		self.comment = uidata.String('Comment', '', 'rw')
		storemethod = uidata.Method('Store', self.uiStore)
		mycontainer = uidata.MediumContainer('Pixel Size Calibrator')
		mycontainer.addObjects((self.uimag, self.uipixsize, self.comment, storemethod))
		self.uiserver.addObject(mycontainer)

	def uiStore(self):
		self.store()
		return ''

	def store(self):
		caldata = data.PixelSizeCalibrationData()
		caldata['magnification'] = self.uimag.get()
		caldata['pixelsize'] = self.uipixsize.get()
		caldata['comment'] = self.comment.get()
		self.publish(caldata, database=True)
