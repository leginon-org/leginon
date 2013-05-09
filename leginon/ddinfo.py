#!/usr/bin/env python
import os
from leginon import leginondata
import sys
import glob

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

def getRawFrameSessionPathFromImagePath(imagepath):
	'''
	Raw Frames are saved by session under parallel directory of leginon.
	For example, leginon image path of '/mydata/leginon/13may01a/rawdata' uses
	'/mydata/frames/13may01a' to store frames.
	'''
	# backward compatibility
	if glob.glob(os.path.join(imagepath,'*.frames')):
		return imagepath
	baseframe_dirname = 'frames'
	pathbits = imagepath.split('/')
	leginonbasepath = '/'.join(pathbits[:-3])
	sessionrawdatapath = '/'.join(pathbits[-2:])
	rawframe_sessionpath = os.path.join(leginonbasepath,baseframe_dirname,sessionrawdatapath)
	return rawframe_sessionpath

def getRawFrameType(session_image_path):
	rawframe_basepath = getRawFrameSessionPathFromImagePath(session_image_path)
	entries = os.listdir(rawframe_basepath)
	for path in entries:
		if 'frame' in path and os.path.isdir(os.path.join(rawframe_basepath,path)):
			return 'singles'
	return 'stack'

if __name__ == '__main__':
	infopath = sys.argv[1]
	if infopath == 'all':
		saveAllPreviousToDatabase()
		sys.exit()
	imagename = sys.argv[2]
	imagename = imagename.split('.mrc')[0]
	imagedata = leginondata.AcquisitionImageData(filename=imagename).query(results=1)[0]
	saveImageDDinfoToDatabase(imagedata,infopath)
