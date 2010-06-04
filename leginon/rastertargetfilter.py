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
		'raster offset': False,
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
		self.fromtarget = None
		self.donetargetids = []
		self.is_odd = True
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
		angle = math.degrees(angle)
		return spacing,angle

	def autoRasterEllipse(self,params):
		spacing = self.settings['raster spacing']
		a2 = params['a'] * 2 / spacing
		b2 = params['b'] * 2 / spacing
		angledeg = int(round(params['alpha'] * 180 / 3.14159))
		self.logger.info('a2 %.1f, b2 %.1f, angle %d' % (a2,b2,angledeg))
		self.settings['ellipse a'] = a2
		self.settings['ellipse b'] = b2
		self.settings['ellipse angle'] = angledeg
		self.setSettings(self.settings)
		self.onTest()
		return a2, b2, angledeg

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
		# create raster
		for target in targetlist:
			tiltoffset = self.researchPattern(target)
			self.goodindices = raster.createIndices2(limita,limitb,limitanglerad-anglerad,self.settings['raster offset'],self.is_odd,tiltoffset)
			self.savePattern(target)
			oldtarget = leginondata.AcquisitionImageTargetData(initializer=target)
			self.targetdata = oldtarget
			rasterpoints = self.makeRaster()
			for rp in rasterpoints:
				newtarget = leginondata.AcquisitionImageTargetData(initializer=target)
				newtarget['delta row'] += rp[0]
				newtarget['delta column'] += rp[1]
				newtarget['fromtarget'] = target
				newlist.append(newtarget)
			if not self.test or len(targetlist) % 2:
				self.is_odd = not self.is_odd
				self.setOffsetToolBar()
			self.donetargetids.append(target.dbid)
		return newlist

	def getAlpha(targetdata):
		imageref = target.special_getitem('image', dereference=False)
		if imageref:
			image = leginondata.AcquisitionImageData.direct_query(imageref.dbid, readimages=False)
			alpha = image['scope']['stage position']['alpha']
		else:
			alpha = 0
		return alpha

	def researchFromtarget(self,targetdata):
		fromtarget = None
		target = targetdata
		while not fromtarget:
			imageref = target.special_getitem('image', dereference=False)
			if imageref:
				image = self.researchDBID(leginondata.AcquisitionImageData, imageref.dbid, readimages=False)
				target = image['target']
			else:
				break
			if target:
				fromtarget = target['fromtarget']
			else:
				break
		if fromtarget:
			self.logger.info("Ancestor From Target: %d " % fromtarget.dbid)
		else:
			fromtarget = targetdata
		self.fromtarget = fromtarget
		return fromtarget

	def researchPattern(self,targetdata):
		# tilt pattern offset
		imageref = targetdata.special_getitem('image', dereference=False)
		if imageref:
			image = self.researchDBID(leginondata.AcquisitionImageData, imageref.dbid, readimages=False)
			tiltalpha = int(round(image['scope']['stage position']['a'] * 180.0 / 3.14159))
			has_pattern = False
			# accept pattern upto 2 deg error
			for t in (0,-1,1,-2,2):
				tpq = leginondata.TiltRasterPatternData(session=self.session,tilt=tiltalpha+t)
				tpresult = tpq.query(results=1)
				if tpresult:
					tiltoffset = (tpresult[0]['offset']['row'],tpresult[0]['offset']['col'])
					has_pattern = True
					break
			if not has_pattern:
				tiltoffset = (0,0)
				self.logger.warning('no offset pattern found for tilt at %d deg, default to (%.2f,%.2f)' % (tiltalpha,tiltoffset[0],tiltoffset[1]))
		else:
			self.logger.warning('no image associated with the target %d' %targetdata.dbid)
			tiltoffset = (0,0)
		# section pattern
		fromtarget = self.researchFromtarget(targetdata)
		q = leginondata.TargetRasterPatternData(target=fromtarget)
		result = q.query(results=1,readimages=False)
		if result:
			self.is_odd = bool(result[0]['pattern'])
			self.setOffsetToolBar()
		print "Pattern: section-",self.is_odd," tilt-",tiltoffset[0]==0.0
		return tiltoffset

	def savePattern(self,targetdata):
		pattern = int(self.is_odd)
		fromtarget = self.researchFromtarget(targetdata)
		q = leginondata.TargetRasterPatternData(target=fromtarget)
		result = q.query(results=1)
		if not result or pattern != result[0]['pattern']:
			patterndata = leginondata.TargetRasterPatternData()
			patterndata['target'] = fromtarget
			patterndata['pattern'] = pattern
			self.publish(patterndata, database=True, dbforce=True) 	
		
	def setToggleOffset(self,value):
		self.is_odd = value
		self.savePattern(self.fromtarget)

	def setOffsetToolBar(self):
		if self.is_odd:
			self.panel.setDefaultOffset()
		else:
			self.panel.setAlternateOffset()
