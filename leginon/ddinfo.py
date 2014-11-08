#!/usr/bin/env python
import os
from leginon import leginondata
import sys
import glob
import math

def parseInfoTxt(infopath):
	if not os.path.isfile(infopath):
		return False
	infile = open(infopath,'r')
	params = {}
	for line in infile:
		bits = line.split('=', 1)  # split on first =
		bits = map(str.strip, bits)  # strip off white space
		params[bits[0]]=bits[1]
	return params

def commitToDatabase(imagedata,params):
	cameradata = imagedata['camera']
	for key in params.keys():
		qkey = leginondata.DDinfoKeyData(name=key)
		qvalue = leginondata.DDinfoValueData(camera=cameradata, infokey=qkey,infovalue=params[key])
		qvalue.insert()

def saveImageDDinfoToDatabase(imagedata,infopath):
	params = parseInfoTxt(infopath)
	if params:
		commitToDatabase(imagedata,params)

def saveAllPreviousToDatabase():
	qcam = leginondata.CameraEMData()
	qcam['save frames'] = True
	acqimages = leginondata.AcquisitionImageData(camera=qcam).query()
	for imagedata in acqimages:
		# check for frames dir
		camdata = imagedata['camera']
		session = imagedata['session']
		impath = session['image path']
		fname = imagedata['filename']
		infoname = os.path.join(impath, fname+'.frames', 'info.txt')
		if os.path.exists(infoname):
			# check for existing ddinfo in db
			info = leginondata.DDinfoValueData(camera=camdata).query()
			if not info:
				print 'saving:', infoname
				saveImageDDinfoToDatabase(imagedata, infoname)

def saveSessionDDinfoToDatabase(sessiondata):
	qcam = leginondata.CameraEMData(session=sessiondata)
	qcam['save frames'] = True
	acqimages = leginondata.AcquisitionImageData(camera=qcam).query()
	for imagedata in acqimages:
		infopath = os.path.join(sessiondata['image path'],imagedata['filename']+'.frames','info.path')
		saveImageDDinfoToDatabase(imagedata,infopath)

def getRawFrameSessionPathFromSessionPath(session_path):
	'''
	Raw Frames are saved by session under parallel directory of leginon.
	For example, leginon image path of '/mydata/leginon/13may01a/rawdata' uses
	'/mydata/frames/13may01a' to store frames.

	This function allows frame path to be passed in as well.

	Possible senerios:
	1. input: /mydata/leginon/mysession/rawdata;  output: /mydata/frames/mysession/rawdata.
	2. input: /mydata/leginon/myuser/mysession/rawdata;  output: /mydata/frames/myuser/mysession/rawdata.
	3. input: /mydata/frames/mysession/rawdata; output=input
	'''
	# goal is to replace legdir with framedir
	framedir = 'frames'
	legdir = 'leginon'

	## Taking care of multiple legdirs in path...
	## Only replace the final legdir with framedir
	legsplit = session_path.split(legdir)
	framesplit = session_path.split(framedir)
	# Handles the case session frame path is the input
	if len(legsplit) == 1 and len(framesplit) > 1 and os.path.isdir(framesplit[0]):
		return session_path
	# Actual replacement
	legjoin = legdir.join(legsplit[:-1])
	rawframe_sessionpath = legjoin + framedir + legsplit[-1]
	return rawframe_sessionpath

def getRawFrameType(session_path):
	'''
	Determine Frame Type from either session image path or session frame path.
	'''
	rawframe_basepath = getRawFrameSessionPathFromSessionPath(session_path)
	entries = os.listdir(rawframe_basepath)
	for path in entries:
		if 'frame' in path and os.path.isdir(os.path.join(rawframe_basepath,path)):
			return 'singles'
	return 'stack'

def readPositionsFromAlignLog(filename):
	'''
	Reads from dosefgpu_driftcorr log file the shifts applied to each frame
	'''
	f = open(filename)
	text = f.read()
	lines = text[text.find('Sum Frame'):text.find('Save Sum')].split('\n')[1:-2]
	positions = []
	for line in lines:
		position_strings = line.split('shift:')[-1].split()
		positions.append((float(position_strings[0]),float(position_strings[1])))
	return positions

def printDriftStats(filenamepattern, apix):

	filelist = glob.glob(filenamepattern+'_st_Log.txt')
	if len(filelist) == 0:
		return

	allshifts = []
	imgdata = leginondata.AcquisitionImageData(filename=filelist[0].split('_st_Log.txt')[0]).query()[0]
	fps = 1000.0 / imgdata['camera']['frame time']
	for file in filelist:
		positions = readPositionsFromAlignLog(file)
		positions.insert(0,positions[0])
		shifts = []
		for i in range(len(positions)-1):
			shifts.append(math.hypot(positions[i+1][0] - positions[i][0], positions[i+1][1] - positions[i][1]))
		allshifts.append(shifts)

	import numpy
	a = numpy.array(allshifts)
	for d in range(a.shape[1]):
		suba = a[:,d]
		print "frame_%d %6.4f %6.4f" % (d,suba.mean()*apix*fps,suba.std()*apix*fps)

if __name__ == '__main__':
	infopath = sys.argv[1]
	if infopath == 'all':
		saveAllPreviousToDatabase()
		sys.exit()
	imagename = sys.argv[2]
	imagename = imagename.split('.mrc')[0]
	imagedata = leginondata.AcquisitionImageData(filename=imagename).query(results=1)[0]
	saveImageDDinfoToDatabase(imagedata,infopath)
