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

def getUseBufferFromImage(imagedata):
	'''
	Buffer server is used if BufferHostData is defined for the camera
	and not disabled.
	'''
	r = leginondata.BufferHostData(ccdcamera=imagedata['camera']['ccdcamera']).query(results=1)
	if not r:
		return False
	return not r[0]['disabled']

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

def getBufferFrameSessionPathFromImage(imdata):
	'''
	Find the buffer host frame path defined by the session. The path has
	similar format as SessionData frame path, i.e., this is the directory
	containing all image movies.
	'''
	dcamera = imdata['camera']['ccdcamera']
	session = imdata['session']
	session_path = session['image path']
	# get buffer host name and base path
	r = leginondata.BufferHostData(ccdcamera=dcamera, disabled=False).query(results=1)
	if not r:
		return False
	host = r[0]
	# query
	r = leginondata.BufferFramePathData(session=session,host=host).query(results=1)
	if r:
		return r[0]['buffer frame path']
	# new record
	# leginon is a required directory
	legdir = 'leginon'
	legsplit = session_path.split(legdir)
	if len(legsplit) <= 1:
		return False
	# by using os.path.join, '/' need to be removed in legsplit[-1]
	session_part = legsplit[-1][1:]
	buffer_framepath = os.path.join(host['buffer base path'],session_part)

	q = leginondata.BufferFramePathData(session=session,host=host)
	q['buffer frame path'] = buffer_framepath
	q.insert()
	return buffer_framepath

def getRawFrameTypeFromSession(sessiondata):
	'''
	Use sessiondata to find the raw frame type.
	'''
	r = leginondata.BufferFramePathData(session=sessiondata).query(results=1)
	if  r:
		ftype = checkRawFrameTypeInPath(r[0]['buffer frame path'])
	if not r or ftype is False:
		ftype = checkRawFrameTypeInPath(sessiondata['frame path'])
	return ftype

def getRawFrameType(session_path):
	'''
	Determine Frame Type from either session image path or session frame path.
	'''
	rawframe_basepath = getRawFrameSessionPathFromSessionPath(session_path)
	return checkRawFrameTypeInPath(rawframe_basepath)

def checkRawFrameTypeInPath(image_frame_path):
	'''
	Use the content of the path to determine the fram types.
	False means unknown due to missing path, path not a directory or
	missing content to determine the type.
	'''
	if not os.path.isdir(image_frame_path):
		return False
	entries = os.listdir(image_frame_path)
	if not entries:
		return False
	for path in entries:
		if 'frame' in path and os.path.isdir(os.path.join(image_frame_path,path)):
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
		shift_bits = line.split('shift:')
		# Issue #4234
		if len(shift_bits) <=1:
			continue
		position_strings = shift_bits[1].split()
		position_x = float(position_strings[0])
		position_y = float(position_strings[1])
		positions.append((position_x,position_y))
	return positions

def calculateFrameShiftFromPositions(positions,running=1):
	# place holder for running first frame shift duplication
	offset = int((running-1)/2)
	shifts = offset*[None,]
	for p in range(len(positions)-1):
		shift = math.hypot(positions[p][0]-positions[p+1][0],positions[p][1]-positions[p+1][1])
		shifts.append(shift)
	# duplicate first and last shift for the end points if running
	for i in range(offset):
		shifts.append(shifts[-1])
		shifts[i] = shifts[offset]
	return shifts

def printDriftStats(filenamepattern, apix):

	filelist = glob.glob(filenamepattern+'_st_Log.txt')
	if len(filelist) == 0:
		return

	allshifts = []
	imgdata = leginondata.AcquisitionImageData(filename=filelist[0].split('_st_Log.txt')[0]).query()[0]
	fps = 1000.0 / imgdata['camera']['frame time']
	for filepath in filelist:
		positions = readPositionsFromAlignLog(filepath)
		shifts = calculateFrameShiftFromPositions(positions,running=1)
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
