#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import sys
import gonmodel

if len(sys.argv) != 8:
	print "usage:", sys.argv[0], "xfile yfile magfile gonx gony pixx pixy"
	sys.exit()

xfilename = sys.argv[1]
yfilename = sys.argv[2]
magfilename = sys.argv[3]
gonx = float(sys.argv[4])
gony = float(sys.argv[5])
pixx = float(sys.argv[6])
pixy = float(sys.argv[7])

xmod = gonmodel.GonModel()
ymod = gonmodel.GonModel()
maginfo = gonmodel.MagInfo(magfilename)

xmod.read_gonshelve(xfilename)
ymod.read_gonshelve(yfilename)

modavgx = maginfo.get('modavgx')
modavgy = maginfo.get('modavgy')

gonx1 = xmod.rotate(maginfo, pixx, pixy)
gony1 = ymod.rotate(maginfo, pixx, pixy)

gonx1 = gonx1 * modavgx
gony1 = gony1 * modavgy

gonx1 = xmod.predict(gonx,gonx1)
gony1 = ymod.predict(gony,gony1)

print gonx1, gony1
