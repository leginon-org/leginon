#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import data
import targetfinder
import uidata
import Mrc
import camerafuncs
import threading
import ice
import Numeric
import imagefun

class RasterFinder(targetfinder.TargetFinder):
	def __init__(self, id, session, nodelocations, **kwargs):
		targetfinder.TargetFinder.__init__(self, id, session, nodelocations, **kwargs)
		self.cam = camerafuncs.CameraFuncs(self)
		self.icecalc = ice.IceCalculator()
		self.rasterpoints = None

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

		self.testfile = uidata.String('Filename', '', 'rw', persist=True)
		readmeth = uidata.Method('Read Image', self.readImage)
		cameraconfigure = self.cam.uiSetupContainer()
		acqmeth = uidata.Method('Acquire Image', self.acqImage)
		testmeth = uidata.Method('Test All', self.everything)
		self.originalimage = uidata.Image('Original', None, 'r')
		originalcont = uidata.LargeContainer('Original')
		originalcont.addObjects((self.testfile, readmeth, cameraconfigure, acqmeth, testmeth, self.originalimage))

		### raster points
		self.rasterspacing = uidata.Integer('Raster Spacing', 100, 'rw', persist=True)
		self.rasterlimit = uidata.Integer('Raster Limit', 5, 'rw', persist=True)
		rastermeth = uidata.Method('Create Raster Points', self.createRaster)
		self.rasterimage = uidata.TargetImage('Raster Points Image', None, 'r')
		self.rasterimage.addTargetType('Raster Points')
		rastercont = uidata.LargeContainer('Raster Points')
		rastercont.addObjects((self.rasterspacing, self.rasterlimit, rastermeth, self.rasterimage))

		## ice analysis
		self.boxsize = uidata.Float('Stats Box Size', 15.0, 'rw', persist=True)
		self.icei0 = uidata.Float('Zero Thickness', 1000.0, 'rw', persist=True)
		self.icetmin = uidata.Float('Minimum Mean Thickness', 0.05, 'rw', persist=True)
		self.icetmax = uidata.Float('Maximum Mean Thickness', 0.2, 'rw', persist=True)
		self.icetstd = uidata.Float('Maximum StdDev Thickness', 0.2, 'rw', persist=True)
		icemeth = uidata.Method('Analyze Ice', self.ice)
		self.goodice = uidata.Sequence('Good Ice', [], 'r')

		icecont = uidata.Container('Ice Analysis')
		icecont.addObjects((self.boxsize, self.icei0, self.icetmin, self.icetmax, self.icetstd, icemeth, self.goodice))

		### post processing of targets
		focuscont = uidata.Container('Focus Targets')
		self.conv_foc = uidata.Boolean('Do Convolve', False, 'rw', persist=True)
		self.conv_foc_template = uidata.Sequence('Convolve Template', [], 'rw', persist=True)
		self.const_foc_template = uidata.Sequence('Constant Template', [], 'rw', persist=True)
		focuscont.addObjects((self.conv_foc, self.conv_foc_template, self.const_foc_template))

		acqcont = uidata.Container('Acquisition Targets')
		self.conv_acq = uidata.Boolean('Do Convolve', False, 'rw', persist=True)
		self.conv_acq_template = uidata.Sequence('Convolve Template', [], 'rw', persist=True)
		self.const_acq_template = uidata.Sequence('Constant Template', [], 'rw', persist=True)
		acqcont.addObjects((self.conv_acq, self.conv_acq_template, self.const_acq_template))

		postcont = uidata.Container('Target Post Processing')
		postcont.addObjects((focuscont, acqcont))

		## image
		self.goodiceimage = uidata.TargetImage('Good Ice Image', None, 'r')
		self.goodiceimage.addTargetType('acquisition')
		self.goodiceimage.addTargetType('focus')

		submitmeth = uidata.Method('Submit', self.submit)

		goodicecontainer = uidata.LargeContainer('Good Ice')
		goodicecontainer.addObjects((icecont, postcont, self.goodiceimage, submitmeth))

		container = uidata.LargeContainer('Raster Finder')
		container.addObjects((self.usercheckon, originalcont, rastercont, goodicecontainer))
		self.uiserver.addObject(container)

	def readImage(self):
		filename = self.testfile.get()
		orig = Mrc.mrc_to_numeric(filename)
		self.original = orig
		self.originalimage.set(orig)

	def acqImage(self):
		self.cam.uiApplyAsNeeded()
		imdata = self.cam.acquireCameraImageData()
		orig = imdata['image']
		self.original = orig
		self.originalimage.set(orig)

	def transpose_points(self, points):
		newpoints = []
		for point in points:
			newpoints.append((point[1],point[0]))
		return newpoints

	def createRaster(self):
		'''
		from center of image, generate a raster of points
		'''
		imageshape = self.original.shape
		spacing = self.rasterspacing.get()
		limit = self.rasterlimit.get()
		rcenter = imageshape[0]/2
		ccenter = imageshape[1]/2
		points = []
		for rlayer in range(-limit, limit+1):
			r = int(rcenter + rlayer * spacing)
			if r < 0 or r >= imageshape[0]: continue
			for clayer in range(-limit, limit+1):
				c = int(ccenter + clayer * spacing)
				if c < 0 or c >= imageshape[1]: continue
				points.append((r,c))

		self.rasterimage.setImage(self.original)
		self.rasterimage.setTargetType('Raster Points', self.transpose_points(points))
		self.rasterpoints = points
		print 'full raster has %s points' % (len(points),)

	def get_box_stats(self, image, coord, boxsize):
		## select the region of interest
		b2 = boxsize / 2
		rmin = int(coord[0]-b2)
		rmax = int(coord[0]+b2)
		cmin = int(coord[1]-b2)
		cmax = int(coord[1]+b2)
		## beware of boundaries
		if rmin < 0:  rmin = 0
		if rmax >= image.shape[0]:  rmax = image.shape[0]-1
		if cmin < 0:  cmin = 0
		if cmax >= image.shape[1]:  cmax = image.shape[1]-1

		subimage = image[rmin:rmax+1, cmin:cmax+1]
		roi = Numeric.ravel(subimage)
		mean = imagefun.mean(roi)
		std = imagefun.stdev(roi, known_mean=mean)
		n = len(roi)
		stats = {'mean':mean, 'std': std, 'n':n}
		return stats

	def ice(self):
		i0 = self.icei0.get()
		tmin = self.icetmin.get()
		tmax = self.icetmax.get()
		tstd = self.icetstd.get()
		boxsize = self.boxsize.get()

		self.icecalc.set_i0(i0)

		## calculate stats around each raster point
		goodpoints = []
		mylist = []
		for rasterpoint in self.rasterpoints:
			box_stats = self.get_box_stats(self.original, rasterpoint, boxsize)
			t = self.icecalc.get_thickness(box_stats['mean'])
			ts = self.icecalc.get_stdev_thickness(box_stats['std'], box_stats['mean'])
			if (tmin <= t <= tmax) and (ts < tstd):
				goodpoints.append(rasterpoint)
				mylist.append( (rasterpoint, t, ts))
				stat_str = 'OK:  '
			else:
				stat_str = 'BAD: '
			ice_stat = '  mean: %.4f,     std: %.4f' % (t,ts)
			stat_str = stat_str + str(rasterpoint) + ice_stat
			print stat_str

		goodpoints = self.transpose_points(goodpoints)
		print '%s points with good ice' % (len(goodpoints),)

		self.goodice.set(mylist)
		self.goodiceimage.setImage(self.original)
		self.goodiceimage.imagedata = self.currentimagedata

		### run template convolution
		# takes x,y instead of row,col
		if self.conv_foc.get():
			focus_points = self.applyTargetTemplate(goodpoints, 'focus')
		else:
			focus_points = []
		if self.conv_acq.get():
			acq_points = self.applyTargetTemplate(goodpoints, 'acquisition')
		else:
			acq_points = goodpoints

		## add constant targets
		const_foc = self.const_foc_template.get()
		focus_points.extend(const_foc)
		const_acq = self.const_acq_template.get()
		acq_points.extend(const_acq)

		self.goodiceimage.setTargetType('acquisition', acq_points)
		self.goodiceimage.setTargetType('focus', focus_points)

	def applyTargetTemplate(self, centers, type):
		if type == 'focus':
			vects = self.conv_foc_template.get()
		elif type == 'acquisition':
			vects = self.conv_acq_template.get()
		newtargets = []
		for center in centers:
			for vect in vects:
				target = center[0]+vect[0], center[1]+vect[1]
				newtargets.append(target)
		return newtargets

	def everything(self):
		self.createRaster()
		# ice
		self.ice()

	def findTargets(self, imdata):
		## check if targets already found on this image
		previous = self.researchImageTargets(imdata)
		if previous:
			self.targetlist = previous
			return

		## automated part
		self.original = imdata['image']
		self.everything()

		## user part
		if self.usercheckon.get():
			self.notifyUserSubmit()
			self.userpause.clear()
			self.userpause.wait()
		targetlist = self.getTargetDataList('focus')
		self.targetlist.extend(targetlist)
		targetlist = self.getTargetDataList('acquisition')
		self.targetlist.extend(targetlist)

	def submit(self):
		self.userpause.set()

	def getTargetDataList(self, typename):
		targetlist = []
		for imagetarget in self.goodiceimage.getTargetType(typename):
			column, row = imagetarget
			imagedata = self.goodiceimage.imagedata
			imagearray = imagedata['image']
			drow = row - imagearray.shape[0]/2
			dcol = column - imagearray.shape[1]/2

			targetdata = self.newTargetData(imagedata, typename, drow, dcol)
			targetlist.append(targetdata)
		return targetlist
