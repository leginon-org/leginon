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
import holefinderback
import uidata
import Mrc
import camerafuncs
import threading
import ice
try:
	import numarray as Numeric
except:
	import Numeric
import gui.wx.HoleFinder

class HoleFinder(targetfinder.TargetFinder):
	panelclass = gui.wx.HoleFinder.Panel
	settingsclass = data.HoleFinderSettingsData
	defaultsettings = {
		'user check': False,
		'skip': False,
		'image filename': '',
		'edge lpf': True,
		'edge lpf size': 5,
		'edge lpf sigma': 1.0,
		'edge': True,
		'edge type': 'sobel',
		'edge log size': 9,
		'edge log sigma': 1.4,
		'edge absolute': False,
		'edge threshold': 100.0,
	}
	def __init__(self, id, session, managerlocation, **kwargs):
		targetfinder.TargetFinder.__init__(self, id, session, managerlocation, **kwargs)
		self.hf = holefinderback.HoleFinder()
		self.cam = camerafuncs.CameraFuncs(self)
		self.icecalc = ice.IceCalculator()

		self.userpause = threading.Event()

		#if self.__class__ == ClickTargetFinder:
		#	self.defineUserInterface()
		#	self.start()
		self.defineUserInterface()
		self.start()

	#def defineUserInterface(self):
		#cameraconfigure = self.cam.uiSetupContainer()
		#acqmeth = uidata.Method('Acquire Image', self.acqImage)
		#testmeth = uidata.Method('Test All', self.everything)

	def defineUserInterface(self):
		targetfinder.TargetFinder.defineUserInterface(self)

		self.originalimage = uidata.Image('Original', None, 'r')

		### edge detection
		self.edgeson = uidata.Boolean('Find Edges On', True, 'rw', persist=True)
		self.edgethresh = uidata.Number('Threshold', 100.0, 'rw', persist=True)
		self.filtertype = uidata.SingleSelectFromList('Filter Type', ['sobel', 'laplacian3', 'laplacian5', 'laplacian-gaussian'], 0, persist=True)
		self.glapsize = uidata.Integer('LoG Size', 9, 'rw', persist=True)
		self.glapsigma = uidata.Number('LoG Sigma', 1.4, 'rw', persist=True)
		self.edgeabs = uidata.Boolean('Absolute Value', False, 'rw', persist=True)
		edgemeth = uidata.Method('Find Edges', self.findEdges)
		self.edgeimage = uidata.Image('Edge Image', None, 'r')
		edgecont = uidata.LargeContainer('Edge Finder')
		edgecont.addObjects((self.edgeson, self.filtertype, self.glapsize, self.glapsigma, self.edgeabs, self.edgethresh, edgemeth, self.edgeimage,))


		### Correlate Template
		self.ringlist = uidata.Sequence('Ring Diameters', [(30,40)], 'rw', persist=True)
		self.cortype = uidata.SingleSelectFromList('Correlation Type', ['cross correlation', 'phase correlation'], 0, persist=True)
		self.corfilt = uidata.Number('Low Pass Filter', 0.0, 'rw', persist=True)
		cormeth = uidata.Method('Correlate Template', self.correlateTemplate)
		self.corimage = uidata.Image('Correlation Image', None, 'r')
		corcont = uidata.LargeContainer('Template Correlation')
		corcont.addObjects((self.ringlist, self.cortype, self.corfilt, cormeth, self.corimage))

		### threshold
		self.threshvalue = uidata.Number('Threshold Value', 3.0, 'rw', persist=True)
		threshmeth = uidata.Method('Threshold', self.threshold)
		self.threshimage = uidata.Image('Thresholded Image', None, 'r')
		threshcont = uidata.LargeContainer('Threshold')
		threshcont.addObjects((self.threshvalue, threshmeth, self.threshimage))

		### blobs
		self.blobborder = uidata.Integer('Border', 20, 'rw', persist=True)
		self.maxblobsize = uidata.Integer('Max Blob Size', 1000, 'rw', persist=True)
		self.maxblobs = uidata.Integer('Max Number of Blobs', 300, 'rw', persist=True)
		findblobmeth = uidata.Method('Find Blobs', self.findBlobs)
		self.allblobs = uidata.Sequence('All Blobs', [], 'r')
		self.allblobsimage = uidata.TargetImage('All Blobs Image', None, 'r')
		self.allblobsimage.addTargetType('All Blobs')
		self.latspacing = uidata.Number('Spacing', 150.0, 'rw', persist=True)
		self.lattol = uidata.Number('Tolerance', 0.1, 'rw', persist=True)

		self.holestatsrad = uidata.Number('Hole Stats Radius', 15.0, 'rw', persist=True)
		self.icei0 = uidata.Number('Zero Thickness', 1000.0, 'rw', persist=True)


		fitlatmeth = uidata.Method('Fit Lattice', self.fitLattice)
		self.latblobs = uidata.Sequence('Lattice Blobs', [], 'r')
		self.latblobsimage = uidata.TargetImage('Lattice Blobs Image', None, 'r')
		self.latblobsimage.addTargetType('Lattice Blobs')

		self.icetmin = uidata.Float('Minimum Mean Thickness', 0.05, 'rw', persist=True)
		self.icetmax = uidata.Float('Maximum Mean Thickness', 0.2, 'rw', persist=True)
		self.icetstd = uidata.Float('Maximum StdDev Thickness', 0.2, 'rw', persist=True)

		icemeth = uidata.Method('Analyze Ice', self.ice)
		self.goodholes = uidata.Sequence('Good Holes', [], 'r')
		self.goodholesimage = uidata.TargetImage('Good Holes Image', None, 'r')

		# target templates
		self.use_target_template = uidata.Boolean('Use Target Template', False, 'rw', persist=True)
		self.foc_target_template = uidata.Sequence('Focus Template', [], 'rw', persist=True)
		# thickness limit on focus template
		foc_template_limit = uidata.Container('Focus Template Thickness')
		self.focthickon = uidata.Boolean('On', False, 'rw', persist=True)
		self.focicerad = uidata.Float('Focus Stats Radius', 10, 'rw', persist=True)
		self.focicetmin = uidata.Float('Focus Minimum Mean Thickness', 0.05, 'rw', persist=True)
		self.focicetmax = uidata.Float('Focus Maximum Mean Thickness', 0.5, 'rw', persist=True)
		self.focicetstd = uidata.Float('Focus Maximum StdDev Thickness', 0.5, 'rw', persist=True)
		foc_template_limit.addObjects((self.focthickon, self.focicerad, self.focicetmin, self.focicetmax, self.focicetstd))

		self.acq_target_template = uidata.Sequence('Acqusition Template', [], 'rw', persist=True)
		self.focus_one_hole = uidata.SingleSelectFromList('Focus One Hole', ['Off', 'Any Hole', 'Good Hole'], 0, permissions='rw', persist=True)
		self.goodholesimage.addTargetType('acquisition', [], (0,255,0))
		self.goodholesimage.addTargetType('focus', [], (0,0,255))

		allblobscontainer = uidata.LargeContainer('All Blobs')
		allblobscontainer.addObjects((self.blobborder, self.maxblobs, self.maxblobsize, findblobmeth, self.allblobs, self.allblobsimage))
		latticeblobscontainer = uidata.LargeContainer('Lattice Blobs')
		latticeblobscontainer.addObjects(( self.latspacing, self.lattol, self.holestatsrad, self.icei0, fitlatmeth, self.latblobs, self.latblobsimage))
		blobcont = uidata.LargeContainer('Blobs')
		blobcont.addObjects((allblobscontainer, latticeblobscontainer))

		goodholescontainer = uidata.LargeContainer('Good Holes')
		goodholescontainer.addObjects((self.icetmin, self.icetmax, self.icetstd, icemeth, self.goodholes, self.use_target_template, self.foc_target_template, foc_template_limit, self.acq_target_template, self.focus_one_hole, self.goodholesimage, ))

		container = uidata.LargeContainer('Hole Finder')
		container.addObjects((edgecont,corcont,threshcont, blobcont, goodholescontainer))
		self.uicontainer.addObject(container)

	def readImage(self, filename):
		orig = Mrc.mrc_to_numeric(filename)
		self.hf['original'] = orig
		self.currentimagedata = None
		self.originalimage.set(orig)

	def acqImage(self):
		self.cam.uiApplyAsNeeded()
		imdata = self.cam.acquireCameraImageData()
		orig = imdata['image']
		self.hf['original'] = orig
		self.originalimage.set(orig)

	def findEdges(self):
		self.logger.info('find edges')
		n = self.glapsize.get()
		sig = self.glapsigma.get()
		ab = self.edgeabs.get()
		filt = self.filtertype.getSelectedValue()
		lowpasson = self.settings['edge lpf']
		lowpassn = self.settings['edge lpf size']
		lowpasssig = self.settings['edge lpf sigma']
		edgethresh = self.edgethresh.get()
		self.hf.configure_edges(filter=filt, size=n, sigma=sig, absvalue=ab, lp=lowpasson, lpn=lowpassn, lpsig=lowpasssig, thresh=edgethresh)
		self.hf.find_edges()
		# convert to Float32 to prevent seg fault
		self.edgeimage.set(self.hf['edges'].astype(Numeric.Float32))

	def correlateTemplate(self):
		self.logger.info('correlate ring template')
		ringlist = self.ringlist.get()
		# convert diameters to radii
		radlist = []
		for ring in ringlist:
			radring = (ring[0] / 2.0, ring[1] / 2.0)
			radlist.append(radring)
		self.hf.configure_template(ring_list=radlist)
		self.hf.create_template()
		cortype = self.cortype.getSelectedValue()
		corfilt = self.corfilt.get()
		self.hf.configure_correlation(cortype, corfilt)
		self.hf.correlate_template()
		self.corimage.set(self.hf['correlation'].astype(Numeric.Float32))

	def threshold(self):
		self.logger.info('threshold')
		tvalue = self.threshvalue.get()
		self.hf.configure_threshold(tvalue)
		self.hf.threshold_correlation()
		# convert to Float32 to prevent seg fault
		self.threshimage.set(self.hf['threshold'].astype(Numeric.Float32))

	def blobCenters(self, blobs):
		centers = []
		for blob in blobs:
			c = tuple(blob.stats['center'])
			centers.append((c[1],c[0]))
		return centers

	def findBlobs(self):
		self.logger.info('find blobs')
		border = self.blobborder.get()
		blobsize = self.maxblobsize.get()
		maxblobs = self.maxblobs.get()
		self.hf.configure_blobs(border=border, maxblobsize=blobsize, maxblobs=maxblobs)
		self.hf.find_blobs()
		blobs = self.hf['blobs']
		centers = self.blobCenters(blobs)
		self.logger.info('Blobs: %s' % (len(centers),))
		self.allblobs.set(centers)
		self.allblobsimage.setImage(self.hf['original'])
		self.allblobsimage.setTargetType('All Blobs', centers)

	def fitLattice(self):
		self.logger.info('fit lattice')
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
		self.logger.info('Holes: %s' % (len(centers),))
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
		self.logger.info('limit thickness')
		i0 = self.icei0.get()
		tmin = self.icetmin.get()
		tmax = self.icetmax.get()
		tstd = self.icetstd.get()
		self.hf.configure_ice(i0=i0,tmin=tmin,tmax=tmax,tstd=tstd)
		self.hf.calc_ice()
		goodholes = self.hf['holes2']
		centers = self.blobCenters(goodholes)
		allcenters = self.blobCenters(self.hf['holes'])

		focus_points = []

		## replace an acquisition target with a focus target
		onehole = self.focus_one_hole.getSelectedValue()
		if centers and onehole != 'Off':
			## if only one hole, this is useless
			if len(allcenters) < 2:
				self.logger.info('need more than one hole if you want to focus on one of them')
				centers = []
			elif onehole == 'Any Hole':
				fochole = self.focus_on_hole(centers, allcenters)
				focus_points.append(fochole)
			elif onehole == 'Good Hole':
				if len(centers) < 2:
					self.logger.info('need more than one good hole if you want to focus on one of them')
					centers = []
				else:
					## use only good centers
					fochole = self.focus_on_hole(centers, centers)
					focus_points.append(fochole)

		self.logger.info('Holes with good ice: %s' % (len(centers),))
		self.goodholes.set(centers)
		self.goodholesimage.setImage(self.hf['original'])
		self.goodholesimage.imagedata = self.currentimagedata
		# takes x,y instead of row,col
		if self.use_target_template.get():
			newtargets = self.applyTargetTemplate(centers)
			acq_points = newtargets['acquisition']
			focus_points.extend(newtargets['focus'])
		else:
			acq_points = centers

		self.goodholesimage.setTargetType('acquisition', acq_points)
		self.goodholesimage.setTargetType('focus', focus_points)
		self.logger.info('Acquisition Targets: %s' % (len(acq_points),))
		self.logger.info('Focus Targets: %s' % (len(focus_points),))
		hfprefs = self.storeHoleFinderPrefsData(self.currentimagedata)
		self.storeHoleStatsData(hfprefs)

	def centroid(self, points):
		## find centroid
		cx = cy = 0.0
		for point in points:
			cx += point[0]
			cy += point[1]
		cx /= len(points)
		cy /= len(points)
		return cx,cy

	def focus_on_hole(self, good, all):
		cx,cy = self.centroid(all)
		focpoint = None

		## make a list of the bad holes
		bad = []
		for point in all:
			if point not in good:
				bad.append(point)

		## if there are bad holes, use one
		if bad:
			point = bad[0]
			closest_dist = Numeric.hypot(point[0]-cx,point[1]-cy)
			closest_point = point
			for point in bad:
				dist = Numeric.hypot(point[0]-cx,point[1]-cy)
				if dist < closest_dist:
					closest_dist = dist
					closest_point = point
			return closest_point

		## now use a good hole for focus
		point = good[0]
		closest_dist = Numeric.hypot(point[0]-cx,point[1]-cy)
		closest_point = point
		for point in good:
			dist = Numeric.hypot(point[0]-cx,point[1]-cy)
			if dist < closest_dist:
				closest_dist = dist
				closest_point = point
		good.remove(closest_point)
		return closest_point

	def bypass(self):
		self.goodholesimage.setTargetType('acquisition', [])
		self.goodholesimage.setTargetType('focus', [])
		self.goodholesimage.setImage(self.hf['original'])
		self.goodholesimage.imagedata = self.currentimagedata

	def applyTargetTemplate(self, centers):
		self.logger.info('apply template')
		imshape = self.hf['original'].shape
		acq_vect = self.acq_target_template.get()
		foc_vect = self.foc_target_template.get()
		newtargets = {'acquisition':[], 'focus':[]}
		for center in centers:
			self.logger.info('applying template to hole at %s' % (center,))
			for vect in acq_vect:
				target = center[0]+vect[0], center[1]+vect[1]
				tarx = target[0]
				tary = target[1]
				if tarx < 0 or tarx >= imshape[1] or tary < 0 or tary >= imshape[0]:
					self.logger.info('skipping template point %s: out of image bounds' % (vect,))
					continue
				newtargets['acquisition'].append(target)
			for vect in foc_vect:
				target = center[0]+vect[0], center[1]+vect[1]
				tarx = target[0]
				tary = target[1]
				if tarx < 0 or tarx >= imshape[1] or tary < 0 or tary >= imshape[0]:
					self.logger.info('skipping template point %s: out of image bounds' % (vect,))
					continue
				## check if target has good thickness
				if self.focthickon.get():
					rad = self.focicerad.get()
					tmin = self.focicetmin.get()
					tmax = self.focicetmax.get()
					tstd = self.focicetstd.get()
					coord = target[1], target[0]
					stats = self.hf.get_hole_stats(self.hf['original'], coord, rad)
					if stats is None:
						self.logger.info('skipping template point %s:  stats region out of bounds' % (vect,))
						continue
					tm = self.icecalc.get_thickness(stats['mean'])
					ts = self.icecalc.get_stdev_thickness(stats['std'], stats['mean'])
					self.logger.info('template point %s stats:  mean: %s, stdev: %s' % (vect, tm, ts))
					if (tmin <= tm <= tmax) and (ts < tstd):
						self.logger.info('template point %s passed thickness test' % (vect,))
						newtargets['focus'].append(target)
						break
				else:
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

	def storeHoleStatsData(self, prefs):
		holes = self.hf['holes']
		for hole in holes:
			stats = hole.stats
			holestats = data.HoleStatsData(session=self.session, prefs=prefs)
			holestats['row'] = stats['center'][0]
			holestats['column'] = stats['center'][1]
			holestats['mean'] = stats['hole_mean']
			holestats['stdev'] = stats['hole_std']
			holestats['thickness-mean'] = stats['thickness-mean']
			holestats['thickness-stdev'] = stats['thickness-stdev']
			holestats['good'] = stats['good']
			self.publish(holestats, database=True)

	def storeHoleFinderPrefsData(self, imagedata):
		hfprefs = data.HoleFinderPrefsData()
		hfprefs.update({
			'session': self.session,
			'image': imagedata,
			'user-check': self.settings['user check'],
			'skip-auto': self.settings['skip'],

			'edge-lpf-on': self.settings['edge lpf'],
			'edge-lpf-size': self.settings['edge lpf size'],
			'edge-lpf-sigma': self.settings['edge lpf sigma'],
			'edge-filter-type': self.filtertype.getSelectedValue(),
			'edge-threshold': self.edgethresh.get(),

			'template-rings': self.ringlist.get(),
			'template-correlation-type': self.cortype.getSelectedValue(),
			'template-lpf': self.corfilt.get(),

			'threshold-value': self.threshvalue.get(),
			'blob-border': self.blobborder.get(),
			'blob-max-number': self.maxblobs.get(),
			'blob-max-size': self.maxblobsize.get(),
			'lattice-spacing': self.latspacing.get(),
			'lattice-tolerance': self.lattol.get(),
			'stats-radius': self.holestatsrad.get(),
			'ice-zero-thickness': self.icei0.get(),

			'ice-min-thickness': self.icetmin.get(),
			'ice-max-thickness': self.icetmax.get(),
			'ice-max-stdev': self.icetstd.get(),
			'template-on': self.use_target_template.get(),
			'template-focus': self.foc_target_template.get(),
			'template-acquisition': self.acq_target_template.get(),
		})

		self.publish(hfprefs, database=True)
		return hfprefs

	def findTargets(self, imdata, targetlist):
		## check if targets already found on this image
		previous = self.researchTargets(image=imdata)
		if previous:
			return

		## auto or not?
		self.hf['original'] = imdata['image']
		self.currentimagedata = imdata
		if self.settings['skip']:
			self.bypass()
		else:
			self.everything()

		## user part
		if self.settings['user check']:
			self.notifyUserSubmit()
			self.userpause.clear()
			self.userpause.wait()
			self.unNotifyUserSubmit()

		### publish targets from goodholesimage
		self.targetsFromClickImage(self.goodholesimage, 'focus', targetlist)
		self.targetsFromClickImage(self.goodholesimage, 'acquisition', targetlist)

	def submit(self):
		self.userpause.set()

