#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright under
#       Apache License, Version 2.0
#       For terms of the license agreement
#       see  http://leginon.org
#

from leginon import leginondata
import targetfinder
import icetargetfinder
import scorefinderback
from pyami import ordereddict
import threading
import ice
import instrument
import os.path
import math
import gui.wx.ScoreTargetFinder
import version
import itertools

invsqrt2 = math.sqrt(2.0)/2.0

class ScoreTargetFinder(icetargetfinder.IceTargetFinder):
	panelclass = gui.wx.ScoreTargetFinder.Panel
	settingsclass = leginondata.ScoreTargetFinderSettingsData
	defaultsettings = dict(icetargetfinder.IceTargetFinder.defaultsettings)
	defaultsettings.update({
				'script':'hole_finding.sh',
				'score key':'score',
				'score threshold':0,
	})
	targetnames = icetargetfinder.IceTargetFinder.targetnames

	def __init__(self, id, session, managerlocation, **kwargs):
		icetargetfinder.IceTargetFinder.__init__(self, id, session, managerlocation, **kwargs)
		self.hf = scorefinderback.HoleFinder()
		self.hf.logger = self.logger

		self.start()

	def _getStatsKeys(self):
		return [self.settings['score key'],]

	def _findHoles(self):
		'''
		configure and run holefinder in the back module. Raise exception
		to the higher level to handle.
		'''
		# shell script
		script = self.settings['script']
		if not os.path.exists(script):
			raise ValueError('shell script %s does not exists' % script)
		name = '_'.join(self.name.split(' '))
		job_name = '%s_%s' % (self.session['name'],name)
		# input mrc image filepath
		if self.currentimagedata:
			mrc_path = os.path.join(self.session['image path'],self.currentimagedata['filename']+'.mrc')
			if not os.path.exists(mrc_path):
				self.logger.warning('writing missing mrc file to %s' % mrc_path)
				from pyami import mrc
				mrc.write(self.currentimagedata['image'],mrc_path)
		else:
			raise RuntimeError('Need image to find holes')
		threshold = self.settings['score threshold']
		# configure and run
		self.hf.configure_holefinder(script, job_name, mrc_path, out_dir=self.session['image path'], score_key=self.settings['score key'], threshold=threshold)
		try:
			self.hf.run_holefinder()
		except scorefinderback.ScoreResultMissingError as e:
			self.logger.warning(e)
		except Exception:
			raise
		return

	def storeHoleStatsData(self, score_prefs, input_name='holes'):
		holes = self.hf[input_name]
		for hole in holes:
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
			self.publish(holestats, database=True)

	def _getScriptPref(self):
		return self.settings['script']

	def storeHoleFinderPrefsData(self, imagedata):
		hfprefs = leginondata.ScoreTargetFinderPrefsData()
		hfprefs.update({
			'session': self.session,
			'image': imagedata,
			'user-check': self.settings['user check'],
			'skip-auto': self.settings['skip'],
			'queue': self.settings['queue'],

			'stats-radius': self.settings['lattice hole radius'],
			'ice-zero-thickness': self.settings['lattice zero thickness'],

			'ice-min-thickness': self.settings['ice min mean'],
			'ice-max-thickness': self.settings['ice max mean'],
			'ice-max-stdev': self.settings['ice max std'],
			'ice-min-stdev': self.settings['ice min std'],
			'template-on': self.settings['target template'],
			'template-focus': self.settings['focus template'],
			'template-acquisition': self.settings['acquisition template'],
			'script': self._getScriptPref(),
			'score-key': self.settings['score key'],
			'score-threshold':self.settings['score threshold'],
			'filter-ice-on-convolved-on': self.settings['filter ice on convolved'],
		})

		self.publish(hfprefs, database=True)
		return hfprefs
