#!/usr/bin/env python
import sys
from leginon import leginondata

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
	q['buffer base path']=buffer_base_path
	results= q.query()
	if results:
		print('Buffer/Camera pair exists as row of DEF_id=%d of leginondb.BufferHostData.\n  You should use database admin tools to disable/enable' % (results[0].dbid,))
		sys.exit(1)
	q['disabled']=False
	q.insert()
	print('Camera %s is paired to Bufer host %s to be saved under %s' % (c['name'],buffer_hostname, buffer_base_path))

print('DONE') 
