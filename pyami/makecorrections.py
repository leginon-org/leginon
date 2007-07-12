#!/usr/bin/env python

import ccd
import mrc
import sinedon
import leginondata
import mem

import sinedon.data
sinedon.data.holdImages(False)

db = sinedon.getConnection('leginondata')
corrector = ccd.Corrector()

session = leginondata.SessionData(name='07jun05b')

print 'BIAS'
query = leginondata.AcquisitionImageData(session=session, label='bias1')
images = db.query(query, readimages=False)
print 'Found %d images' % (len(images),)
for image in images:
	filename = image['filename']
	print 'Inserting:  ', filename
	corrector.insertBias(image['image'])
finalbias = corrector.bias()
print 'saving bias.mrc'
mrc.write(finalbias, 'bias.mrc')

print 'DARK'
query = leginondata.AcquisitionImageData(session=session, label='dark1')
images = db.query(query, readimages=False)
print 'Found %d images' % (len(images),)
for image in images:
	filename = image['filename']
	exptime = image['camera']['exposure time']
	print 'Inserting:  ', filename
	corrector.insertDark(image['image'], exptime)
finaldark = corrector.dark()
print 'saving dark.mrc'
mrc.write(finaldark, 'dark.mrc')

print 'BRIGHT'
query = leginondata.AcquisitionImageData(session=session, label='bright1')
images = db.query(query, readimages=False)
print 'Found %d images' % (len(images),)
for image in images:
	filename = image['filename']
	exptime = image['camera']['exposure time']
	print 'Inserting:  ', filename
	corrector.insertBright(image['image'], exptime)
finalflat = corrector.flat()
print 'saving flat.mrc'
mrc.write(finalflat, 'flat.mrc')
