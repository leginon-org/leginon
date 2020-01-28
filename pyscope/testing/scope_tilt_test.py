#!/usr/bin/env python
from pyscope import fei
import time

c = fei.Tecnai()
distance = 1.0
display_scale = 180.0/3.14159
display_unit = 'degrees'
repeats = 2
functionname = 'StagePosition'

getfunc = getattr(c,'get'+functionname)
setfunc = getattr(c,'set'+functionname)

p0 = getfunc()

c.setStageSpeed(0.1)

for i in range(repeats):
	for d in (distance, -distance):
		p = getfunc()
		p1 = {'a':p['a']+d}
		t0 = time.time()
		setfunc(p1)
		t1 = time.time()
		print '%s by %.2f %s took %.6f seconds' % (functionname, d*display_scale, display_unit, t1 -t0)

setfunc(p0)
