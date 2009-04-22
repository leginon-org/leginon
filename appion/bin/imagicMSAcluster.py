#!/usr/bin/env python
# Python script to upload a template to the database, and prepare images for import




	####	need to change mode to 755 of the batch file that is created
	####	how do I specify the filename from the pulldown menu?



import os
import shutil
import time
import sys
import re
import appionScript
import appionData
import apParam
import apRecon
import apDisplay
import apIMAGIC
import apEMAN
import apFile
import apDatabase
import apStack
import apProject

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

		return 

	#=====================
	def checkConflicts(self):
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
			aligndata = appionData.ApAlignAnalysisRunData.direct_query(self.params['analysisId']) 
			self.params['rundir'] = aligndata['path']['path']
		else:
			apDisplay.printError("Analysis not in the database")

	def createImagicBatchFile(self,clusternumber):
		# IMAGIC batch file creation
		batchending = "_"+str(self.params['ignore_images'])+"_"+str(self.params['ignore_members'])
		filename = os.path.join(self.params['rundir'], "imagicMSAcluster_classes_"+str(clusternumber)+batchending+".batch")
		f = open(filename, 'w')
                f.write("#!/bin/csh -f\n")
                f.write("setenv IMAGIC_BATCH 1\n")
		f.write("/usr/local/IMAGIC/msa/classify.e <<EOF > imagicMSAcluster_classes_"+str(clusternumber)+".log\n")
		f.write("IMAGES/VOLUMES\n")
		f.write("start\n")
		f.write(str(self.params['ignore_images'])+"\n")
		f.write("69\n")
		f.write("YES\n")
		f.write(str(clusternumber)+"\n")
		f.write("classes_"+str(clusternumber)+"_imagesignored_"+str(self.params['ignore_images'])+"\n")
		f.write("EOF\n")
		f.write("/usr/local/IMAGIC/msa/classum.e <<EOF >> imagicMSAcluster_classes_"+str(clusternumber)+".log\n")
		f.write("start\n")
		f.write("classes_"+str(clusternumber)+"_imagesignored_"+str(self.params['ignore_images'])+"\n")
		f.write("classums_"+str(clusternumber)+"_imagesignored_"+str(self.params['ignore_images'])+"_membersignored_"+str(self.params['ignore_members'])+"\n")
		f.write("YES\n")
		f.write("NONE\n")
		f.write(str(self.params['ignore_members'])+"\n")
		f.write("EOF\n")
		f.close()

		return filename

        def readClassesFile(self, clsfile, clusternumber):
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
		
		### loop through all the values in list, put each value into corresponding list
		for item in range(clusternumber):
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

        def getAlignParticleData(self, partnum):
                alignpartq = appionData.ApAlignParticlesData()
                alignpartq['alignstack'] = self.analysisdata['alignstack']
                alignpartq['partnum'] = partnum
                alignparts = alignpartq.query(results=1)
		return alignparts[0]

	def insertClusterRun(self, insert=False):               
		### create a clustering run object 
		clusterrunq = appionData.ApClusteringRunData()
		clusterrunq['runname'] = self.params['runname']
		clusterrunq['pixelsize'] = self.params['apix']
		clusterrunq['boxsize'] = self.params['boxsize']
		clusterrunq['description'] = self.params['description']
		clusterrunq['num_particles'] = self.params['num_particles']	
		clusterrunq['alignstack'] = self.analysisdata['alignstack']
		clusterrunq['analysisrun'] = self.analysisdata
		clusterrunq['project|projects|project'] = self.analysisdata['project|projects|project']

                apDisplay.printMsg("inserting clustering parameters into database")
                if insert is True:
                        clusterrunq.insert()
                self.clusterrun = clusterrunq

		return 

	def insertClusterStack(self, clusternumber, insert=False):
		clusterstackq = appionData.ApClusteringStackData()
		clusterstackq['num_classes'] = clusternumber
		clusterstackq['avg_imagicfile'] = "classums_"+str(clusternumber)+"_imagesignored_"+\
			str(self.params['ignore_images'])+"_membersignored_"+str(self.params['ignore_members'])+".hed"
		clusterstackq['clusterrun'] = self.clusterrun
                clusterstackq['ignore_images'] = self.params['ignore_images']
                clusterstackq['ignore_members'] = self.params['ignore_members']
		clusterstackq['path'] = appionData.ApPathData(path=os.path.abspath(self.params['rundir']))
		clusterstackq['hidden'] = False

                apDisplay.printMsg("inserting clustering stack into database")
                if insert is True:
                        clusterstackq.insert()
		
		### inserting particles into database
                apDisplay.printColor("Inserting particle classification data, please wait", "cyan")
                
		### read .cls file that contains information regarding particle classification
                clsfile = os.path.join(self.params['rundir'], "classes_"+str(clusternumber)+"_imagesignored_"+str(self.params['ignore_images'])+".cls")
                cls_particle_data, classqualities, particles_in_class = self.readClassesFile(clsfile, clusternumber)
			
		for i in range(clusternumber):
			### insert the particles
			cls_num = i + 1
			cls_quality = classqualities[i]
			num_particles = particles_in_class[i]
			particles = cls_particle_data[i]
			for partnum in particles:
				alignpartdata = self.getAlignParticleData(partnum) 
				cpartq = appionData.ApClusteringParticlesData()
				cpartq['clusterstack'] = clusterstackq
				cpartq['alignparticle'] = alignpartdata
				cpartq['refnum'] = cls_num
				cpartq['partnum'] = partnum
				cpartq['clusterreference'] = None
				cpartq['imagic_cls_quality'] = cls_quality
				if insert is True:
					cpartq.insert()	
				lastnum = partnum		
		return

	#=====================
	def start(self):
		### get analysis paramteres
		self.analysisdata = appionData.ApAlignAnalysisRunData.direct_query(self.params['analysisId'])
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
		if self.params['commit'] is True:
                        self.insertClusterRun(insert=True)
		else:
			 apDisplay.printWarning("not committing results to DB")

		### split the cluster numbers
		numclasslist = self.params['num_classes'].split(",")
		for item in numclasslist:
			clusternumber = int(item)
			apDisplay.printColor("\n==========================\nprocessing class averages for "
				+str(clusternumber)+" classes\n==========================\n", "green")		

			### create IMAGIC batch file
			batchfile = self.createImagicBatchFile(clusternumber)	

			### execute IMAGIC batch file
			clustertime0 = time.time()
			os.system("chmod 775 "+str(batchfile))
			apIMAGIC.executeImagicBatchFile(batchfile)
			logfile = open(os.path.join(self.params['rundir'], "imagicMSAcluster_classes_"+str(clusternumber)+".log"))
			loglines = logfile.readlines()
			for line in loglines:
				if re.search("ERROR in program", line):
					apDisplay.printError("ERROR IN IMAGIC SUBROUTINE, please check the logfile: imagicMSAcluster_classes_"\
						+str(clusternumber)+".log")
			apDisplay.printColor("finished IMAGIC in "+apDisplay.timeString(time.time()-clustertime0), "cyan")
			
			### normalize 
			classfile = "classums_"+str(clusternumber)+"_imagesignored_"+str(self.params['ignore_images'])+\
				"_membersignored_"+str(self.params['ignore_members'])+"\n")
			emancmd = "proc2d "+classfile+" "+classfile+".norm.hed norm"
			while os.path.isfile(classfile+".norm.img"):
				apStack.removeStack(alignstack+".norm.img")
			apEMAN.executeEmanCmd(emancmd)
			os.rename(classfile+".norm.hed", classfile)
			os.rename(classfile+".norm.img", classfile[:-4]+".img")

			### insert cluster stack into database
                        if self.params['commit'] is True:
                                self.insertClusterStack(clusternumber, insert=True)
                        else:
                                apDisplay.printWarning("not committing results to DB")

	
	
#=====================
#=====================
if __name__ == '__main__':
	imagicCluster = imagicClusterScript()
	imagicCluster.start()
	imagicCluster.close()

	
