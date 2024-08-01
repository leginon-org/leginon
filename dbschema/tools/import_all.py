#!/usr/bin/env python
import sys
import os
import glob
from sinedon import directq

import sinedon

# Set these in order of the applications to be imported.
# The last one is most important to be consistent
# All names will get 'MSI-' prefix except Calibrations
APP_ORDER=['Calibrations','Diffr','Tomo','Tilt','T']

def confirmDBHost():
	db_params = sinedon.getConfig('leginondata')
	db_host = db_params['host']
	db_name = db_params['db']
	answer=input('Are you ready to import to %s: %s? (Y/y/N/n)' % (db_host, db_name))
	if answer.lower() != 'y':
		sys.exit()

class Importer(object):
	'''
	Import what is in json_dir to a clean database.
	'''
	json_dir = 'unknown'
	def __init__(self):
		print(('--------Working on %s-------' % self.json_dir))
		self.db_params = sinedon.getConfig('leginondata')
		self.db_host=self.db_params['host']
		dir0 = os.path.abspath(os.path.curdir)
		if not os.path.isdir(self.json_dir):
			print(('Error: no %s directory with json files' % self.json_dir))
			return
		os.chdir(self.json_dir)
		self.runAll()
		os.chdir(dir0)

	def runAll(self):
		NotImplemented()

class ViewerTableCreater(object):
	def __init__(self):
		self.db_params = sinedon.getConfig('leginondata')
		self.db_host=self.db_params['host']
		if 'engine' in list(self.db_params.keys()) and self.db_params['engine'] != '':
			self.db_engine = self.db_params['engine']
		else:
			self.db_engine = 'MyISAM'
		self.run()

	def _createViewerImageStatusTable(self):
		"""
		create empty table for webviewer
		"""
		query = "DROP TABLE IF EXISTS `ViewerImageStatus`;"
		directq.complexMysqlQuery('leginondata',query)
		query = """
			CREATE TABLE `ViewerImageStatus` (
				`DEF_id` int(11) NOT NULL AUTO_INCREMENT,
				`DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
				`REF|SessionData|session` int(11) DEFAULT NULL,
				`REF|AcquisitionImageData|image` int(11) DEFAULT NULL,
				`status` enum('hidden','visible','exemplar','trash') DEFAULT NULL,
				PRIMARY KEY (`DEF_id`),
				KEY `DEF_timestamp` (`DEF_timestamp`),
				KEY `REF|SessionData|session` (`REF|SessionData|session`),
				KEY `REF|AcquisitionImageData|image` (`REF|AcquisitionImageData|image`),
				KEY `status` (`status`)
			) ENGINE=%s DEFAULT CHARSET=latin1;
			""" % (self.db_engine)
		directq.complexMysqlQuery('leginondata',query)

	def _createViewerCommentTable(self):
		"""
		create empty table for webviewer
		"""
		# viewer_comment is used in loi.php
		query = "DROP TABLE IF EXISTS `viewer_comment`;"
		directq.complexMysqlQuery('leginondata',query)
		query = """
			CREATE TABLE `viewer_comment` (
				`id` int(11) NOT NULL AUTO_INCREMENT,
				`timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
				`sessionId` int(11) DEFAULT NULL,
				`type` enum('rt','post') DEFAULT NULL,
				`imageId` int(11) DEFAULT NULL,
				`name` text,
				`comment` text,
				PRIMARY KEY (`id`),
				KEY `timestamp` (`timestamp`),
				KEY `sessionId` (`sessionId`),
				KEY `imageId` (`imageId`),
				KEY `type` (`type`)
			) ENGINE=%s DEFAULT CHARSET=latin1;
			""" % (self.db_engine)
		directq.complexMysqlQuery('leginondata',query)
		# ImageCommentData is used in imageviewer.php
		query = "DROP TABLE IF EXISTS `ImageCommentData`;"
		directq.complexMysqlQuery('leginondata',query)
		query = """
			CREATE TABLE `ImageCommentData` (
				`DEF_id` int(11) NOT NULL AUTO_INCREMENT,
				`DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
				`REF|SessionData|session` int(11) DEFAULT NULL,
				`REF|AcquisitionImageData|image` int(11) DEFAULT NULL,
				`comment` text DEFAULT NULL,
				PRIMARY KEY (`DEF_id`),
				KEY `DEF_timestamp` (`DEF_timestamp`),
				KEY `REF|SessionData|session` (`REF|SessionData|session`),
				KEY `REF|AcquisitionImageData|image` (`REF|AcquisitionImageData|image`),
				KEY `comment` (`comment`(128))
			) ENGINE=%s DEFAULT CHARSET=latin1;
			""" % (self.db_engine)
		directq.complexMysqlQuery('leginondata',query)

	def _createViewerDelImageTable(self):
		"""
		create empty table for webviewer
		"""
		query = "DROP TABLE IF EXISTS `viewer_del_image`;"
		directq.complexMysqlQuery('leginondata',query)
		query = """
			CREATE TABLE `viewer_del_image` (
				`id` int(11) NOT NULL AUTO_INCREMENT,
				`timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
				`username` varchar(50) DEFAULT NULL,
				`sessionId` int(11) DEFAULT NULL,
				`imageId` int(11) DEFAULT NULL,
				`status` enum('deleted','marked') DEFAULT NULL,
				PRIMARY KEY (`id`),
				KEY `timestamp` (`timestamp`),
				KEY `username` (`username`),
				KEY `sessionId` (`sessionId`),
				KEY `imageId` (`imageId`),
				KEY `status` (`status`)
			) ENGINE=%s DEFAULT CHARSET=latin1;
			""" % (self.db_engine)
		directq.complexMysqlQuery('leginondata',query)

	def run(self):
		self._createViewerImageStatusTable()
		self._createViewerCommentTable()
		self._createViewerDelImageTable()

class InstrumentImporter(Importer):
	'''
	Import instruments to a clean database.
	'''
	json_dir = 'instrument'
	def runAll(self):
		from dbschema.tools import import_leginon_instruments
		app = import_leginon_instruments.ClientJsonLoader(['',self.db_host])
		app.run()

class CalibrationImporter(Importer):
	'''
	Import calibrations to a clean database.
	'''
	json_dir = 'cal'
	def runAll(self):
		from dbschema.tools import import_leginon_cal
		cal_files = glob.glob('%s_*.json' % (self.json_dir))
		for c in cal_files:
			try:
				app = import_leginon_cal.CalibrationJsonLoader(['',self.db_host, c])
				app.run()
			except KeyError as e:
				print(('Warning: Skipped %s: %s' % (c, e)))
				continue

class ReferenceImporter(Importer):
	'''
	Import reference images to a clean database.
	'''
	json_dir = 'ref'
	def runAll(self):
		from dbschema.tools import import_leginon_ref
		ref_files = glob.glob('%s_*.json' % (self.json_dir))
		for c in ref_files:
			app = import_leginon_ref.ReferenceJsonLoader(['',self.db_host, c])
			app.run()

class BufferHostImporter(Importer):
	'''
	Import buffer host settings to a clean database.
	'''
	json_dir = 'bufferhost'
	def runAll(self):
		from dbschema.tools import import_leginon_bufferhost
		ref_files = glob.glob('%s_*.json' % (self.json_dir))
		for c in ref_files:
			app = import_leginon_bufferhost.BufferHostJsonLoader(['',self.db_host, c])
			app.run()


from leginon import importexport
from dbschema.tools import import_leginon_settings
class AppImporter(Importer):
	'''
	Import applications to a clean database.
	This import settings as default for the clean database.  Not a good
	solution if all users have different settings that they want to keep.
	'''
	json_dir = 'app'
	def runAll(self):
		patterns=APP_ORDER
		for p in patterns:
			pp = '*%s.xml' % (p,)
			xmlfiles = glob.glob(pp)
			for xmlfile in xmlfiles:
				self.importXml(xmlfile)
				jsonfile = xmlfile[:-3]+'json'
				self.importSettings(jsonfile)

	def importXml(self,xmlfile):
		print(('***importing Application from %s' % xmlfile))
		app = importexport.ImportExport(**self.db_params)
		app.importApplication(xmlfile)

	def getSettingsFileName(self, jsonfile):
		pattern = '*%s' % (jsonfile,)
		jsons = glob.glob(pattern)
		if len(jsons) != 1:
			raise ValueError('Did not find unique *%s' % jsonfile)
		return jsons[0]

	def importSettings(self,jsonfile):
		new_jsonfile = self.getSettingsFileName(jsonfile)
		app = import_leginon_settings.SettingsJsonLoader(new_jsonfile)
		app.run()


from dbschema.tools import import_leginon_presets
class PresetImporter(Importer):
	'''
	Import presets in directories named by APP_ORDER.
	Presets from the same scope-camera pair will be overwritten by the latter app.
	'''
	json_dir = 'preset'
	def runAll(self):
		import_order = APP_ORDER
		for a in import_order:
			if os.path.isdir(a):
				os.chdir(a)
				cal_files = glob.glob('%s_*.json' % self.json_dir)
				for c in cal_files:
					print(c)
					app = import_leginon_presets.CalibrationJsonLoader(['', self.db_host, c])
					app.run()
					app = None
				os.chdir('..')

def mysqlReminder():
	"""
	Tables and data to be imported
	"""
	print('---------------')
	for name in ('projects','projectowners','privileges','install','processingdb','shareexperiments','userdetails'):
		p = sinedon.getConfig('projectdata')
		msg = 'mysql -h %s -u %s -p%s %s < ./tables/%s.sql' % (p['host'],p['user'],p['passwd'],p['db'], name)
		print(msg)
	for name in ('GroupData','UserData'):
		p = sinedon.getConfig('leginondata')
		msg = 'mysql -h %s -u %s -p%s %s < ./tables/%s.sql' % (p['host'],p['user'],p['passwd'],p['db'], name)
		print(msg)
	print('---------------')
	answer=input('Did you import with the above mysql commands ? (Y/y/N/n) ')
	if answer.lower() != 'y':
		sys.exit(0)


def cleanProcessingdb():
	"""
	Refresh processingdb appion database assignment
	"""
	try:
		query=" TRUNCATE TABLE processingdb"
		directq.complexMysqlQuery('projectdata',query)
	except Exception as e:
		print("Error: processingdb not found.  The mysql commands above failed")
		sys.exit(1)

if __name__=='__main__':
	confirmDBHost()
	mysqlReminder()
	app=ViewerTableCreater()
	cleanProcessingdb()
	app=InstrumentImporter()
	app=CalibrationImporter()
	app=AppImporter()
	app=PresetImporter()
	app=ReferenceImporter()
	app=BufferHostImporter()
