#!/usr/bin/env python
import sys
from leginon import leginondata

if len(sys.argv) < 3:
	print "This program copies existing GatanK2Counting matrix and stage model calibrations to GatanK2Super"
	print "Usage copycal.py hostname high_tension"
	print "high tension is an integer in volts, i.e., 200000"
	sys.exit()

hostname = sys.argv[1]
high_tension = int(sys.argv[2])
if len(sys.argv) == 4:
	commit = int(sys.argv[3])
else:
	commit = 0

results = leginondata.InstrumentData(hostname=hostname,name='GatanK2Counting').query(results=1)
if not results:
	print "ERROR: incorrect hostname...."
	r = leginondata.InstrumentData(name='GatanK2Counting').query(results=1)
	if r:
		print "  Try %s instead" % r[0]['hostname']
	else:
		print "  No GatanK2Counting camera found"
	sys.exit()

sourcecam = results[0]
#sourcecam = leginondata.InstrumentData(hostname=hostname,name='GatanK2Super').query(results=1)[0]
destcam = leginondata.InstrumentData(hostname=hostname,name='GatanK2Super').query(results=1)[0]
pixelsize_scale = 2

def insertDest(newdata):
	print "Rerun the script with extra option of 1 at the end to insert to database"
	if commit == 1:
		newdata.insert()
	print ""
	return

onecaldata = leginondata.MatrixCalibrationData(ccdcamera=sourcecam).query(results=1)[0]
temdata = onecaldata['tem']
magsdata = leginondata.MagnificationsData(instrument=temdata).query(results=1)[0]

#PixelSizeCalibrationData
for mag in magsdata['magnifications']:
	# PixelSizeCarlibationData
	q = leginondata.PixelSizeCalibrationData(ccdcamera=sourcecam,magnification=mag)
	#q['high tension']=high_tension
	results = q.query(results=1)
	if results:
		caldata = results[0]
		newdata = leginondata.PixelSizeCalibrationData(initializer=caldata)
		newdata['ccdcamera'] = destcam
		pixelsize = caldata['pixelsize']
		pixelsize /= pixelsize_scale
		newdata['pixelsize'] = pixelsize
		print 'PixelSizeCalibrationData',newdata['magnification'],newdata['pixelsize']
		insertDest(newdata)

#StageModelCalibrationData
for axis in ('x','y'):
	results = leginondata.StageModelCalibrationData(ccdcamera=sourcecam,axis=axis).query(results=1)
	if results:
		newdata = leginondata.StageModelCalibrationData(initializer=results[0])
		newdata['ccdcamera'] = destcam
		print 'StageModelCalibrationData', newdata['period']
		insertDest(newdata)

	for mag in magsdata['magnifications']:
		q = leginondata.StageModelMagCalibrationData(ccdcamera=sourcecam,axis=axis,magnification=mag)
		q['high tension'] = high_tension
		results = q.query(results=1)
		if results:
			newdata = leginondata.StageModelMagCalibrationData(initializer=results[0])
			newdata['ccdcamera'] = destcam
			newdata['mean'] /= pixelsize_scale 
			print 'StageModelMagCalibrationData', newdata['magnification'],newdata['mean']
			insertDest(newdata)

for mag in magsdata['magnifications']:
	# MatrixCarlibationData
	for matrix_type in ('stage position','image shift','defocus','beam shift'):
		q = leginondata.MatrixCalibrationData(ccdcamera=sourcecam,magnification=mag,type=matrix_type)
		q['high tension']=high_tension
		results = q.query(results=1)
		if results:
			caldata = results[0]
			newdata = leginondata.MatrixCalibrationData(initializer=caldata)
			newdata['ccdcamera'] = destcam
			matrix = caldata['matrix']
			matrix /= pixelsize_scale
			newdata['matrix'] = matrix
			print 'MatrixCalibrationData', newdata['type'],newdata['magnification'],newdata['matrix'][0,0]
			insertDest(newdata)

raw_input('hit enter when ready to quit') 
