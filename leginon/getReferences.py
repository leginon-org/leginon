#!/usr/bin/env python
import sys
from leginon import leginondata
if len(sys.argv) != 2:
	print 'getReferences.py filename'
	sys.exit()

filename = sys.argv[1]
sessionname = filename.split('_')[0]
if filename[-4:] == '.mrc':
	filename = filename[:-4]

sdata = leginondata.SessionData(name=sessionname).query()[0]
results = leginondata.AcquisitionImageData(session=sdata,filename=filename).query()
if not results:
	print 'image not found'
	sys.exit()

a = results[0]

darkdata = a['dark']
brightdata = a['norm']['bright']
print 'reference session path: %s' % brightdata['session']['image path']
print 'norm image: %s' % a['norm']['filename']
print 'bright image: %s' % brightdata['filename']

cameraname = a['camera']['ccdcamera']['name']
if cameraname == 'GatanK2Counting' or cameraname == 'GatanK2Super':
	print 'dark image values are always zero in counting mode camera'
else:
	print 'dark image: %s' % darkdata['filename']
	nframes = darkdata['camera']['nframes']
	if nframes:
		print 'scale dark image down by %d before using it on single frame' % (nframes)
