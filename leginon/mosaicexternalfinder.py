import subprocess
import json
import os
import multiprocessing
import time
import math

from pyami import groupfun
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
		result_map = map(lambda x: pointInPolygon(x[1],x[0],b.vertices), points)
		if max(result_map):
			total += 1
			has_point[i] = True
			if total == total_points:
					break
	return has_point

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
		},
		'target multiple':1,
	}
	defaultsettings.update(mosaictarget_defaultsettings)
	# autofinder part is different
	auto_square_finder_defaultsettings = {
			'scoring script':'sq_finding.sh',
			'area-min': 100,
			'area-max': 10000,
	}
	defaultsettings.update(auto_square_finder_defaultsettings)
	eventoutputs = mosaictargetfinder.MosaicClickTargetFinder.eventoutputs
	targetnames = mosaictargetfinder.MosaicClickTargetFinder.targetnames

	def __init__(self, id, session, managerlocation, **kwargs):
		super(MosaicTargetFinderBase, self).__init__(id, session, managerlocation, **kwargs)
		self.start()
		self.ext_blobs ={}

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
			self.logger.info('running external square finding')
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
			self.logger.warning("external square finding did not run")
			self.ext_blobs[label] = []
			return
		f = open(outpath,'r')
		# returns one line
		line = f.readlines()[0]
		blob_dicts = json.loads(line)
		blobs = []
		def _revindex(value_tuple):
			return value_tuple[1],value_tuple[0]
		for n, b in enumerate(blob_dicts):
			#ptolemy write its coordinates in (col, row) modify them first.
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

	def setFilterSettings(self, example_blobs):
		if example_blobs:
			# use the stats of the example blobs
			sizes = map((lambda x: x.stats['n']), example_blobs)
			size_min = min(sizes)
			size_max = max(sizes)
			self.settings['area-min'] = size_min
			self.settings['area-max'] = size_max
			self.setSettings(self.settings, False)
			return
		pass

	def storeScoreSquareFinderPrefs(self):
		prefs = leginondata.ScoreSquareFinderPrefsData()
		prefs['image'] = self.mosaicimagedata
		prefs['area-min'] = self.settings['area-min']
		prefs['area-max'] = self.settings['area-max']
		self.publish(prefs, database=True)
		return prefs

	def filterStats(self, blobs):	
		'''
		filter based on blob stats
		'''
		self.sq_prefs = self.storeScoreSquareFinderPrefs()
		size_min = self.settings['area-min']
		size_max = self.settings['area-max']
		good_blobs = []
		for blob in blobs:
			row = blob.stats['center'][0]
			column = blob.stats['center'][1]
			size = blob.stats['n']
			mean = blob.stats['mean']
			score = blob.stats['score']
			if (size_min <= size <= size_max):
				good_blobs.append(blob)
			else:
				stats = leginondata.SquareStatsData(score_prefs=self.sq_prefs, row=row, column=column, mean=mean, size=size, score=score)
				stats['good'] = False
				# only publish bad stats
				self.publish(stats, database=True)
		self.logger.info('fitering number of blobs down number to %d' % len(good_blobs))
		return good_blobs

	def sampleBlobs(self, blobs, total_targets_need):
		'''
		first sort into three classes by size, and then take the top scorers
		to return.
		'''
		total_blobs = len(blobs)
		if total_blobs <= total_targets_need:
			# Nothing to do. Take all.
			return blobs
		n_class = self.settings['target grouping']['classes']
		index_groups = self.groupBlobsBySize(blobs, n_class)
		range_list = groupfun.calculateIndexRangesInClassEvenDistribution(total_targets_need, n_class)
		# number_of_samples_in_classes
		nsample_in_classes = map((lambda x: x[1]-x[0]), range_list)
		# final blobs sampled
		samples = []
		for c in range(n_class):
			# n of blobs to sample in the class
			nsample = nsample_in_classes[c]
			# sampled blobs
			sample_blobs_in_class = []
			# sampled blob indices
			sample_indices = []
			nblobs = len(index_groups[c])
			if nsample >= nblobs:
				blobs_in_class = map((lambda x: blobs[x]), index_groups[c])
				sample_indices = index_groups[c]
				if nsample > nblobs:
					self.logger.error('group should have more or equal nsample by area: (%d vs %d)' % (len(sample_blobs_in_class), nsample))
					nsample_in_classes[c+1] += nsample - nblobs
			else:
				sample_blobs_in_class, sample_indices = self._sampleByTopScorer(blobs, nsample, index_groups[c], c)
			samples.extend(sample_blobs_in_class)
		return samples

	def _sampleByTopScorer(self, blobs, nsample, indices, class_index):
		# use dictionary key sorting to get top scored blobs
		blob_indices_at_score_in_class = {}
		for i in indices:
			score = blobs[i].stats['score']
			if score not in blob_indices_at_score_in_class.keys():
				blob_indices_at_score_in_class[score] = []
			blob_indices_at_score_in_class[score].append(i)
		# sort the blobs by score in float
		keys = blob_indices_at_score_in_class.keys()
		keys.sort()
		keys.reverse()
		sample_blobs_in_class = []
		sample_indices = []
		for j, score in enumerate(keys):
			if len(sample_indices) >= nsample:
					break
			# there may be multiple blobs at the same score
			for i in blob_indices_at_score_in_class[score]:
				sample_blobs_in_class.append(blobs[i])
				sample_indices.append(i)
				if len(sample_indices) == nsample:
					break
		self.logger.info('score range sampled for blob area group %d: %.3f to %.3f' % (class_index+1, keys[0], keys[j]))
		return sample_blobs_in_class, sample_indices

class MosaicScoreTargetFinder(MosaicTargetFinderBase):
	panelclass = gui.wx.MosaicScoreTargetFinder.Panel
	settingsclass = leginondata.MosaicScoreTargetFinderSettingsData
	defaultsettings = dict(MosaicTargetFinderBase.defaultsettings)

	eventoutputs = mosaictargetfinder.MosaicClickTargetFinder.eventoutputs
	targetnames = mosaictargetfinder.MosaicClickTargetFinder.targetnames

	def __init__(self, id, session, managerlocation, **kwargs):
		super(MosaicScoreTargetFinder, self).__init__(id, session, managerlocation, **kwargs)
		self.tileblobmap = {}
		self.finder_blobs = []
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

	def createMosaicImage(self):
		super(MosaicScoreTargetFinder, self).createMosaicImage()
		if not self.hasValidScoringScript():
			return
		if self.mosaic and self.tileblobmap and self.finder_scale_factor:
			self.finder_blobs = []
			s = self.finder_scale_factor
			for imid, targetlists in self.targetmap.items():
					tile = self.tilemap[imid]
					shape = tile.image.shape
					label = '%d' % imid
					if label in self.ext_blobs.keys():
						self.tileblobmap[imid] = self.ext_blobs[label]
						self.addFinderBlobs(tile, imid)

	def addFinderBlobs(self, tile, imid):
					s = self.finder_scale_factor
					for b in self.tileblobmap[imid]:
						#statistics are calculated on finder_mosaic
						vertices = map((lambda x: self._tile2MosaicPosition(tile, (x[0]*s,x[1]*s), self.finder_mosaic)), b.vertices)
						r,c = self._tile2MosaicPosition(tile, b.stats['center'], self.finder_mosaic)
						new_info_dict = dict(b.info_dict)
						new_info_dict['vertices'] = list(vertices)
						# center of the blob on finder_mosaic coordinate
						# _tile2MosaicPosition standard is (row, col)
						new_info_dict['center'] = r,c
						self.finder_blobs.append(StatsBlob(new_info_dict, len(self.finder_blobs)))

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
		for imid in imids:
			self.p[imid].join()
			self.p[imid].terminate()
			self.p.pop(imid)
		new_imids = set(imids).difference(self.tileblobmap.keys())
		for imid in new_imids:
			label = '%d' % imid
			outpath = self.getOutPath(label)
			self.loadBlobs(label, outpath)
			self.tileblobmap[imid] = self.ext_blobs['%d' % imid]
			s = self.finder_scale_factor
			tile = self.tilemap[imid]
			self.addFinderBlobs(tile,imid)
		return list(self.finder_blobs)
