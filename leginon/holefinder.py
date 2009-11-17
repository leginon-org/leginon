#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import leginondata
import targetfinder
import holefinderback
from pyami import ordereddict
import threading
import ice
import instrument
import os.path
import math
import gui.wx.HoleFinder

class HoleFinder(targetfinder.TargetFinder):
	panelclass = gui.wx.HoleFinder.Panel
	settingsclass = leginondata.HoleFinderSettingsData
	defaultsettings = dict(targetfinder.TargetFinder.defaultsettings)
	defaultsettings.update({
		'skip': False,
		'image filename': '',
		'edge lpf': {
			'sigma': 1.0,
		},
		'edge': True,
		'edge type': 'sobel',
		'edge log size': 9,
		'edge log sigma': 1.4,
		'edge absolute': False,
		'edge threshold': 100.0,
		'template rings': [(30, 40)],
		'template type': 'cross',
		'template lpf': {
			'sigma': 1.0,
		},
		'threshold': 3.0,
		'blobs border': 20,
		'blobs max': 300,
		'blobs max size': 1000,
		'lattice spacing': 150.0,
		'lattice tolerance': 0.1,
		'lattice hole radius': 15.0,
		'lattice zero thickness': 1000.0,
		'ice min mean': 0.05,
		'ice max mean': 0.2,
		'ice max std': 0.2,
		'focus hole': 'Off',
		'target template': False,
		'focus template': [(0, 0)],
		'acquisition template': [(0, 0)],
		'focus template thickness': False,
		'focus stats radius': 10,
		'focus min mean thickness': 0.05,
		'focus max mean thickness': 0.5,
		'focus max stdev thickness': 0.5,
	})
	def __init__(self, id, session, managerlocation, **kwargs):
		targetfinder.TargetFinder.__init__(self, id, session, managerlocation, **kwargs)
		self.hf = holefinderback.HoleFinder()
		self.icecalc = ice.IceCalculator()

		self.images = {
			'Original': None,
			'Edge': None,
			'Template': None,
			'Threshold': None,
			'Blobs': None,
			'Lattice': None,
			'Final': None,
		}
		self.imagetargets = {
			'Original': {},
			'Edge': {},
			'Template': {},
			'Threshold': {},
			'Blobs': {},
			'Lattice': {},
			'Final': {},
		}
		self.filtertypes = [
			'sobel',
			'laplacian3',
			'laplacian5',
			'laplacian-gaussian'
		]
		# ...

		self.cortypes = ['cross', 'phase']
		self.focustypes = ['Off', 'Any Hole', 'Good Hole']
		self.userpause = threading.Event()

		self.start()

	def readImage(self, filename):
		self.hf['original'] = targetfinder.TargetFinder.readImage(self, filename)

	def findEdges(self):
		self.logger.info('find edges')
		n = self.settings['edge log size']
		sig = self.settings['edge log sigma']
		ab = self.settings['edge absolute']
		edges = self.settings['edge']
		filt = self.settings['edge type']
		lpfsettings = self.settings['edge lpf']
		lowpasssig = lpfsettings['sigma']
		edgethresh = self.settings['edge threshold']
		self.hf.configure_edges(filter=filt, size=n, sigma=sig, absvalue=ab, lpsig=lowpasssig, thresh=edgethresh, edges=edges)
		self.hf.find_edges()
		# convert to Float32 to prevent seg fault
		self.setImage(self.hf['edges'], 'Edge')

	def correlateTemplate(self):
		self.logger.info('correlate ring template')
		ringlist = self.settings['template rings']
		# convert diameters to radii
		radlist = []
		for ring in ringlist:
			radring = (ring[0] / 2.0, ring[1] / 2.0)
			radlist.append(radring)
		self.hf.configure_template(ring_list=radlist)
		self.hf.create_template()
		cortype = self.settings['template type']
		lpfsettings = self.settings['template lpf']
		corsigma = lpfsettings['sigma']
		if cortype == 'phase' and corsigma:
			corfilt = (corsigma,)
		else:
			corfilt = None
		self.hf.configure_correlation(cortype, corfilt)
		self.hf.correlate_template()
		self.setImage(self.hf['correlation'], 'Template')

	def threshold(self):
		self.logger.info('threshold')
		tvalue = self.settings['threshold']
		self.hf.configure_threshold(tvalue)
		self.hf.threshold_correlation()
		# convert to Float32 to prevent seg fault
		self.setImage(self.hf['threshold'], 'Threshold')

	def blobCenters(self, blobs):
		centers = []
		for blob in blobs:
			c = tuple(blob.stats['center'])
			centers.append((c[1],c[0]))
		return centers

	def blobStatsTargets(self, blobs):
		targets = []
		for blob in blobs:
			target = {}
			target['x'] = blob.stats['center'][1]
			target['y'] = blob.stats['center'][0]
			target['stats'] = ordereddict.OrderedDict()
			target['stats']['Size'] = blob.stats['n']
			target['stats']['Mean'] = blob.stats['mean']
			target['stats']['Std. Dev.'] = blob.stats['stddev']
			targets.append(target)
		return targets

	def findBlobs(self):
		self.logger.info('find blobs')
		border = self.settings['blobs border']
		blobsize = self.settings['blobs max size']
		maxblobs = self.settings['blobs max']
		self.hf.configure_blobs(border=border, maxblobsize=blobsize, maxblobs=maxblobs)
		self.hf.find_blobs()
		blobs = self.hf['blobs']
		targets = self.blobStatsTargets(blobs)
		self.logger.info('Number of blobs: %s' % (len(targets),))
		self.setTargets(targets, 'Blobs')

	def holeStatsTargets(self, holes):
		targets = []
		for hole in holes:

			mean = float(hole.stats['hole_mean'])
			tmean = self.icecalc.get_thickness(mean)
			std = float(hole.stats['hole_std'])
			tstd = self.icecalc.get_stdev_thickness(std, mean)

			target = {}
			target['x'] = hole.stats['center'][1]
			target['y'] = hole.stats['center'][0]
			target['stats'] = ordereddict.OrderedDict()
			target['stats']['Mean Intensity'] = mean
			target['stats']['Mean Thickness'] = tmean
			target['stats']['S.D. Intensity'] = std
			target['stats']['S.D. Thickness'] = tstd
			targets.append(target)
		return targets

	def fitLattice(self):
		self.logger.info('fit lattice')
		latspace = self.settings['lattice spacing']
		lattol = self.settings['lattice tolerance']

		self.hf.configure_lattice(spacing=latspace, tolerance=lattol)
		self.hf.blobs_to_lattice()
		self.logger.info('Number of lattice blobs: %s' % (len(self.hf['holes']),))
		self.latticeHoleStats()

	def latticeHoleStats(self):
		r = self.settings['lattice hole radius']
		i0 = self.settings['lattice zero thickness']
		self.icecalc.set_i0(i0)
		self.hf.configure_holestats(radius=r)
		self.hf.calc_holestats()
		holes = self.hf['holes']
		targets = self.holeStatsTargets(holes)
		self.setTargets(targets, 'Lattice')

	def ice(self):
		self.logger.info('limit thickness')
		i0 = self.settings['lattice zero thickness']
		tmin = self.settings['ice min mean']
		tmax = self.settings['ice max mean']
		tstd = self.settings['ice max std']
		self.hf.configure_ice(i0=i0,tmin=tmin,tmax=tmax,tstd=tstd)
		self.hf.calc_ice()
		goodholes = self.hf['holes2']
		centers = self.blobCenters(goodholes)
		allcenters = self.blobCenters(self.hf['holes'])

		focus_points = []

		## replace an acquisition target with a focus target
		onehole = self.settings['focus hole']
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
		# takes x,y instead of row,col
		if self.settings['target template']:
			newtargets = self.applyTargetTemplate(centers)
			acq_points = newtargets['acquisition']
			focus_points.extend(newtargets['focus'])
		else:
			acq_points = centers
		# need just one focus point
		focpoint = self.focus_on_hole(focus_points,focus_points)
		focus_points = [focpoint]

		self.setTargets(acq_points, 'acquisition', block=True)
		self.setTargets(focus_points, 'focus', block=True)
		self.logger.info('Acquisition Targets: %s' % (len(acq_points),))
		self.logger.info('Focus Targets: %s' % (len(focus_points),))
		if type(self.currentimagedata) == type(leginondata.AcquisitionImageData()):
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
			closest_dist = math.hypot(point[0]-cx,point[1]-cy)
			closest_point = point
			for point in bad:
				dist = math.hypot(point[0]-cx,point[1]-cy)
				if dist < closest_dist:
					closest_dist = dist
					closest_point = point
			return closest_point

		## now use a good hole for focus
		point = good[0]
		closest_dist = math.hypot(point[0]-cx,point[1]-cy)
		closest_point = point
		for point in good:
			dist = math.hypot(point[0]-cx,point[1]-cy)
			if dist < closest_dist:
				closest_dist = dist
				closest_point = point
		good.remove(closest_point)
		return closest_point

	def bypass(self):
		self.setTargets([], 'acquisition', block=True)
		self.setTargets([], 'focus', block=True)
		self.setTargets([], 'preview', block=True)

	def applyTargetTemplate(self, centers):
		self.logger.info('apply template')
		imshape = self.hf['original'].shape
		acq_vect = self.settings['acquisition template']
		foc_vect = self.settings['focus template']
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
				if self.settings['focus template thickness']:
					rad = self.settings['focus stats radius']
					tmin = self.settings['focus min mean thickness']
					tmax = self.settings['focus max mean thickness']
					tstd = self.settings['focus max stdev thickness']
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
			holestats = leginondata.HoleStatsData(session=self.session, prefs=prefs)
			holestats['row'] = stats['center'][0]
			holestats['column'] = stats['center'][1]
			holestats['mean'] = stats['hole_mean']
			holestats['stdev'] = stats['hole_std']
			holestats['thickness-mean'] = stats['thickness-mean']
			holestats['thickness-stdev'] = stats['thickness-stdev']
			holestats['good'] = stats['good']
			self.publish(holestats, database=True)

	def storeHoleFinderPrefsData(self, imagedata):
		hfprefs = leginondata.HoleFinderPrefsData()
		hfprefs.update({
			'session': self.session,
			'image': imagedata,
			'user-check': self.settings['user check'],
			'skip-auto': self.settings['skip'],
			'queue': self.settings['queue'],

			'edge-lpf-sigma': self.settings['edge lpf']['sigma'],
			'edge-filter-type': self.settings['edge type'],
			'edge-threshold': self.settings['edge threshold'],

			'template-rings': self.settings['template rings'],
			'template-correlation-type': self.settings['template type'],
			'template-lpf': self.settings['template lpf']['sigma'],

			'threshold-value': self.settings['threshold'],
			'blob-border': self.settings['blobs border'],
			'blob-max-number': self.settings['blobs max'],
			'blob-max-size': self.settings['blobs max size'],
			'lattice-spacing': self.settings['lattice spacing'],
			'lattice-tolerance': self.settings['lattice tolerance'],
			'stats-radius': self.settings['lattice hole radius'],
			'ice-zero-thickness': self.settings['lattice zero thickness'],

			'ice-min-thickness': self.settings['ice min mean'],
			'ice-max-thickness': self.settings['ice max mean'],
			'ice-max-stdev': self.settings['ice max std'],
			'template-on': self.settings['target template'],
			'template-focus': self.settings['focus template'],
			'template-acquisition': self.settings['acquisition template'],
		})

		self.publish(hfprefs, database=True)
		return hfprefs

	def findTargets(self, imdata, targetlist):
		self.setStatus('processing')
		autofailed = None

		## auto or not?
		self.hf['original'] = imdata['image']
		self.currentimagedata = imdata
		self.setImage(imdata['image'], 'Original')
		if not self.settings['skip']:
			autofailed = False
			try:
				self.everything()
			except Exception, e:
				self.logger.error('auto target finder failed: %s' % (e,))
				autofailed = True

		## user part
		if self.settings['user check'] or autofailed:
			while True:
				self.waitForUserCheck()
				ptargets = self.processPreviewTargets(imdata, targetlist)
				if not ptargets:
					break
				self.panel.targetsSubmitted()

		self.logger.info('Publishing targets...')
		### publish targets from goodholesimage
		self.publishTargets(imdata, 'focus', targetlist)
		self.publishTargets(imdata, 'acquisition', targetlist)
		self.setStatus('idle')

