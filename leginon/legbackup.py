#!/usr/bin/env python

import os
import glob
import leginondata

def getSession(session_name):
	ses = leginondata.SessionData(name=session_name)
	session = ses.query(results=1)[0]
	return session

imageclasses = (
	leginondata.AcquisitionImageData,
	leginondata.DarkImageData,
	leginondata.BrightImageData,
	leginondata.NormImageData,
)

def getDBImageInfo(session_data):
	allimages = []
	for imclass in imageclasses:
		imgq = imclass(session=session_data)
		imgs = imgq.query(readimages=False)
		allimages.extend(imgs)
	info = {}
	for image in allimages:
		mrcfilename = image['filename'] + '.mrc'
		fullpath = os.path.join(session_data['image path'], mrcfilename)
		size = os.path.getsize(fullpath)
		info[image['filename']] = {'file': fullpath, 'size': size}
	return info

def getDirImageInfo(path):
	mrcs = os.path.join(path, '*.mrc')
	print mrcs
	mrcfiles = glob.glob(mrcs)
	info = {}
	for mrcfile in mrcfiles:
		size = os.path.getsize(mrcfile)
		basename = os.path.basename(mrcfile)[:-4]
		info[basename] = {'filename':mrcfile, 'size': size}
	return info

def printImageInfo(infolist):
	for key,value in infolist.items():
		print key, value['size']

def backupSession(session_name, backup_dir):
	session_data = getSession(session_name)
	dbinfo = getDBImageInfo(session_name)
		

if __name__ == '__main__':
	import sys
	session_name = sys.argv[1]
	info = getDirImageInfo(session_name)
	printImageInfo(info)
