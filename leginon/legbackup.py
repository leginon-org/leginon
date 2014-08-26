#!/usr/bin/env python

import os
import shutil
import errno
import glob
from leginon import leginondata

def mkdirs(newdir):
	originalumask = os.umask(02)
	try:
		os.makedirs(newdir)
	except OSError, err:
		os.umask(originalumask)
		if err.errno != errno.EEXIST or not os.path.isdir(newdir) and os.path.splitdrive(newdir)[1]:
			raise
	os.umask(originalumask)

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
		try:
			size = os.path.getsize(fullpath)
		except:
			print 'skipping unaccessible file: ', fullpath
			continue
		info[image['filename']] = {'file': fullpath, 'size': size}
	return info

def getDirImageInfo(path):
	mrcs = os.path.join(path, '*.mrc')
	mrcfiles = glob.glob(mrcs)
	info = {}
	for mrcfile in mrcfiles:
		size = os.path.getsize(mrcfile)
		basename = os.path.basename(mrcfile)[:-4]
		info[basename] = {'file':mrcfile, 'size': size}
	return info

def printImageInfo(infolist):
	for key,value in infolist.items():
		print key, value['size']

def backupSession(session_name, backup_base):
	try:
		session_data = getSession(session_name)
	except:
		session_data = None
	if not session_data:
		print 'could not find session %s in database' % (session_name,)
		return

	previous = getBackupInfo(session_data)
	if previous:
		print 'Previous backups for this session:'
		for p in previous:
			print '  ', p[0], p[1]
		ans = raw_input('Do you with to continue this the current backup? (y/n): ')
		if ans != 'y':
			print 'aborting'
			return
	else:
		print 'No previous backup of this session'

	dbinfo = getDBImageInfo(session_data)
	print 'DB***************'
	printImageInfo(dbinfo)
	backupdir = os.path.join(backup_base, session_name)
	mkdirs(backupdir)
	backupinfo = getDirImageInfo(backupdir)
	print 'DIR***************'
	printImageInfo(backupinfo)

	for key,value in dbinfo.items():
		if key in backupinfo and backupinfo[key]['size'] == value['size']:
			print 'file already backed up: ', key+'.mrc'
		else:
			backupfile = os.path.join(backupdir, key+'.mrc')
			try:
				shutil.copyfile(value['file'], backupfile)
				print 'copied:  ', backupfile
			except:
				print 'unable to make backup:  ', backupfile

	storeBackupInfo(session_data, backupdir)

def storeBackupInfo(session_data, path):
	b = leginondata.ImageBackup(session=session_data, path=path)
	b.insert(force=True)

def getBackupInfo(session_data):
	b = leginondata.ImageBackup(session=session_data)
	backups = b.query()
	paths = []
	for backup in backups:
		paths.append((backup.timestamp, backup['path']))
	return paths



if __name__ == '__main__':
	import sys
	session_name = sys.argv[1]
	backupdir = sys.argv[2]
	backupSession(session_name, backupdir)
