#!/usr/bin/env python
import sys
import os
import time
import leginon.leginondata
import leginon.ddinfo

def getSessionData(sessionname):
	# get Session
	q = leginon.leginondata.SessionData(name=sessionname)
	r = q.query()
	if not r:
		print 'ERROR: Session does not exist.'
		sys.exit(1)
	sessiondata = r[0]
	print '---------------'
	print 'Session %s belongs to %s %s' % (sessiondata['name'],sessiondata['user']['firstname'],sessiondata['user']['lastname'])
	print 'with comment "%s"' % (sessiondata['comment'])
	print '---------------'
	session_verified = raw_input('Is this the session you want to work on? (Y/N)')
	if session_verified.upper() != 'Y':
		print 'aborted'
		sys.exit()
	return sessiondata

def getAllImagesWithRawFrames(sessiondata):
	# get images with frame saved
	camq = leginon.leginondata.CameraEMData(session=sessiondata)
	camq['save frames'] = True
	imageq = leginon.leginondata.AcquisitionImageData(session=sessiondata,camera=camq)
	all = imageq.query()
	print '---------------'
	print "Total of %d images should have frames saved" % (len(all))
	return all

def limitImagesToRemoveByStatus(all,status,sessiondata):
	to_remove = []
	q = leginon.leginondata.ViewerImageStatus(session=sessiondata)
	if status == 'hidden':
		# pick hidden images
		q['status'] = 'hidden'
		hiddens = q.query()
		hiddenids = map((lambda x: x['image'].dbid), hiddens)
		for imagedata in all:
			if imagedata.dbid in hiddenids:
				to_remove.append(imagedata)

	elif status == 'not-best':
		# remove exemplar from images to be removed
		q['status'] = 'exemplar'
		bests = q.query()
		bestids = map((lambda x: x['image'].dbid), bests)
		for imagedata in all:
			if imagedata.dbid not in bestids:
				to_remove.append(imagedata)
	elif status == 'all':
		to_remove = all
	else:
		print 'ERROR: Unknown status option'
		sys.exit(1)
	return to_remove

def	removeOldframes(to_remove,timelimit=3600*2):
	timenow = time.time()
	not_exist_count = 0
	remove_count = 0
	recent_count = 0
	remove_list = []
	for imagedata in to_remove:
		session_frames_path = leginon.ddinfo.getRawFrameSessionPathFromImagePath(imagedata['session']['image path'])
		framedir = os.path.join(session_frames_path,imagedata['filename']+'.frames')
		if not os.path.isdir(framedir):
			framepath = os.path.join(session_frames_path,imagedata['filename']+'.frames.mrc')
			if os.path.isfile(framepath):
				filestat = os.stat(framepath)
				if (timenow - timelimit) > filestat.st_mtime:
					remove_list.append((framepath,''))
				else:
					recent_count += 1
			else:
				# aligned images do not have raw frames in its name
				not_exist_count += 1
		else:
			ok_to_remove = True
			files = os.listdir(framedir)
			# Check if any file in the directory is last modified within the timelimit
			for file in files:
				framepath = os.path.join(framedir,file)
				filestat = os.stat(framepath)
				if (timenow - timelimit) < filestat.st_mtime:
					ok_to_remove = False
			# removing files and then directory
			if ok_to_remove:
				print framedir,' will be removed'
				remove_list.append((framedir,files))
			else:
				recent_count += 1
	if len(remove_list) > 0:
		# Last chance to back out
		want_to_remove = raw_input('Are you sure? (Y/N)')
		if want_to_remove.upper() == 'Y':
			for framedir,files in remove_list:
				print '...removing %s' % (framedir)
				for file in files:
					framepath = os.path.join(framedir,file)
					os.remove(framepath)
				if os.path.isdir(framedir):
					os.rmdir(framedir)
				else:
					# framedir is a file
					os.remove(framedir)
				if not os.path.exists(framedir):
					remove_count += 1
				else:
					print framedir,' is still there. Something is wrong'
					sys.exit(1)
	return remove_count,recent_count,not_exist_count

if __name__ == '__main__':
	valid_status = ('hidden','not-best','all')
	if len(sys.argv) != 3:
		print 'Usage: cleanddraw.py sessionname status'
		print '  sessionname (str): Leginon session name'
		print '  status (choice): "hidden", "not-best", or "all"'
		sys.exit()
	# check input
	sessionname = sys.argv[1]
	status = sys.argv[2]
	if status not in valid_status:
		print 'ERROR: Unknown status option'
		sys.exit(1)

	sessiondata = getSessionData(sessionname)
	all = getAllImagesWithRawFrames(sessiondata)
	if len(all) == 0:
		print 'No raw frame saved for this session'
		sys.exit()

	print '---------------'
	to_remove = limitImagesToRemoveByStatus(all,status,sessiondata)

	remove_count,recent_count,not_exist_count = removeOldframes(to_remove,timelimit=3600*2)
	print '---------------'
	print "Total of %d frame directories removed." % (remove_count)
	print "Total of %d frame directories too new to remove." % (recent_count)
