#!/usr/bin/env python
import sys

from pyami import scriptrun
from leginon import leginondata
from appionlib import apDisplay
from sinedon import directq

class BufferHostSetter(scriptrun.ScriptRun):
	def setOptions(self, parser):
		parser.add_option("--buffer_host", dest="buffer_host",
			help="Buffer hostname to setup, e.g. --buffer_host=buffer01")
		msg='root path where frames are put on the buffer host. For example, instead of primary_storage_host:/data/frames/sessionname, you want to put it under buffer_host:/bufferdata/frames/sessionname, you should enter /bufferdata.'
		parser.add_option("--base_path", dest="base_path",
			help=msg, metavar="PATH")
		parser.add_option("--camera_host", dest="camera_host",
			help="Camera hostname to setup, e.g. --camera_host=scope1cam1")
		parser.add_option("--change_status", dest="change_status", default=False,
			action="store_true", help="Change status of the existing record")

	def checkOptionConflicts(self,params):
		camera_hostname = params['camera_host']
		# validate cameras
		self.cameras = leginondata.InstrumentData(hostname=camera_hostname).query()
		if not self.cameras:
			apDisplay.printError('No camera on this host')
		cnames = map((lambda x: x['name']), self.cameras)
		print('Host %s contains %d cameras: %s' % (camera_hostname, len(self.cameras), ','.join(cnames)))

	def run(self):
		buffer_hostname = self.params['buffer_host']
		buffer_base_path = self.params['base_path']
		for c in self.cameras:
			q = leginondata.BufferHostData(ccdcamera=c)
			q['buffer hostname']=self.params['buffer_host']
			results= q.query(results=1)
			if not results:
				last_status = True
				# User sinedon to do initial insert
				q = leginondata.BufferHostData(ccdcamera=c)
				q['buffer hostname']=buffer_hostname
				q['buffer base path']=buffer_base_path
				q['disabled']= not last_status
				q.insert(force=True)
				print('Camera %s is paired to Bufer host %s to be saved under %s' % (c['name'],buffer_hostname, buffer_base_path))
				continue
			else:
				r = results[0]
			if r['buffer base path'] != buffer_base_path:
				# update and set to active.
				q = "update BufferHostData set `buffer base path`='%s', `disabled`='0' where `DEF_id`=%d;" % (buffer_base_path, r.dbid)
				directq.complexMysqlQuery('leginondata',q)
				print('Base path changed')
				print('Enable buffer host to direct frames here')
				continue
			else:
				enable_str = 'enabled'
				if r['disabled']:
					enable_str = 'disabled'
			last_status = r['disabled']
			if self.params['change_status']:
				print('Buffer/Camera pair is already correct as DEF_id=%d of leginondb.BufferHostData.\n  It is curently %s' % (r.dbid, enable_str))
				q = "update BufferHostData set `disabled`='%d' where `DEF_id`=%d;" % (int(not last_status), r.dbid)
				directq.complexMysqlQuery('leginondata',q)
				print('Status changed')
		print('DONE')

if __name__=='__main__':
	app=BufferHostSetter()
	app.run()
