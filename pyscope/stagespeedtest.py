#!/usr/bin/env python

#scope = 'SimTEM'
scope = 'Tecnai'

n = 3

holders = ['single tilt', 'cryo']

mags = [
	50,
	5000,
	50000,
]

positions = [
	(0, 0),
	(0, 0),
	(0, 10e-6),
]

import itertools
import time
#import pyscope.tecnai
import pyscope.registry

log_file = 'speedtest%s.log' % (int(time.time()))

t = pyscope.registry.getClass(scope)()

t.setCorrectedStagePosition(False)

def write_log(fields):
	line = '\t'.join(map(str, fields)) + '\n'
	f = open(log_file, 'a')
	f.write(line)
	f.close()

for i, holder, mag, (x1,y1) in itertools.product(range(n), holders, mags, positions):
	t.setHolderType(holder)
	t.setMagnification(mag)
	time.sleep(0.25)
	pos0 = t.getStagePosition()
	x0,y0 = pos0['x'], pos0['y']
	t0 = time.time()

	t.setStagePosition({'x':x1, 'y':y1})

	t1 = time.time()
	pos2 = t.getStagePosition()
	x2,y2 = pos2['x'],pos2['y']

	fields = [i,holder,mag,x0,y0,x1,y1,x2,y2,t0,t1]
	write_log(fields)
