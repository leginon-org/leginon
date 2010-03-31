#!/usr/bin/env python

# this will save the particle stack number into the header of a stack.
# use this if you want to run cenalignint, and keep track of the particles.
# NOTE!!! CONFORMS TO EMAN CONVENTION, STARTS AT 0!!!!

import sys
try:
	import EMAN
except ImportError:
	print "EMAN module did not get imported"

if __name__ == "__main__":

	if len(sys.argv) < 2:
		print "usage: renumber.py [filename]"
		sys.exit()

	filename=sys.argv[1]

	n=EMAN.fileCount(filename)[0]
	im=EMAN.EMData()
	for i in range(n):
		im.readImage(filename,i)
		im.setNImg(i)
		im.writeImage(filename,i)
		print i
