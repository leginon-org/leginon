#!/usr/bin/env python
import sys
import os
import time
import leginon.leginondata
import leginon.ddinfo
from appionlib import appiondata
from appionlib import apProject

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

def setAppiondb(sessionname):
	projectid = apProject.getProjectIdFromSessionName(sessionname)
	apProject.setDBfromProjectId(projectid, die=True)

def getAllImagesWithRawFrames(sessiondata):
	# get images with frame saved
	camq = leginon.leginondata.CameraEMData(session=sessiondata)
	camq['save frames'] = True
	imageq = leginon.leginondata.AcquisitionImageData(session=sessiondata,camera=camq)
	all = imageq.query()
	print '---------------'
	print "Total of %d images should have frames saved" % (len(all))
	#return [leginon.leginondata.AcquisitionImageData().direct_query(2271163)]
	return all

def getAlignedImageIds(imagedata):
	if '-a' in imagedata['filename']:
		alignimagepairdata = appiondata.ApDDAlignImagePairData(result=imagedata).query()[0]
		imagedata = alignimagepairdata['source']
	pairs = appiondata.ApDDAlignImagePairData(source=imagedata).query()
	aligned = map((lambda x: x['result'].dbid), pairs)
	return imagedata,aligned

def limitImagesToRemoveByStatus(all,status,sessiondata):
	to_remove = []
	to_remove_ids = []
	q = leginon.leginondata.ViewerImageStatus(session=sessiondata)
	if status == 'hidden':
		# pick hidden images
		q['status'] = 'hidden'
		hiddens = q.query()
		hiddenids = map((lambda x: x['image'].dbid), hiddens)
		for imagedata in all:
			source_imagedata, alignedimageids = getAlignedImageIds(imagedata)
			print '.'
			if len(alignedimageids)>0:
				# if one of the aligned image is not hidden, the source movie should not be remove
				if not (set(alignedimageids).issubset(set(hiddenids))):
					continue
			else:
				# when there is no alignment, then check if the source is hidden
				if not source_imagedata.dbid in hiddenids:
					continue
			if source_imagedata.dbid not in to_remove_ids:
				to_remove.append(source_imagedata)
				to_remove_ids.append(source_imagedata.dbid)

	elif status == 'not-best':
		# remove exemplar from images to be removed
		q['status'] = 'exemplar'
		bests = q.query()
		bestids = map((lambda x: x['image'].dbid), bests)
		for imagedata in all:
			source_imagedata, alignedimageids = getAlignedImageIds(imagedata)
			# only when none of the versions is exemplar would it be o.k. to remove
			if source_imagedata not in bestids and len(set(alignedimageids).intersection(set(bestids))) == 0:
				if source_imagedata.dbid not in to_remove_ids:
					to_remove.append(source_imagedata)
					to_remove_ids.append(source_imagedata.dbid)
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
	if to_remove:
		session_frames_path = leginon.ddinfo.getRawFrameSessionPathFromImagePath(to_remove[0]['session']['image path'])
	for imagedata in to_remove:
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
	print 'total  %d movies to be removed' % len(remove_list)
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
	setAppiondb(sessionname)
	all = getAllImagesWithRawFrames(sessiondata)
	if len(all) == 0:
		print 'No raw frame saved for this session'
		sys.exit()

	print '---------------'
	to_remove = limitImagesToRemoveByStatus(all,status,sessiondata)
	print 'to_remove',len(to_remove)
	remove_count,recent_count,not_exist_count = removeOldframes(to_remove,timelimit=3600*2)
	print '---------------'
	print "Total of %d frame directories removed." % (remove_count)
	print "Total of %d frame directories too new to remove." % (recent_count)
