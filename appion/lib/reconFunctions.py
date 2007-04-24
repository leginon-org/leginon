#!/usr/bin/env python
# Python functions for selexon.py

import os, re, sys
import tempfile
import cPickle
import data
#import dbdatakeeper
import convolver
import Mrc
import numarray.nd_image
import imagefun
import peakfinder
import correlator
import math
import string
import particleData
import apDB

#db=dbdatakeeper.DBDataKeeper()
#partdb=dbdatakeeper.DBDataKeeper(db='dbparticledata')
db = apDB.db
partdb = apDB.apdb

def createDefaults():
	# create default values for parameters
	params={}
	params['runid']='recon1'
	params['stackid']=None
	params['modelid']=None
	params['dir']=os.path.abspath('.')+'/'
	params['volumes']=[]
	params['classavgs']=[]
	params['classvars']=[]
	params['iterations']=[]
	params['fscs']=[]
	params['package']='EMAN'
	return params

def createModelDefaults():
	params={}
	params['apix']=None
	params['boxsize']=None
	params['description']=None
	params['path']=None
	params['name']=None

def defineIteration():
	iteration={}
	iteration['num']=None
	iteration['angIncr']=None
	iteration['mask']=None
	iteration['imask']=None
	iteration['lpfilter']=None
	iteration['hpfilter']=None
	iteration['pad']=None
	iteration['hard']=None
	iteration['classkeep']=None
	iteration['classiter']=None
	iteration['median']=None
	iteration['phasecls']=None
	iteration['refine']=None
	return iteration
	
def printHelp():
	print "\nUsage:\nuploadRecon.py stackid=<n> modelid=<n> [package=<packagename>] [dir=/path/to/directory]\n"
	print "Example: uploadRecon.py stackid=23 modelid=20 package=EMAN\n"
	print "runid=<name>         : name assigned to this reconstruction"
	print "stackid=<n>          : stack Id in the database"
	print "modelid=<n>          : starting model id in the database"
	print "package=<package>    : reconstruction package used (EMAN by default)"
	print "dir=<path>           : directory containing the results of the reconstruction"
	print "                       (current dir is default)"
	print "\n"

	sys.exit(1)

def parseInput(args,params):
	# check that there are enough input parameters
	if (len(args)<2 or args[1]=='help') :
		printHelp()

	# save the input parameters into the "params" dictionary
	for arg in args[1:]:
		elements=arg.split('=')
		if (elements[0]=='runid'):
			params['runid']=elements[1]
		elif (elements[0]=='stackid'):
			params['stackid']=int(elements[1])
		elif (elements[0]=='modelid'):
			params['modelid']=int(elements[1])
		elif (elements[0]=='package'):
			params['package']=int(elements[1])
		elif (elements[0]=='dir'):
			params['dir']=elements[1]
			if not(params['dir'][-1]=='/'):
				params['dir']=params['dir']+'/'
		else:
			print "undefined parameter '"+arg+"'\n"
			sys.exit(1)
        
def checkStackId(params):
	stackinfo=partdb.direct_query(data.stackParams, params['stackid'])
	if not stackinfo:
		print "\nERROR: Stack ID",params['stackid'],"does not exist in the database"
		sys.exit()
	else:
		params['stack']=stackinfo
		print "Stack:",stackinfo['stackPath']+stackinfo['name']
	return
	
def checkModelId(params):
	modelinfo=partdb.direct_query(data.initialModel, params['modelid'])
	if not modelinfo:
		print "\nERROR: Initial model ID",params['modelid'],"does not exist in the database"
		sys.exit()
	else:
		params['model']=modelinfo
		print "Initial Model:",modelinfo['path']+modelinfo['name']
	return

def listFiles(params):
	for f in os.listdir(params['dir']):
		if re.match("threed\.\d+a\.mrc",f):
			params['volumes'].append(f)
		if re.match("classes\.\d+\.img",f):
			params['classavgs'].append(f)
		if re.match("fsc.eotest.\d+",f):
			params['fscs'].append(f)
			
def parseLogFile(params):
	# parse out the refine command from the .emanlog to get the parameters for each iteration
	logfile=params['dir']+'.emanlog'
	print "parsing eman log file:",logfile
	lines=open(logfile,'r')
	for line in lines:
		# if read a refine line, get the parameters
		line=string.rstrip(line)
		if re.search("refine \d+ ", line):
			emanparams=line.split(' ')
			iteration=defineIteration()
			iteration['num']=emanparams[1]
			for p in emanparams:
				elements=p.split('=')
				if elements[0]=='ang':
					iteration['angIncr']=float(elements[1])
				elif elements[0]=='mask':
					iteration['mask']=int(elements[1])
				elif elements[0]=='imask':
					iteration['imask']=int(elements[1])
				elif elements[0]=='pad':
					iteration['pad']=int(elements[1])
				elif elements[0]=='hard':
					iteration['hard']=int(elements[1])
				elif elements[0]=='classkeep':
					iteration['classkeep']=float(elements[1])
				elif elements[0]=='classiter':
					iteration['classiter']=int(elements[1])
				elif elements[0]=='median':
					iteration['median']=True
				elif elements[0]=='phasecls':
					iteration['phasecls']=True
				elif elements[0]=='refine':
					iteration['refine']=True
			params['iterations'].append(iteration)
				
def insertReconRun(params):
	runq=particleData.reconRun()
	runq['name']=params['runid']
	runq['stackId']=params['stack']
	runq['initialModelId']=params['model']
	runq['package']=params['package']
	runq['path']=params['dir']
	result=partdb.query(runq, results=1)

## 	if result:
## 		print "\nERROR: run already exists in the database\n"
## 		sys.exit()	        

## 	else:

	if not result:
		print "inserting reconstruction run into database"
		partdb.insert(runq)

		runq=particleData.reconRun()
		runq['name']=params['runid']
		runq['stackId']=params['stack']
		runq['initialModelId']=params['model']
		runq['package']=params['package']
		runq['path']=params['dir']
		result=partdb.query(runq, results=1)
		
	# save run entry in the parameters
	params['reconRun']=result[0]

	return

def insertIteration(params):
	for iteration in params['iterations']:
		refineparamsq=particleData.refinementParams()
		refineparamsq['angIncr']=iteration['angIncr']
		refineparamsq['mask']=iteration['mask']
		refineparamsq['imask']=iteration['imask']
		refineparamsq['lpfilter']=iteration['lpfilter']
		refineparamsq['hpfilter']=iteration['hpfilter']
		refineparamsq['fourier_padding']=iteration['pad']
		refineparamsq['EMAN_hard']=iteration['hard']
		refineparamsq['EMAN_classkeep']=iteration['classkeep']
		refineparamsq['EMAN_classiter']=iteration['classiter']
		refineparamsq['EMAN_median']=iteration['median']
		refineparamsq['EMAN_phasecls']=iteration['phasecls']
		refineparamsq['EMAN_refine']=iteration['refine']
		result=partdb.query(refineparamsq, results=1)

		# insert unique iteration parameters
		if not result:
			partdb.insert(refineparamsq)
			refineparamsq=particleData.refinementParams()
			refineparamsq['angIncr']=iteration['angIncr']
			refineparamsq['mask']=iteration['mask']
			refineparamsq['imask']=iteration['imask']
			refineparamsq['lpfilter']=iteration['lpfilter']
			refineparamsq['hpfilter']=iteration['hpfilter']
			refineparamsq['fourier_padding']=iteration['pad']
			refineparamsq['EMAN_hard']=iteration['hard']
			refineparamsq['EMAN_classkeep']=iteration['classkeep']
			refineparamsq['EMAN_classiter']=iteration['classiter']
			refineparamsq['EMAN_median']=iteration['median']
			refineparamsq['EMAN_phasecls']=iteration['phasecls']
			refineparamsq['EMAN_refine']=iteration['refine']
			result=partdb.query(refineparamsq, results=1)

		refineParams=result[0]

		# insert resolution data
		fsc='fsc.eotest.'+iteration['num']
		if fsc in params['fscs']:
			#fsc file with path:
			fscfile=params['dir']+fsc

			resq=particleData.resolution()
			resq['fscfile']=fscfile
			result=partdb.query(resq)
			if not result:
				# calculate the resolution:
				halfres=calcRes(fscfile, params['model'])
				resq['half']=halfres
				partdb.insert(resq)
				resq=particleData.resolution()
				resq['fscfile']=fscfile
				result=partdb.query(resq, results=1)
			resolutionId=result[0]
		
		# insert refinement results
		refineq=particleData.refinement()
		refineq['reconRunId']=params['reconRun']
		refineq['refinementParamsId']=refineParams
		refineq['iteration']=iteration['num']
		refineq['resolutionId']=resolutionId
		classavg='classes.'+iteration['num']+'.img'
		classvar='classes.'+iteration['num']+'.var.img'
		volumeSnapshot='threed.'+iteration['num']+'a.png'
		volumeDensity='threed.'+iteration['num']+'a.mrc'
		if classavg in params['classavgs']:
			refineq['classAverage']=params['dir']+classavg
		if classvar in params['classvars']:
			refineq['classVariance']=params['dir']+classvar
		if volumeDensity in params['volumes']:
			refineq['volumeSnapshot']=params['dir']+volumeSnapshot
			refineq['volumeDensity']=params['dir']+volumeDensity
		result=partdb.query(refineq, results=1)
		if not result:
			partdb.insert(refineq)
	
	return

def calcRes(fscfile, model):
	# calculate the resolution at 0.5

	# get box size and pixel size from model
	boxsize=int(model['boxsize'])
	apix=float(model['pixelsize'])
	
	lastx = 0
	lasty = 0
	f=open(fscfile,'r')
	for line in f:
		line=string.rstrip(line)
		bits=line.split('\t')
		x=float(bits[0])
		y=float(bits[1])
		if float(y)>0.5:
			lastx=x
			lasty=y
		else:
			# get difference of fsc points
			diffy=lasty-y
			# get distance from 0.5
			distfsc=(0.5-y)/diffy
			#get interpolated spatial frequency
			intfsc=x-(distfsc*(x-lastx))

			res=boxsize*apix/intfsc
			return res
	return
	
def writeReconLog(commandline):
        f=open('.reconlog','a')
        out=""
        for n in commandline:
                out=out+n+" "
        f.write(out)
        f.write("\n")
        f.close()
