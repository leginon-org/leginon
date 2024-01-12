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
from leginon import statssquare
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

class MosaicTargetFinderBase(mosaictargetfinder.MosaicClickTargetFinder):
	panelclass = gui.wx.MosaicScoreTargetFinder.Panel
	settingsclass = leginondata.MosaicScoreTargetFinderSettingsData
	defaultsettings = dict(targetfinder.ClickTargetFinder.defaultsettings)
	# same as MosaicClickTargetFinder
	mosaictarget_defaultsettings = dict(mosaictargetfinder.MosaicClickTargetFinder.mosaictarget_defaultsettings)
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
			blobs = self._runExternalBlobFinder(mosaic_image_path, label)
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

	def _runExternalBlobFinder(self, mosaic_image_path,label='all'):
		outdir = os.path.dirname(mosaic_image_path)
		job_basename = self.getJobBasename(label)
		outpath = os.path.join(outdir, '%s.json' % job_basename)
		if os.path.isfile(outpath):
			os.remove(outpath)
		# This process must create the output '%s.json' % job_basename at outpath
		scoring_script = self.settings['scoring script']
		shell_source = '/bin/bash'
		if scoring_script.endswith('csh'):
			shell_source = '/bin/csh'
		cmd = 'source %s %s %s %s' % (scoring_script, job_basename, mosaic_image_path, outdir)
		proc = subprocess.Popen(cmd, shell=True, executable=shell_source)
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
			b['tile_image'] = self._getTileImage(label)
			b['squares'] = []
			blobs.append(statssquare.StatsBlob(b, n)) # (row, col)
		self.ext_blobs[label] = blobs

	def _getTileImage(label):
		'''
		full mosaic has no tile image id. Tile based one should overwrite this.
		'''
		return None

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
			squares = blob.squares
			tile_image = blob.tile_image
			edge_mosaic_shape = self.finder_edge_mosaicimage.shape
			try:
				on_edge = self.finder_edge_mosaicimage[row,column]
			except Exception as e:
				self.logger.debug('edge filtering error: %s' % e)
				on_edge = True
			if (value_min <= blob.stats[key] <= value_max) and not on_edge:
				good_blobs.append(blob)
				is_good = True
			else:
				is_good = False
			# publish all square stats
			stats = leginondata.SquareStatsData(session=self.session, score_prefs=self.sq_prefs, row=row, column=column, mean=mean, size=size, score=score, tile_image=tile_image)
			stats['good'] = False
			stats['on_edge'] = on_edge
			stats.insert()
			# link SquareStatsData with PtolemySquareData if available
			for sq in squares:
				sqdata = leginondata.PtolemySquareData().direct_query(sq)
				q = leginondata.PtolemySquareStatsLinkData(stats=stats, ptolemy=sqdata)
				q.insert()
				# add to score history
				q_score = leginondata.PtolemyScoreHistoryData(session=self.session, list=self.mosaicimagelist['targets'], square=sqdata, score=stats['score'],set_number=1)
				q_score.insert()
		self.logger.info('Filtering number of blobs down number to %d' % len(good_blobs))
		return good_blobs

	def _getGrouperValueMinMax(self):
		value_min = self.settings['filter-min']
		value_max = self.settings['filter-max']
		return value_min, value_max

	def _setSampler(self, grouper, total_target_need,randomize_blobs):
		return groupfun.BlobTopScoreSampler(grouper, total_target_need, self.logger,randomize_blobs)

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
		self.p[imid] = multiprocessing.Process(target=self._runExternalBlobFinder, args=(mrcpath,label))
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
		'''
		Merge small and nearby blobs on finder_mosaic
		'''
		blob_values = self.mblob_values
		if len(self.tilemap) > 2 and len(blob_values) >= 10:
			self.logger.info('Running blob merging')
			self._mergeFinderBlobs()
		# create finder_blobs
		self.finder_blobs = []
		for info_dict in self.mblob_values:
			c = info_dict['center']
			info_dict['center'] = int(c[0]), int(c[1])
			self.finder_blobs.append(statssquare.StatsBlob(info_dict, len(self.finder_blobs)))

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
			j0 = too_close[0][i]
			j1 = too_close[1][i]
			bj0 = blob_values[j0]['brightness']
			bj1 = blob_values[j1]['brightness']
			cj0 = centers[j0]
			cj1 = centers[j1]
			wj0 = blob_values[j0]['area']
			wj1 = blob_values[j1]['area']
			if self.settings['simpleblobmerge']: #just keep the one with the larger area * brightness
				signal1 = bj0 * wj0
				signal2 = bj1 * wj1
				if (signal1 < signal2):
					to_remove.append(j0)
				else:
					to_remove.append(j1)
			else:
				new_center = tuple(((cj0*wj0+cj1*wj1)/(wj0+wj1)).tolist()) # (row, col)
				# decide which one to remove
				j0image, drow0, dcol0 = self._mosaicToTargetOnMosaic(cj0[0], cj0[1], self.finder_mosaic)
				j1image, drow1, dcol1 = self._mosaicToTargetOnMosaic(cj1[0], cj1[1], self.finder_mosaic)
				merged_image, drow, dcol = self._mosaicToTargetOnMosaic(new_center[0], new_center[1], self.finder_mosaic)
				# keep the blob on tile where the new_center belongs to.
				# BUG: ocassionally this still gives different tile assignment
				# than the full-size mosaic due to rounding error, but it is close enough.
				if j1image.dbid == merged_image.dbid:
					j_remove = j0
					j_keep = j1
				else:
					j_remove = j1
					j_keep = j0
					self.logger.debug('keep merged center on %d' % j0image.dbid)
				to_remove.append(j_remove)
				b1 = blob_values[j_remove]['brightness']
				b2 = blob_values[j_keep]['brightness']
				w1 = blob_values[j_remove]['area']
				w2 = blob_values[j_keep]['area']
				c1 = centers[j_remove]
				c2 = centers[j_keep]
				new_area = w1+w2
				new_brightness = (b1*w1+b2*w2)/(w1+w2)
				new_score = max(blob_values[j_remove]['score'],blob_values[j_keep]['score'])
				new_squares = list(blob_values[j_remove]['squares'])
				new_squares.extend(blob_values[j_keep]['squares'])
				# merge vertices as convex hull
				# use union set to avoid duplicates
				v = set(blob_values[j_remove]['vertices'])
				v.union(blob_values[j_keep]['vertices'])
				new_vertices = convexhull.convexHull(list(v))
				# update
				self.mblob_values[j_keep].update({
						'area':new_area,
						'center':new_center,
						'score':new_score,
						'brightness':new_brightness,
						'vertices':new_vertices,
						'squares':new_squares,
				})
		# pop merged
		to_remove = list(set(to_remove))
		to_remove.sort()
		to_remove.reverse()
		self.logger.info('%d blobs were merged to others' % len(to_remove))
		for i in to_remove:
			self.mblob_values.pop(i)

	def createMosaicImage(self, is_final=True):
		'''
		Create mosaic image of each tile adding/loading.
		'''
		super(MosaicScoreTargetFinder, self).createMosaicImage(is_final)
		if not self.hasValidScoringScript() or not is_final:
			return
		# first time this function is call self.tileblobmap is empty
		if self.mosaic and self.tileblobmap and self.finder_scale_factor:
			self.finder_blobs = []
			self.mblob_values = []
			s = self.finder_scale_factor
			for imid, targetlists in self.targetmap.items():
					tile = self.tilemap[imid]
					shape = tile.image.shape
					label = '%d' % imid
					if label in self.ext_blobs.keys():
						# tileblobmap holds StatsBlobs on tile image
						self.tileblobmap[imid] = self.ext_blobs[label]
						# mblob_values holds blobinof on mosaic image
						self.addMosaicBlobValues(tile, imid)
			# merge finder blobs
			self.mergeFinderBlobs()

	def addMosaicBlobValues(self, tile, imid):
		'''
		Mosaic blobs are blobs on self.finder_mosaic
		'''
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
			new_info_dict['signal'] = new_info_dict['area'] * new_info_dict['brightness']  
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

	def _getTileImage(self, label):
		'''
		PerTileSquareFinder label is tile image id
		'''
		return leginondata.AcquisitionImageData().direct_query(int(label))
