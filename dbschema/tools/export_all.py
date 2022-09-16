#!/usr/bin/env python
import sys
import os
import glob
import json

import sinedon
import leginon.leginondata

# Set these in order of the applications to be imported.
# The last one is most important to be consistent
# All names will get 'MSI-' prefix except Calibrations
APP_ORDER=['Calibrations','Diffr','Tomo','Tilt','T']


def confirmDBHost():
	db_params = sinedon.getConfig('leginondata')
	db_host = db_params['host']
	db_name = db_params['db']
	answer=raw_input('Are you ready to export from %s: %s? (Y/y/N/n)' % (db_host, db_name))
	if answer.lower() != 'y':
		sys.exit()

class Exporter(object):
	'''
	Import what is in json_dir to a clean database.
	'''
	json_dir = 'unknown'
	def __init__(self, instruments=[]):
		print('--------Working on %s-------' % self.json_dir)
		self.db_params = sinedon.getConfig('leginondata')
		self.db_host=self.db_params['host']
		self.dir0 = os.path.abspath(os.path.curdir)
		if not os.path.isdir(self.json_dir):
			os.mkdir(self.json_dir)
			print('Making %s directory to add json files' % self.json_dir)
		os.chdir(self.json_dir)
		self.instruments = instruments
		self.runAll()
		os.chdir(self.dir0)

	def runAll(self):
		NotImplemented()

class InstrumentExporter(Exporter):
	'''
	Import instruments to a clean database.
	'''
	json_dir = 'instrument'
	def runAll(self):
		from dbschema.tools import export_leginon_instruments
		include_sim = False
		app = export_leginon_instruments.InstrumentJsonMaker(['',self.db_host, None, include_sim])
		app.run()
		self.instruments = app.instruments

class CalibrationExporter(Exporter):
	'''
	Import calibrations to a clean database.
	'''
	json_dir = 'cal'
	def runAll(self):
		# read cameras
		instrument_json = os.path.join(self.dir0,'instrument/instruments.json')
		f=open(instrument_json,'r')
		instruments = json.loads(f.read())
		cams = filter((lambda x:x['InstrumentData']['cs'] is None), instruments)
		tems = filter((lambda x:x['InstrumentData']['cs'] is not None), instruments)
		print(map((lambda x:x['InstrumentData']['name']),cams))
		print(map((lambda x:x['InstrumentData']['name']),tems))
		from dbschema.tools import export_leginon_cal
		for c in cams:
			c = c['InstrumentData']
			for t in tems:
				t = t['InstrumentData']
				params = ['',self.db_host,c['hostname'],c['name'],t['name']]
				print('params', params)
				app = export_leginon_cal.CalibrationJsonMaker(params)
				app.run()

class ReferenceExporter(Exporter):
	'''
	Import reference images to a clean database.
	'''
	json_dir = 'ref'
	def getCCDCameras(self):
		ccdcameras=[]
		for instr in self.instruments:
			if not instr['cs']:
				ccdcameras.append(instr)
		return ccdcameras

	def runAll(self):
		cams = self.getCCDCameras()
		from dbschema.tools import export_leginon_ref
		for c in cams:
			cam_host=c['hostname']
			cam_name=c['name']
			print('Exporting references for %s:%s' % (cam_host,cam_name))
			app = export_leginon_ref.ReferenceJsonMaker(['',self.db_host, cam_host, cam_name])
			app.run()

class BufferHostExporter(ReferenceExporter):
	'''
	Import bufferhost settings to a clean database.
	'''
	json_dir = 'bufferhost'

	def runAll(self):
		cams = self.getCCDCameras()
		from dbschema.tools import export_leginon_bufferhost
		for c in cams:
			cam_host=c['hostname']
			cam_name=c['name']
			print('Exporting buffer hosts for %s:%s' % (cam_host,cam_name))
			app = export_leginon_bufferhost.BufferHostJsonMaker(['',self.db_host, cam_host, cam_name])
			app.run()

from leginon import importexport
from dbschema.tools import export_leginon_settings
class AppExporter(Exporter):
	'''
	Export applications for a clean database.
	This export settings from the most recent launched sessiona.  Not a good
	solution if all users have different settings that they want to keep.
	'''
	json_dir = 'app'
	def determinePrefix(self):
		'''
		Find possible prefix.
		'''
		app_prefixes= ['']
		return app_prefixes

	def getRecentApp(self, name):
		'''
		Application of the most recent version.
		'''
		print('app name %s' % (name))
		r = leginon.leginondata.ApplicationData(name=name).query(results=1)
		if r:
			return r[0]
		else:
			return None

	def getRecentAppSession(self, app_name):
		'''
		Return the session that the recent version application was run from.
		'''
		appdata = self.getRecentApp(app_name)
		if not appdata:
			return None
		r = leginon.leginondata.LaunchedApplicationData(application=appdata).query(results=1)
		if r:
			return r[0]['session']
		else:
			return None

	def runAll(self):
		from dbschema.tools import export_leginon_settings
		prefixes = self.determinePrefix()
		patterns=APP_ORDER

		# app_session_name attribute for preset/app/settings import
		self.app_session_names = []
	
		for p in patterns:
			for px in prefixes:
				if 'Cal' not in p:
					middle = 'MSI-'
				else:
					middle = ''
				app_name = '%s%s%s' % (px, middle, p)
				session = self.getRecentAppSession(app_name)
				if session is None:
					continue
				# make app_session_name attribute for preset import
				self.app_session_names.append((p,app_name,session['name']))
				#export settings
				self.exportSettings(session['name'],app_name)
				#export xml
				self.exportXml(app_name)

	def exportXml(self,app_name):
		app = importexport.ImportExport(**self.db_params)
		dump = app.exportApplication(app_name, None)
		xmlpath = '%s.xml' % app_name
		f=open(xmlpath,'w')
		f.write(dump)
		f.close()

	def exportSettings(self,session_name,app_name):
		app = export_leginon_settings.SettingsJsonMaker(session_name)
		app.run(app_name)


from dbschema.tools import export_leginon_presets
class PresetExporter(Exporter):
	'''
	Import presets in directories named by APP_ORDER.
	Presets from the same scope-camera pair will be overwritten by the latter app.
	'''
	json_dir = 'preset'
	def __init__(self, instruments=[], app_session_names=[]):
		self.app_session_names = app_session_names
		super(PresetExporter,self).__init__(instruments)

	def runAll(self):
		export_order = self.app_session_names
		for a in export_order:
			app_type, app_name, session_name = a
			# organize json files by APP_ORDER
			if not os.path.isdir(app_type):
				os.mkdir(app_type)
				print('Making %s directory to add json files' % app_type)
			os.chdir(app_type)
			app = export_leginon_presets.PresetJsonMaker(session_name)
			app.run(app_name)
			os.chdir('..')

def mysqlReminder():
	"""
	Tables to be exported
	"""
	print('---------------')
	print('Please run these commands to export essential mysql tables')
	dir0 = os.path.abspath(os.path.curdir)
	sql_dir = os.path.join(dir0,'tables')
	if not os.path.isdir(sql_dir):
			os.mkdir(sql_dir)
			print('Making %s directory to add sql files' % sql_dir)
	
	for name in ('projects','projectowners','privileges','install','processingdb','shareexperiments','userdetails'):
		p = sinedon.getConfig('projectdata')
		msg = 'mysqldump -h %s -u %s -p%s %s %s > ./tables/%s.sql' % (p['host'],p['user'],p['passwd'],p['db'], name, name)
		print(msg)
	for name in ('GroupData','UserData'):
		p = sinedon.getConfig('leginondata')
		msg = 'mysqldump -h %s -u %s -p%s %s %s > ./tables/%s.sql' % (p['host'],p['user'],p['passwd'],p['db'], name, name)
		print(msg)
	print('---------------')

if __name__=='__main__':
	confirmDBHost()
	app1=InstrumentExporter()
	app=CalibrationExporter()
	app2=AppExporter(app1.instruments)
	app=PresetExporter(app1.instruments, app2.app_session_names)
	app=ReferenceExporter(app1.instruments)
	app=BufferHostExporter(app1.instruments)
	mysqlReminder()
