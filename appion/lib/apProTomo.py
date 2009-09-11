#!/usr/bin/env python

import math
import numpy


def parseTilt(tiltfile):
	f=open(tiltfile)
	lines=f.readlines()
	f.close()
	
	#first loop through file to find image names
	#using two loops for complete parsing for ease of coding
	imagedict={}
	parameterdict={}
	for n in lines:
		words=n.split()
		if 'FILE' in words:
			imagenum=int(words[1])
			imagedict[imagenum]={'filename':words[3]}
		elif 'PSI' in words:
			parameterdict['psi']=float(words[1])
		elif 'THETA' in words:
			parameterdict['theta']=float(words[1])
		elif 'PHI' in words:
			parameterdict['phi']=float(words[1])
		elif 'TILT' in words and 'AZIMUTH' in words:
			parameterdict['azimuth'] = float(words[2])
		elif 'TILT' in words and 'SERIES' in words:
			seriesname=words[2]
			
	for n in lines:
		words=n.split()
		if 'ORIGIN' in words:
			imagenum=int(words[1])
			xcoord=float(words[4])
			ycoord=float(words[5])
			imagedict[imagenum]['x']=xcoord
			imagedict[imagenum]['y']=ycoord
		elif 'TILT' in words and 'ANGLE' in words:
			imagenum=int(words[1])
			tilt=float(words[4])
			rotation=float(words[6])
			imagedict[imagenum]['tilt']=tilt
			imagedict[imagenum]['rotation']=rotation			
	return imagedict, parameterdict, seriesname

def writeTiltFile(outfilename, seriesname, imagedict, parameterdict=False):
	f=open(outfilename,'w')
	f.write('\n')
	f.write( ' TILT SERIES %s\n' % seriesname)
	if parameterdict:
		f.write('\n\n   PARAMETER\n')
		f.write('     PSI   %8.3f\n' % parameterdict['psi'])
		f.write('     THETA %8.3f\n' % parameterdict['theta'])
		f.write('     PHI   %8.3f\n' % parameterdict['phi'])
		f.write('\n\n   PARAMETER\n\n')
		f.write('     TILT AZIMUTH %8.3f\n' % parameterdict['azimuth'])
	else:
		f.write('\n\n   PARAMETER\n\n')
		f.write('     TILT AZIMUTH %8.3f\n' % 0.0)
	f.write('\n\n')
	keys=imagedict.keys()
	keys.sort()
	for n in keys:
		f.write('   IMAGE %-5d FILE %s\n' % (n, imagedict[n]['filename']))
	f.write('\n')
	for n in keys:
		f.write('   IMAGE %-5d ORIGIN  [ %8.3f %8.3f ]\n' % (n, imagedict[n]['x'], imagedict[n]['y']))
	f.write('\n')
	for n in keys:
		f.write('   IMAGE %-5d TILT ANGLE %8.3f   ROTATION %8.3f\n' % (n, imagedict[n]['tilt'], imagedict[n]['rotation']))
	f.write('\n\n\n END\n\n')
	f.close()

def createRefineDefaults(imgref, indir, outdir, tmp=''):
	refinedict={}
	refinedict['imgref']=imgref
	refinedict['bckbody']=100
	refinedict['alismp']=1

	refinedict['alibox_x']=512
	refinedict['alibox_y']=512

	refinedict['corbox_x']=64
	refinedict['corbox_y']=64

	refinedict['imgmsktype']=''

	refinedict['imgmsk_x']=''
	refinedict['imgmsk_y']=''
	refinedict['imgmskapo_x']=''
	refinedict['imgmskapo_y']=''

	refinedict['refmsktype']=''
	
	refinedict['refmsk_x']=''
	refinedict['refmsk_y']=''
	refinedict['refmskapo_x']=''
	refinedict['refmskapo_y']=''

	refinedict['hipass_x']=0.01
	refinedict['hipass_y']=0.01
	refinedict['hipassapo_x']=0.05
	refinedict['hipassapo_y']=0.05
	
	refinedict['lopass_x']=0.2
	refinedict['lopass_y']=0.2
	refinedict['lopassapo_x']=0.05
	refinedict['lopassapo_y']=0.05
	
	refinedict['cormod']='xcf'
	
	refinedict['guess']='false'
	
	refinedict['lastitr']=''
	
	refinedict['reflow']=''
	refinedict['refhigh']=''
	
	refinedict['fitmin']=''
	refinedict['fitmax']=''
	
	refinedict['map_x']=512
	refinedict['map_y']=512
	refinedict['map_z']=512
	
	refinedict['mapsmp']=1
	
	refinedict['sffx']='.img'
	refinedict['inp']=indir+'/'
	refinedict['out']=outdir+'/'
	refinedict['tmp']=tmp
	refinedict['cor']='.xcf'
	return refinedict
	
def writeRefineParamFile(refinedict,paramfile):
	f=open(paramfile,'w')
	keys=refinedict.keys()
	for key in keys:
		val=str(refinedict[key])
		f.write('%s=%s\n' % (key, val))
	f.close()

def convertGlobalTransformProtomoToImod(protomoprefix,imodprefix, center=(1024,1024)):
	# need to get the center from the file when this is called
	protomotltfile = protomoprefix+"-fitted.tlt"
	imodtltfile = imodprefix+".prexg"
	f=open(protomotltfile,'r')
	fout = open(imodtltfile,'w')
	lines = f.readlines()
	rotations = []
	origins = []
	tiltaz = 90.0
	allaffines = []
	for line in lines:
		if (line.find('ORIGIN') >= 0):
			items = line.split()
			origins.append((float(items[-3]),float(items[-2]))) 
		elif (line.find('ROTATION') >= 0):
			items = line.split()
			rotations.append(float(items[-1]))
		elif (line.find('TILT AZIMUTH') >= 0):
			items = line.split()
			tiltaz = float(items[-1])
	#protomo tilt azimuth vertical is 90 deg, imod is 0 deg
	tiltazrad = (tiltaz - 90.0) * 3.14159 / 180.0
	tiltazaffine = numpy.matrix([[math.cos(tiltazrad),-math.sin(tiltazrad),0],[math.sin(tiltazrad),math.cos(tiltazrad),0],[0,0,1]])
	shiftsum0 = 0
	shiftsum1 = 0
	for i in range(0,len(rotations)):
		theta = - (rotations[i]) * 3.14159 / 180.0
		rotationaffine = numpy.matrix([[math.cos(theta),-math.sin(theta),0],[math.sin(theta),math.cos(theta),0],[0,0,1]])
		shiftaffine = numpy.matrix([[1,0,origins[i][0]],[0,1,origins[i][1]],[0,0,1]])
		centeraffine = numpy.matrix([[1,0,center[0]],[0,1,center[1]],[0,0,1]])
		totalaffine = shiftaffine.I * rotationaffine * tiltazaffine.I * centeraffine
		imodaffine = totalaffine
		allaffines.append(imodaffine)
		shiftsum0 += imodaffine[0,2]
		shiftsum1 += imodaffine[1,2]
	# imod global shift need to be referenced to the average shift or the series
	shiftavg0 = shiftsum0 / len(rotations)
	shiftavg1 = shiftsum1 / len(rotations)
	for i in range(0,len(rotations)):
		imodaffine = allaffines[i]
		shift = (imodaffine[0,2] - shiftavg0, imodaffine[1,2] - shiftavg1)
		outline = '%11.7f %11.7f %11.7f %11.7f %11.3f %11.3f\n' % (
			imodaffine[0,0],imodaffine[0,1],imodaffine[1,0],imodaffine[1,1],shift[0],shift[1])
		fout.write(outline)
	fout.close()
