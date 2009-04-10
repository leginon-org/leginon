#!/usr/bin/env python

### create model from EMAN startAny function and automatically calls uploadModel.py

import os
import re
import sys
import time
import math
import shutil
### appion
import appionScript
import apEMAN
import apDisplay
import apChimera
import apStack
import apSymmetry
import apFile
import apParam
import apVolume
import appionData

#=====================
#=====================
class createModelScript(appionScript.AppionScript):

	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog [options]")

		### Ints
		self.parser.add_option("--cluster-id", dest="clusterid", type="int",
			help="clustering stack id", metavar="ID")
		self.parser.add_option("--align-id", dest="alignid", type="int",
			help="alignment stack id", metavar="ID")

		### Floats
		self.parser.add_option("--contour", dest="contour", type="float", default=3.0,
			help="Chimera snapshot contour", metavar="#")
		self.parser.add_option("--zoom", dest="zoom", type="float", default=1.1,
			help="Chimera snapshot zoom", metavar="#")

		### Strings
		self.parser.add_option("--include", dest="includelist",
			help="list of EMAN style class numbers to include, e.g. --include=0,5,3", metavar="#,#")
		self.parser.add_option("--exclude", dest="excludelist",
			help="list of EMAN style class numbers to exclude, e.g. --exclude=0,5,3", metavar="#,#")
		self.parser.add_option("--symm", dest="symm", default="c1",
			help="symmetry id or name, e.g. --symm=c3 or --symm=25", metavar="TEXT")

		### Choices
		self.startmethods = ( "any", "csym", "oct", "icos" )
		self.parser.add_option("--method", dest="method",
			help="EMAN common lines method: startIcos, startCSym, startAny, startOct", metavar="TEXT", 
			type="choice", choices=self.startmethods, default="any")

		### Program specific parameters
		"""
		startAny  <imagefile> [sym=<c?>] [proc=<num proc>] [rounds=<2-5>] [mask=<rad>] [lp=<radius>]
		startcsym  <centered particles> <# to keep> [sym=<c?>] [imask=<rad>] [nosym] [fixrot=<side angle>]
		startoct  <centered particles> <# to keep> [nosym]
		starticos  <centered particles> <# to keep> [imask=<rad>] [nosym]
		"""
		self.parser.add_option("--mask", dest="mask", type="int",
			help="any: Mask radius", metavar="INT")
		self.parser.add_option("--rounds", dest="rounds", type="int", default=5,
			help="any: Rounds of Euler angle determination to use", metavar="INT")
		self.parser.add_option("--numkeep", dest="numkeep",
			help="csym/icos/oct: Number of classes per projection, use <10% of the total classes", metavar="INT")
		self.parser.add_option("--imask", dest="imask",
			help="csym/icos: Inside mask used to exclude inside regions", metavar="INT")

	#=====================
	def checkConflicts(self):
		### check the method
		if self.params['method'] is None:
			apDisplay.printError("Please enter the EMAN commonline method")
		#if self.params['method'] != 'any' and self.params['numkeep'] is None:
		#	apDisplay.printError("Please enter the number of particles per view, e.g. --numkeep=120")

		if self.params['description'] is None:
			apDisplay.printError("Please enter a description")

		### get the symmetry data
		if self.params['symm'] is None:
			apDisplay.printError("Symmetry was not defined")			
		else:
			self.symmdata = apSymmetry.findSymmetry(self.params['symm'])
			self.params['symm_id'] = self.symmdata.dbid
			self.params['symm_name'] = self.symmdata['eman_name']
			apDisplay.printMsg("Selected symmetry %s with id %s"%(self.symmdata['eman_name'], self.symmdata.dbid))

		if self.params['method'] == 'oct' and self.params['symm_name'] != 'oct':
			apDisplay.printError("startoct only works on octahedral symmetry")
		if self.params['method'] == 'icos' and self.params['symm_name'] != 'icos':
			apDisplay.printError("starticos only works on icosahedral symmetry")
		if self.params['method'] == 'csym' and self.params['symm_name'][0] != 'c':
			apDisplay.printError("startcsym only works on c symmetries")
		if self.params['method'] == 'any' and self.params['symm_name'] != 'c1':
			apDisplay.printError("startAny only works on c1 symmetry")

		### check for missing and duplicate entries
		if self.params['clusterid'] is None:
			apDisplay.printError("Please provide --cluster-id")	
		### get the stack ID from the other IDs
		self.clusterstackdata = appionData.ApClusteringStackData.direct_query(self.params['clusterid'])
		self.alignstackdata = self.clusterstackdata['clusterrun']['alignstack']
		self.params['stackid'] = self.alignstackdata['stack'].dbid

		### check and make sure we got the stack id
		if self.params['stackid'] is None:
			apDisplay.printError("stackid was not defined")

		### check that we only have one of include and exclude
		if self.params['includelist'] is not None and self.params['excludelist'] is not None:
			apDisplay.printError("both --include and --exclude were defined, only one is allowed")

	#=====================
	def setRunDir(self):
		stackdata = apStack.getOnlyStackData(self.params['stackid'], msg=False)
		path = stackdata['path']['path']
		uppath = os.path.dirname(os.path.dirname(os.path.abspath(path)))
		self.params['rundir'] = os.path.join(uppath, "models", self.params['runname'])

	#=====================
	def uploadDensity(self, volfile):
		### insert 3d volume density
		densq = appionData.Ap3dDensityData()
		densq['path'] = appionData.ApPathData(path=os.path.dirname(os.path.abspath(volfile)))
		densq['name'] = os.path.basename(volfile)
		densq['hidden'] = False
		densq['norm'] = True
		densq['symmetry'] = self.symmdata
		densq['pixelsize'] = self.clusterstackdata['clusterrun']['pixelsize']
		densq['boxsize'] = self.clusterstackdata['clusterrun']['boxsize']
		#densq['lowpass'] = None
		#densq['highpass'] = None
		densq['mask'] = self.params['mask']
		densq['description'] = self.params['description']+" from eman start-"+self.params['method']
		#densq['resolution'] = None
		densq['session'] = apStack.getSessionDataFromStackId(self.params['stackid'])
		densq['md5sum'] = apFile.md5sumfile(volfile)
		densq['eman'] = self.params['method']
		if self.params['commit'] is True:
			densq.insert()
		return

	#=====================
	def getClusterStack(self):
		"""
		get selected class averages from cluster stack
		"""
		numclusters = self.clusterstackdata['num_classes']

		if self.params['excludelist'] is None and self.params['includelist'] is None:
			### Case 1: Keep all classes
			self.params['keepfile'] = None
			apDisplay.printMsg("Keeping all %d clusters"%(numclusters))
		else:
			### Case 2: Keep subset of classes

			### list of classes to be excluded
			excludelist = []
			if self.params['excludelist'] is not None:
				excludestrlist = self.params['excludelist'].split(",")
				for excludeitem in excludestrlist:
					excludelist.append(int(excludeitem.strip()))
			apDisplay.printMsg("Exclude list: "+str(excludelist))

			### list of classes to be included
			includelist = []
			if self.params['includelist'] is not None:
				includestrlist = self.params['includelist'].split(",")
				for includeitem in includestrlist:
					includelist.append(int(includeitem.strip()))
			apDisplay.printMsg("Include list: "+str(includelist))

			### write kept cluster numbers to file
			self.params['keepfile'] = os.path.join(self.params['rundir'], "keepfile-"+self.timestamp+".list")
			apDisplay.printMsg("writing to keepfile "+self.params['keepfile'])
			kf = open(self.params['keepfile'], "w")
			count = 0
			for clusternum in range(numclusters):
				if ( (len(includelist) > 0 and clusternum in includelist) 
				 or (len(excludelist) > 0 and not clusternum in excludelist) ):
					count+=1
					kf.write(str(clusternum)+"\n")
			kf.close()
			apDisplay.printMsg("Keeping %d of %d clusters"%(count,numclusters))

			### override number of clusters with new number
			numclusters = count

		### create the new sub stack
		newstack = os.path.join(self.params['rundir'], "rawclusters.hed")
		oldstack = os.path.join(self.clusterstackdata['path']['path'], self.clusterstackdata['avg_imagicfile'])
		apFile.removeStack(newstack)
		apStack.makeNewStack(oldstack, newstack, self.params['keepfile'])

		if not os.path.isfile(newstack):
			apDisplay.printError("No cluster stack was created")

		return newstack, numclusters

	#=====================
	def getClusterParticles(self):
		"""
		get selected particles from cluster stack
		"""
		### list of classes to be excluded
		excludelist = []
		if self.params['excludelist'] is not None:
			excludestrlist = self.params['excludelist'].split(",")
			for excludeitem in excludestrlist:
				excludelist.append(int(excludeitem.strip()))
		apDisplay.printMsg("Exclude list: "+str(excludelist))

		### list of classes to be included
		includelist = []
		if self.params['includelist'] is not None:
			includestrlist = self.params['includelist'].split(",")
			for includeitem in includestrlist:
				includelist.append(int(includeitem.strip()))		
		apDisplay.printMsg("Include list: "+str(includelist))

		apDisplay.printMsg("Querying for clustered particles")	
		clusterpartq = appionData.ApClusteringParticlesData()
		clusterpartq['clusterstack'] = self.clusterstackdata
		particles = clusterpartq.query()
		apDisplay.printMsg("Sorting "+str(len(particles))+" clustered particles")	

		### write included particles to text file
		includeParticle = []
		excludeParticle = 0
		#f = open("test.log", "w")
		count = 0
		for part in particles:
			count += 1
			if count % 250 == 0:
				sys.stderr.write(".")
			alignpart = part['alignparticle']
			classnum = int(part['refnum'])-1
			emanstackpartnum = alignpart['stackpart']['particleNumber']-1

			if includelist and classnum in includelist:
				includeParticle.append(emanstackpartnum)
				#f.write("%d\t%d\t%d\tinclude\n"%(count, emanstackpartnum, classnum))
			elif excludelist and not classnum in excludelist:
				includeParticle.append(emanstackpartnum)
				#f.write("%d\t%d\t%d\tinclude\n"%(count, emanstackpartnum, classnum))
			else:
				excludeParticle += 1
				#f.write("%d\t%d\t%d\texclude\n"%(count, emanstackpartnum, classnum))
		#f.close()
		sys.stderr.write("\n")
		includeParticle.sort()
		apDisplay.printMsg("Keeping "+str(len(includeParticle))+" and excluding "+str(excludeParticle)+" particles")

		### write kept particles to file
		self.params['keepfile'] = os.path.join(self.params['rundir'], "keepfile-"+self.timestamp+".list")
		apDisplay.printMsg("writing to keepfile "+self.params['keepfile'])
		kf = open(self.params['keepfile'], "w")
		for partnum in includeParticle:
			kf.write(str(partnum)+"\n")
		kf.close()

		### get number of particles
		numparticles = len(includeParticle)

		### create the new sub stack
		stackdata = apStack.getOnlyStackData(self.params['stackid'])
		oldstack = os.path.join(stackdata['path']['path'], stackdata['name'])
		newstack = os.path.join(self.params['rundir'], "rawparticles.hed")
		apFile.removeStack(newstack)
		apStack.makeNewStack(oldstack, newstack, self.params['keepfile'])

		if not os.path.isfile(newstack):
			apDisplay.printError("No stack was created")

		return newstack, numparticles

	#=====================
	def start(self):
		if self.params['method'] == 'any':
			### startAny uses class averages
			clusterstack, numimages = self.getClusterStack()
		else:
			### starticos, startoct, startcsym uses individual particles
			clusterstack, numimages = self.getClusterParticles()

		if self.params['method'] != 'any':
			if self.params['numkeep'] is not None and numimages/10 < int(self.params['numkeep']):
				apDisplay.printWarning("particle number of "+ self.params['numkeep'] 
					+ " is greater than 10% of the number of selected classes")
			elif self.params['numkeep'] is None:
				self.params['numkeep'] = int(math.floor(numimages/20.0))+1
				apDisplay.printWarning("numkeep was not defined, using %d particles"%(self.params['numkeep']))

		nproc = apParam.getNumProcessors()

		#construct command for each of the EMAN commonline method
		if self.params['method'] == 'any':
			startcmd = "startAny "+clusterstack+" proc="+str(nproc)
			startcmd +=" sym="+self.symmdata['eman_name']
			if self.params['mask'] is not None:
				startcmd +=" mask="+str(self.params['mask'])
			else:
				maskrad = math.floor(self.clusterstackdata['clusterrun']['boxsize']/2.0)
				startcmd +=" mask=%d"%(maskrad)
			if self.params['rounds'] is not None:
				startcmd +=" rounds="+str(self.params['rounds'])

		elif self.params['method'] == 'csym':
			startcmd = "startcsym "+clusterstack+" "
			startcmd +=" "+str(self.params['numkeep'])
			startcmd +=" sym="+self.symmdata['eman_name']
			if self.params['imask'] is not None:
				startcmd +=" imask="+self.params['imask']

		elif self.params['method'] == 'oct':
			startcmd = "startoct "+clusterstack+" "
			startcmd +=" "+str(self.params['numkeep'])

		elif self.params['method'] == 'icos':
			startcmd = "starticos "+clusterstack+" "
			startcmd +=" "+str(self.params['numkeep'])
			if self.params['imask'] is not None:
				startcmd +=" imask="+self.params['imask']

		apDisplay.printMsg("Creating 3D model with EMAN function: start"+self.params['method'])
		apFile.removeFile("threed.0a.mrc")
		apFile.removeFile("eman.log")
		apEMAN.executeEmanCmd(startcmd, verbose=False, logfile="eman.log")
		#apEMAN.executeEmanCmd(startcmd, verbose=True)

		finalmodelname = "threed-%s-eman_start%s.mrc"%(self.timestamp, self.params['method'])
		finalmodelpath = os.path.join(self.params['rundir'], finalmodelname)
		apDisplay.printMsg("Final model name: "+finalmodelname)
		finalmodel = "threed.0a.mrc"
		if os.path.isfile(finalmodel):
			emancmd = "proc3d %s %s norm=0,1 origin=0,0,0"%(finalmodel, finalmodelpath)
			#shutil.move(finalmodel, finalmodelpath)
			apEMAN.executeEmanCmd(emancmd, verbose=True)
			if not apVolume.isValidVolume(finalmodelpath):
				apDisplay.printError("Created volume is not valid")
		else:
			apDisplay.printError("No 3d model was created")

		### upload it
		self.uploadDensity(finalmodelpath)

		### chimera imaging
		apChimera.renderSnapshots(finalmodelpath, contour=self.params['contour'],
			zoom=self.params['zoom'], sym=self.symmdata['eman_name'])
		apChimera.renderAnimation(finalmodelpath, contour=self.params['contour'],
			zoom=self.params['zoom'], sym=self.symmdata['eman_name'])

#=====================
#=====================
if __name__ == '__main__':
	createModel = createModelScript()
	createModel.start()
	createModel.close()
