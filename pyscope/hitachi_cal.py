#!/usr/bin/env python
import sys
import time
from pyscope import hitachi
from pyscope import instrumenttype
search_for = 'TEM'
try:
	h = instrumenttype.getInstrumentTypeInstance(search_for)
	if h.__class__.__name__ not in ('Hitachi','HT7800'):
		raise ValueError("TEM %s is not of Hitachi subclass" % h.__class__.__name__)
except Exception, e:
	print "Error", e
	sys.exit(1)

h.findMagnifications()
# This is a test of get/set defocus
# focus change only affect the zoom-1 if already in zoom-1
# and affect low-mag if already in low-mag. Low-mag scale is not in hitachi gui.
mags = h.getMagnifications()
h.setMagnification(4000)
m0 = h.getMagnification()
h.setDefocus(0)
d0 = h.getDefocus()
print 'D0', d0
f0 = h.getFocus()
print 'F0', f0
h.setDefocus(2e-5)
d1 = h.getDefocus()
print 'Defocus set to', d1
print h.getFocus()
for m in mags:
	h.setMagnification(m)
	d = h.getDefocus()
	f=h.getFocus()
	print '%d %.3f %.6f' % (m, d*1e6, f)
h.setMagnification(m0)
h.setDefocus(d0)
f0a=h.getFocus()
print 'Return Focus', f0a
if abs(f0 - f0a) > 3e-3:
	raise ValueError('Focus did not return')
