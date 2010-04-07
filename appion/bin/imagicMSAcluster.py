#!/usr/bin/env python
# Python script to upload a template to the database, and prepare images for import




	####	need to change mode to 755 of the batch file that is created
	####	how do I specify the filename from the pulldown menu?



import os
import shutil
import time
import sys
import re
import subprocess

from appionlib import appionScript
from appionlib import appiondata
from appionlib import apDisplay
from appionlib import apIMAGIC
from appionlib import apFile
from appionlib import apParam
from appionlib import apStack

#=====================
#=====================
class imagicClusterScript(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage( "Usage: %prog --file=<name> --apix=<pixel> --outdir=<dir> "
			+"[options]")

		self.parser.add_option("--imagicAnalysisId", dest="analysisId",
			help="ID of particle analysis", metavar="int")
		self.parser.add_option("--ignore_images", dest="ignore_images", type="int", default=0,
			help="percentage of images to ignore when constructing classes", metavar="INT")
		self.parser.add_option("--num_classes", dest="num_classes", type="str",
			help="number of classes to create", metavar="STR")
		self.parser.add_option("--ignore_members", dest="ignore_members", type="int", default=0,
			help="percentage of worst class members to ignore", metavar="INT")
		self.parser.add_option("--num_eigenimages", dest="num_eigenimages", type="int", default=69,
			help="number of eigenimages to use when computing class averages (from most representative to least representative)", metavar="INT")

		return

	#=====================
	def checkConflicts(self):
		### check for IMAGIC installation
		self.imagicroot = apIMAGIC.checkImagicExecutablePath()
	
		### check input parameters
		if self.params['analysisId'] is None:
			apDisplay.printError("There is no imagic analysis Id specified")
		if self.params['runname'] is None:
			apDisplay.printError("enter a run ID")
		if self.params['num_classes'] is None:
			apDisplay.printError("enter number of classes that you want")

		return

	#=====================
	def setRunDir(self):

		# get reference-free classification and reclassification parameters
		if self.params['analysisId'] is not None:
			aligndata = appiondata.ApAlignAnalysisRunData.direct_query(self.params['analysisId'])
			self.params['rundir'] = aligndata['path']['path']
		else:
			apDisplay.printError("Analysis not in the database")

	def createImagicBatchFile(self,numclusters):
		self.params['classfile'] = "classes_%d_eigens_%d_imagesignored_%d.cls" \
			% (numclusters, self.params['num_eigenimages'], self.params['ignore_images'])
		self.params['classumfile'] = "classums_%d_eigens_%d_imagesignored_%d_membersignored_%d.hed" \
			% (numclusters, self.params['num_eigenimages'], self.params['ignore_images'], self.params['ignore_members'])
		
		# IMAGIC batch file creation
		batchending = "_%d_%d_%d" % (self.params['num_eigenimages'], self.params['ignore_images'], self.params['ignore_members'])
		filename = os.path.join(self.params['rundir'], "imagicMSAcluster_classes_"+str(numclusters)+batchending+".batch")
		f = open(filename, 'w')
		f.write("#!/bin/csh -f\n")
		f.write("setenv IMAGIC_BATCH 1\n")
		f.write(str(self.imagicroot)+"/msa/classify.e <<EOF > imagicMSAcluster_classes_"+str(numclusters)+".log\n")
		f.write("IMAGES/VOLUMES\n")
		f.write("start\n")
		f.write(str(self.params['ignore_images'])+"\n")
		f.write(str(self.params['num_eigenimages'])+"\n")
		f.write("YES\n")
		f.write(str(numclusters)+"\n")
		f.write("%s\n" % (self.params['classfile'][:-4]))
		f.write("EOF\n")
		f.write(str(self.imagicroot)+"/msa/classum.e <<EOF >> imagicMSAcluster_classes_"+str(numclusters)+".log\n")
		f.write("start\n")
		f.write("%s\n" % (self.params['classfile'][:-4]))
		f.write("%s\n" % (self.params['classumfile'][:-4]))
		f.write("YES\n")
		f.write("NONE\n")
		f.write(str(self.params['ignore_members'])+"\n")
		f.write("EOF\n")
		f.close()

		return filename

	def readClassesFile(self, clsfile, numclusters):
		if not os.path.isfile(clsfile):
			apDisplay.printError("could not read class file, "+clsfile)

		### open file and convert all values into integeres / floats in a list
		f = open(clsfile, 'r')
		filestring = f.read()
		filestring = filestring.replace('\n','')
		list = filestring.split()
		objects = [eval(P) for P in list]
		position = 0
		cls_particle_data = []
		classqualities = []
		particles_in_class = []

		if self.params['ignore_members'] > 0:
			### read the .plt file that has all the internal variances of each raw particle, and figure 
			### out which particles were NOT summed up to belong to that specific class
			pltfile = os.path.join(self.params['rundir'], self.params['classfile'][:-4]+".plt")
			pf = open(pltfile, "r")
			pflines = pf.readlines()
			pf.close()

		### loop through all the values in list, put each value into corresponding list
		for item in range(numclusters):
			classnumber = objects[position]
			num_particles = objects[position+1]
			classquality = objects[position+2]
			position = position + 3
			particles = []
			for particle in range(num_particles):
				particles.append(objects[position])
				position = position + 1
			cls_particle_data.append(particles)
			classqualities.append(classquality)
			particles_in_class.append(num_particles)
		

		
		return cls_particle_data, classqualities, particles_in_class

	def calcResolution(self, partlist, stackfile, apix):
		### group particles by refnum
		reflistsdict = {}
		for partdict in partlist:
			refnum = partdict['template']
			partnum = partdict['num']
			if not refnum in reflistsdict:
				reflistsdict[refnum] = []
			reflistsdict[refnum].append(partnum)

		### get resolution
		self.resdict = {}
		boxsizetuple = apFile.getBoxSize(stackfile)
		boxsize = boxsizetuple[0]
		for refnum in reflistsdict.keys():
			partlist = reflistsdict[refnum]
			esttime = 3e-6 * len(partlist) * boxsize**2
			apDisplay.printMsg("Ref num %d; %d parts; est time %s"
				%(refnum, len(partlist), apDisplay.timeString(esttime)))

			frcdata = apFourier.spectralSNRStack(stackfile, apix, partlist, msg=False)
			frcfile = "frcplot-%03d.dat"%(refnum)
			apFourier.writeFrcPlot(frcfile, frcdata, apix, boxsize)
			res = apFourier.getResolution(frcdata, apix, boxsize)

			self.resdict[refnum] = res

			return
				
	def getAlignParticleData(self, partnum):
		alignpartq = appiondata.ApAlignParticlesData()
		alignpartq['alignstack'] = self.analysisdata['alignstack']
		alignpartq['partnum'] = partnum
		alignparts = alignpartq.query(results=1)
		return alignparts[0]

	def insertClusterRun(self):
		### create a clustering run object
		clusterrunq = appiondata.ApClusteringRunData()
		clusterrunq['runname'] = self.params['runname']
		clusterrunq['pixelsize'] = self.params['apix']
		clusterrunq['boxsize'] = self.params['boxsize']
		clusterrunq['description'] = self.params['description']
		clusterrunq['num_particles'] = self.params['num_particles']
		clusterrunq['alignstack'] = self.analysisdata['alignstack']
		clusterrunq['analysisrun'] = self.analysisdata

		apDisplay.printMsg("inserting clustering parameters into database")
		if self.params['commit'] is True:
			clusterrunq.insert()
		else:
			apDisplay.printWarning("not committing results to DB")
		self.clusterrun = clusterrunq

		return

	def insertClusterStack(self, numclusters):
		pathdata = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))

		### clusterStack object
		clusterstackq = appiondata.ApClusteringStackData()
		clusterstackq['num_classes'] = numclusters
		clusterstackq['avg_imagicfile'] = self.params['classumfile']
		clusterstackq['clusterrun'] = self.clusterrun
		clusterstackq['ignore_images'] = self.params['ignore_images']
		clusterstackq['ignore_members'] = self.params['ignore_members']
		clusterstackq['num_factors'] = self.params['num_eigenimages']
		clusterstackq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
		clusterstackq['hidden'] = False

		### first insertion into database, if commit is checked
		apDisplay.printMsg("inserting clustering stack into database")
		if self.params['commit'] is True:
			clusterstackq.insert()
		else:
			apDisplay.printWarning("not committing results to DB")

		### inserting particles into database
		if self.params['commit'] is True:
			apDisplay.printColor("Inserting particle classification data, please wait", "cyan")

		### read .cls file that contains information regarding particle classification
		clsfile = os.path.join(self.params['rundir'], self.params['classfile'])
		cls_particle_data, classqualities, particles_in_class = self.readClassesFile(clsfile, numclusters)

		for i in range(numclusters):
			### insert the particles
			cls_num = i + 1
			cls_quality = classqualities[i]
			num_particles = particles_in_class[i]
			particles = cls_particle_data[i]
			
#			### calculate SSNR resolution for class
#			partlist = ""
#			stackfile = self.params['classumfile']
#			self.calcResolution(partlist, stackfile, self.params['apix'])
			
			### Clustering Particle object
			clusterrefq = appiondata.ApClusteringReferenceData()
			clusterrefq['refnum'] = cls_num
			clusterrefq['clusterrun'] = self.clusterrun
			clusterrefq['path'] = pathdata
			clusterrefq['num_particles'] = num_particles			
			
			for partnum in particles:
				alignpartdata = self.getAlignParticleData(partnum)
				cpartq = appiondata.ApClusteringParticlesData()
				cpartq['clusterstack'] = clusterstackq
				cpartq['alignparticle'] = alignpartdata
				cpartq['refnum'] = cls_num
				cpartq['partnum'] = partnum
				cpartq['clusterreference'] = clusterrefq
				cpartq['imagic_cls_quality'] = cls_quality
				if self.params['commit'] is True:
					cpartq.insert()
				lastnum = partnum
		return

	#=====================
	def start(self):
		### get analysis paramteres
		self.analysisdata = appiondata.ApAlignAnalysisRunData.direct_query(self.params['analysisId'])
		pixelsize = self.analysisdata['alignstack']['pixelsize']
		boxsize = self.analysisdata['alignstack']['boxsize']
		bin = self.analysisdata['imagicMSArun']['bin']
		self.params['apix'] = float(pixelsize) * int(bin)
		self.params['boxsize'] = int(boxsize) / int(bin)
		self.params['num_particles'] = self.analysisdata['alignstack']['num_particles']

		starttime=time.time()
		print self.params
		print "... stack pixel size: "+str(self.params['apix'])
		print "... stack box size: "+str(self.params['boxsize'])
		apDisplay.printColor("Running IMAGIC .batch file: See imagicMSAcluster log file(s) corresponding to # of classes for details", "cyan")

		### insert run into database
		self.insertClusterRun()

		### split the cluster numbers
		numclasslist = self.params['num_classes'].split(",")
		for item in numclasslist:
			numclusters = int(item)
			apDisplay.printColor("\n==========================\nprocessing class averages for "
				+str(numclusters)+" classes\n==========================\n", "green")

			### create IMAGIC batch file
			batchfile = self.createImagicBatchFile(numclusters)

			### execute IMAGIC batch file
			clustertime0 = time.time()
			proc = subprocess.Popen("chmod 775 "+str(batchfile), shell=True)
			proc.wait()
			apIMAGIC.executeImagicBatchFile(batchfile)
			logfile = open(os.path.join(self.params['rundir'], "imagicMSAcluster_classes_"+str(numclusters)+".log"))
			loglines = logfile.readlines()
			for line in loglines:
				if re.search("ERROR in program", line):
					apDisplay.printError("ERROR IN IMAGIC SUBROUTINE, please check the logfile: imagicMSAcluster_classes_"\
						+str(numclusters)+".log")
			apDisplay.printColor("finished IMAGIC in "+apDisplay.timeString(time.time()-clustertime0), "cyan")

			### normalize
			classfile = os.path.join(self.params['rundir'], self.params['classumfile'])
			emancmd = "proc2d "+classfile+" "+classfile+".norm.hed norm"
			while os.path.isfile(classfile+".norm.img"):
				apStack.removeStack(alignstack+".norm.img")
			apParam.runCmd(emancmd, "EMAN")
			os.rename(classfile+".norm.hed", classfile)
			os.rename(classfile+".norm.img", classfile[:-4]+".img")

			### connect to database
			self.insertClusterStack(numclusters)



#=====================
#=====================
if __name__ == '__main__':
	imagicCluster = imagicClusterScript()
	imagicCluster.start()
	imagicCluster.close()



