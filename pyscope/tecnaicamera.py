import ccdcamera
import numpy
import comtypes.client

class TecnaiCamera(ccdcamera.CCDCamera):
	name = 'TecnaiCamera'
	def __init__(self):
		ccdcamera.CCDCamera.__init__(self)

		import comtypes.client
		self.temscripting = comtypes.client.CreateObject('TEMScripting.Instrument.1')
		import comtypes.gen.TEMScripting
		self.temscripting_module = comtypes.gen.TEMScripting

		self.acquisition = self.temscripting.Acquisition
		## !!! select first camera, not always good idea
		self.ccd = self.acquisition.Cameras[0]
		self.acquisition.AddAcqDevice(self.ccd)
		self.constantsize_scale = {
			self.temscripting_module.AcqImageSize_Full: 1.0,
			self.temscripting_module.AcqImageSize_Half: 0.5,
			self.temscripting_module.AcqImageSize_Quarter: 0.25,
		}

		self.ccd.AcqParams.ImageCorrection = self.temscripting_module.AcqImageCorrection_Unprocessed
		self.ccd.AcqParams.ExposureMode = self.temscripting_module.AcqExposureMode_None
		try:
			self.ccd.Info.ShutterMode = self.temscripting_module.AcqShutterMode_PreSpecimen
		except:
			self.ccd.Info.ShutterMode = self.ccd.Info.ShutterModes[0]

		self.exposuretype = 'none'
		self.geometry = self.geometryFromAcqParams()

	def getCameraSize(self):
		ccdinfo = self.ccd.Info
		ccdheight = ccdinfo.Height
		ccdwidth = ccdinfo.Width
		return {'x': ccdwidth, 'y': ccdheight}

	def getBinnings(self):
		return self.ccd.Info.Binnings

	def geometryFromAcqParams(self):
		camerasize = self.getCameraSize()
		acqparams = self.ccd.AcqParams
		imagesize = acqparams.ImageSize
		imagescale = self.constantsize_scale[imagesize]
		binning = acqparams.Binning

		unbinned_width = int(imagescale*camerasize['x'])
		unbinned_height = int(imagescale*camerasize['y'])
		binned_width = unbinned_width / binning
		binned_height = unbinned_height / binning
		offset_x = (camerasize['x'] - unbinned_width) / 2
		offset_y = (camerasize['y'] - unbinned_height) / 2
		geometry = {
			'dimension': {'x': binned_width, 'y': binned_height},
			'binning': {'x': binning, 'y': binning},
			'offset': {'x': offset_x, 'y': offset_y},
		}
		return geometry

	def geometryToAcqParams(self, newgeometry):
		geometry = self.geometryFromAcqParams()
		geometry.update(newgeometry)
		camerasize = self.getCameraSize()
		dimension = geometry['dimension']
		binning = geometry['binning']
		offset = geometry['offset']

		## prepare binning
		if binning['x'] != binning['y']:
			raise ValueError('binning x and y must be same: %s' % (binning,))
		binning = binning['x']
		if binning not in self.getBinnings():
			raise ValueError('binning %s not supported' % (binning,))

		## prepare dimension
		unbinned = {}
		unbinned['x'] = dimension['x'] * binning
		unbinned['y'] = dimension['y'] * binning
		imagesize = None
		for size, scale in self.constantsize_scale.items():
			allowed_width = scale * camerasize['x']
			allowed_height = scale * camerasize['y']
			if unbinned['x'] == allowed_width and unbinned['y'] == allowed_height:
				imagesize = size
				imagescale = scale
		if imagesize is None:
			raise ValueError('Unbinned dimension %s not allowed' % (unbinned,))

		## prepare offset (arbitrary offset not allowed, just verify)
		for axis in ('x','y'):
			if offset[axis] != (camerasize[axis]-unbinned[axis])/2:
				raise ValueError('only centered offset allowed, not: %s' % (offset,))
		
		## now configure camera
		acqparams = self.ccd.AcqParams
		acqparams.ImageSize = imagesize
		acqparams.Binning = binning

	def setGeometry(self, geometry):
		self.geometry.update(geometry)

	def getGeometry(self):
		return dict(self.geometry)

	def getOffset(self):
		geometry = self.getGeometry()
		return geometry['offset']

	def setOffset(self, value):
		geometry = {'offset': value}
		self.setGeometry(geometry)

	def getDimension(self):
		geometry = self.getGeometry()
		return geometry['dimension']

	def setDimension(self, value):
		geometry = {'dimension': value}
		self.setGeometry(geometry)

	def getBinning(self):
		geometry = self.getGeometry()
		return geometry['binning']

	def setBinning(self, value):
		geometry = {'binning': value}
		self.setGeometry(geometry)

	def getExposureTime(self):
		return self.ccd.AcqParams.ExposureTime*1000.0

	def setExposureTime(self, value):
		self.ccd.AcqParams.ExposureTime = value/1000.0

	def getExposureTypes(self):
		return ['none']

	def getExposureType(self):
		return self.exposuretype

	def setExposureType(self, value):
		self.exposuretype = value

	def _getImage(self):
		self.geometryToAcqParams(self.geometry)
		print 'ACQUIRE'
		images = self.acquisition.AcquireImages()
		print 'IMAGE'
		image = images[0]
		print 'ASSAFEARRAY'
		image_array = image.AsSafeArray
		print 'ASARRAY'
		image_array = numpy.array(image_array, dtype=numpy.uint16)
		rows = self.geometry['dimension']['y']
		cols = self.geometry['dimension']['x']
		image_array.shape = (rows, cols)
		print 'RETURN'
		return image_array

	def getPixelSize(self):
		psize = self.ccd.Info.PixelSize
		return {'x': psize.X, 'y': psize.Y}

