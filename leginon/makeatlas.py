#!/usr/bin/env python

import mosaic
import node
from leginon import leginondata
import sys
from pyami import mrc
import calibrationclient
import os.path
import sinedon

filenames = sys.argv[1:]

db = sinedon.getConnection('leginondata')

ses = leginondata.SessionData()

n = node.Node('asdf',ses)
n.instrument = None
c = calibrationclient.ModeledStageCalibrationClient(n)
#c = calibrationclient.StageCalibrationClient(n)
m = mosaic.EMMosaic(c)

for filename in filenames:
	print 'FILE', filename
	qfilename = os.path.split(filename)[-1][:-4]
	imquery = leginondata.AcquisitionImageData(filename=qfilename)
	images = db.query(imquery, results=1)
	if not images:
		print '** file not in db **'
		continue
	imagedata = images[0]
	m.addTile(imagedata)

mosaicimage = m.getMosaicImage(None)

n.exit()

mrc.write(mosaicimage, 'mosaic.mrc')

