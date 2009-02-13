import targetfilter
import leginondata
import gui.wx.RasterTargetFilter
import presets
import calibrationclient
import raster
import instrument
import math
import numpy

class RasterTargetFilter(targetfilter.TargetFilter):
	'''
	Example of a TargetFilter subclass
	'''
	panelclass = gui.wx.RasterTargetFilter.Panel
	settingsclass = leginondata.RasterTargetFilterSettingsData
	defaultsettings = dict(targetfilter.TargetFilter.defaultsettings)
	defaultsettings.update({
		'raster spacing': 50.0,
		'raster angle': 0.0,
		'raster movetype': None,
		'raster overlap': 0.0,
		'raster preset': None,
		'ellipse angle': 0.0,
		'ellipse a': 1.0,
		'ellipse b': 1.0,
	})

	def __init__(self, *args, **kwargs):
		targetfilter.TargetFilter.__init__(self, *args, **kwargs)

		self.instrument = instrument.Proxy(self.objectservice, self.session)
		self.presetsclient = presets.PresetsClient(self)
		self.calclients = {
			'image shift': calibrationclient.ImageShiftCalibrationClient(self),
			'stage position': calibrationclient.StageCalibrationClient(self),
			'modeled stage position':
												calibrationclient.ModeledStageCalibrationClient(self)
		}

		self.targetdata = None
		if self.__class__ == RasterTargetFilter:
			self.start()

	def autoSpacingAngle(self, targetdata=None):
		if targetdata is None:
			if self.targetdata is None:
				self.logger.error('Need Target Input to calculate')
				return 100,0
			targetdata = self.targetdata
		imageref = targetdata.special_getitem('image', dereference=False)
		imageid = imageref.dbid
		imagedata = self.researchDBID(leginondata.AcquisitionImageData, imageid, readimages=False)

		tem = imagedata['scope']['tem']
		cam = imagedata['camera']['ccdcamera']
		ht = imagedata['scope']['high tension']

		# transforming from target mag
		targetpresetname = self.settings['raster preset']
		targetpreset = self.presetsclient.getPresetByName(targetpresetname)
		mag1 = targetpreset['magnification']
		dim1 = targetpreset['dimension']['x']
		bin1 = targetpreset['binning']['x']
		fulldim = dim1 * bin1
		p1 = (0,fulldim)

		# transforming into mag of atlas
		mag2 = imagedata['scope']['magnification']
		bin2 = imagedata['camera']['binning']['x']

		movetype = self.settings['raster movetype']
		p2 = self.calclients[movetype].pixelToPixel(tem, cam, ht, mag1, mag2, p1)
		# bin
		p2 = p2[0]/float(bin2), p2[1]/float(bin2)
		# atlas scaling
		try:
			atlasscale = self.mosaic.scale
		except AttributeError:
			atlasscale = 1
		p2 = atlasscale*p2[0], atlasscale*p2[1]
		# overlap
		overlap = self.settings['raster overlap']
		overlapscale = 1.0 - overlap/100.0
		p2 = overlapscale*p2[0], overlapscale*p2[1]
		
		spacing = numpy.hypot(*p2)
		angle = numpy.arctan2(*p2)
		#coordinate on image is left-handed and angle in makeRaster is right-handed
		angle = math.degrees((-1)*angle)
		return spacing,angle

	def makeRaster(self):
		spacing = self.settings['raster spacing']
		angledeg = self.settings['raster angle']
		anglerad = math.radians(angledeg)
		rasterpoints = raster.createRaster3(spacing, anglerad, self.goodindices)
		return rasterpoints

	def filterTargets(self, targetlist):
		self.logger.info('filtering target list:  convolve targets with a raster')
		newlist = []
		angledeg = self.settings['raster angle']
		anglerad = math.radians(angledeg)
		# define goodindices for raster convolution
		limitangledeg = self.settings['ellipse angle']
		limitanglerad = math.radians(limitangledeg)
		# use ellipse diameter to define raster limit
		limita = self.settings['ellipse a'] / 2.0
		limitb = self.settings['ellipse b'] / 2.0
		self.goodindices = raster.createIndices2(limita,limitb,limitanglerad-anglerad)
		# create raster
		for target in targetlist:
			oldtarget = leginondata.AcquisitionImageTargetData(initializer=target)
			self.targetdata = oldtarget
			rasterpoints = self.makeRaster()
			for rp in rasterpoints:
				newtarget = leginondata.AcquisitionImageTargetData(initializer=target)
				newtarget['delta row'] += rp[0]
				newtarget['delta column'] += rp[1]
				newtarget['fromtarget'] = target
				newlist.append(newtarget)
		return newlist
