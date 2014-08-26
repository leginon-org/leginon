#!/usr/bin/env python

#scope = 'SimTEM'
scope = 'Tecnai'

n = 1

mags = [
	190,
	6500,
	52000,
]

positions1 = [
	(0, 0),
	(0, 0),
	(5e-6, 0),
	(0, 0),
	(100e-6, 0),
	(0, 0),
	(0, 5e-6),
	(0, 0),
	(0, 100e-6),
	(0, 0),
	(5e-6, 5e-6),
	(0, 0),
	(100e-6, 100e-6),
	(0, 0),
]

positions = [
	(0, 0),
	(0, 0),
	(5e-6, 0),
	(0, 0),
	(100e-6, 0),
	(0, 0),
	(100e-6, 100e-6),
	(0, 0),
]

import time
#import pyscope.tecnai
import pyscope.registry

log_file = 'speedtest%s.log' % (int(time.time()))

t = pyscope.registry.getClass(scope)()

t.setCorrectedStagePosition(False)
t.findMagnifications()

def write_log(fields):
	line = '\t'.join(map(str, fields)) + '\n'
	f = open(log_file, 'a')
	f.write(line)
	f.close()

for i in range(n):
	print 'iteration', i
	for mag in mags:
		print 'mag', mag
		for (x1,y1) in positions:
			print 'position', x1,y1
			t.setMagnification(mag)
			time.sleep(0.25)
			pos0 = t.getStagePosition()
			x0,y0 = pos0['x'], pos0['y']
			t0 = time.time()
		
			t.setStagePosition({'x':x1, 'y':y1})
		
			t1 = time.time()
			pos2 = t.getStagePosition()
			x2,y2 = pos2['x'],pos2['y']
		
			fields = [i,mag,x0,y0,x1,y1,x2,y2,t0,t1]
			write_log(fields)

del t
