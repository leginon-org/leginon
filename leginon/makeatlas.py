#!/usr/bin/env python

import mosaic
import node
import dbdatakeeper
import data
import sys
import Mrc
import calibrationclient
import os.path

filenames = sys.argv[1:]

db = dbdatakeeper.DBDataKeeper()

ses = data.SessionData()

n = node.Node('asdf',ses)
n.instrument = None
c = calibrationclient.ModeledStageCalibrationClient(n)
#c = calibrationclient.StageCalibrationClient(n)
m = mosaic.EMMosaic(c)

for filename in filenames:
	print 'FILE', filename
	qfilename = os.path.split(filename)[-1][:-4]
	imquery = data.AcquisitionImageData(filename=qfilename)
	images = db.query(imquery, results=1)
	if not images:
		print '** file not in db **'
		continue
	imagedata = images[0]
	m.addTile(imagedata)

mosaicimage = m.getMosaicImage(None)

n.exit()

Mrc.numeric_to_mrc(mosaicimage, 'mosaic.mrc')

