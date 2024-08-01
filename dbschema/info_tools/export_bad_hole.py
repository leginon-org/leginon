#!/usr/bin/env python
import os
from leginon import leginondata, projectdata, calibrationclient
from sinedon import directq
import pyami.fileutil
import pyami.jpg
from pyami import mrc
from dbschema.info_tools import export_targets

PRESET_PIXEL_SIZE_MAX = 5e-10 #meters
MIN_NUMBER_OF_IMAGES_AT_PRESET = 1

class BadHoleExporter(export_targets.Exporter):
	info = 'targets'

	def writeTargetAndInfo(self, imagedata):
		'''
		Write out parentimage holestats and prefs where it is not used.
		'''
		img = imagedata
		while (img and img['target'] and img['target']['image'] and img['target']['preset']):
			target0 = self.getZeroVersionTarget(img['target'])
			parent_img = target0['image']
			# Check holefinder and jahcfinder. Only want the most recent one
			r = leginondata.HoleFinderPrefsData(image=parent_img).query(results=1)
			if r:
				qstats = leginondata.HoleStatsData(prefs=r[0], good=False)
				bad_stats = qstats.query()
			else:
				bad_stats = []
			pref_key = 'prefs'
			#
			if not bad_stats:
				# Check ScoreFinder. Only want the most recent one
				r = leginondata.ScoreTargetFinderPrefsData(image=parent_img).query(results=1)
				if r:
					qstats = leginondata.HoleStatsData(good=False)
					qstats['score-prefs']=r[0]
					bad_stats = qstats.query()
				else:
					bad_stats = []
				pref_key = 'score-prefs'
				if not bad_stats:
					# nothing to write out
					img = target0['image']
					continue
			# write once per targetlist
			parent_preset = target0['image']['preset']['name']
			if parent_preset not in list(self.targetlist.keys()):
				self.targetlist[parent_preset] = []
			if target0['list'].dbid not in self.targetlist[parent_preset]:

				# most recent last
				bad_stats.reverse()
				for i, b in enumerate(bad_stats):
					line = '%d\t%d_%d\t%d\t%d\t%.3f\t%.3f\t%.3f\t%.4f\t%.4f\t%s\t%s' % (img.dbid, target0['image'].dbid, i+1, b['row'], b['column'], b['mean'],b['stdev'],b[pref_key]['ice-zero-thickness'],b['thickness-mean'],b['thickness-stdev'], img['scope'].timestamp.strftime("%Y-%m-%d %H:%M:%S"), target0['image']['filename'])
					self.logger.info(line)
					self.writeResults(target0, line)
				self.targetlist[parent_preset].append(target0['list'].dbid)
			img = target0['image']

	def setTitle(self):
		self.result_title ='ChildImageId\tImageId_StatNumber\tYCoord\tXCoord\tmean(I)\tstdev(I)\tI0\tmean(Thickness)\tstdev(Thickness)\tTimeStamp\tLeginonImageFilename'

if __name__=='__main__':
	session_name = input('Which session ? ')
	base_path = input('Where to save under ? (default: ./%s) ' % session_name)
	if not base_path:
		base_path = './%s' % session_name
	app = BadHoleExporter(session_name, base_path)
	app.run()
