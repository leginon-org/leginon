#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import calibrationclient
import leginondata
import event
import instrument
import imagewatcher
import mosaic
import threading
import node
import targethandler
from pyami import convolver, imagefun, mrc
import numpy
ma = numpy.ma
import pyami.quietscipy
import scipy.ndimage as nd
import mosaictargetfinder
import gui.wx.MosaicSectionFinder
import os
import libCVwrapper
import math
import polygon
import raster
import presets
import time
try:
	set = set
except NameError:
	import sets
	set = sets.Set

class MosaicSectionFinder(mosaictargetfinder.MosaicClickTargetFinder):
	panelclass = gui.wx.MosaicSectionFinder.Panel
	settingsclass = leginondata.MosaicSectionFinderSettingsData
	defaultsettings = dict(mosaictargetfinder.MosaicClickTargetFinder.defaultsettings)
	defaultsettings.update({
		'autofinder': False,
		'min region area': 0.01,
		'max region area': 0.8,
		'axis ratio': 2.0,
		've limit': 50,
		'find section options':'Limit by Sections',
#		'black on white': False,
#		'limit region in sections': False,
		'section area': 99.0,
		'section axis ratio': 1.0,
		'max sections': 5,
		'adjust section area': 0.0,
		'section display': False,
		'raster preset': None,
		'raster spacing': 50,
		'raster angle': 0,
		'raster movetype': 'stage position',
	})

	eventoutputs = mosaictargetfinder.MosaicClickTargetFinder.eventoutputs + [event.MosaicDoneEvent]
	def __init__(self, id, session, managerlocation, **kwargs):
		self.mosaicselectionmapping = {}
		mosaictargetfinder.MosaicClickTargetFinder.__init__(self, id, session, managerlocation, **kwargs)

		self.onesectionarea = None
		self.oldonesectionarea1 = None		
		self.regionarrays = []
		self.regionellipses = []
		self.regionimage = None

		if self.__class__ == MosaicSectionFinder:
			self.start()


	def handleTargetListDone(self, targetlistdoneevent):
		if self.settings['create on tile change'] == 'final':
			self.logger.debug('create final')
			self.createMosaicImage()
			self.logger.debug('done create final')
		if self.settings['autofinder']:
			self.logger.debug('auto target finder')
			self.autoTargetFinder()
			self.logger.debug('done auto target finder')

#	def createMosaicImage(self):
#		self.logger.info('targets displayed, setting region []...')
#		self.setTargets([], 'region')
#		self.beep()

	def reduceRegions(self,regions,axisratiolimits,velimit,sectionimage = None):
			regionarrays = []
			regionellipses = []
			displaypoints = []
			self.regionpolygon = []
			for i,region in enumerate(regions):
				regionpolygon = region['regionEllipse']
				regionaxismajor = regionpolygon[2]
				regionaxisminor = regionpolygon[3]
				axisratio = regionaxismajor/regionaxisminor
				if axisratio > axisratiolimits[0] and axisratio < axisratiolimits[1]:
					overlap = False
					regionrow = int(regionpolygon[0])
					regioncol = int(regionpolygon[1])
					for j,regionellipse in enumerate(regionellipses):
						halfminor = 0.5*regionellipse[3]
						if regionrow > regionellipse[0]-halfminor and regionrow < regionellipse[0]+halfminor and regioncol > regionellipse[1]-halfminor and regioncol < regionellipse[1]+halfminor:
							overlap = True
							break
					insidesections = False
					if sectionimage != None:
						if sectionimage[(regionrow,regioncol)] == 1:
							insidesections = True
					else:
						insidesections = True
					if not overlap and insidesections:
						regionellipse = region['regionEllipse']
						regionarray = region['regionBorder']
#						self.logger.info('Region %d has %d points' % (i, regionarray.shape[1]))
						## reduce to 20 points
						regionarray = libCVwrapper.PolygonVE(regionarray, velimit)
						rregionarray = regionarray.transpose()
						regionarrays.append(rregionarray)
						regionellipses.append(regionellipse)
					
						regiondisplaypoints = self.transpose_points(rregionarray)
						displaypoints.extend(regiondisplaypoints)				
						regionphi = regionpolygon[4]
						#print regionrow,regioncol,regionaxismajor,regionaxisminor,regionphi
			
			return regionarrays,regionellipses,displaypoints
	
	def regionsByLabel(self,image,mint,maxt,minsize,maxsize):
		imshape = image.shape

		sigma = 3.0
		smooth=nd.gaussian_filter(image,sigma)
		masked_region = numpy.ma.masked_inside(smooth,mint,maxt)
		regionimage = ma.getmask(masked_region)
		base=nd.generate_binary_structure(2,2)
		iteration = 3
		regionimage=nd.binary_erosion(regionimage,structure=base,iterations=iteration)
		regionlabel,nlabels = nd.label(regionimage)

		ones = numpy.ones(imshape)
		if nlabels > 0:
			regionareas = nd.sum(ones,regionlabel,range(1,nlabels+1))
		else:
			regionareas = []
		if nlabels == 1:
			regionareas = [regionareas]

		ngoodregion = 0
		newregionimage = numpy.zeros(imshape)
		for i, area in enumerate(regionareas):
			if area < minsize*0.2 or area > maxsize:
				continue
			else:
				ngoodregion += 1
				newregionimage += numpy.where(regionlabel==(i+1),1,0)

#		finalregionimage=nd.binary_fill_holes(newregionimage,structure=base)
		finalregionimage = newregionimage
		finalregionlabel,ngoodregion = nd.label(finalregionimage)

		if ngoodregion > 0:
			regioncenters = nd.center_of_mass(ones,finalregionlabel,range(1,ngoodregion+1))
		else:
			regioncenters = []
		if ngoodregion == 1:
			regioncenters = [regioncenters]
				
		return finalregionimage,ngoodregion,regioncenters
		
	def regionsFromCenters(self,centers,maxsize):	
		halfedge = math.sqrt(maxsize)/(2*(1+math.sqrt(2.0)))
		halfbox = math.sqrt(maxsize)/2
		regionimage = numpy.zeros(self.mosaicimage.shape)
		regionarrays=[]
		for center in centers:
			polygon = [
					[center[0]-halfedge,center[1]-halfbox],
					[center[0]+halfedge,center[1]-halfbox],
					[center[0]+halfbox,center[1]-halfedge],
					[center[0]+halfbox,center[1]+halfedge],
					[center[0]+halfedge,center[1]+halfbox],
					[center[0]-halfedge,center[1]+halfbox],
					[center[0]-halfbox,center[1]+halfedge],
					[center[0]-halfbox,center[1]-halfedge]
				]
			regionarray = numpy.array(polygon,numpy.float32)
			regionarrays.append(regionarray)
		return regionarrays
		
	def findRegions(self):
		imshape = self.mosaicimage.shape
		self.regionarrays = []
		self.regionellipses = []
		self.regionimage = numpy.zeros(imshape)
		maxsize = self.settings['max region area']
		minsize = self.settings['min region area']
		onesectionarea1 = self.settings['section area']
		sectionaxisratio = float(self.settings['section axis ratio'])
		maxsection = self.settings['max sections']
		displaysection = self.settings['section display']
		findsectionoption = self.settings['find section options']
		modifyarea = self.settings['adjust section area']

		newareasetting = False
		if self.oldonesectionarea1 == None or self.oldonesectionarea1 != self.settings['section area'] or modifyarea < 0.01:
			newareasetting = True
		self.oldonesectionarea1 = onesectionarea1

		if findsectionoption == 'Sections Only':
			sectiononly = True
			limitbysection = False
		else:
			if findsectionoption == 'Limit by Sections':
				limitbysection = True
				sectiononly = False
			else:
				limitbysection = False
				sectiononly = False		

		minsize /= 100.0
		maxsize /= 100.0
		onesectionarea = onesectionarea1 / 100.0
		modifyarea = modifyarea / 100.0

		tileshape = self.mosaic.tiles[0].image.shape
		tilearea = tileshape[0] * tileshape[1]
		mosaicarea = imshape[0] * imshape[1]
		areascale = self.mosaic.scale * self.mosaic.scale
		scale = areascale * tilearea / mosaicarea
		minsize = scale * minsize
		maxsize = scale * maxsize
		onesectionarea = scale * onesectionarea

		if findsectionoption =='Regions from Centers':
			manualcenters = self.panel.getTargetPositions('region')
			if manualcenters:
				manualcenters = self.transpose_points(manualcenters)
			maxsizepixel = maxsize * mosaicarea
			self.regionarrays = self.regionsFromCenters(manualcenters,maxsizepixel)
			self.regionellipses = manualcenters
			return

		velimit = self.settings['ve limit']
		mint = self.settings['min threshold']
		maxt = self.settings['max threshold']
		axisratiolimit = self.settings['axis ratio']
		
		# make zero border
		pad = 2
		self.mosaicimage[:pad] = 0
		self.mosaicimage[-pad:] = 0
		self.mosaicimage[:,:pad] = 0
		self.mosaicimage[:,-pad:] = 0
		t00=time.time()
		print "-------------"
		
		# get background stats
		background = numpy.where(self.mosaicimage>maxt,1,0)
		backgroundlabel,nlabels = nd.label(background)
		bkgrndmean = nd.mean(self.mosaicimage,labels=backgroundlabel)
		bkgrndstddev = nd.standard_deviation(self.mosaicimage,labels=backgroundlabel)
		t01=time.time()
		print "---%5.1f-----background mean %f, stddev %f" % ((t01-t00),bkgrndmean, bkgrndstddev)
				
		#refresh to setting if not auto adjust
		if self.onesectionarea == None or newareasetting:
			self.onesectionarea = onesectionarea

		tolerance = 0.5
		onesectionmin = self.onesectionarea*(1-tolerance)
		multisections=self.onesectionarea*maxsection*(1+tolerance)

		sectiondisplaypoints=[]
		sectionarrays = []
		sectionellipses = []
		
#		Find Section with simple thresholding and Label in scipy.ndimage for now until
#		better segamentation is available for sections that connects to the edge

#		if limitbysection or sectiononly:
		uselibCV = False
		if uselibCV and (limitbysection or sectiononly):
			
			#find sections
			count = 0	
			maxt1 = bkgrndmean+2*bkgrndstddev
			mosaicmax = self.mosaicimage.max()
			stepmaxt = 0.49*(mosaicmax - maxt1)
			stepscale = 0.8
			
			axisratiomax = sectionaxisratio * maxsection
			axisratiomin = sectionaxisratio / maxsection
			axisratiolimits = [axisratiomin,axisratiomax]

			while len(sectionarrays) == 0 and maxt1 < mosaicmax:
				count += 1
				regions = None
				minsize1 = onesectionmin
				maxsize1 = multisections
				m = numpy.clip(self.mosaicimage, mint, maxt1)
				regions,image = libCVwrapper.FindRegions(m, minsize1, maxsize1, WoB=False)
				sectionarrays,sectionellipses,sectiondisplaypoints = self.reduceRegions(regions,axisratiolimits,velimit,None)
				minsize1 = stepscale*onesectionmin
				maxt1 += stepmaxt

			self.logger.info('found %i sections after %i iterations' % (len(sectionarrays),count))
			
		if len(sectiondisplaypoints) == 0:
			if uselibCV and (not limitbysection):
				# rough section by threshold only
				masked_section = numpy.ma.masked_inside(self.mosaicimage,mint,maxt)
				sectionimage = masked_section.mask()
				nlabel = 1
			else:
				# good section as image only - smooth,threshold,size limit etc.
				minsizepixels = onesectionmin * mosaicarea
				maxsizepixels = multisections * mosaicarea
				sectionimage, nsection,sectionellipses = self.regionsByLabel(self.mosaicimage,mint,maxt,minsizepixels,maxsizepixels)
				self.logger.info('use sectionimage for rastering and found %d good sections' %nsection)
		else:
			sectionimage = polygon.plotPolygons(imshape,sectionarrays)
			nonmissingregion = numpy.where(self.mosaicimage==0,0,1)
			sectionimage = sectionimage*nonmissingregion
		
		# get section stats
		sectionlabel,nlabels = nd.label(sectionimage)

		# skip everything if no section found
		if nlabels == 0:
			return
		sectionarea = sectionimage.sum()
		sectionmean = nd.mean(self.mosaicimage,labels=sectionlabel)
#		sectionstddev = nd.standard_deviation(self.mosaicimage,labels=sectionlabel)
		sectionareanum = sectionarea / (self.onesectionarea * mosaicarea)
		sectionareaint = int(round(sectionareanum))
		
		if abs(sectionareanum-sectionareaint) < modifyarea:
			self.onesectionarea = float(sectionarea) /(sectionareaint * mosaicarea)
			areapercenttile = 100 * self.onesectionarea /scale
			self.logger.info('modify per-section area to %f for next round' %areapercenttile)
		t02=time.time()
		print "----%5.1f----section num %d mean %f" % ((t02-t01),sectionareaint, sectionmean)
		
		if not (limitbysection or sectiononly):
			sectionimage = None
		else:
			self.regionimage = sectionimage
		
		if sectiononly:
			regionarrays = sectionarrays
			regionellipses = sectionellipses
			displaypoints = sectiondisplaypoints
		else:
			
			# find tissue
		
			if modifyarea > 0.0001:
				nregionmin = max(len(sectionarrays),sectionareaint)
			else:
				nregionmin = max(len(sectionarrays),1)

				
			tissuecontrast = (sectionmean-mint)/abs(mint-sectionmean)
			
			if tissuecontrast >0:
				black_on_white = True
				white_on_black = False
			else:
				black_on_white = False
				white_on_black = True
		
			maxt2 = sectionmean+bkgrndstddev*tissuecontrast

			count = 0
			regionarrays = []
			displaypoints = []
			stepscale = 0.2
			while len(regionarrays) < nregionmin and maxt2*tissuecontrast > sectionmean*tissuecontrast:
				count += 1
				avgt = (mint+maxt2)/2
				mint2a = avgt-(maxt2-mint)*tissuecontrast/2
				maxt2a = avgt+(maxt2-mint)*tissuecontrast/2
				m = numpy.clip(self.mosaicimage, mint2a, maxt2a)
				regions,image = libCVwrapper.FindRegions(m, minsize, maxsize, WoB=white_on_black, BoW=black_on_white)
				regionarrays,regionellipses,displaypoints = self.reduceRegions(regions,[1.0,self.settings['axis ratio']],velimit,sectionimage)
				minsize = stepscale*minsize
				maxt2 = maxt2-stepscale*bkgrndstddev*tissuecontrast
				if minsize*mosaicarea < 4:
					break
		
			self.logger.info('found %i regions after %i iterations' % (len(regionarrays),count))
			t03=time.time()
			print "----%5.1f----tissue" % ((t03-t02),)
			if displaysection:
				displaypoints.extend(sectiondisplaypoints)

		self.regionarrays = regionarrays
		self.regionellipses = regionellipses

		self.setTargets(displaypoints, 'region', block=True)
			
	def clearRegions(self):
		imshape = self.mosaicimage.shape
		self.regionarrays = []
		self.regionimage = None
		self.clearTargets('region')

	def autoSpacingAngle(self):
		try:
			imagedata = self.imagemap[self.imagemap.keys()[0]]
		except IndexError:
			self.logger.warning('need displayed atlas to calculate the spacing and angle')
			return self.settings['raster spacing'],self.settings['raster angle']

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

		try:
			p2 = self.calclients[self.settings['raster movetype']].pixelToPixel(tem, cam, ht, mag1, mag2, p1)
		except Exception, e:
			self.logger.warning('Failed to calculate raster: %s' % e)

		# bin
		p2 = p2[0]/float(bin2), p2[1]/float(bin2)
		# atlas scaling
		atlasscale = self.mosaic.scale
		p2 = atlasscale*p2[0], atlasscale*p2[1]
		# overlap
		overlap = self.settings['raster overlap']
		overlapscale = 1.0 - overlap/100.0
		p2 = overlapscale*p2[0], overlapscale*p2[1]
		
		spacing = numpy.hypot(*p2)
		angle = numpy.arctan2(*p2)
		angle = math.degrees(angle)
		return spacing,angle

	def makeRaster(self):
		shape = self.mosaicimage.shape
		spacing = self.settings['raster spacing']
		angledeg = self.settings['raster angle']
		anglerad = math.radians(angledeg)
		rasterpoints = raster.createRaster(shape, spacing, anglerad)

		if self.settings['autofinder']:
			self.regionarrays=[]
		else:
			#if self.regionarrays is not defined, make it an empty array
			try:
				len(self.regionarrays)
			except TypeError:
				self.regionarrays=[]

		# if self.regionarrays is empty, check for manually picked region
		if (len(self.regionarrays) < 1 and self.settings['find section options']!='Regions from Centers') or not self.settings['autofinder']:

			manualregion = self.panel.getTargetPositions('region')
			if manualregion:
				manualregion = self.transpose_points(manualregion)
				manualregionarray = numpy.array(manualregion)
				self.regionarrays = [manualregionarray]

		if len(self.regionarrays) > 0:
			rasterpoints = self.insideRegionArrays(rasterpoints,spacing)
		else:
			if self.regionimage is not None:
				rasterpoints = self.insideRegionImage(rasterpoints)
				
		fullrasterdisplay = self.transpose_points(rasterpoints)
		self.setTargets(fullrasterdisplay, 'acquisition', block=True)

	def insideRegionImage(self, rasterpoints):
		results = []
		for point in rasterpoints:
			row = int(round(point[0]))
			col = int(round(point[1]))
			if row < 0 or row >= self.regionimage.shape[0]:
				continue
			if col < 0 or col >= self.regionimage.shape[1]:
				continue
			if self.regionimage[row,col]:
				results.append(point)
		return results

	def insideRegionArrays(self, rasterpoints,spacing):
		fullrasterset = set()

		## this block will reduce the number of raster points
		if self.regionarrays:
			region = self.regionarrays[0]
			gmin0 = gmax0 = region[0][0]
			gmin1 = gmax1 = region[0][1]
			for region in self.regionarrays:
				min0 = min(region[:,0])
				min1 = min(region[:,1])
				max0 = max(region[:,0])
				max1 = max(region[:,1])
				if min0 < gmin0:
					gmin0 = min0
				if min1 < gmin1:
					gmin1 = min1
				if max0 > gmax0:
					gmax0 = max0
				if max1 > gmax1:
					gmax1 = max1
			gmin0 -= (2*spacing)
			gmin1 -= (2*spacing)
			gmax0 += (2*spacing)
			gmax1 += (2*spacing)
			newrasterpoints = []
			for rasterpoint in rasterpoints:
				if gmin0 < rasterpoint[0] < gmax0:
					if gmin1 < rasterpoint[1] < gmax1:
						newrasterpoints.append(rasterpoint)
			rasterpoints = newrasterpoints

		#for region in self.regionarrays:
		for region in self.regionarrays:
			### keep raster points that are either in the polygon
			### or near the polygon
			fillraster = polygon.pointsInPolygon(rasterpoints, region)
			fullrasterset = fullrasterset.union(fillraster)

			leftovers = list(set(rasterpoints).difference(fillraster))
			if len(region) > 1:
				distances = polygon.distancePointsToPolygon(leftovers, region)
			else:
			# handle the case for one point in the region
				regionlist = region.tolist()
				regionlist =[(regionlist[0][0],regionlist[0][1]),(regionlist[0][0]+1,regionlist[0][1]+1)]
				newregion = numpy.array(regionlist)
				distances = polygon.distancePointsToPolygon(leftovers, newregion)
				
			isnear = distances < spacing
			#nearraster = numpy.compress(distances<spacing, rasterpoints)
			nearraster = []
			for i, point in enumerate(leftovers):
				if isnear[i]:
					nearraster.append(point)
			fullrasterset = fullrasterset.union(nearraster)
		# set is unordered, so use original rasterpoints for order
		fullraster = []
		for point in rasterpoints:
			if point in fullrasterset:
				fullraster.append(point)

		return fullraster


	def makeFocusTarget(self):
		if not self.regionellipses:
			return
		middle = len(self.regionellipses) / 2
		middleregion = self.regionellipses[middle]
		center = middleregion[0],middleregion[1]
		
		focusdisplay = self.transpose_points([center])
		self.setTargets(focusdisplay, 'focus', block=True)

	def autoTargetFinder(self):
		self.logger.info('Finding regions...')
		self.findRegions()
		self.logger.info('Filling regions with raster...')
		self.makeRaster()
		self.logger.info('Making focus target...')
		self.makeFocusTarget()
		## user part
		if self.settings['user check']:
			self.setStatus('user input')
			self.logger.info('Waiting for user to check targets...')
			self.panel.submitTargets()
			self.userpause.clear()
			self.userpause.wait()
			self.panel.targetsSubmitted()
		self.setStatus('processing')

		## get targets from image
		targets = {}
		targets['acquisition'] = self.panel.getTargetPositions('acquisition')
		targets['focus'] = self.panel.getTargetPositions('focus')
		
		## new target list
		#if targets['acquisition'] or targets['focus']:
		targetlist = self.newTargetList()
		self.publish(targetlist, database=True, dbforce=True)
		##### commented out so it will still publish,
		#####   even if empty target list
		#else:
		#	self.setStatus('idle')
		#	return

		for type in ('focus', 'acquisition'):
			n = len(targets[type])
			self.logger.info('Publishing %d %s targets...' % (n, type))
			for t in targets[type]:
				## convert to TargetData
				c,r = t
				imagedata, drow, dcol = self._mosaicToTarget(r, c)
				targetdata = self.newTargetForTile(imagedata, drow, dcol, type=type, list=targetlist)
				self.publish(targetdata, database=True, dbforce=True)

		self.publish(targetlist, pubevent=True)
		self.setStatus('idle')
