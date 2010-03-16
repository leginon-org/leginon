#!/usr/bin/env python
# get eulers from proj.img file

import sys, os
from math import pi
try:
	import EMAN
except ImportError:
	print "EMAN module did not get imported"

if __name__ == "__main__":
	if len(sys.argv) !=3:
		print "Usage: getProjEulers.py <infile> <outfile>\n"
		sys.exit(1)

	projfile = sys.argv[1]
	outfile = sys.argv[2]

	out = open(outfile, "w")

	count,imgtype = EMAN.fileCount(projfile)
	imgs = EMAN.EMData()
	imgs.readImage(projfile,0,1)
	for i in range(count):
		imgs.readImage(projfile,i,1)
		e = imgs.getEuler()
		alt = e.alt()*180./pi
		az = e.az()*180./pi
		phi = e.phi()*180./pi
		out.write("%i\t%f\t%f\t%f\n" % (i,alt,az,phi))
	out.close()
