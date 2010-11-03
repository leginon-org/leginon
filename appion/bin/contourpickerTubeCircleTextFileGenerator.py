#!/usr/bin/env python
from appionlib import appiondata
from leginon import leginondata
import sys

if len(sys.argv)<=1:
	print 'Usage: %s [experimentname] [sessionid]' % (sys.argv[0],)

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

file = open('contourpickerTubeCircleData-' + session + '.txt','w')
file.write('experiment_name ' + session + '\n')
file.write('experiment_description ' + sessiond[0]['comment'] + '\n')

numimages = 0
for imgdata in imgtree:
	partq['image'] = imgdata
	partd = partq.query()
	if len(partd)>0:
		numimages+=1
file.write('nimages ' + str(numimages) + '\n')

numparticles = 0.0
numcircles = 0.0
numtubes = 0.0
for imgdata in imgtree:
	partq['image'] = imgdata
	partd = partq.query()
	maxversion = 0
	for part in partd:
		if int(part['version'])>maxversion and part['runID']==sys.argv[2]:
			maxversion = int(part['version'])
	for part in partd:
		if int(part['version'])==maxversion and part['runID']==sys.argv[2]:
			numparticles+=1
			if part['particleType']=='Circle':
				numcircles+=1	
			if part['particleType']=='Tube':
				numtubes+=1	
file.write('nparticles ' + str(numparticles) + '\n')
percenttubes = numtubes/numparticles
percent = percenttubes*100
percent *= 100
percent = int(percent)
percent = percent/100.0
file.write('%tubes ' + str(percent))
	
