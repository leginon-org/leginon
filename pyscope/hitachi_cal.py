#!/usr/bin/env python
import sys
from pyscope import hitachi
try:
	h = hitachi.Hitachi()
except Exception, e:
	print "Error", e
	sys.exit(1)

h.findMagnifications()
mags = h.getMagnifications()
m0 = h.getMagnification()
d0 = h.getDefocus()
f0 = h.getFocus()
h.setDefocus(1e-5)
d1 = h.getDefocus()
for m in mags:
	h.setMagnification(m)
	d = h.getDefocus()
	print '%d %.3f' % (m, d*1e-6)
h.setMagnification(m0)
h.setDefocus(d0)
if f0 != h.getFocus():
	raise ValueError('Focus did not return')
