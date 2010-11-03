#!/usr/bin/env python
from appionlib import appiondata
from leginon import leginondata
import os
import sys

if len(sys.argv)<=1:
	print 'Usage:\n %s [experimentname] [sessionid]' % (sys.argv[0],)

session = sys.argv[1] 
preset = sys.argv[3]

sessionq = leginondata.SessionData(name=session)
presetq=leginondata.PresetData(name=preset)
imgquery = leginondata.AcquisitionImageData()
imgquery['preset']  = presetq
imgquery['session'] = sessionq
imgtree = imgquery.query(readimages=False)
partq = appiondata.ApContour()
sessiond = sessionq.query()

file = open('contourpickerData-' + session + '.txt','w')
file.write('session_id ' + sys.argv[2] + '\n')
file.write('usr_id ' + os.getlogin() + '\n')
file.write('experiment_name ' + session + '\n')
file.write('experiment_description ' + sessiond[0]['comment'] + '\n')
file.write('nimages ' + str(len(imgtree)) + '\n')

for imgdata in imgtree:
	file.write('START_IMAGE' + '\n')
	partq['image'] = imgdata
	partd = partq.query()
	if len(partd)>0:
		file.write('image_refID ' + str(partd[0]['image'].dbid) + '\n') 
	file.write('image_name ' + imgdata['filename'] + '\n') 
	if len(partd)>0:
		file.write('time_roi ' + str(partd[0].timestamp) + '\n') 
	#file.write('time_roi ' + partd[0]['DEF_timestamp'] + '\n') 
	file.write('dfac = 1\n')
	maxversion = 0
	numparticles = 0
	for part in partd:
		if int(part['version'])>maxversion and part['runID']==sys.argv[2]:
			maxversion = int(part['version'])
	for part in partd:
		if int(part['version'])==maxversion and part['runID']==sys.argv[2]:
			numparticles+=1
	file.write('version_id ' + str(maxversion) + '\n')
	file.write('ncontours ' + str(numparticles) + '\n')
	pointq = appiondata.ApContourPoint()
	for part in partd:
		if int(part['version'])==maxversion and part['runID']==sys.argv[2]:
	#		file.write('contour_number ' + )
			file.write('method_used ' + part['method'] + ' ')
			pointq['contour'] = part
			pointd = pointq.query()
			for point in pointd:
				file.write(str(point['x']) + ',' + str(point['y']) + ';')
			file.write('\n')
	file.write('END_IMAGE' + '\n')
	
