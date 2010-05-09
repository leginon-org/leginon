#!/usr/bin/env python
# Upload pik or box files to the database

#python
import os
import re
import sys
import time
import glob
import math
import tarfile
#appion
from appionlib import appionScript
from appionlib import appiondata
from appionlib import apParam
from appionlib import apDisplay
from appionlib import apStack
from appionlib import apRecon
from appionlib import apEulerJump
from appionlib import apCoranPlot
from appionlib import apDatabase
from appionlib import apEMAN
from appionlib import apEulerDraw
from appionlib import apChimera
from appionlib import apSymmetry

#=====================
#=====================
class UploadReconScript(appionScript.AppionScript):

	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --runname=<name> --stackid=<int> --modelid=<int>\n\t "
			+"--description='<quoted text>'\n\t [ --package=EMAN --jobid=<int> --oneiter=<iter> --startiter=<iter> --zoom=<float> "
			+"--contour=<contour> --rundir=/path/ --commit ]")

		### integers
		self.parser.add_option("-i", "--oneiter", dest="oneiter", type="int",
			help="Only upload one iteration", metavar="INT")
		self.parser.add_option("--startiter", dest="startiter", type="int",
			help="Begin upload from this iteration", metavar="INT")
		self.parser.add_option("-s", "--stackid", dest="stackid", type="int",
			help="Stack id in the database", metavar="INT")
		self.parser.add_option("-m", "--modelid", dest="modelid", type="int",
			help="Initial model id in the database", metavar="INT")
		self.parser.add_option("-j", "--jobid", dest="jobid", type="int",
			help="Jobfile id in the database", metavar="INT")

		### floats
		self.parser.add_option("-z", "--zoom", dest="zoom", type="float", default=1.75,
			help="Zoom factor for snapshot rendering (1.75 by default)", metavar="FLOAT")
		self.parser.add_option("-c", "--contour", dest="contour", type="float", default=1.5,
			help="Sigma level at which snapshot of density will be contoured (1.5 by default)", metavar="FLOAT")
		self.parser.add_option("--mass", dest="mass", type="int",
			help="Mass (in kDa) at which snapshot of density will be contoured", metavar="kDa")
		self.parser.add_option("--filter", dest="snapfilter", type="float",
			help="Low pass filter in angstrum for snapshot rendering (0.6*FSC_0.5 by default)", metavar="FLOAT")

		### true / false
		self.parser.add_option("--chimera-only", dest="chimeraonly", default=False,
			action="store_true", help="Do not do any reconstruction calculations only run chimera")
		self.parser.add_option("--euler-only", dest="euleronly", default=False,
			action="store_true", help="Do not do any reconstruction calculations only run euler jump calculation")

		### choices
		self.packages = ( "EMAN", "EMAN/MsgP", "EMAN/SpiCoran")
		self.parser.add_option("-k", "--package", dest="package", default="EMAN",
			help="Reconstruction package used (EMAN by default)", metavar="TEXT",
			type="choice", choices=self.packages, )

	#=====================
	def checkConflicts(self):
		if self.params['package'] not in self.packages:
			apDisplay.printError("No valid reconstruction package method specified")
		# msgPassing requires a jobId in order to get the jobfile & the paramters
		if ((self.params['package'] == 'EMAN/MsgP' or self.params['package'] == 'EMAN/SpiCoran')
		 and self.params['jobid'] is None):
			err = self.tryToGetJobID()
			if err:
				apDisplay.printError(self.params['package']
					+" refinement requires a jobid. Please enter a jobId,"
					+" e.g. --jobid=734" + '\n' + err)
		if self.params['package'] != "EMAN/SpiCoran":
			### check if we have coran files
			corans = glob.glob("classes_coran.*.hed")
			if corans and len(corans) > 0:
				apDisplay.printError("You used coran in the recon, but it was not selected\n"
					+"set package to coran, e.g. --package='EMAN/SpiCoran'")
		if self.params['stackid'] is None:
			apDisplay.printError("please enter a stack id, e.g. --stackid=734")
		if self.params['modelid'] is None:
			apDisplay.printError("please enter a starting model id, e.g. --modelid=34")
		if self.params['description'] is None:
			apDisplay.printError("please enter a recon description, e.g. --description='my fav recon'")
		if self.params['runname'] is None:
			apDisplay.printError("please enter a recon run name, e.g. --runname=recon11")
		if self.params['jobid']:
			# if jobid is supplied, get the job info from the database
			self.params['jobinfo'] = self.getClusterJobDataFromID(self.params['jobid'])
			if self.params['jobinfo'] is None:
				apDisplay.printError("jobid supplied does not exist: "+str(self.params['jobid']))
		else:
			self.params['jobinfo'] = None
		if self.params['chimeraonly'] is True:
			self.params['commit'] = False

	#==================
	#==================
	def getClusterJobDataFromID(self, jobid):
		return appiondata.ApAppionJobData.direct_query(jobid)

	#=====================
	def tryToGetJobID(self):
		jobname = self.params['runname'] + '.job'
		jobtype = 'recon'
		jobpath = self.params['rundir']
		qpath = appiondata.ApPathData(path=os.path.abspath(jobpath))
		q = appiondata.ApAppionJobData(name=jobname, jobtype=jobtype, path=qpath)
		results = q.query()
		if len(results) == 1:
			## success, only one job id found
			self.params['jobid'] = results[0].dbid
			return ''
		elif len(results) > 1:
			## fail because too many job ids
			jobids = [result.dbid for result in results]
			return 'Several Job IDs found for this run: %s\nYou will have to manually specify a jobid' % (jobids,)
		else:
			## no job found
			self.params['jobid'] = None
			return ''

	#=====================
	def setRunDir(self):
		jobdata = self.getClusterJobDataFromID(self.params['jobid'])
		if jobdata:
			self.params['rundir'] = jobdata['path']['path']

	#==================
	#==================
	def listFiles(self):
		for key in ('classavgs', 'classvars', 'volumes', 'fscs', 'emanavgs', 'msgpavgs', 'coranavgs'):
			self.params[key] = []
		for f in os.listdir(self.params['rundir']):
			if re.match("threed\.\d+a\.mrc",f):
				self.params['volumes'].append(f)
			if re.match("classes\.\d+\.img",f):
				self.params['classavgs'].append(f)
			if re.match("fsc.eotest.\d+",f):
				self.params['fscs'].append(f)
			if re.match("classes_eman\.\d+\.img",f):
				self.params['emanavgs'].append(f)
			if re.match("classes_msgp\.\d+\.img",f):
				self.params['msgpavgs'].append(f)
			if re.match("classes_coran\.\d+\.img",f):
				self.params['coranavgs'].append(f)

	#==================
	#==================
	def convertClassAvgFiles(self):
		files_classavg = []
		files_classold = []
		files_classgood = []
		for f in os.listdir(self.params['rundir']):
			if re.match("classes_eman\.\d+\.img",f):
				return
			if re.match("classes_coran\.\d+\.img",f):
				return
			if re.match("classes_msgp\.\d+\.img",f):
				return
			if re.match("classes\.\d+\.img",f):
				files_classavg.append(f)
			if re.match("classes\.\d+\.old\.img",f):
				files_classold.append(f)
			if re.match("goodavgs\.\d+\.img",f):
				files_classgood.append(f)
		if self.params['package']=='EMAN':
			for f in files_classavg:
				for ext in ['.img','.hed']:
					oldf = f.replace('.img',ext)
					newf = oldf.replace('classes','classes_eman')
					os.rename(oldf,newf)
					os.symlink(newf,oldf)
		elif self.params['package']=='EMAN/SpiCoran':
			for f in files_classavg:
				for ext in ['.img','.hed']:
					oldf = f.replace('.img',ext)
					newf = oldf.replace('classes','classes_coran')
					os.rename(oldf,newf)
					os.symlink(newf,oldf)
			for f in files_classold:
				for ext in ['.img','.hed']:
					oldf = f.replace('.img',ext)
					newf = oldf.replace('classes','classes_eman')
					new2f = newf.replace('old.','')
					os.rename(oldf,new2f)
		elif self.params['package']=='EMAN/MsgP':
			for f in files_classgood:
				for ext in ['.img','.hed']:
					oldf = f.replace('.img',ext)
					newf = oldf.replace('goodavgs','classes_msgp')
					os.rename(oldf,newf)
					os.symlink(newf,oldf)
			for f in files_classavg:
				for ext in ['.img','.hed']:
					oldf = f.replace('.img',ext)
					newf = oldf.replace('classes','classes_eman')
					os.rename(oldf,newf)

	#==================
	#==================
	def insertResolutionData(self, iteration):
		fsc = 'fsc.eotest.'+iteration['num']
		fscfile = os.path.join(self.params['rundir'],fsc)

		if not os.path.isfile(fscfile):
			apDisplay.printWarning("Could not find FSC file: "+fscfile)

		iteration['fscfile'] = fscfile
		if fsc in self.params['fscs']:
			resq=appiondata.ApResolutionData()

			# calculate the resolution:
			halfres = apRecon.calcRes(fscfile, self.params['boxsize'], self.params['apix'])

			# save to database
			resq['half'] = halfres
			resq['fscfile'] = fsc

			apDisplay.printMsg("inserting FSC resolution data into database")
			if self.params['commit'] is True:
				resq.insert()
			else:
				apDisplay.printWarning("not committing results to database")

			return resq

	#==================
	#==================
	def insertRMeasureData(self, iteration):
		volumeDensity='threed.'+iteration['num']+'a.mrc'

		volPath = os.path.join(self.params['rundir'], volumeDensity)
		if not os.path.exists(volPath):
			apDisplay.printWarning("R Measure failed, volume density not found: "+volPath)
			return None

		resolution = apRecon.runRMeasure(self.params['apix'], volPath)

		if resolution is None:
			return None

		resq=appiondata.ApRMeasureData()
		resq['volume']=volumeDensity
		resq['rMeasure']=resolution

		apDisplay.printMsg("inserting R Measure Data into database")
		if self.params['commit'] is True:
			resq.insert()
		else:
			apDisplay.printWarning("not committing results to database")

		return resq

	#==================
	#==================
	def readParticleLog(self, path, iternum):
		plogf = os.path.join(path,"particle.log")
		if not os.path.isfile(plogf):
			apDisplay.printError("no particle.log file found")

		f=open(plogf,'r')
		badprtls=[]
		n=str(int(iternum)+1)
		for line in f:
			rline=line.rstrip()
			if re.search("X\t\d+\t"+str(iternum)+"$",rline):
				bits=rline.split()
				badprtls.append(bits[1])
			# break out of into the next iteration
			elif re.search("X\t\d+\t"+n+"$",rline):
				break
		f.close()
		return badprtls

	#==================
	#==================
	def insertFSC(self, fscfile, refineIterData, commit=True):
		if not os.path.isfile(fscfile):
			apDisplay.printWarning("Could not open FSC file: "+fscfile)

		f = open(fscfile,'r')
		apDisplay.printMsg("inserting FSC Data into database")
		numinserts = 0
		for line in f:
			fscq = appiondata.ApFSCData()
			fscq['refineIter'] = refineIterData
			line = line.rstrip()
			bits = line.split('\t')
			fscq['pix'] = int(bits[0])
			fscq['value'] = float(bits[1])

			numinserts+=1
			if commit is True:
				fscq.insert()
		apDisplay.printMsg("inserted "+str(numinserts)+" rows of FSC data into database")
		f.close()


	#==================
	#==================
	def insertRefinementRun(self):
		runq=appiondata.ApRefineRunData()
		#first two must be unique
		runq['runname']=self.params['runname']
		runq['stack']=self.params['stack']

		#Recon upload can be continued
		earlyresult=runq.query(results=1)
		if earlyresult:
			apDisplay.printWarning("Run already exists in the database.\nIdentical data will not be reinserted")
		# empty <> than None for Sinedon query
		paramdescription = self.params['description']
		if not paramdescription:
			paramdescription=None

		runq['job']=self.params['jobinfo']
		runq['initialModel']=self.params['model']
		runq['package']=self.params['package']
		runq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
		runq['description']=paramdescription
		runq['initialModel']=self.params['model']

		result=runq.query(results=1)

		if earlyresult and not result:
			if self.params['commit'] is True:
				apDisplay.printError("Refinement Run parameters have changed")
			else:
				apDisplay.printWarning("Refinement Run parameters have changed")

		# get stack apix
		self.params['apix'] = apStack.getStackPixelSizeFromStackId(self.params['stack'].dbid)

		apDisplay.printMsg("inserting Refinement Run into database")
		if self.params['commit'] is True:
			runq.insert()
		else:
			apDisplay.printWarning("not committing results to database")

		#if we insert runq then this returns no results !!!
		# this is a workaround (annoying & bad)
		runq=appiondata.ApRefineRunData()
		runq['runname']=self.params['runname']
		runq['stack']=self.params['stack']
		runq['job']=self.params['jobinfo']
		runq['initialModel']=self.params['model']
		runq['package']=self.params['package']
		runq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
		runq['description']=paramdescription
		runq['package']=self.params['package']
		runq['initialModel']=self.params['model']

		result = runq.query(results=1)

		# save run entry in the parameters
		if result:
			self.params['refineRun'] = result[0]
		elif self.params['commit'] is True:
			apDisplay.printWarning("Refinement Run was not found, setting to inserted values")
			self.params['refineRun'] = runq
		else:
			apDisplay.printWarning("Refinement Run was not found, setting to 'None'")
			self.params['refineRun'] = None
		return True


	#==================
	#==================
	# Parse MsgPassing params through EMAN jobfile
	def parseMsgPassingParams(self):
		emanJobFile = os.path.join(self.params['rundir'], self.params['jobinfo']['name'])
		if os.path.isfile(emanJobFile):
			lines=open(emanJobFile,'r')
			j=0
			for i,line in enumerate(lines):
				line=line.rstrip()
				if re.search("^msgPassing_subClassification.py", line):
					msgpassparams=line.split()
					iteration = self.params['iterations'][j]
					for p in msgpassparams:
						elements=p.split('=')
						if elements[0]=='corCutOff':
							iteration['msgpasskeep']=float(elements[1])
						elif elements[0]=='minNumOfPtcls':
							iteration['msgpassminp']=int(elements[1])
					j+=1
			lines.close()
		else:
			apDisplay.printError("EMAN Job file: "+emanJobFile+" does not exist!")

	#==================
	#==================
	def findEmanJobFile(self):
		# first find the job file, if it doesn't exist, use the .eman log file
		if 'jobinfo' in self.params and self.params['jobinfo'] is not None:
			logfile = os.path.join(self.params['rundir'], self.params['jobinfo']['name'])
			if os.path.isfile(logfile):
				return logfile
		else:
			self.params['jobinfo'] = None
		logfile = os.path.join(self.params['rundir'], 'eman.log')
		if os.path.isfile(logfile):
			return logfile
		logfile = os.path.join(self.params['rundir'], '.emanlog')
		if os.path.isfile(logfile):
			return logfile
		apDisplay.printError("Could not find eman job or log file")

	#==================
	#==================
	def defineIteration(self):
		iteration = {
			'ang': None,
			'classiter': None,
			'classkeep': None,
			'euler2': None,
			'filt3d': None,
			'fscls': None,
			'goodbad': None,
			'maxshift': None,
			'hard': None,
			'hpfilter': None,
			'imask': None,
			'lpfilter': None,
			'mask': None,
			'median': None,
			'msgpasskeep': None,
			'msgpassminp': None,
			'num': None,
			'pad': None,
			'perturb': None,
			'phasecls': None,
			'refine': None,
			'shrink': None,
			'xfiles': None,
		}
		return iteration

	#==================
	#==================
	def parseLogFile(self):
		# parse out the refine command from the .emanlog to get the parameters for each iteration
		logfile = self.findEmanJobFile()
		apDisplay.printMsg("parsing eman log file: "+logfile)
		lines=open(logfile,'r')
		self.params['iterations'] = []
		for line in lines:
			# if read a refine line, get the parameters
			line=line.rstrip()
			if re.search("refine \d+ ", line):
				emanparams=line.split(' ')
				if emanparams[0] is "#":
					emanparams.pop(0)
				# get rid of first "refine"
				emanparams.pop(0)
				iteration=self.defineIteration()
				iteration['num']=emanparams[0]
				iteration['sym']=''
				for p in emanparams:
					elements=p.strip().split('=')
					if elements[0]=='ang':
						iteration['ang']=float(elements[1])
					elif elements[0]=='mask':
						iteration['mask']=int(float(elements[1]))
					elif elements[0]=='imask':
						iteration['imask']=int(float(elements[1]))
					elif elements[0]=='pad':
						iteration['pad']=int(float(elements[1]))
					elif elements[0]=='sym':
						iteration['sym'] = apSymmetry.findSymmetry(elements[1])
					elif elements[0]=='maxshift':
						iteration['maxshift']=int(float(elements[1]))
					elif elements[0]=='hard':
						iteration['hard']=int(float(elements[1]))
					elif elements[0]=='classkeep':
						iteration['classkeep']=float(elements[1].strip())
					elif elements[0]=='classiter':
						iteration['classiter']=int(float(elements[1]))
					elif elements[0]=='filt3d':
						iteration['filt3d']=int(float(elements[1]))
					elif elements[0]=='shrink':
						iteration['shrink']=int(float(elements[1]))
					elif elements[0]=='euler2':
						iteration['euler2']=int(float(elements[1]))
					elif elements[0]=='xfiles':
						## trying to extract "xfiles" as entered into emanJobGen.php
						values = elements[1]
						apix,mass,alito = values.split(',')
						iteration['xfiles']=float(mass)
					elif elements[0]=='amask1':
						iteration['amask1']=float(elements[1])
					elif elements[0]=='amask2':
						iteration['amask2']=float(elements[1])
					elif elements[0]=='amask3':
						iteration['amask3']=float(elements[1])
					elif elements[0]=='median':
						iteration['median']=True
					elif elements[0]=='phasecls':
						iteration['phasecls']=True
					elif elements[0]=='fscls':
						iteration['fscls']=True
					elif elements[0]=='refine':
						iteration['refine']=True
					elif elements[0]=='goodbad':
						iteration['goodbad']=True
					elif elements[0]=='perturb':
						iteration['perturb']=True
				self.params['iterations'].append(iteration)
			if re.search("coran_for_cls.py \d+ ", line):
					self.params['package']='EMAN/SpiCoran'
			if re.search("msgPassing_subClassification.py \d+ ", line):
					self.params['package']='EMAN/MsgP'
		apDisplay.printColor("Found "+str(len(self.params['iterations']))+" iterations", "green")
		lines.close()

	#==================
	#==================
	def getEulersFromProj(self, iternum):
		# get Eulers from the projection file
		eulers=[]
		projfile="proj."+iternum+".txt"
		projfile=os.path.join(self.params['rundir'], projfile)
		#print "reading file, "+projfile
		if not os.path.exists:
			apDisplay.printError("no projection file found for iteration "+iter)
		f = open(projfile,'r')
		for line in f:
			line=line[:-1] # remove newline at end
			i=line.split()
			angles=[i[1],i[2],i[3]]
			eulers.append(angles)
		f.close()
		return eulers

	#==================
	#==================
	def insertIteration(self, iteration):
		refineparamsq=appiondata.ApEmanRefineIterData()
		refineparamsq['ang']=iteration['ang']
		refineparamsq['lpfilter']=iteration['lpfilter']
		refineparamsq['hpfilter']=iteration['hpfilter']
		refineparamsq['pad']=iteration['pad']
		refineparamsq['EMAN_maxshift']=iteration['maxshift']
		refineparamsq['EMAN_hard']=iteration['hard']
		refineparamsq['EMAN_classkeep']=iteration['classkeep']
		refineparamsq['EMAN_classiter']=iteration['classiter']
		refineparamsq['EMAN_filt3d']=iteration['filt3d']
		refineparamsq['EMAN_shrink']=iteration['shrink']
		refineparamsq['EMAN_euler2']=iteration['euler2']
		refineparamsq['EMAN_xfiles']=iteration['xfiles']
		refineparamsq['EMAN_median']=iteration['median']
		refineparamsq['EMAN_phasecls']=iteration['phasecls']
		refineparamsq['EMAN_fscls']=iteration['fscls']
		refineparamsq['EMAN_refine']=iteration['refine']
		refineparamsq['EMAN_goodbad']=iteration['goodbad']
		refineparamsq['EMAN_perturb']=iteration['perturb']
		refineparamsq['MsgP_cckeep']=iteration['msgpasskeep']
		refineparamsq['MsgP_minptls']=iteration['msgpassminp']

		#create Chimera snapshots
		fscfile = os.path.join(self.params['rundir'], "fsc.eotest."+iteration['num'])
		halfres = apRecon.calcRes(fscfile, self.params['boxsize'], self.params['apix'])
		if self.params['snapfilter']:
			halfres = self.params['snapfilter']
		volumeDensity = 'threed.'+iteration['num']+'a.mrc'
		volDensPath = os.path.join(self.params['rundir'], volumeDensity)

		apChimera.filterAndChimera(volDensPath, halfres, self.params['apix'], 
			self.params['boxsize'], 'snapshot', self.params['contour'], self.params['zoom'],
			sym=iteration['sym']['eman_name'], mass=self.params['mass'])

		## uncommment this for chimera image only runs...
		if self.params['chimeraonly'] is True:
			return

		# insert resolution data
		if halfres != True:
			resData = self.insertResolutionData(iteration)
		else:
			apDisplay.printWarning("resolution reported as nan, not committing results to database")
			return
		RmeasureData = self.insertRMeasureData(iteration)

		if self.params['package']== 'EMAN':
			refineclassavg='classes_eman.'+iteration['num']+'.img'
			postrefineclassavg=None
		elif self.params['package']== 'EMAN/SpiCoran':
			refineclassavg='classes_eman.'+iteration['num']+'.img'
			postrefineclassavg='classes_coran.'+iteration['num']+'.img'
		elif self.params['package']== 'EMAN/MsgP':
			refineclassavg='classes_eman.'+iteration['num']+'.img'
			postrefineclassavg='classes_msgp.'+iteration['num']+'.img'
		else:
			apDisplay.printError("Refinement Package Not Valid")

		# insert refinement results
		refineq = appiondata.ApRefineIterData()
		refineq['refineRun'] = self.params['refineRun']
		refineq['emanParams'] = refineparamsq
		refineq['iteration'] = iteration['num']
		refineq['resolution'] = resData
		refineq['rMeasure'] = RmeasureData
		refineq['mask'] = iteration['mask']
		refineq['imask'] = iteration['imask']
		refineq['symmetry']=iteration['sym']
		refineq['exemplar'] = False
		classvar = 'classes.'+iteration['num']+'.var.img'
		refineq['refineClassAverages'] = refineclassavg
		refineq['postRefineClassAverages'] = postrefineclassavg
		if classvar in self.params['classvars']:
			refineq['classVariance'] = classvar
		if volumeDensity in self.params['volumes']:
			refineq['volumeDensity'] = volumeDensity

		apDisplay.printMsg("inserting Refinement Data into database")
		if self.params['commit'] is True:
			refineq.insert()
		else:
			apDisplay.printWarning("not committing results to database")

		#insert FSC data
		fscfile = os.path.join(self.params['rundir'], "fsc.eotest."+iteration['num'])
		self.insertFSC(fscfile, refineq, self.params['commit'])
		halfres = apRecon.calcRes(fscfile, self.params['boxsize'], self.params['apix'])
		apDisplay.printColor("FSC 0.5 Resolution: "+str(halfres), "cyan")

		# get projections eulers for iteration:
		eulers = self.getEulersFromProj(iteration['num'])

		# get list of bad particles for this iteration
		badprtls = self.readParticleLog(self.params['rundir'], iteration['num'])

		# expand cls.*.tar into temp file
		clsf=os.path.join(self.params['rundir'], "cls."+iteration['num']+".tar")
		#print "reading",clsf
		clstar=tarfile.open(clsf)
		clslist=clstar.getmembers()
		clsnames=clstar.getnames()
		#print "extracting",clsf,"into temp directory"
		for clsfile in clslist:
			clstar.extract(clsfile,self.params['tmpdir'])
		clstar.close()

		# for each class, insert particle alignment info into database
		apDisplay.printColor("Inserting Particle Classification Data for "
			+str(len(clsnames))+" classes", "magenta")
		t0 = time.time()
		for cls in clsnames:
			self.insertRefineParticleData(cls, iteration, eulers, badprtls, refineq, len(clsnames))
		apDisplay.printColor("\nFinished in "+apDisplay.timeString(time.time()-t0), "magenta")

		# remove temp directory
		for file in os.listdir(self.params['tmpdir']):
			os.remove(os.path.join(self.params['tmpdir'],file))
		os.rmdir(self.params['tmpdir'])

		#create euler freq map
		apDisplay.printMsg("creating euler frequency map")
		refrunid = int(self.params['refineRun'].dbid)
		iternum = int(iteration['num'])
		if self.params['package'] != 'EMAN':
			postrefine = True
		else:
			postrefine = False

		apEulerDraw.createEulerImages(refrunid, iternum, path=self.params['rundir'], postrefine=postrefine)
		return

	#==================
	#==================
	def insertRefineParticleData(self,cls,iteration,eulers,badprtls,refineq,numcls,euler_convention='zxz'):
		# get the corresponding proj number & eulers from filename
		replace=re.compile('\D')
		projnum=int(replace.sub('',cls))

		clsfilename=os.path.join(self.params['tmpdir'],cls)
		sys.stderr.write(".")
		#f=open(clsfilename)
		#apDisplay.printMsg("Class "+str(projnum+1)+" of "+str(numcls)+": inserting "
		#	+str(len(f.readlines())-2)+" particles")
		#f.close()

		# for each cls file get alignments for particles
		f=open(clsfilename)
		coranfail = False
		for line in f:
			# skip line if not a particle
			if re.search("start",line):
				prtlaliq=appiondata.ApRefineParticleData()

				# gather alignment data from line
				ali=line.split()
				prtlnum = int(ali[0])

				# check if bad particle
				if str(prtlnum) in badprtls:
					prtlaliq['refine_keep'] = False

				prtlnum+=1 # offset for EMAN
				qualf=float(ali[2].strip(','))
				other=ali[3].split(',')
				rot=float(other[0])*180./math.pi
				shx=float(other[1])
				shy=float(other[2])
				if (other[3]=='1') :
					prtlaliq['mirror']=True

				# SPIDER coran kept particle
				corank =	None
				if self.params['package']== 'EMAN/SpiCoran':
					if len(other) > 4:
						corank=bool(int(other[4]))
					else:
						if coranfail is False:
							apDisplay.printWarning("Coran failed on this iteration")
							coranfail = True

				# message passing kept particle
				if self.params['package']== 'EMAN/MsgP' and len(ali) > 4:
					msgk=bool(int(ali[4]))
				else:
					msgk=None
				# find particle in stack database
				defid = self.params['stackmapping'][prtlnum]
				stackp = appiondata.ApStackParticleData.direct_query(defid)

				if not stackp:
					apDisplay.printError("particle "+str(prtlnum)+" not in stack id="+str(self.params['stack'].dbid))

				# insert classification info
				prtlaliq['refineIter']=refineq
				prtlaliq['particle']=stackp
				prtlaliq['shiftx']=shx
				prtlaliq['shifty']=shy
				prtlaliq['euler1']=eulers[projnum][0]
				prtlaliq['euler2']=eulers[projnum][1]
				prtlaliq['euler3']=rot
				prtlaliq['quality_factor']=qualf
				if self.params['package']== 'EMAN/MsgP':
					prtlaliq['postRefine_keep']=msgk
				else:
					prtlaliq['postRefine_keep']=corank
				prtlaliq['euler_convention']=euler_convention

				#apDisplay.printMsg("inserting Particle Classification Data into database")
				if self.params['commit'] is True:
					prtlaliq.insert()

		f.close()
		return

	#=====================
	def start(self):
		if self.params['rundir'] is None or not os.path.isdir(self.params['rundir']):
			apDisplay.printError("upload directory does not exist: "+str(self.params['rundir']))


		### create temp directory for extracting data
		self.params['tmpdir'] = os.path.join(self.params['rundir'], "temp")
		apParam.createDirectory(self.params['tmpdir'], warning=True)

		### make sure that the stack & model IDs exist in database
		emanJobFile = self.findEmanJobFile()
		self.params['stack'] = apStack.getOnlyStackData(self.params['stackid'])
		self.params['stackmapping'] = apRecon.partnum2defid(self.params['stackid'])
		self.params['model'] = appiondata.ApInitialModelData.direct_query(self.params['modelid'])
		self.params['boxsize'] = apStack.getStackBoxsize(self.params['stackid'])

		### parse out the refinement parameters from the log file
		self.parseLogFile()

		### parse out the message passing subclassification parameters from the job/log file
		if self.params['package'] == 'EMAN/MsgP':
			self.parseMsgPassingParams()

		### convert class average files from old to new format
		self.convertClassAvgFiles()

		### get a list of the files in the directory
		self.listFiles()

		### create a refinementRun entry in the database
		self.insertRefinementRun()

		if self.params['euleronly'] is False:
			### insert the Iteration info
			for iteration in self.params['iterations']:
				### if only uploading one iteration, skip to that one
				if self.params['oneiter'] and int(iteration['num']) != self.params['oneiter']:
					continue
				### if beginning at later iteration, skip to that one
				if self.params['startiter'] and int(iteration['num']) < self.params['startiter']:
					continue
				apDisplay.printColor("\nUploading iteration "+str(iteration['num'])+" of "
					+str(len(self.params['iterations']))+"\n", "green")
				for i in range(75):
					sys.stderr.write("#")
				sys.stderr.write("\n")
				self.insertIteration(iteration)

		### calculate euler jumps
		if self.params['commit'] is True:
			reconrunid = self.params['refineRun'].dbid
			stackid = self.params['stack'].dbid
			if self.params['oneiter'] is None and len(self.params['iterations']) > 1:
				apDisplay.printMsg("calculating euler jumpers for recon="+str(reconrunid))
				eulerjump = apEulerJump.ApEulerJump()
				eulerjump.calculateEulerJumpsForEntireRecon(reconrunid, stackid)
			### coran keep plot
			if self.params['package']=='EMAN/SpiCoran':
				apCoranPlot.makeCoranKeepPlot(reconrunid)
			apRecon.setGoodBadParticlesFromReconId(reconrunid)

#=====================
#=====================
if __name__ == '__main__':
	uploadRecon = UploadReconScript()
	uploadRecon.start()
	uploadRecon.close()


