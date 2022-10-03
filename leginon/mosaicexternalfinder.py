import subprocess
import json
import os
import multiprocessing
import time
import math
import numpy

from pyami import groupfun, convexhull
from leginon import leginondata
from leginon import mosaictargetfinder
from leginon import targetfinder
import gui.wx.MosaicScoreTargetFinder

def pointInPolygon(x,y,poly):
	'''
	Ray tracing method from https://stackoverflow.com/questions/36399381/whats-the-fastest-way-of-checking-if-a-point-is-inside-a-polygon-in-python
	'''
	n = len(poly)
	inside = False
	p1x,p1y = poly[0]
	for i in range(n+1):
		p2x,p2y = poly[i % n] #even ?
		if y > min(p1y,p2y):
			if y <= max(p1y,p2y):
				if x <= max(p1x,p2x):
					if p1y != p2y:
						# x intercept
						xints = (y-p1y)*(p2x-p1x)/(p2y-p1y)+p1x
					if p1x == p2x or x <= xints:
						inside = not inside
		p1x,p1y = p2x,p2y
	return inside

def pointsInBlobs(blobs, points):
	if len(blobs) == 0:
		return []
	has_point =  map((lambda x: False), blobs)
	if len(points) == 0:
		return has_point
	total_points = len(points)
	total = 0
	for i, b in enumerate(blobs):
		result_map = map(lambda x: pointInPolygon(x[0],x[1],b.vertices), points)
		if max(result_map):
			total += 1
			has_point[i] = True
			if total == total_points:
					break
	return has_point

def getDistanceArray(centers):
	'''
	using array math to get a square of distance matrix between all pairs of centers.
	'''
	s = len(centers)
	#create repeating 2D array
	x = numpy.repeat(centers[:,0],s).reshape((s,s))
	y = numpy.repeat(centers[:,1],s).reshape((s,s))
	# use transposed array to calculate square of distance.
	a = (x-x.T)**2+(y-y.T)**2
	return a

class StatsBlob(object):
	def __init__(self, info_dict, index):
		'''Simple blob object with image and stats as attribute
			both input and output center/vertices = (row, col) on image
		'''
		mean = info_dict['brightness']
		stddev = 1.0
		size = info_dict['area']
		score = info_dict['score']
		center = info_dict['center'][0],info_dict['center'][1]
		vertices = info_dict['vertices']
		self.center_modified = False
		# n in blob is the same as size from Ptolemy. Need n for displaying stats
		# in gui.
		self.stats = {"label_index": index, "center":center, "n":size, "size":size, "mean":mean, "score":score}
		self.vertices = vertices
		self.info_dict = info_dict

class MosaicTargetFinderBase(mosaictargetfinder.MosaicClickTargetFinder):
	panelclass = gui.wx.MosaicScoreTargetFinder.Panel
	settingsclass = leginondata.MosaicScoreTargetFinderSettingsData
	defaultsettings = dict(targetfinder.ClickTargetFinder.defaultsettings)
	# same as MosaicClickTargetFinder
	mosaictarget_defaultsettings = {
		# unlike other targetfinders, no wait is default
		'wait for done': False,
		#'no resubmit': True,
		# maybe not
		'calibration parameter': 'stage position',
		'scale image': True,
		'scale size': 512,
		'create on tile change': 'all',
		'target grouping': {
			'total targets': 10,
			'classes': 1,
			'group method': 'value delta',
		},
		'target multiple':1,
	}
	defaultsettings.update(mosaictarget_defaultsettings)
	# autofinder part is different
	auto_square_finder_defaultsettings = {
			'scoring script':'sq_finding.sh',
			'filter-min': 100,
			'filter-max': 10000,
			'filter-key': 'Size',
	}
	defaultsettings.update(auto_square_finder_defaultsettings)
	eventoutputs = mosaictargetfinder.MosaicClickTargetFinder.eventoutputs
	targetnames = mosaictargetfinder.MosaicClickTargetFinder.targetnames

	def __init__(self, id, session, managerlocation, **kwargs):
		super(MosaicTargetFinderBase, self).__init__(id, session, managerlocation, **kwargs)
		self.ext_blobs ={}
		self.start()

	def hasValidScoringScript(self):
		scoring_script = self.settings['scoring script']
		if not os.path.isfile(scoring_script):
			if self.script_exists == False:
				#log error just once.
				return
			else:
				self.script_exists = False
				self.logger.error('Scoring script %s does not exist.' % scoring_script)
				return
		else:
			self.script_exists = True
		return self.script_exists

	def findSquareBlobs(self):
		"""
		Get blobs at finder scale with stats. In this case, make finder-size mosaic
		mrc image, run scoring script, and then load the resulting blobs.
		"""
		# Scale to smaller finder size
		# TODO where did this call to ?
		if not self.hasValidScoringScript():
			self.logger.error('Failed square finding without scoring script')
			self.script_exists = None #reset
			return []
		self.scaleFinderMosaicImage()
		if self.mosaicimagedata and 'filename' in self.mosaicimagedata.keys():
			label='all'
			mosaic_image_path = os.path.join(self.session['image path'],self.mosaicimagedata['filename']+'.mrc')
			self.logger.info('Running external square finding')
			blobs = self._runExternalBlobFinder(self.mosaicimagedata['image'],mosaic_image_path, label)
			self.loadBlobs(label, self.getOutPath(label))
			# show blob target and stats
			return self.ext_blobs[label]
		return []

	def getOutPath(self, label):
		job_basename = self.getJobBasename(label)
		outpath = os.path.join(self.session['image path'],'%s.json' % job_basename)
		return outpath

	def getJobBasename(self, label):
		'''
		JobBasename is used as cluster job name (extension job) in sq_finding.sh
		and output file name (extension json)
		'''
		return '%s_%s' % (self.session['name'], label)

	def _runExternalBlobFinder(self, imagearray, mosaic_image_path,label='all'):
		outdir = os.path.dirname(mosaic_image_path)
		job_basename = self.getJobBasename(label)
		outpath = os.path.join(outdir, '%s.json' % job_basename)
		if os.path.isfile(outpath):
			os.remove(outpath)
		# This process must create the output '%s.json' % job_basename at outpath
		scoring_script = self.settings['scoring script']
		cmd = 'source %s %s %s %s' % (scoring_script, job_basename, mosaic_image_path, outdir)
		proc = subprocess.Popen(cmd, shell=True)
		proc.wait()

	def loadBlobs(self, label, outpath):
		'''
		load target locations and score as StatsBlob
		'''
		if not os.path.isfile(outpath):
			self.logger.warning("External square finding did not run")
			self.ext_blobs[label] = []
			return
		try:
			f = open(outpath,'r')
			# returns one line
			line = f.readlines()[0]
			f.close()
		except IndexError:
			# empty file means no blob found
			self.ext_blobs[label] = []
			return
		except Exception as e:
			# probably access error
			self.logger.error("Square finder read error: %s" % e)
			self.ext_blobs[label] = []
			return
		blob_dicts = json.loads(line)
		blobs = []
		def _revindex(value_tuple):
			return value_tuple[1],value_tuple[0]
		for n, b in enumerate(blob_dicts):
			#ptolemy write its coordinates in (x,y) modify them first.
			b['center'] = _revindex(b['center'])
			b['vertices'] = list(map((lambda x: _revindex(x)),b['vertices']))
			blobs.append(StatsBlob(b, n)) # (row, col)
		self.ext_blobs[label] = blobs

	def filterPoints(self, blobs, example_points, panel_points):
		'''
		Return boolean for each blob.
		has_priority: at least one example_point is in the blob
		to_avoid: at least one panel_point is in the blob
		display_array: some image array to display in the gui as Thresholded image.
		'''
		return self.filterPointsByVertices(self.finder_blobs, example_points, panel_points)

	def filterPointsByVertices(self, blobs, example_points, panel_points):
		has_priority = pointsInBlobs(blobs, example_points)
		to_avoid = pointsInBlobs(blobs, panel_points)
		return has_priority, to_avoid, None

	def _mapBlobStatsKey(self, key):
		return key.lower()

	def setFilterSettings(self, example_blobs):
		if example_blobs:
			# use the stats of the example blobs
			settings_key = self._mapBlobStatsKey(self.settings['filter-key'])
			if settings_key in example_blobs[0].stats.keys():
				sizes = map((lambda x: x.stats[settings_key]), example_blobs)
				size_min = min(sizes)
				size_max = max(sizes)
				self.settings['filter-min'] = size_min
				self.settings['filter-max'] = size_max
				self.setSettings(self.settings, False)
				return
			else:
				self.logger.error('Filter key %s not found in stats' % self.settings['filter-key'])

	def storeScoreSquareFinderPrefs(self):
		prefs = leginondata.ScoreSquareFinderPrefsData()
		prefs['image'] = self.mosaicimagedata
		prefs['filter-min'] = self.settings['filter-min']
		prefs['filter-max'] = self.settings['filter-max']
		prefs['filter-key'] = self.settings['filter-key']
		self.publish(prefs, database=True)
		return prefs

	def filterStats(self, blobs):	
		'''
		filter based on blob stats
		'''
		self.sq_prefs = self.storeScoreSquareFinderPrefs()
		value_min = self.settings['filter-min']
		value_max = self.settings['filter-max']
		key = self._mapBlobStatsKey(self.settings['filter-key'])
		good_blobs = []
		for i, blob in enumerate(blobs):
			if i == 0 and key not in blob.stats.keys():
				self.logger.error('Filter key %s not found in stats' % self.settings['filter-key'])
				return good_blobs
			row = blob.stats['center'][0]
			column = blob.stats['center'][1]
			size = blob.stats['n']
			mean = blob.stats['mean']
			score = blob.stats['score']
			if (value_min <= blob.stats[key] <= value_max):
				good_blobs.append(blob)
			else:
				stats = leginondata.SquareStatsData(score_prefs=self.sq_prefs, row=row, column=column, mean=mean, size=size, score=score)
				stats['good'] = False
				# only publish bad stats
				self.publish(stats, database=True)
		self.logger.info('Filtering number of blobs down number to %d' % len(good_blobs))
		return good_blobs

	def _getGrouperValueMinMax(self):
		value_min = self.settings['filter-min']
		value_max = self.settings['filter-max']
		return value_min, value_max

	def _setSampler(self, grouper, total_target_need):
		return groupfun.BlobTopScoreSampler(grouper, total_target_need, self.logger)

	def _getBlobStatsKeyForGrouping(self):
		return self.settings['filter-key'].lower()

	def _getIndexRangeByValueClass(self, codes, n_class,s):
		value_min = self.settings['filter-min']*s
		value_max = self.settings['filter-max']*s
		return groupfun.calculateIndexRangesInClassValue(codes, n_class, value_min, value_max)

class MosaicScoreTargetFinder(MosaicTargetFinderBase):
	"""
	External script score finder that operates on individual grid atlas tile.  Multithread
	process is added when each tile is added, and then loaded later. 
	"""
	panelclass = gui.wx.MosaicScoreTargetFinder.Panel
	settingsclass = leginondata.MosaicScoreTargetFinderSettingsData
	defaultsettings = dict(MosaicTargetFinderBase.defaultsettings)

	eventoutputs = mosaictargetfinder.MosaicClickTargetFinder.eventoutputs
	targetnames = mosaictargetfinder.MosaicClickTargetFinder.targetnames

	def __init__(self, id, session, managerlocation, **kwargs):
		super(MosaicScoreTargetFinder, self).__init__(id, session, managerlocation, **kwargs)
		self.tileblobmap = {}
		self.finder_blobs = []
		self.mblob_values = []
		self.start()
		self.p = {}
		self.script_exists = None

	def _addTile(self, imagedata):
		super(MosaicScoreTargetFinder, self)._addTile(imagedata)
		if not self.hasValidScoringScript():
			return
		mrcpath = os.path.join(imagedata['session']['image path'], imagedata['filename']+'.mrc')
		imid = imagedata.dbid
		label = '%d' % imid
		self.logger.info('running external square finding on imgid=%d' % imid)
		job_basename = self.getJobBasename(label)
		self.p[imid] = multiprocessing.Process(target=self._runExternalBlobFinder, args=(imagedata['image'], mrcpath,label))
		self.p[imid].start()

	def clearTiles(self):
		super(MosaicScoreTargetFinder, self).clearTiles()
		self.tileblobmap = {}
		self.finder_blobs = []
		self.mblob_values = []
		self.ext_blobs = {}
		self.p = {}

	def getMergingDistance(self, sizes, means):
		if len(sizes) == 0:
			return 10000.0
		size_array = numpy.array(sizes)
		mean_array = numpy.array(means)
		# accept blobs excluding very dark ones works except when the whole
		# grid is thick.
		top_mean = numpy.percentile(mean_array, 10)
		filtered_size_array = size_array[numpy.where(mean_array >= top_mean)]
		# use the size at top 90 percentile since the max may be torn squares.
		top_size = numpy.percentile(filtered_size_array,90)
		max_length = math.sqrt(top_size)
		# calculate length displayed on finder_mosaic
		some_imid = list(self.tilemap.keys())[0]
		tile = self.tilemap[some_imid]
		# map two positions on tile to that of finder_posaic
		r0,c0 = self._tile2MosaicPosition(tile, (0,0), self.finder_mosaic)
		r,c = self._tile2MosaicPosition(tile, (max_length,0), self.finder_mosaic)
		self.logger.info('Merging distance on mosaic = %.1f' % (float(r-r0),))
		return r-r0

	def mergeFinderBlobs(self):
		blob_values = self.mblob_values
		if len(self.tilemap) > 2 and len(blob_values) >= 10:
			self.logger.info('Running blob merging')
			self._mergeFinderBlobs()
		# create finder_blobs
		self.finder_blobs = []
		for info_dict in self.mblob_values:
			c = info_dict['center']
			info_dict['center'] = int(c[0]), int(c[1])
			self.finder_blobs.append(StatsBlob(info_dict, len(self.finder_blobs)))

	def _mergeFinderBlobs(self):
		'''
		Merging blobs based on distance on finder_mosaic.
		'''
		blob_values = self.mblob_values
		centers = numpy.array(map((lambda x: x['center']), blob_values))
		sizes = map((lambda x: x['area']), blob_values )
		means = map((lambda x: x['brightness']), blob_values )
		max_distance = self.getMergingDistance(sizes, means)
		# distance
		d_array = getDistanceArray(centers)
		max_d2 = max_distance*max_distance
		too_close = numpy.where(d_array < max_d2, 1,0).nonzero()
		# exclude the symmetrical distance and distance to self.
		c = numpy.array(too_close[1]-too_close[0])
		unique_close = numpy.where(c > 0, 1,0).nonzero()[0]
		# update values of the second blob
		to_remove = []
		for i in unique_close:
			first = too_close[0][i]
			second = too_close[1][i]
			to_remove.append(first)
			b1 = blob_values[first]['brightness']
			b2 = blob_values[second]['brightness']
			w1 = blob_values[first]['area']
			w2 = blob_values[second]['area']
			c1 = centers[first]
			c2 = centers[second]
			new_area = w1+w2
			new_brightness = (b1*w1+b2*w2)/(w1+w2)
			new_center = tuple(((c1*w1+c2*w2)/(w1+w2)).tolist())
			new_score = max(blob_values[first]['score'],blob_values[second]['score'])
			# merge vertices as convex hull
			# use union set to avoid duplicates
			v = set(blob_values[first]['vertices'])
			v.union(blob_values[second]['vertices'])
			new_vertices = convexhull.convexHull(list(v))
			# update
			self.mblob_values[second].update({
					'area':new_area,
					'center':new_center,
					'score':new_score,
					'brightness':new_brightness,
					'vertices':new_vertices
			})
		# pop merged
		to_remove = list(set(to_remove))
		to_remove.sort()
		to_remove.reverse()
		self.logger.info('%d blobs were merged to others' % len(to_remove))
		for i in to_remove:
			self.mblob_values.pop(i)

	def createMosaicImage(self, is_final=True):
		super(MosaicScoreTargetFinder, self).createMosaicImage(is_final)
		if not self.hasValidScoringScript() or not is_final:
			return
		if self.mosaic and self.tileblobmap and self.finder_scale_factor:
			self.finder_blobs = []
			self.mblob_values = []
			s = self.finder_scale_factor
			for imid, targetlists in self.targetmap.items():
					tile = self.tilemap[imid]
					shape = tile.image.shape
					label = '%d' % imid
					if label in self.ext_blobs.keys():
						self.tileblobmap[imid] = self.ext_blobs[label]
						self.addMosaicBlobValues(tile, imid)
			# merge finder blobs
			self.mergeFinderBlobs()

	def addMosaicBlobValues(self, tile, imid):
		s = self.finder_scale_factor
		for b in self.tileblobmap[imid]:
			#statistics are calculated on finder_mosaic
			vertices = map((lambda x: self._tile2MosaicPosition(tile, (x[0],x[1]), self.finder_mosaic)), b.vertices)
			r,c = self._tile2MosaicPosition(tile, (b.stats['center'][0],b.stats['center'][1]), self.finder_mosaic)
			new_info_dict = dict(b.info_dict)
			new_info_dict['vertices'] = list(vertices)
			# center of the blob on finder_mosaic coordinate
			# _tile2MosaicPosition standard is (row, col)
			new_info_dict['center'] = r,c
			self.mblob_values.append(new_info_dict)

	def findSquareBlobs(self):
		"""
		Get blobs at finder scale with stats. In this case load the
		blobs found during _addTile
		"""
		if self.script_exists == False:
			self.logger.error('You must reload the atlas if you have changed the script path')
			return []
		if not self.hasValidScoringScript():
			self.logger.error('Failed square finding without scoring script')
			self.script_exists = None #reset
			return []
		imids = list(map((lambda x: int(x)),self.p.keys()))
		# gather subprocesses
		self.logger.info('Gathering finder results')
		for imid in imids:
			self.p[imid].join()
			self.p[imid].terminate()
			self.p.pop(imid)
		self.logger.info('All scripts finished')
		new_imids = set(imids).difference(self.tileblobmap.keys())
		for imid in new_imids:
			label = '%d' % imid
			outpath = self.getOutPath(label)
			self.loadBlobs(label, outpath)
			self.tileblobmap[imid] = self.ext_blobs['%d' % imid]
			tile = self.tilemap[imid]
			self.addMosaicBlobValues(tile,imid)
		# merge finder blobs
		self.mergeFinderBlobs()
		return list(self.finder_blobs)
