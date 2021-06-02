#!/usr/bin/env python
'''
This test script is used to find K3 orientation at
each step of parameter setting.
'''
from pyscope import dmsem
d = dmsem.GatanK3()
configs = dmsem.configs

def sumOrientation(d):
	if d.isSEMCCD2019orUp() or not d.isDM231orUp():
		k2_rotate = d.getDmsemConfig('k2','rotate')
		k2_flip = d.getDmsemConfig('k2','flip')
		return k2_rotate, k2_flip
	#default
	return 0, False

d.setExposureTime(400)
for b in (True,):
	print '****Save Frame set to %s******' % b
	print 'config isDM231 or up', d.isDM231orUp()
	d.setSaveRawFrames(b)
	print 'config isSEMCCD2019 or up', d.isSEMCCD2019orUp()
	rotate, flip = sumOrientation(d)
	print 'frame saving sum rotation', rotate
	print 'frame saving sum flip', flip
	try:
		print 'frame RotationFlipDefault', d.getFrameSavingRotateFlipDefault()
	except:
		print 'getFrameSavingRotationFlipDefault not defined'
	filesave_params = d.calculateFileSavingParams()
	expected_rotationFlip = int(not flip)*4
	print '*****FileSaving RotationFlip value should be %d' % expected_rotationFlip
	print 'frame rotationFlip value', filesave_params['rotationFlip']
	print '*****Appion value******'
	print 'appion frame rotate', d.getFrameRotate()
	print 'appion frame flip', d.getFrameFlip()
d.setSaveRawFrames(False)

raw_input('hit return to quit')
