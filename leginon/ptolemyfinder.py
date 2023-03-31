#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright under
#       Apache License, Version 2.0
#       For terms of the license agreement
#       see  http://leginon.org
#

from leginon import leginondata
from leginon import icetargetfinder
from leginon import scorefinder
from leginon import ptolemyfinderback
from leginon import ptolemyhandler as ph

import math
import gui.wx.PtolemyMmTargetFinder

class PtolemyMmTargetFinder(scorefinder.ScoreTargetFinder):
	panelclass = gui.wx.PtolemyMmTargetFinder.Panel
	settingsclass = leginondata.PtolemyMmTargetFinderSettingsData
	defaultsettings = dict(icetargetfinder.IceTargetFinder.defaultsettings)
	defaultsettings.update({
				'score key':'score',
				'score threshold':0,
	})
	targetnames = scorefinder.ScoreTargetFinder.targetnames

	def __init__(self, id, session, managerlocation, **kwargs):
		scorefinder.ScoreTargetFinder.__init__(self, id, session, managerlocation, **kwargs)
		self.hf = ptolemyfinderback.HoleFinder()
		self.hf.logger = self.logger
		self.ptolemy_square = None

		self.start()

	def processImageData(self, imagedata):
		try:
			self.ptolemy_square = ph.get_ptolemy_square(imagedata)
		except Exception as e:
			self.logger.error(e)
			self.ptolemy_square = None
		super(PtolemyMmTargetFinder, self).processImageData(imagedata)

	def _getStatsKeys(self):
		return [self.settings['score key'],]

	def hasValidScoringServer(self):
		r = requests.get(ph.BASEURL)
		if not r.ok:
			return True
		else:
			self.logger.error('url %s not accessible.' % ph.BASEURL)
			return

	def _findHoles(self):
		'''
		configure and run holefinder in the back module. Raise exception
		to the higher level to handle.
		'''
		# TODO rename script to server address or something
		if not self.currentimagedata:
			raise RuntimeError('Need image to find holes')
		if 'target' not in self.currentimagedata.keys():
			raise RuntimeError('Need imagedata from ptolemy square finder to find holes')
		threshold = self.settings['score threshold']
		# configure and run
		# configure ice i0 before holefinder as required by ptolemy
		i0 = self.settings['lattice zero thickness']
		self.hf.configure_ice(i0=i0)
		#
		self.hf.configure_holefinder(imagedata=self.currentimagedata, score_key=self.settings['score key'], threshold=threshold)
		try:
			self.hf.run_holefinder()
		except ptolemyfinderback.ScoreResultMissingError as e:
			self.logger.warning(e)
		except Exception:
			raise
		return

	def _getScriptPref(self):
		'''
		Return what goes into ScoreTargetFinderPrefsData under script field
		'''
		return ph.BASEURL

	def storeHoleStatsData(self, score_prefs, input_name='holes'):
		holes = self.hf[input_name]
		for hole in holes:
			# ptolemy active learning record
			phole = leginondata.PtolemyHoleData(session=self.session, square=self.ptolemy_square, hole_id=hole.info_dict['hole_id'], image=self.currentimagedata)
			phole['center_x']=hole.info_dict['center'][1]
			phole['center_y']=hole.info_dict['center'][0]
			phole.insert()
			# stats
			stats = hole.stats
			holestats = leginondata.HoleStatsData(session=self.session)
			holestats['finder-type'] = 'score'
			holestats['score'] = stats[self.settings['score key']]
			holestats['score-prefs'] = score_prefs
			# IceTargetFinder HoleStats
			holestats['row'] = stats['center'][0] * self.shrink_factor + self.shrink_offset[0]
			holestats['column'] = stats['center'][1] * self.shrink_factor + self.shrink_offset[1]
			holestats['mean'] = stats['hole_mean']
			holestats['stdev'] = stats['hole_std']
			holestats['thickness-mean'] = stats['thickness-mean']
			holestats['thickness-stdev'] = stats['thickness-stdev']
			holestats['good'] = stats['good']
			holestats['hole-number'] = stats['hole_number']
			holestats['convolved'] = stats['convolved']
			holestats['ptolemy'] = phole
			self.publish(holestats, database=True)

	def researchHoleWithStats(self, imagedata, row, col):
		'''
		Use row and col from image and HoleStatsData to find PtolemyHoleData
		'''
		if 'target' not in imagedata:
			self.logger.error('Test image results can not give feed back to ptolemy')
			return None
		pref_q = leginondata.ScoreTargetFinderPrefsData(image=imagedata)
		q = leginondata.HoleStatsData(column=col, row=row)
		q['score-prefs']=pref_q
		results = q.query(results=1)
		if not results:
			return self.findNearestHole(pref_q, row, col)
		return results[0]['ptolemy']

	def findNearestHole(self, prefdata, row, col):
		stats = leginondata.HoleStatsData()
		stats['score-prefs'].query()
		if not stats:
			self.logger.error('no holes found by Ptolemy')
			return None
		magnitudes = map((lambda x: (col-x['column'])**2+(row-x['row'])**2), stats)
		nearest_index =  magnitudes.index(min(magnitudes))
		nearest = stats[magnitudes.index(min(magnitudes))]['ptolemy']
		return nearest

	def newTargetForImage(self, imagedata, drow, dcol, fortile=False, **kwargs):
		"""
		make new target on image. ptolemy_hole is added here.
		"""
		kwargs['ptolemy_hole'] = None
		if 'type' in kwargs and kwargs['type'] == 'acquisition':
			imageshape = imagedata.imageshape()
			half = (imageshape[0]//2,imageshape[1]//2)
			row = half[0]+drow
			col = half[1]+dcol
			ptolemy_hole = self.researchHoleWithStats(imagedata, row, col)
			kwargs['ptolemy_hole'] = ptolemy_hole
		return super(PtolemyMmTargetFinder, self).newTargetForImage(imagedata, drow, dcol, fortile, **kwargs)
