#!/usr/bin/env python

import data
import targetfinder
import holefinderback
import uidata
import Mrc
import camerafuncs
import threading

class HoleFinder(targetfinder.TargetFinder):
	def __init__(self, id, session, nodelocations, **kwargs):
		targetfinder.TargetFinder.__init__(self, id, session, nodelocations, **kwargs)
		self.hf = holefinderback.HoleFinder()
		self.cam = camerafuncs.CameraFuncs(self)
		self.icecalc = holefinderback.IceCalculator()

		self.userpause = threading.Event()

		#if self.__class__ == ClickTargetFinder:
		#	self.defineUserInterface()
		#	self.start()
		self.defineUserInterface()
		self.start()

	def defineUserInterface(self):
		targetfinder.TargetFinder.defineUserInterface(self)
		self.uidataqueueflag.set(False)

		self.usercheckon = uidata.Boolean('User Check', False, 'rw', persist=True)
		self.usequantifoil = uidata.Boolean('Quantifoil', True, 'rw', persist=True)

		self.testfile = uidata.String('Filename', '', 'rw', persist=True)
		readmeth = uidata.Method('Read Image', self.readImage)
		cameraconfigure = self.cam.configUIData()
		acqmeth = uidata.Method('Acquire Image', self.acqImage)
		testmeth = uidata.Method('Test All', self.everything)
		self.originalimage = uidata.Image('Original', None, 'r')
		originalcont = uidata.LargeContainer('Original')
		originalcont.addObjects((self.testfile, readmeth, cameraconfigure, acqmeth, testmeth, self.originalimage))

		### edge detection
		self.edgeson = uidata.Boolean('Find Edges On', True, 'rw', persist=True)
		self.lowpasson = uidata.Boolean('Low Pass Filter On', True, 'rw', persist=True)
		self.lowpasssize = uidata.Integer('Low Pass Filter Size', 5, 'rw', persist=True)
		self.lowpasssigma = uidata.Float('Low Pass Filter Sigma', 1.0, 'rw', persist=True)
		self.filtertype = uidata.SingleSelectFromList('Filter Type', ['laplacian3', 'laplacian5', 'laplacian-gaussian', 'sobel'], 0, persist=True)
		self.glapsize = uidata.Integer('LoG Size', 9, 'rw', persist=True)
		self.glapsigma = uidata.Float('LoG Sigma', 1.4, 'rw', persist=True)
		self.edgeabs = uidata.Boolean('Absolute Value', False, 'rw', persist=True)
		edgemeth = uidata.Method('Find Edges', self.findEdges)
		self.edgeimage = uidata.Image('Edge Image', None, 'r')
		edgecont = uidata.LargeContainer('Edge Finder')
		edgecont.addObjects((self.edgeson, self.lowpasson, self.lowpasssize, self.lowpasssigma, self.filtertype, self.glapsize, self.glapsigma, self.edgeabs, edgemeth, self.edgeimage,))


		### Correlate Template
		self.ringlist = uidata.Array('Ring Diameters', [(30,40)], 'rw', persist=True)
		self.cortype = uidata.SingleSelectFromList('Correlation Type', ['cross correlation', 'phase correlation'], 0, persist=True)
		cormeth = uidata.Method('Correlate Template', self.correlateTemplate)
		self.corimage = uidata.Image('Correlation Image', None, 'r')
		corcont = uidata.LargeContainer('Template Correlation')
		corcont.addObjects((self.ringlist, self.cortype, cormeth, self.corimage))

		### threshold
		self.threshvalue = uidata.Float('Threshold Value', 3.0, 'rw', persist=True)
		threshmeth = uidata.Method('Threshold', self.threshold)
		self.threshimage = uidata.Image('Thresholded Image', None, 'r')
		threshcont = uidata.LargeContainer('Threshold')
		threshcont.addObjects((self.threshvalue, threshmeth, self.threshimage))

		### blobs
		self.blobborder = uidata.Integer('Border', 20, 'rw', persist=True)
		self.maxblobsize = uidata.Integer('Max Blob Size', 1000, 'rw', persist=True)
		self.maxblobs = uidata.Integer('Max Number of Blobs', 300, 'rw', persist=True)
		findblobmeth = uidata.Method('Find Blobs', self.findBlobs)
		self.allblobs = uidata.Sequence('All Blobs', [])
		self.allblobsimage = uidata.TargetImage('All Blobs Image', None, 'r')
		self.allblobsimage.addTargetType('All Blobs')
		self.latspacing = uidata.Float('Spacing', 150.0, 'rw', persist=True)
		self.lattol = uidata.Float('Tolerance', 0.1, 'rw', persist=True)

		self.holestatsrad = uidata.Float('Hole Stats Radius', 15.0, 'rw', persist=True)
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
		self.use_target_template = uidata.Boolean('Use Target Template', False, 'rw', persist=True)
		self.foc_target_template = uidata.Array('Focus Template', [], 'rw', persist=True)
		self.acq_target_template = uidata.Array('Acqusition Template', [], 'rw', persist=True)
		submitmeth = uidata.Method('Submit', self.submit)
		self.goodholesimage.addTargetType('acquisition')
		self.goodholesimage.addTargetType('focus')

		allblobscontainer = uidata.LargeContainer('All Blobs')
		allblobscontainer.addObjects((self.blobborder, self.maxblobs, self.maxblobsize, findblobmeth, self.allblobs, self.allblobsimage))
		laticeblobscontainer = uidata.LargeContainer('Latice Blobs')
		laticeblobscontainer.addObjects(( self.latspacing, self.lattol, self.holestatsrad, self.icei0, fitlatmeth, self.latblobs, self.latblobsimage))
		blobcont = uidata.LargeContainer('Blobs')
		blobcont.addObjects((allblobscontainer, laticeblobscontainer))

		goodholescontainer = uidata.LargeContainer('Good Holes')
		goodholescontainer.addObjects((self.icetmin, self.icetmax, self.icetstd, icemeth, self.goodholes, self.use_target_template, self.foc_target_template, self.acq_target_template, self.goodholesimage, submitmeth))

		container = uidata.LargeContainer('Hole Finder')
		container.addObjects((self.usercheckon, originalcont,edgecont,corcont,threshcont, blobcont, goodholescontainer))
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
		lowpasson = self.lowpasson.get()
		lowpassn = self.lowpasssize.get()
		lowpasssig = self.lowpasssigma.get()
		self.hf.configure_edges(filter=filt, size=n, sigma=sig, absvalue=ab, lp=lowpasson, lpn=lowpassn, lpsig=lowpasssig)
		self.hf.find_edges()
		self.edgeimage.set(self.hf['edges'])

	def correlateTemplate(self):
		ringlist = self.ringlist.get()
		# convert diameters to radii
		radlist = []
		for ring in ringlist:
			radring = (ring[0] / 2.0, ring[1] / 2.0)
			radlist.append(radring)
		self.hf.configure_template(ring_list=radlist)
		self.hf.create_template()
		cortype = self.cortype.getSelectedValue()
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
		blobsize = self.maxblobsize.get()
		maxblobs = self.maxblobs.get()
		self.hf.configure_blobs(border=border, maxblobsize=blobsize, maxblobs=maxblobs)
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
		if self.use_target_template.get():
			newtargets = self.applyTargetTemplate(centers)
			acq_points = newtargets['acquisition']
			focus_points = newtargets['focus']
		else:
			acq_points = centers
			focus_points = []
		self.goodholesimage.setTargetType('acquisition', acq_points)
		self.goodholesimage.setTargetType('focus', focus_points)

	def applyTargetTemplate(self, centers):
		acq_vect = self.acq_target_template.get()
		foc_vect = self.foc_target_template.get()
		newtargets = {'acquisition':[], 'focus':[]}
		for center in centers:
			for vect in acq_vect:
				target = center[0]+vect[0], center[1]+vect[1]
				newtargets['acquisition'].append(target)
			for vect in foc_vect:
				target = center[0]+vect[0], center[1]+vect[1]
				newtargets['focus'].append(target)
		return newtargets

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
		## automated part
		self.hf['original'] = imdata['image']
		self.everything()

		## user part
		if self.usercheckon.get():
			self.userpause.clear()
			self.userpause.wait()
		self.getTargetDataList('focus')
		self.getTargetDataList('acquisition')

	def submit(self):
		self.userpause.set()

	def getTargetDataList(self, typename):
		for imagetarget in self.goodholesimage.getTargetType(typename):
			column, row = imagetarget
			# using self.currentiamge.shape could be bad
			target = {'delta row': row - self.numarray.shape[0]/2,
								'delta column': column - self.numarray.shape[1]/2}
			imageinfo = self.imageInfo()
			target.update(imageinfo)
			targetdata = data.AcquisitionImageTargetData(id=self.ID(), type=typename, version=0)
			targetdata.friendly_update(target)
			self.targetlist.append(targetdata)
