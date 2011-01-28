#!/usr/bin/env python

import MySQLdb
import sinedon.dbconfig
import leginon.leginondata
import time
import numpy
import sinedon

sinedon.existing_file = 'skip'

baseconfig = {'user': 'pulokas', 'passwd': 'jim5my', 'host': 'cronus4'}

def resetTestDB():
	db = MySQLdb.connect(**baseconfig)
	for dbname in ('transtest1', 'transtest2', 'importmapping'):
		print 'dropping', dbname
		cur = db.cursor()
		cur.execute('drop database %s' % (dbname,))
		print 'creating', dbname
		cur = db.cursor()
		cur.execute('create database %s' % (dbname,))

def initTestDB():
	### first database
	sinedon.dbconfig.setConfig('leginondata', db='transtest1', **baseconfig)

	##### session1
	session1 = leginon.leginondata.SessionData(name='session1')
	session1['image path'] = '/home/pulokas/dev/myami-trunk/sinedon/images'
	session1.insert()

	# session1 simulate target
	target = leginon.leginondata.AcquisitionImageTargetData(session=session1, number=1)
	target.insert()

	time.sleep(1.0)

	# session1 image on that target
	image = leginon.leginondata.AcquisitionImageData(session=session1, target=target, filename='session1.file1')
	image['image'] = numpy.arange(64)
	image['image'].shape = 8,8
	image.insert()

	time.sleep(1.0)

	#### session2
	session2 = leginon.leginondata.SessionData(name='session2')
	session2.insert()

	# simulate target
	target = leginon.leginondata.AcquisitionImageTargetData(session=session2, number=1)
	target.insert()

	time.sleep(1.0)

	# image on that target
	image = leginon.leginondata.AcquisitionImageData(session=session2, target=target, filename='session2.file1')
	image.insert()

	time.sleep(0.2)

	# target on that image
	target = leginon.leginondata.AcquisitionImageTargetData(session=session2, image=image, number=1)
	target.insert()

	time.sleep(1.0)

	# image on that target
	image = leginon.leginondata.AcquisitionImageData(session=session2, target=target, filename='session2.file1.file1')
	image.insert()

	time.sleep(1.0)

	# insert target
	target = leginon.leginondata.AcquisitionImageTargetData(session=session2, number=5)
	target.insert()
	# force insert duplicate of that target
	target = leginon.leginondata.AcquisitionImageTargetData(session=session2, number=5)
	target.insert(force=True)

	### second database
	sinedon.dbconfig.setConfig('leginondata', db='transtest2', **baseconfig)
	# insert session1
	session1 = leginon.leginondata.SessionData(name='session1')
	session1.insert()
	# insert 3 targets and images
	for i in range(3):
		target = leginon.leginondata.AcquisitionImageTargetData(session=session1)
		target.insert(force=True)
		filename = 'session1.file%d' % (i,)
		image = leginon.leginondata.AcquisitionImageData(session=session1, target=target, filename=filename)
		image.insert()

def test2():
	import sinedon
	import sinedon.data
	import leginon.leginondata

	resetTestDB()
	initTestDB()

	sinedon.setConfig('importdata', db='importmapping')

	print '********************************************************'

	sinedon.setConfig('leginondata', db='dbemdata')

	session = leginon.leginondata.SessionData(name='11jan12c')
	a = leginon.leginondata.AcquisitionImageData(session=session)
	a = a.query(readimages=False, results=1)
	a = a[0]
	tem = a['scope']['tem']
	cam = a['camera']['ccdcamera']
	mag = a['scope']['magnification']
	
	pcal = leginon.leginondata.PixelSizeCalibration(tem=tem, ccdcamera=cam, magnification=mag)
	pcal = pcal.query(results=1)
	if pcal:
		pcal = pcal[0]
	else:
		raise RuntimeError('no cal')

	sinedon.setConfig('leginondata', db='transtest2')

	# insert a1 into db2
	pcal.insert()

def test3():
	import sinedon
	import sinedon.data
	import leginon.leginondata

	resetTestDB()
	initTestDB()

	sinedon.setConfig('importdata', db='importmapping')

	print '********************************************************'

	sinedon.setConfig('leginondata', db='dbemdata')

	session = leginon.leginondata.SessionData(name='11jan12c')
	a = leginon.leginondata.AcquisitionImageData(session=session)
	a = a.query(readimages=False)

	t = leginon.leginondata.AcquisitionImageTargetData(session=session)
	t = t.query(readimages=False)

	sinedon.setConfig('leginondata', db='transtest2')

	# insert a1 into db2
	t.reverse()
	a.reverse()
	for t2 in t:
		t2.insert()
	for a2 in a:
		a2.insert()

# test altering data before copy
def test4():
	import sinedon
	import sinedon.data
	import leginon.leginondata

	resetTestDB()
	initTestDB()

	sinedon.setConfig('leginondata', db='transtest1')

	ses = leginon.leginondata.SessionData(name='session2')
	ses = ses.query()
	ses = ses[0]

	images = leginon.leginondata.AcquisitionImageData(session=ses)
	images = images.query()
	targets = leginon.leginondata.AcquisitionImageTargetData(session=ses)
	targets = targets.query()

	ses.__setitem__('name', 'session2b', force=True)

	sinedon.setConfig('leginondata', db='transtest2')

	for target in targets:
		target.insert()
	for image in images:
		image.insert()


if __name__ == '__main__':
	test4()
