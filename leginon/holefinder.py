#!/usr/bin/env python

import targetfinder
import holefinderback
import uidata
import Mrc
import camerafuncs

class HoleFinder(targetfinder.TargetFinder):
	def __init__(self, id, session, nodelocations, **kwargs):
		targetfinder.TargetFinder.__init__(self, id, session, nodelocations, **kwargs)
		self.hf = holefinderback.HoleFinder()
		self.cam = camerafuncs.CameraFuncs(self)
		self.icecalc = holefinderback.IceCalculator()

		self.currentimage = None

		#if self.__class__ == ClickTargetFinder:
		#	self.defineUserInterface()
		#	self.start()
		self.defineUserInterface()
		self.start()

	def defineUserInterface(self):
		targetfinder.TargetFinder.defineUserInterface(self)
		self.uidataqueueflag.set(False)

		self.testfile = uidata.String('Filename', '', 'rw', persist=True)
		readmeth = uidata.Method('Read Image', self.readImage)
		cameraconfigure = self.cam.configUIData()
		acqmeth = uidata.Method('Acquire Image', self.acqImage)
		testmeth = uidata.Method('Test All', self.everything)
		self.originalimage = uidata.Image('Original', None, 'r')
		originalcont = uidata.Container('Original')
		originalcont.addObjects((self.testfile, readmeth, cameraconfigure, acqmeth, testmeth, self.originalimage))

		### edge detection
		self.edgeson = uidata.Boolean('Find Edges On', True, 'rw', persist=True)
		self.filtertype = uidata.SingleSelectFromList('Filter Type', ['laplacian', 'laplacian-gaussian'], 0, persist=True)
		self.glapsize = uidata.Integer('LoG Size', 9, 'rw', persist=True)
		self.glapsigma = uidata.Float('LoG Sigma', 1.4, 'rw', persist=True)
		self.edgeabs = uidata.Boolean('Absolute Value', False, 'rw', persist=True)
		edgemeth = uidata.Method('Find Edges', self.findEdges)
		self.edgeimage = uidata.Image('Edge Image', None, 'r')
		edgecont = uidata.Container('Edge Finder')
		edgecont.addObjects((self.edgeson, self.filtertype, self.glapsize, self.glapsigma, self.edgeabs, edgemeth, self.edgeimage,))


		### Correlate Template
		self.mindia = uidata.Float('Minimum Diameter', 20.0, 'rw', persist=True)
		self.maxdia = uidata.Float('Maximum Diameter', 40.0, 'rw', persist=True)
		self.cortype = uidata.SingleSelectFromList('Correlation Type', ['cross correlation', 'phase correlation'], 0, persist=True)
		cormeth = uidata.Method('Correlate Template', self.correlateTemplate)
		self.corimage = uidata.Image('Correlation Image', None, 'r')
		corcont = uidata.Container('Template Correlation')
		corcont.addObjects((self.mindia, self.maxdia, self.cortype, cormeth, self.corimage))

		### threshold
		self.threshvalue = uidata.Float('Threshold Value', 3.0, 'rw', persist=True)
		threshmeth = uidata.Method('Threshold', self.threshold)
		self.threshimage = uidata.Image('Thresholded Image', None, 'r')
		threshcont = uidata.Container('Threshold')
		threshcont.addObjects((self.threshvalue, threshmeth, self.threshimage))

		### blobs
		self.blobborder = uidata.Integer('Border', 20, 'rw', persist=True)
		findblobmeth = uidata.Method('Find Blobs', self.findBlobs)
		self.allblobs = uidata.Sequence('All Blobs', [])
		self.allblobsimage = uidata.TargetImage('All Blobs Image', None, 'r')
		self.allblobsimage.addTargetType('All Blobs')
		self.latspacing = uidata.Float('Spacing', 150.0, 'rw', persist=True)
		self.lattol = uidata.Float('Tolerance', 0.1, 'rw', persist=True)

		self.holestatsrad = uidata.Float('Hole Stats Radius', 15, 'rw', persist=True)
		self.icei0 = uidata.Float('Zero Thickness', 1000.0, 'rw', persist=True)


		fitlatmeth = uidata.Method('Fit Lattice', self.fitLattice)
		self.latblobs = uidata.Sequence('Lattice Blobs', [])
		self.latblobsimage = uidata.TargetImage('Lattice Blobs Image', None, 'r')
		self.latblobsimage.addTargetType('Lattice Blobs')

		self.icetmin = uidata.Float('Minimum Mean Thickness', 0.05, 'rw', persist=True)
		self.icetmax = uidata.Float('Maximum Mean Thickness', 0.2, 'rw', persist=True)
		self.icetstd = uidata.Float('Maximum StdDev Thickness', 0.2, 'rw', persist=True)

		icemeth = uidata.Method('Analyze Ice', self.ice)
		self.goodholes = uidata.Sequence('Good Holes', [])
		self.goodholesimage = uidata.TargetImage('Good Holes Image', None, 'r')
		self.goodholesimage.addTargetType('Good Holes')
		blobcont = uidata.Container('Blobs')
		blobcont.addObjects((self.blobborder, findblobmeth, self.allblobs, self.allblobsimage, self.latspacing, self.lattol, self.holestatsrad, self.icei0, fitlatmeth, self.latblobs, self.latblobsimage, self.icetmin, self.icetmax, self.icetstd, icemeth, self.goodholes, self.goodholesimage))

		container = uidata.MediumContainer('Hole Finder')
		container.addObjects((originalcont,edgecont,corcont,threshcont, blobcont))
		self.uiserver.addObject(container)

	def readImage(self):
		filename = self.testfile.get()
		orig = Mrc.mrc_to_numeric(filename)
		self.hf['original'] = orig
		self.originalimage.set(orig)

	def acqImage(self):
		config = self.cam.cameraConfig()
		imdata = self.cam.acquireCameraImageData(config)
		orig = imdata['image']
		self.hf['original'] = orig
		self.originalimage.set(orig)

	def findEdges(self):
		n = self.glapsize.get()
		sig = self.glapsigma.get()
		ab = self.edgeabs.get()
		filt = self.filtertype.getSelectedValue()
		self.hf.configure_edges(filter=filt, size=n, sigma=sig, absvalue=ab)
		self.hf.find_edges()
		self.edgeimage.set(self.hf['edges'])

	def correlateTemplate(self):
		mindia = self.mindia.get()
		maxdia = self.maxdia.get()
		cortype = self.cortype.getSelectedValue()
		minrad = mindia / 2.0
		maxrad = maxdia / 2.0
		self.hf.configure_template(min_radius=minrad, max_radius=maxrad)
		self.hf.create_template()
		self.hf.configure_correlation(cortype)
		self.hf.correlate_template()
		self.corimage.set(self.hf['correlation'])

	def threshold(self):
		tvalue = self.threshvalue.get()
		self.hf.configure_threshold(tvalue)
		self.hf.threshold_correlation()
		self.threshimage.set(self.hf['threshold'])

	def blobCenters(self, blobs):
		centers = []
		for blob in blobs:
			c = tuple(blob.stats['center'])
			centers.append((c[1],c[0]))
		return centers

	def findBlobs(self):
		border = self.blobborder.get()
		self.hf.configure_blobs(border=border)
		self.hf.find_blobs()
		blobs = self.hf['blobs']
		centers = self.blobCenters(blobs)
		self.allblobs.set(centers)
		self.allblobsimage.setImage(self.hf['original'])
		self.allblobsimage.setTargetType('All Blobs', centers)

	def fitLattice(self):
		latspace = self.latspacing.get()
		lattol = self.lattol.get()
		r = self.holestatsrad.get()
		i0 = self.icei0.get()
		self.icecalc.set_i0(i0)

		self.hf.configure_lattice(spacing=latspace, tolerance=lattol)
		self.hf.blobs_to_lattice()

		self.hf.configure_holestats(radius=r)
		self.hf.calc_holestats()

		holes = self.hf['holes']
		centers = self.blobCenters(holes)
		mylist = []
		for hole in holes:
			mean = float(hole.stats['hole_mean'])
			tmean = self.icecalc.get_thickness(mean)
			std = float(hole.stats['hole_std'])
			tstd = self.icecalc.get_stdev_thickness(std, mean)
			center = tuple(hole.stats['center'])
			mylist.append({'m':mean, 'tm': tmean, 's':std, 'ts': tstd, 'c':center})
		self.latblobs.set(mylist)
		self.latblobsimage.setImage(self.hf['original'])
		self.latblobsimage.setTargetType('Lattice Blobs', centers)

	def ice(self):
		i0 = self.icei0.get()
		tmin = self.icetmin.get()
		tmax = self.icetmax.get()
		tstd = self.icetstd.get()
		self.hf.configure_ice(i0=i0,tmin=tmin,tmax=tmax,tstd=tstd)
		self.hf.calc_ice()
		goodholes = self.hf['holes2']
		centers = self.blobCenters(goodholes)
		self.goodholes.set(centers)
		self.goodholesimage.setImage(self.hf['original'])
		# takes x,y instead of row,col
		self.goodholesimage.setTargetType('Good Holes', centers)

	def everything(self):
		# find edges
		self.findEdges()
		# correlate template
		self.correlateTemplate()
		# threshold
		self.threshold()
		# find blobs
		self.findBlobs()
		# lattice
		self.fitLattice()
		# ice
		self.ice()

	def findTargets(self, imdata):
		self.hf['original'] = imdata['image']
		self.currentimage = imdata['image']
		self.everything()
		# prepare targets for publishing
		self.buildTargetDataList()

	def buildTargetDataList(self):
		'''
		loop through a list of blobs and convert them to target data
		'''
		holes = self.hf['holes2']
		for hole in holes:
			column, row = hole.stats['center']
			# using self.currentiamge.shape could be bad
			target = {'delta row': row - self.currentimage.shape[0]/2,
								'delta column': column - self.currentimage.shape[1]/2}
			imageinfo = self.imageInfo()
			target.update(imageinfo)
			targetdata = AcquisitionImageTargetData(id=self.ID())
			targetdata.friendly_update(target)
			self.targetlist.append(targetdata)

