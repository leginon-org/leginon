import leginondata

class CameraClient(object):
	def __init__(self):
		self.resetRepeatConfig()

	def resetRepeatConfig(self):
		self.repeat_scopedata = None
		self.repeat_cameradata = None

	def acquireCameraImageData(self, repeatconfig=False, scopeclass=leginondata.ScopeEMData, allow_retracted=False):
		'''Acquire a raw image from the currently configured CCD camera'''
		if not allow_retracted:
			try:
				inserted = self.instrument.ccdcamera.Inserted
			except:
				inserted = True
			if not inserted:
				self.logger.info('inserting camera')
				self.instrument.ccdcamera.Inserted = True

		imagedata = leginondata.CameraImageData()
		imagedata['session'] = self.session
		if repeatconfig and None not in (self.repeat_scopedata, self.repeat_cameradata):
			## acquire image, use previous scope/camera params, except system time
			imagedata['scope'] = self.repeat_scopedata
			imagedata['camera'] = self.repeat_cameradata
			for key in ('scope','camera'):
				if 'system time' in imagedata[key]:
					imagedata[key]['system time'] = self.instrument.tem.SystemTime
		else:
			## acquire image, get new scope/camera params
			scopedata = self.instrument.getData(scopeclass)
			cameradata = self.instrument.getData(leginondata.CameraEMData)
			imagedata['scope'] = scopedata
			imagedata['camera'] = cameradata
			self.repeat_scopedata = imagedata['scope']
			self.repeat_cameradata = imagedata['camera']
		imagedata['image'] = self.instrument.ccdcamera.Image
		return imagedata
