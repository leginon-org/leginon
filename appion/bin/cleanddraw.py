#!/usr/bin/env python
import sys
import os
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
	all_source = []
	for imagedata in all:
		sourcedata, results = getAlignedImageIds(imagedata)
		# include only non-aligned images
		if len(results) == 0 or sourcedata.dbid == imagedata.dbid:
			all_source.append(imagedata)
		
	print '---------------'
	print "Total of %d images should have frames saved" % (len(all_source))
	return all_source

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
	statusmap = {'hidden':['hidden'],'trash':['trash'],'rejected':['hidden','trash']}
	if status in statusmap.keys():
		hiddenids = []
		# pick hidden images
		for vstatus in statusmap[status]:
			q = leginon.leginondata.ViewerImageStatus(session=sessiondata)
			q['status'] = vstatus
			hiddens = q.query()
			hiddenids.extend(map((lambda x: x['image'].dbid), hiddens))
		hiddenids = list(set(hiddenids))
		hiddenids.sort()
		
		for imagedata in all:
			source_imagedata, alignedimageids = getAlignedImageIds(imagedata)
			sys.stderr.write(".")
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

def	removeFrames(to_remove):
	not_exist_count = 0
	remove_count = 0
	remove_list = []
	if to_remove:
		session_frames_path = to_remove[0]['session']['frame path']
	for imagedata in to_remove:
		framedir = os.path.join(session_frames_path,imagedata['filename']+'.frames')
		if not os.path.isdir(framedir):
			framepath = os.path.join(session_frames_path,imagedata['filename']+'.frames.mrc')
			if os.path.isfile(framepath):
				print framepath,' will be removed'
				remove_list.append((framepath,''))
			else:
				# aligned images do not have raw frames in its name
				not_exist_count += 1
		else:
			files = os.listdir(framedir)
			# removing files and then directory
			print framedir,' will be removed'
			remove_list.append((framedir,files))
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
	return remove_count,not_exist_count

if __name__ == '__main__':
	valid_status = ('hidden','trash','rejected','not-best','all')
	if len(sys.argv) != 3:
		print 'Usage: cleanddraw.py sessionname status'
		print '  sessionname (str): Leginon session name'
		print '  status (choice): "hidden", "trash", "rejected", "not-best", or "all"'
		print '  "rejected" includes both "hidden" and "trash".'
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
	remove_count,not_exist_count = removeFrames(to_remove)
	print '---------------'
	print "Total of %d frame directories removed." % (remove_count)
