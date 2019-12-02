#!/usr/bin/env python
#-----------------------
# change these for your testing
#-----------------------
# import the module of your scope
from pyscope import fei
# create instance of this tem
c = fei.Glacios()
# alpha angle to move in degrees
delta_angle = 60.0
# tilt speed degrees per second
speed = 2.0

#------------------------
# no change required below
#------------------------
import time
display_scale = 180.0/3.14159
display_unit = 'degrees'
distance = delta_angle / display_scale
repeats = 1
functionname = 'StagePosition'

getfunc = getattr(c,'get'+functionname)
setfunc = getattr(c,'set'+functionname)

p0 = getfunc()

c.setStageSpeed(speed) # degrees per second

for i in range(repeats):
	for d in (distance,):
		p = getfunc()
		p1 = {'a':p['a']+d}
		t0 = time.time()
		setfunc(p1)
		t1 = time.time()
		print '%s by %.2f %s took %.6f seconds' % (functionname, d*display_scale, display_unit, t1 -t0)
	time.sleep(6.0)
# reset back to the original
c.setStageSpeed(50.0) #maximal speed since stage limit is about 29 degrees/sec.
setfunc(p0)
