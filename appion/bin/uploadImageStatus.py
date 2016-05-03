#!/usr/bin/env python

import os
import sys
from leginon import leginondata
from sinedon import directq

'''
This script runs much faster if the log file provided is a list of images which need to set status
'''
if len(sys.argv) != 3:
	print 'usage: uploadstatus.py <inputlist> <filetype>'
	print 'inputlist is a list of mrc file full path as known by leginon database'
	print 'filetype is one the three: "exemplar", "hide", "trash" sets status as named; "reverse" sets other images of the same preset to "hidden"'
	sys.exit()

######################################
# Variable section
######################################
# If the file is a list of all known bad images with fullpath and mrc extension, make this variable to 'bad' which will hide them.
# If the file is a list of better images, set to  'better' which will make them exemplars, and leave the status of the rest alone.
# If the file is a reversed selection of bad image, set it to 'good' which will make images not in the list hidden.
filetype = sys.argv[2]

# set filename
infilename = sys.argv[1]

#######################################################
statusmapping = {'exemplar':('exemplar',None), 'reverse':(None,'hidden'), 'hide':('hidden',None), 'trash':('trash',None)}

def setStatus(imagedata,status):
	v_results = leginondata.ViewerImageStatus(image=imagedata,session=imagedata['session']).query()
	if v_results:
		if status is None:
			# delete all existing status
			query = "delete from ViewerImageStatus where `REF|AcquisitionIMageData|image`=%d" % (imagedata.dbid)
			directq.complexMysqlQuery('leginondata',query)
		else:
			for vdata in v_results:
				if vdata['status'] != status:
					query = "update ViewerImageStatus set status='%s' where DEF_id=%d" % (status,vdata.dbid)
					directq.complexMysqlQuery('leginondata',query)
				else:
					pass
	else:
		if status is not None:
			# set viewer image status to hidden
			vdata = leginondata.ViewerImageStatus(image=imagedata,status=status,session=imagedata['session'])
			vdata.insert()
	print 'Set %s.mrc status to %s' % (imagedata['filename'], status)


infile = open(infilename,'r')
lines = infile.readlines()

if filetype != 'reverse':
	# Input file is a list of images to set status on
	for line in lines:
		mrcpath = line.split('.mrc')[0]
		# leginon style /mydata/leginon/sessionname/rawdata
		sessionname = os.path.basename(os.path.dirname(mrcpath).split('/')[-2])
		filename = os.path.basename(mrcpath)
		# query the session, too, for faster result
		qsession = leginondata.SessionData(name=sessionname)
		q = leginondata.AcquisitionImageData(session=qsession,filename=filename)
		r = q.query()
		if r:
			setStatus(r[0],statusmapping[filetype][0])
		else:
			print 'Query failed. image %s.mrc does not exist' % filename
else:
	# Input file is a list of all the good images
	sessionnames = set(map((lambda x: os.path.basename(os.path.dirname(x).split('/')[-2])),lines))
	# create good filename list for each session involved
	filedict = {}
	for sessionname in sessionnames:
		filedict[sessionname] = []
	for line in lines:
		if sessionname in line:
			filedict[sessionname].append(os.path.basename(line.split('.mrc')[0]))
	for sessionname in sessionnames:
		qsession = leginondata.SessionData(name=sessionname)
		# assume all images in the list have the same preset name
		first_image_filename = filedict[sessionname][0]
		try:
			imagedata = leginondata.AcquisitionImageData(filename=first_image_filename).query()[0]
			presetname = imagedata['preset']['name']
		except:
			# unknow preset, means manually acquired
			presetname = None
		# now do all of them
		images = leginondata.AcquisitionImageData(session=qsession).query()
		for imagedata in images:
			# check each image as part of the good filename list for the session
			if imagedata['filename'] not in filedict[sessionname]:
				if presetname:
					if imagedata['preset'] is None or imagedata['preset']['name'] != presetname:
						continue
				else:
					# not manual
					if imagedata['preset'] is not None:
						continue
			
				# set viewer image status to hidden
				setStatus(imagedata,statusmapping[filetype][1])
			else:
				setStatus(imagedata,statusmapping[filetype][0])
