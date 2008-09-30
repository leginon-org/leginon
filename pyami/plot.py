#!/usr/bin/env python

import pylab

def plot(*args, **kwargs):
	pylab.plot(*args, **kwargs)
	pylab.show()

if __name__ == '__main__':
	import mrc
	import sys
	import numextension
	import imagefun
	import numpil
	a = mrc.read(sys.argv[1])
	a2 = mrc.read(sys.argv[2])

	print 'SHAPE', a.shape
	#pow = imagefun.power(a)
	#numpil.write(pow, 'pow.png')
	b = numextension.radialPower(a, 50)
	b2 = numextension.radialPower(a2, 50)
	plot(b[5:])
	plot(b2[5:])
	raw_input('enter to quit')
