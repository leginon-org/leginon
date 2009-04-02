#!/usr/bin/env python

### create model from EMAN startAny function and automatically calls uploadModel.py

import os
import re
import sys
import time
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
import apDatabase
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

		### Strings
		self.parser.add_option("--class-list-keep", dest="keepclasslist",
			help="list of EMAN style class numbers to include in sub-stack, e.g. --class-list-keep=0,5,3", metavar="#,#")
		self.parser.add_option("--class-list-drop", dest="dropclasslist",
			help="list of EMAN style class numbers to exclude in sub-stack, e.g. --class-list-drop=0,5,3", metavar="#,#")
		self.parser.add_option("--symm", dest="symm", default="c1",
			help="symmetry id or name, e.g. --symm=c3 or --symm=25", metavar="TEXT")

		### Choices
		self.startmethods = ( "any", "csym", "oct", "icos" )
		self.parser.add_option("--method", dest="method",
			help="EMAN common lines method: startIcos, startCSym, startAny, startOct", metavar="TEXT", 
			type="choice", choices=self.startmethods, default="normal" )

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
			help="csym/icos/oct: Number of particles per view. ~10% of the total particle", metavar="INT")
		self.parser.add_option("--imask", dest="imask",
			help="csym/icos: Inside mask used to exclude inside regions", metavar="INT")

	#=====================
	def checkConflicts(self):
		### check the method
		if self.params['method'] is None:
			apDisplay.printError("Please enter the EMAN commonline method")
		if self.params['method'] != 'any' and self.params['numkeep'] is None:
			apDisplay.printError("Please enter the number of particles per view, e.g. --numkeep=120")

		### get the symmetry data
		if self.params['symm'] is None:
			apDisplay.printError("Symmetry was not defined")			
		else:
			self.symmdata = apSymmetry.parseSymmetry(self.params['symm'])
			self.params['symm_id'] = self.symmdata.dbid
			self.params['symm_name'] = self.symmdata['eman_name']
			apDisplay.printMsg("Selected symmetry %s with id %s"%(self.symmdata['eman_name'], self.symmdata.dbid))

		### check for missing and duplicate entries
		if self.params['alignid'] is None and self.params['clusterid'] is None:
			apDisplay.printError("Please provide either --cluster-id or --align-id")
		if self.params['alignid'] is not None and self.params['clusterid'] is not None:
			apDisplay.printError("Please provide only one of either --cluster-id or --align-id")		

		### get the stack ID from the other IDs
		if self.params['alignid'] is not None:
			self.alignstackdata = appionData.ApAlignStackData.direct_query(self.params['alignid'])
			self.params['stackid'] = self.alignstackdata['stack'].dbid
		elif self.params['clusterid'] is not None:
			self.clusterstackdata = appionData.ApClusteringStackData.direct_query(self.params['clusterid'])
			self.alignstackdata = self.clusterstackdata['clusterrun']['alignstack']
			self.params['stackid'] = self.alignstackdata['stack'].dbid

		### check and make sure we got the stack id
		if self.params['stackid'] is None:
			apDisplay.printError("stackid was not defined")

		### check that we have a keep or drop list and not both
		if self.params['keepclasslist'] is None and self.params['dropclasslist'] is None:
			apDisplay.printError("class numbers to be included/excluded was not defined")
		if self.params['keepclasslist'] is not None and self.params['dropclasslist'] is not None:
			apDisplay.printError("both --class-list-keep and --class-list-drop were defined, only one is allowed")

	#=====================
	def cleanup(self, norefpath, norefclassid, method):
		clean = "rm -fv CCL.hed CCL.img"
		for file in ("CCL.hed", "CCL.img"):
			if os.path.isfile(file):
				apDisplay.printWarning("Removing file: "+file)
				os.remove(file)
		if self.params['rounds']:
			for n in range(self.params['rounds']):
				modelpath = os.path.join(norefpath, method+"-"+str(norefclassid)+"_"+str(n+1)+".mrc")
				if not os.path.exists(modelpath):
					break

			apDisplay.printWarning("Moving threed.0a.mrc to "+norefpath+" and renaming it "+method+"-"
				+str(norefclassid)+"_"+str(n)+".mrc")
			shutil.copy("threed.0a.mrc", modelpath)

			oldexcludepath = os.path.join(norefpath, "exclude.lst")
			if os.path.exists(oldexcludepath):
				newexcludepath = os.path.join(norefpath, "exclude-"+str(norefclassid)+"_"+str(n)+".mrc")
				apDisplay.printWarning("Moving "+oldexcludepath+" to "+newexcludepath)
				shutil.copy(oldexcludepath, newexcludepath)
		else:
			modelpath = os.path.join(norefpath, method+"-"+str(norefclassid)+".mrc")

			apDisplay.printWarning("Moving threed.0a.mrc to "+norefpath+" and renaming it "+method+"-"
				+str(norefclassid)+".mrc")
			shutil.copy("threed.0a.mrc", modelpath)

			oldexcludepath = os.path.join(norefpath, "exclude.lst")
			if os.path.exists(oldexcludepath):
				newexcludepath = os.path.join(norefpath, "exclude-"+str(norefclassid)+".mrc")
				apDisplay.printWarning("Moving "+oldexcludepath+" to "+newexcludepath)
				shutil.copy(oldexcludepath, newexcludepath)
		return modelpath

	#=====================
	def setRunDir(self):
		stackdata = apStack.getOnlyStackData(self.params['stackid'], msg=False)
		path = stackdata['path']['path']
		uppath = os.path.dirname(os.path.abspath(path))
		self.params['rundir'] = os.path.join(uppath, self.params['runname'])

	#=====================
	def excludedClasses(self, origclassfile, norefpath):
		excludelist = self.params['exclude'].split(",")

		apDisplay.printMsg( "Creating exclude.lst: "+norefpath )

		excludefile = os.path.join(norefpath,"exclude.lst")
		if os.path.isfile(excludefile):
			apDisplay.printWarning("Removing the file 'exclude.lst' from: "+norefpath)
			os.remove(excludefile)

		f = open(excludefile, "w")
		for excludeitem in excludelist:
			f.write(str(excludeitem)+"\n")
		f.close()

		newclassfile = origclassfile+"-new"
		# old file need to be removed or the images will be appended
		if os.path.isfile(newclassfile):
			apDisplay.printWarning("removing old image file: "+newclassfile )
			os.remove(newclassfile+".hed")
			os.remove(newclassfile+".img")

		apDisplay.printMsg("Creating new class averages "+newclassfile)
		excludecmd = ( "proc2d "+origclassfile+".hed "+newclassfile+".hed exclude="+excludefile )
		apEMAN.executeEmanCmd(excludecmd, verbose=True)

		return newclassfile

	#=====================
	def uploadDensity(self, volfile):
		### insert 3d volume density
		densq = appionData.Ap3dDensityData()
		densq['path'] = appionData.ApPathData(path=os.path.dirname(os.path.abspath(volfile)))
		densq['name'] = os.path.basename(volfile)
		densq['hidden'] = False
		densq['norm'] = True
		densq['symmetry'] = self.symmdata
		densq['pixelsize'] = apix
		densq['boxsize'] = self.params['box']
		densq['lowpass'] = self.params['lp']
		#densq['highpass'] = self.params['highpasspart']
		#densq['mask'] = self.params['radius']
		densq['description'] = self.params['description']
		densq['resolution'] = self.params['lp']
		densq['session'] = self.sessiondata
		densq['md5sum'] = apFile.md5sumfile(volfile)
		densq['eman'] = self.params['method']
		if self.params['commit'] is True:
			densq.insert()
		return

	#=====================
	def start(self):
		### new stack path
		stackdata = apStack.getOnlyStackData(self.params['stackid'])
		oldstack = os.path.join(stackdata['path']['path'], stackdata['name'])
		newstack = os.path.join(self.params['rundir'], stackdata['name'])
		apStack.checkForPreviousStack(newstack)

		### list of classes to be excluded
		excludelist = []
		if self.params['dropclasslist'] is not None:
			excludestrlist = self.params['dropclasslist'].split(",")
			for excludeitem in excludestrlist:
				excludelist.append(int(excludeitem.strip()))
		apDisplay.printMsg("Exclude list: "+str(excludelist))

		### list of classes to be included
		includelist = []
		if self.params['keepclasslist'] is not None:
			includestrlist = self.params['keepclasslist'].split(",")
			for includeitem in includestrlist:
				includelist.append(int(includeitem.strip()))		
		apDisplay.printMsg("Include list: "+str(includelist))

		### get particles from align or cluster stack
		if self.params['alignid'] is not None:
			alignpartq =  appionData.ApAlignParticlesData()
			alignpartq['alignstack'] = self.alignstackdata
			particles = alignpartq.query()
		elif self.params['clusterid'] is not None:
			clusterpartq = appionData.ApClusteringParticlesData()
			clusterpartq['clusterstack'] = self.clusterstackdata
			particles = clusterpartq.query()

		### write included particles to text file
		includeParticle = []
		excludeParticle = 0
		f = open("test.log", "w")
		count = 0
		for part in particles:
			count += 1
			#partnum = part['partnum']-1
			if 'alignparticle' in part:
				alignpart = part['alignparticle']
				classnum = int(part['refnum'])-1
			else:
				alignpart = part
				classnum = int(part['ref']['refnum'])-1
			emanstackpartnum = alignpart['stackpart']['particleNumber']-1

			### check score
			if ( self.params['minscore'] is not None 
			 and alignpart['score'] is not None 
			 and alignpart['score'] < self.params['minscore'] ):
				excludeParticle += 1
				f.write("%d\t%d\t%d\texclude\n"%(count, emanstackpartnum, classnum))

			### check spread
			elif ( self.params['minspread'] is not None 
			 and alignpart['spread'] is not None 
			 and alignpart['spread'] < self.params['minspread'] ):
				excludeParticle += 1
				f.write("%d\t%d\t%d\texclude\n"%(count, emanstackpartnum, classnum))

			elif includelist and classnum in includelist:
				includeParticle.append(emanstackpartnum)
				f.write("%d\t%d\t%d\tinclude\n"%(count, emanstackpartnum, classnum))
			elif excludelist and not classnum in excludelist:
				includeParticle.append(emanstackpartnum)
				f.write("%d\t%d\t%d\tinclude\n"%(count, emanstackpartnum, classnum))
			else:
				excludeParticle += 1
				f.write("%d\t%d\t%d\texclude\n"%(count, emanstackpartnum, classnum))

		f.close()
		includeParticle.sort()
		apDisplay.printMsg("Keeping "+str(len(includeParticle))+" and excluding "+str(excludeParticle)+" particles")

		#print includeParticle

		### write kept particles to file
		self.params['keepfile'] = os.path.join(self.params['rundir'], "keepfile-"+self.timestamp+".list")
		apDisplay.printMsg("writing to keepfile "+self.params['keepfile'])
		kf = open(self.params['keepfile'], "w")
		for partnum in includeParticle:
			kf.write(str(partnum)+"\n")
		kf.close()

		### get number of particles
		numparticles = len(includeParticle)
		if excludelist:
			self.params['description'] += ( " ... %d particle substack with %s classes excluded" 
				% (numparticles, self.params['dropclasslist']))
		elif includelist:
			self.params['description'] += ( " ... %d particle substack with %s classes included" 
				% (numparticles, self.params['keepclasslist']))	

		### create the new sub stack
		apStack.makeNewStack(oldstack, newstack, self.params['keepfile'])

		if not os.path.isfile(newstack):
			apDisplay.printError("No stack was created")

		apStack.averageStack(stack=newstack)
		if self.params['commit'] is True:
			apStack.commitSubStack(self.params)
			newstackid = apStack.getStackIdFromPath(newstack)
			apStackMeanPlot.makeStackMeanPlot(newstackid, gridpoints=4)


	#=====================
	def start(self):

		norefClassdata=appionData.ApNoRefClassRunData.direct_query(self.params['norefclass'])

		#Get class average file path through ApNoRefRunData
		norefpath = norefClassdata['norefRun']['path']['path']

		self.params['box'] = apStack.getStackBoxsize((norefClassdata['norefRun']['stack']).dbid)

		#Get class average file name
		norefClassFile = norefClassdata['classFile']
		origclassfile = os.path.join(norefpath, norefClassFile)

		if self.params['exclude'] is not None:
			#create the list of the indexes to be excluded
			classfile = self.excludedClasses(origclassfile, norefpath)
		else:
			#complete path of the class average file
			classfile = origclassfile+"-orig"
			apDisplay.printMsg("copying file "+origclassfile+" to "+classfile)
			shutil.copy(origclassfile+".hed", classfile+".hed")
			shutil.copy(origclassfile+".img", classfile+".img")

		#warn if the number of particles to use for each view is more than 10% of the total number of particles
		if self.params['exclude'] is not None:
			numclass = norefClassdata['num_classes'] - len(self.params['exclude'].split(","))
		else:
			numclass = norefClassdata['num_classes']

		if self.params['partnum'] is not None and numclass/10 < int(self.params['partnum']):
			apDisplay.printWarning("particle number of "+ self.params['partnum'] + " is greater than 10% of the number of selected classes")


		nproc = apParam.getNumProcessors()

		#construct command for each of the EMAN commonline method
		if self.params['method']=='startAny':
			startCmd = "startAny "+classfile+".hed proc="+str(nproc)
			if self.params['symm_name'] is not None:
				startCmd +=" sym="+self.params['symm_name']
			if self.params['mask'] is not None:
				startCmd +=" mask="+str(self.params['mask'])
			if self.params['lp'] is not None:
				startCmd +=" lp="+str(self.params['lp'])
			if self.params['rounds'] is not None:
				startCmd +=" rounds="+str(self.params['rounds'])

		elif self.params['method']=='startCSym':
			startCmd = "startcsym "+classfile+".hed "
			if self.params['partnum'] is not None:
				startCmd +=" "+self.params['partnum']
			if self.params['symm_name'] is not None:
				startCmd +=" sym="+self.params['symm_name']
			if self.params['imask'] is not None:
				startCmd +=" imask="+self.params['imask']

		elif self.params['method']=='startOct':
			startCmd = "startoct "+classfile+".hed "
			if self.params['partnum'] is not None:
				startCmd +=" "+self.params['partnum']

		elif self.params['method']=='startIcos':
			startCmd = "starticos "+classfile+".hed "
			if self.params['partnum'] is not None:
				startCmd +=" "+self.params['partnum']
			if self.params['imask'] is not None:
				startCmd +=" imask="+self.params['imask']

		apDisplay.printMsg("Creating 3D model using class averages with EMAN function of"+self.params['method']+"")
		print startCmd
		apEMAN.executeEmanCmd(startCmd, verbose=False)

		#cleanup the extra files, move the created model to the same folder as the class average and rename it as startAny.mrc
		modelpath = self.cleanup(norefpath, self.params['norefclass'], self.params['method'])

		### upload it
		self.uploadDensity(modelpath)

		### chimera imaging
		apChimera.renderSnapshots(modelpath, contour=1.5, zoom=1.0, sym='c1')
		apChimera.renderAnimation(modelpath, contour=1.5, zoom=1.0, sym='c1')




#=====================
#=====================
if __name__ == '__main__':
	createModel = createModelScript()
	createModel.start()
	createModel.close()
