#!/usr/bin/env python
import sys

from pyami import scriptrun
from leginon import leginondata
from appionlib import apDisplay
from sinedon import directq

class BufferFramePathChanger(scriptrun.ScriptRun):
	def setOptions(self, parser):
		parser.add_option("--session", dest="session_name",
			help="Session to change the buffer frame path, e.g. --session_name=22mar04")
		parser.add_option("--buffer_host", dest="buffer_host",
			help="Buffer hostname in BufferHostData in leginondb, e.g. --buffer_host=buffer01")
		parser.add_option("--new_path", dest="new_path",
			help="New buffer frame path to move the session to, e.g. --new_path=/data/user/session_name/rawdata", metavar="PATH")

	def checkOptionConflicts(self,params):
		results = leginondata.SessionData(name=params['session_name']).query()
		if results < 1:
			apDisplay.printError('Session name does not exist')
		self.session = results[0]
		# validate path
		standard_path = self.session['name']+'/rawdata'
		if not params['new_path'].endswith(standard_path):
			apDisplay.printWarning('New Frame Path not using standard %s' % standard_path)
		#
		# make sure session frame path has being recorder
		results = leginondata.BufferFramePathData(session=self.session).query()
		if results < 1:
			apDisplay.printWarning('Session Frame Path not in the database')
			apDisplay.printWarning('Nothing to do.')
			sys.exit(0)
		self.frame_path_data = results[0]
		# check host
		old_host = self.frame_path_data['host']['buffer hostname']
		new_host = params['buffer_host']
		if old_host != new_host:
			apDisplay.printWarning('You are moving the frames between hosts')
		elif params['new_path'] == self.frame_path_data['buffer frame path']:
			apDisplay.printWarning('New path is the same as the old one')
			apDisplay.printWarning('Nothing to do.')
			sys.exit(0)
		#
		# validate camera and buffer host
		camdata = self.getSessionFrameCamera()
		q = leginondata.BufferHostData(ccdcamera=camdata)
		q['buffer hostname'] = new_host
		results = q.query(results=1)
		need_setup = False
		if not results:
			apDisplay.printWarning('Can not find BufferHostData for camera %s on %s' % (camdata['name'],camdata['hostname']))
			need_setup = True
		self.new_host_data = results[0]
		if not params['new_path'].startswith(self.new_host_data['buffer base path']):
			apDisplay.printWarning('new path must starts with BufferHostData buffer base path %s' % (self.new_host_data['buffer base path']))
			need_setup = True
		if self.new_host_data['disabled']:
			apDisplay.printWarning('Only enabled buffer host is useful here')
			need_setup = True
		if need_setup:
			apDisplay.printWarning('Please run buffer_host_setup.py first')
			sys.exit(1)

	def getSessionFrameCamera(self):
		q=leginondata.CameraEMData(session=self.session)
		q['save frames']=True
		results=q.query(results=1)
		if not results:
			apDisplay.printError('No frame saved in the session to identify the camera')
		return results[0]['ccdcamera']

	def run(self):
		print('Updating BufferFramePath id=%d ...' % self.frame_path_data.dbid)
		query = "update BufferFramePathData set `REF|BufferHostData|host`='%d', `buffer frame path`='%s' where `DEF_id`=%d" % (self.new_host_data.dbid, self.params['new_path'], self.frame_path_data.dbid)
		directq.complexMysqlQuery('leginondata',query)
		print('DONE')
		apDisplay.printWarning('You need to move the files from the old path %s to the new %s on host %s' % (self.frame_path_data['buffer frame path'], self.params['new_path'], self.params['buffer_host']))

if __name__=='__main__':
	app=BufferFramePathChanger()
	app.run()
