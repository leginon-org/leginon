#!/usr/bin/env python
from pyscope import jeolcom
j = jeolcom.Jeol()
j.findMagnifications()
t = raw_input('type end to end')
while not t:
	mag = j.getMagnification()
	print '%d:%d' % (mag,j.getRawFocusOL())
	imageshift = j.def3.GetPLA()
	print '%d:%d,%d' % (mag,imageshift[0],imageshift[1])
	shift = j.def3.GetCLA1()
	print '%d:%d,%d' % (mag,shift[0],shift[1])
	t = raw_input('type end to end')
