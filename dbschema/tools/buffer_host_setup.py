#!/usr/bin/env python
import sys
from leginon import leginondata
from sinedon import directq

buffer_hostname = raw_input('Buffer Hostname to setup ? ')
if not buffer_hostname:
	sys.exit(0)
buffer_base_path = raw_input('root path where frames are put on the buffer host\n For example, instead of primary_storage_host:/data/frames/sessionname, you want to put it under buffer_host:/bufferdata/frames/sessionname, you should enter /bufferdata.\n ? ')
if not buffer_base_path:
	sys.exit(0)

# camera
camera_hostname = raw_input('Camera Hostname to get movie frames from ? ')
# validate cameras
cameras = leginondata.InstrumentData(hostname=camera_hostname).query()
cnames = map((lambda x: x['name']), cameras)
print('Host %s contains %d cameras: %s' % (camera_hostname, len(cameras), ','.join(cnames)))
answer = raw_input('Is this correct ? (Y/N/y/n) ')
if answer.lower() == 'n':
	sys.exit(1)

for c in cameras:
	q = leginondata.BufferHostData(ccdcamera=c)
	q['buffer hostname']=buffer_hostname
	results= q.query(results=1)
	if not results:
		# User sinedon to do initial insert
		q = leginondata.BufferHostData(ccdcamera=c)
		q['buffer hostname']=buffer_hostname
		q['buffer base path']=buffer_base_path
		q['disabled']= not last_status
		q.insert(force=True)
		print('Camera %s is paired to Bufer host %s to be saved under %s' % (c['name'],buffer_hostname, buffer_base_path))
	else:
		r = results[0]
		if r['buffer base path'] != buffer_base_path:
			# update and set to active.
			q = "update BufferHostData set `buffer base path`='%s', `disabled`='0' where `DEF_id`=%d;" % (buffer_base_path, r.dbid)
			directq.complexMysqlQuery('leginondata',q)
			print('Base path changed')
		else:
			enable_str = 'enabled'
			if r['disabled']:
				enable_str = 'disabled'
			last_status = r['disabled']
			print('Buffer/Camera pair is already correct as DEF_id=%d of leginondb.BufferHostData.\n  It is curently %s' % (r.dbid, enable_str))
			answer = raw_input('Do you want to change it ? (Y/N/y/n) ')
			if answer.lower() == 'n':
				continue
			q = "update BufferHostData set `disabled`='%d' where `DEF_id`=%d;" % (int(not last_status), r.dbid)
			directq.complexMysqlQuery('leginondata',q)
			print('Status changed')
print('DONE') 
