#!/usr/bin/env python
from pyscope import instrumenttype
import time

# This tests the first camera found in instruments.cfg
search_for = 'TEM'
c = instrumenttype.getInstrumentTypeInstance(search_for)
distance = 1e-4
display_scale = 1e6
display_unit = 'um'
repeats = 2
functionname = 'StagePosition'

getfunc = getattr(c,'get'+functionname)
setfunc = getattr(c,'set'+functionname)

p0 = getfunc()

for i in range(repeats):
	for d in (distance, -distance):
		p = getfunc()
		p1 = {'x':p['x'],'y':p['y']+d}
		t0 = time.time()
		setfunc(p1)
		t1 = time.time()
		print '%s by %.2f %s took %.6f seconds' % (functionname, d*display_scale, display_unit, t1 -t0)

setfunc(p0)
raw_input('Finished. Hit return to quit')
