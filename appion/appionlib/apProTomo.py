#!/usr/bin/env python

import math
import numpy
import os
from appionlib import apParam
from appionlib import apTomo
from appionlib import apImod
from appionlib import apDisplay
from appionlib import appiondata

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

def convertShiftsToParams(tilts,shifts,center,imagenames=None):
	imagedict={}
	parameterdict={}
	for i, shift in enumerate(shifts):
		imagedict[i]={}
		imagedict[i]['x']=shift['x']+center['x']
		imagedict[i]['y']=shift['y']+center['y']
		imagedict[i]['tilt']=tilts[i]
		imagedict[i]['rotation']=0.0
		if imagenames:
			imagedict[i]['filename']=imagenames[i]
		parameterdict['psi']=0.0
		parameterdict['theta']=0.0
		parameterdict['phi']=0.0
		parameterdict['azimuth']=90.0
	return imagedict,parameterdict,None

def linkImageFiles(imgtree,rawdir):
	filenamelist = []
	for imagedata in imgtree:
		#set up names
		imgpath=imagedata['session']['image path']
		presetname=imagedata['preset']['name']
		imgprefix=presetname+imagedata['filename'].split(presetname)[-1]
		imgname=imgprefix+'.img'
		filenamelist.append(imgprefix)
		
		#create symlinks to files
		linkedpath = os.path.join(rawdir,imgname)
		if os.path.islink(linkedpath):
			os.remove(linkedpath)
		if not os.path.isfile(linkedpath):
			os.symlink(os.path.join(imgpath,imagedata['filename']+'.mrc'),linkedpath)
	return filenamelist

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
		f.write('\n\n   PARAMETER\n')
		f.write('     PSI   %8.3f\n' % 0.0)
		f.write('     THETA %8.3f\n' % 0.0)
		f.write('     PHI   %8.3f\n' % 0.0)
		f.write('\n\n   PARAMETER\n\n')
		f.write('     TILT AZIMUTH %8.3f\n' % 90.0)
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

def resetTiltParams(tiltparams, oldtiltparams, goodstart, goodend):
	imagedict = tiltparams[0]
	oldimagedict = oldtiltparams[0]
	for n in range(0,len(imagedict)):
		if n < goodstart or n > goodend:
			imagedict[n]['x'] = oldimagedict[n]['x']
			imagedict[n]['y'] = oldimagedict[n]['y']
			if n < goodstart:
				imagedict[n]['rotation'] = imagedict[goodstart]['rotation']
			else:
				imagedict[n]['rotation'] = imagedict[goodend]['rotation']
	return imagedict, tiltparams[1],tiltparams[2]

def createRefineDefaults(numimgs, indir, outdir, tmp=''):
	refinedict={}
	refinedict['imgref']= numimgs/2
	refinedict['bckbody']=200
	refinedict['alismp']=1

	refinedict['alibox_x']=512
	refinedict['alibox_y']=512

	refinedict['corbox_x']=128
	refinedict['corbox_y']=128

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
	
	refinedict['cormod']='pcf'
	
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
	
def updateRefineParams(refinedict,imgshape,sample,region,refimg):
	refinedict['alismp']=sample
	refinedict['alibox_x']=int(imgshape[1] * region * 0.01/sample)
	refinedict['alibox_y']=int(imgshape[0] * region * 0.01/sample)
	refinedict['imgref']= refimg
	return refinedict

def setProtomoDir(rootdir):
	print "Setting up directories"
	rawdir=os.path.join(rootdir, 'raw')
	aligndir=os.path.join(rootdir,'align')
	outdir=os.path.join(rootdir,'out')
	cleandir=os.path.join(rootdir,'clean')
	apParam.createDirectory(aligndir,warning=False)
	apParam.createDirectory(outdir,warning=False)
	apParam.createDirectory(cleandir,warning=False)
	apParam.createDirectory(rawdir,warning=False)
	return aligndir, rawdir

def writeRefineParamFile(refinedict,paramfile):
	f=open(paramfile,'w')
	keys=refinedict.keys()
	keys.sort()
	for key in keys:
		val=str(refinedict[key])
		f.write('%s=%s\n' % (key, val))
	f.close()

def parseRefineParamFile(paramfile):
	refinedict = createRefineDefaults(0, '', '', tmp='')
	f=open(paramfile,'r')
	lines = f.readlines()
	for line in lines:
		if line.find('=') >=1 :
			realline = line.strip('\n')
			parts = realline.split('=')
			key = parts[0]
			if len(parts) == 2:
				value = parts[1]
				try:
					refinedict[key] = int(value)
				except ValueError:
					try:
						refinedict[key] = float(value)
					except ValueError:
						refinedict[key] = value
			elif len(parts) < 2:
				refinedict[key] = ''
			elif len(parts) > 2:
				refinedict[key] = '='.join(parts[1:])
	return refinedict

def readProtomoTltFile(protomotltfile):
	f=open(protomotltfile,'r')
	lines = f.readlines()
	rotations = []
	origins = []
	tiltaz = 90.0
	tilts = []
	specimen_euler = {'psi':0.0,'theta':0.0,'phi':0.0}
	for line in lines:
		if (line.find('ORIGIN') >= 0):
			items = line.split()
			origins.append((float(items[-3]),float(items[-2]))) 
		elif (line.find('ROTATION') >= 0):
			items = line.split()
			rotations.append(float(items[-1]))
			tilts.append(float(items[1]))
		elif (line.find('TILT AZIMUTH') >= 0):
			items = line.split()
			tiltaz = float(items[-1])
		elif (line.find('PSI') >= 0):
			items = line.split()
			specimen_euler['psi'] = float(items[-1])
		elif (line.find('THETA') >= 0):
			items = line.split()
			specimen_euler['theta'] = float(items[-1])
		elif (line.find('PHI') >= 0):
			items = line.split()
			specimen_euler['phi'] = float(items[-1])
	f.close()
	return specimen_euler, tiltaz, tilts, origins, rotations

def eulerToAffinematrix(euler, center):
	# axes are in order of x,y,z
	psi = euler['psi'] * 3.14159 / 180.0
	theta = euler['theta'] * 3.14159 / 180.0
	phi = euler['phi'] * 3.14159 / 180.0
	psiaffine = numpy.matrix([[math.cos(psi),-math.sin(psi),0,0],[math.sin(psi),math.cos(psi),0,0],[0,0,1,0],[0,0,0,1]])
	thetaaffine = numpy.matrix([[1,0,0,0],[0,math.cos(theta),-math.sin(theta),0],[0,math.sin(theta),math.cos(theta),0],[0,0,0,1]])
	phiaffine = numpy.matrix([[math.cos(phi),-math.sin(phi),0,0],[math.sin(phi),math.cos(phi),0,0],[0,0,1,0],[0,0,0,1]])
	centeraffine = numpy.matrix([[1,0,0,center[0]],[0,1,0,center[1]],[0,0,1,0],[0,0,0,1]])
	totalaffine = psiaffine * thetaaffine.I * phiaffine * centeraffine
	total2daffine = numpy.matrix(numpy.identity(3))
	total2daffine[:2,:2] = totalaffine[:2,:2]
	total2daffine[:2,2] = totalaffine[:2,3]
	return total2daffine
	
def convertGlobalTransformProtomoToImod(protomoprefix,imodprefix, center=(1024,1024)):
	# axes are in order of x,y,z
	protomotltfile = protomoprefix+"-fitted.tlt"
	imodtltfile = imodprefix+".xf"
	fout = open(imodtltfile,'w')
	specimen_euler, tiltaz, tilts, origins, rotations = readProtomoTltFile(protomotltfile)
	imodaffines = convertProtomoToImod(specimen_euler, tiltaz, origins, rotations,center)
	apImod.writeTransformFile('', imodprefix,imodaffines,'xf')


def convertProtomoToImod(specimen_euler, tiltaz, origins, rotations,center):
	#protomo tilt azimuth vertical is 90 deg, imod is 0 deg
	tiltazrad = (tiltaz - 90.0) * 3.14159 / 180.0
	tiltazaffine = numpy.matrix([[math.cos(tiltazrad),-math.sin(tiltazrad),0],[math.sin(tiltazrad),math.cos(tiltazrad),0],[0,0,1]])
	specimenaffine = eulerToAffinematrix(specimen_euler,center)
	centeraffine = numpy.matrix([[1,0,center[0]],[0,1,center[1]],[0,0,1]])
	shiftsum0 = 0
	shiftsum1 = 0
	allaffines = []
	for i in range(0,len(rotations)):
		theta = - (rotations[i]) * 3.14159 / 180.0
		rotationaffine = numpy.matrix([[math.cos(theta),-math.sin(theta),0],[math.sin(theta),math.cos(theta),0],[0,0,1]])
		shiftaffine = numpy.matrix([[1,0,origins[i][0]],[0,1,origins[i][1]],[0,0,1]])
		totalaffine = shiftaffine.I * rotationaffine * tiltazaffine.I * centeraffine
		allaffines.append(totalaffine)
		shiftsum0 += totalaffine[0,2]
		shiftsum1 += totalaffine[1,2]
	# imod global shift need to be referenced to the average shift or the series
	shiftavg0 = shiftsum0 / len(rotations)
	shiftavg1 = shiftsum1 / len(rotations)
	imodaffines = []
	shifts = []
	for i in range(0,len(rotations)):
		imodaffine = allaffines[i]
		imodaffine[0,2] = imodaffine[0,2] - shiftavg0
		imodaffine[1,2] = imodaffine[1,2] - shiftavg1
		imodaffines.append(imodaffine)
	return imodaffines

def insertProtomoParams(seriesname):
	# general protmo parameters
	protomoq = appiondata.ApProtomoParamsData()
	protomoq['series name'] = seriesname
	protomodata = apTomo.publish(protomoq)
	return protomodata

def insertAlignIteration(alignrundata, protomodata, params, refinedict,refimagedata):
	# protmoalign refinement cycle parameters
	refineparamsq = appiondata.ApProtomoRefinementParamsData()
	refineparamsq['protomo'] = protomodata
	refineparamsq['cycle'] = params['cycle']
	refineparamsq['alismp'] = refinedict['alismp']
	refineparamsq['alibox'] = {'x':refinedict['alibox_x'],'y':refinedict['alibox_y']}
	refineparamsq['cormod'] = refinedict['cormod']
	refineparamsq['imgref'] = refinedict['imgref']
	refineparamsq['reference'] = refimagedata
	refineparamsdata = apTomo.publish(refineparamsq)
	# good cycle used for reset tlt params
	if params['goodcycle'] is None:
		goodrefineparamsdata = None
	else:
		goodq = appiondata.ApProtomoRefinementParamsData(protomo=protomodata,cycle=params['goodcycle'])
		results = goodq.query(results=1)
		if results:
			goodrefineparamsdata = results[0]
		else:
			goodrefineparamsdata = None
	# protomoaligner parameters
	alignerdata = apTomo.insertAlignerParams(alignrundata,params,protomodata,refineparamsdata,goodrefineparamsdata,refimagedata)
	return alignerdata


def insertModel(alignerdata, results):
	# general protmo parameters
	q = appiondata.ApProtomoModelData()
	q['aligner'] = alignerdata
	q['psi'] = results[-2]['psi']
	q['theta'] = results[-2]['theta']
	q['phi'] = results[-2]['phi']
	q['azimuth'] = results[-2]['azimuth']
	modeldata = apTomo.publish(q)
	return modeldata

def insertTiltAlignment(alignerdata,imagedata,number,result,center=None):
	if not center:
		imgshape = imagedata['image'].shape
		center = {'x':imgshape[1]/2,'y':imgshape[0]/2}
	q = appiondata.ApProtomoAlignmentData()
	q['aligner'] = alignerdata
	q['image'] = imagedata
	q['number'] = number
	q['rotation'] = result['rotation']
	q['shift'] = {'x':result['x'] - center['x'], 'y':result['y'] - center['y']}
	aligndata = apTomo.publish(q)
	return aligndata
