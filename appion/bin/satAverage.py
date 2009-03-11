#!/usr/bin/env python

#python
import os
import math
import sys
import time
import re
import cPickle
import random
#eman
import EMAN
#scipy
import numpy
#appion
import appionScript
import appionData
import apDisplay
import apStack
import apRecon
import apEMAN
import apFile



#=====================
#=====================
class satAverageScript(appionScript.AppionScript):

	#=====================
	def makeEvenOddClasses(self, listfile, outputstack, classdata, maskrad):
		f=open(listfile,'r')
		f.readline()
		lines = f.readlines()
		f.close()
		randstr = str(int(random.random()*10e5))
		evenfile = self.rootname+"-even.lst"
		evenf = open(evenfile,'w')
		oddfile = self.rootname+"-odd.lst"
		oddf = open(oddfile,'w')
		evenf.write("#LST\n")
		oddf.write("#LST\n")
		neven=0
		nodd=0
		for i in range(0, len(lines)):
			if i%2:
				nodd+=1
				oddf.write(lines[i])
			else:
				neven+=1
				evenf.write(lines[i])
		evenf.close()
		oddf.close()

		if neven>0:
			self.makeClassAverages(evenfile, self.params['evenstack'], classdata, maskrad)
		if nodd>0:
			self.makeClassAverages(oddfile, self.params['oddstack'], classdata, maskrad)
		apFile.removeFile(evenfile)
		apFile.removeFile(oddfile)

	#=====================
	def getParticleInfo(self, reconid, iteration):
		"""
		Get all particle data for given recon and iteration
		"""
		t0 = time.time()
		cachefile = os.path.join(self.params['rundir'], 
			"refineparticledata-r"+str(reconid)+"-i"+str(iteration)+".cache")
		if os.path.isfile(cachefile):
			apDisplay.printColor("loading refineparticledata from cache file", "cyan")
			f = open(cachefile, 'r')
			refineparticledata = cPickle.load(f)
			f.close()
		else:
			refinerundata = appionData.ApRefinementRunData.direct_query(reconid)
			if not refinerundata:
				apDisplay.printError("Could not find refinerundata for reconrun id="+str(reconid))

			refineq = appionData.ApRefinementData()
			refineq['refinementRun'] = refinerundata
			refineq['iteration'] = iteration
			refinedata = refineq.query(results=1)
			
			if not refinedata:
				apDisplay.printError("Could not find refinedata for reconrun id="
					+str(reconid)+" iter="+str(iteration))

			refinepartq=appionData.ApParticleClassificationData()
			refinepartq['refinement']=refinedata[0]

			apDisplay.printMsg("querying particles on "+time.asctime())
			refineparticledata = refinepartq.query()
			apDisplay.printMsg("saving refineparticledata to cache file")
			f = open(cachefile, 'w')
			cPickle.dump(refineparticledata, f)
			f.close()

		apDisplay.printMsg("received "+str(len(refineparticledata))+" particles in "+apDisplay.timeString(time.time()-t0))
		return refineparticledata

	#=====================
	def procKeepList(self):
		"""
		Removes particles by reading a list of particle numbers generated externally.

		Requirements:
			the input file has one particle per line 
			the first piece of data is the particle number from the db
		"""
		keeplist = []
		f = open(self.params['keeplist'], 'r')
		lines = f.readlines()
		f.close()
		for n in lines:
			words = n.split()
			keeplist.append(int(words[0])+1)
		return keeplist

	#=====================
	def makeClassAverages(self, classlist, outputstack, classdata, maskrad):
		#align images in class
		#print classlist
		images = EMAN.readImages(classlist, -1, -1, 0)
		for image in images:
			image.rotateAndTranslate()
			if image.isFlipped():
				image.hFlip()

		#make class average
		avg = EMAN.EMData()
		avg.makeMedian(images)
		
		#write class average
		e = EMAN.Euler()
		alt = classdata['euler']['euler1']*math.pi/180
		az  = classdata['euler']['euler2']*math.pi/180
		phi = classdata['euler']['euler3']*math.pi/180
		e.setAngle(alt, az, phi)
		avg.setRAlign(e)
		avg.setNImg(len(images))
		avg.applyMask(maskrad, 0)

		avg.writeImage(outputstack,-1)

	#=====================
	def determineClasses(self, particles):
		"""Takes refineparticledata and returns a dictionary of classes"""
		apDisplay.printMsg("sorting refineparticledata into classes")
		t0 = time.time()
		classes={}
		class_stats={}
		quality=numpy.zeros(len(particles))
		for ptcl in range(0,len(particles)):
			quality[ptcl]=particles[ptcl]['quality_factor']
			key=particles[ptcl]['eulers'].dbid
			if key not in classes.keys():
				classes[key]={}
				classes[key]['particles']=[]
			classes[key]['euler']=particles[ptcl]['eulers']
			classes[key]['particles'].append(particles[ptcl])
		class_stats['meanquality']=quality.mean()
		class_stats['stdquality']=quality.std()
		class_stats['max']=quality.max()
		class_stats['min']=quality.min()
		### print stats
		print "-- quality factor stats --"
		print ("mean/std :: "+str(round(class_stats['meanquality'],2))+" +/- "
			+str(round(class_stats['stdquality'],2)))
		print ("min/max  :: "+str(round(class_stats['min'],2))+" <> "
			+str(round(class_stats['max'],2)))
		apDisplay.printMsg("finished sorting in "+apDisplay.timeString(time.time()-t0))
		return classes, class_stats

	#=====================
	def getClassData(self, reconid, iternum):
		t0 = time.time()
		cachefile = os.path.join(self.params['rundir'], 
			"partclassdata-r"+str(reconid)+"-i"+str(iternum)+".cache")
		if os.path.isfile(cachefile):
			apDisplay.printColor("loading particle class data from cache file", "cyan")
			f = open(cachefile, 'r')
			classes = cPickle.load(f)
			f.close()
		else:
			apDisplay.printMsg("determine particle class data from database")
			particles = self.getParticleInfo(reconid, iternum)
			classes, cstats = self.determineClasses(particles)
			f = open(cachefile, 'w')
			apDisplay.printMsg("saving particle class data to cache file")
			cPickle.dump(classes, f)
			f.close()
		apDisplay.printMsg("received "+str(len(classes))+" classes in "+apDisplay.timeString(time.time()-t0))
		return classes


	#######################################################
	#### ITEMS BELOW CAN BE SPECIFIED IN A NEW PROGRAM ####
	#######################################################

	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --reconid=<DEF_id> --iter=<iter> --mask=<radius>\n\t "
			+"[ --stackname=<name> "
			+" --avgjump=<avg> --sigma=<sigma> --eotest ]")
		self.parser.add_option("-r", "--reconid", dest="reconid", type="int",
			help="Reconstruction run id", metavar="INT")
		self.parser.add_option("-m", "--mask", dest="mask", type="int",
			help="Mask radius in pixels", metavar="INT")
		self.parser.add_option("-i", "--iter", dest="iter", type="int",
			help="Final eulers applied to particles will come from this iteration", metavar="INT")
		self.parser.add_option("--stackname", dest="stackname", default="goodavgs.hed",
			help="Name of the stack to write the averages", metavar="file.hed")
		self.parser.add_option("--keep-list", dest="keeplist",
			help="Keep particles in the specified text file, EMAN style 0,1,...", metavar="TEXT")
		self.parser.add_option("--eotest", dest="eotest", default=False,
			action="store_true", help="Perform even/odd test")

	#=====================
	def checkConflicts(self):
		if self.params['reconid'] is None:
			apDisplay.printError("enter a reconstruction ID from the database")
		if self.params['mask'] is None:
			apDisplay.printError("enter a mask radius")
		if self.params['iter'] is None:
			apDisplay.printError("enter an iteration for the final Eulers")
		if self.params['keeplist'] is None:
			apDisplay.printError("enter an keep list file")
		self.params['keeplist'] = os.path.abspath(self.params['keeplist'])
		if not os.path.isfile(self.params['keeplist']):
			apDisplay.printError("could not find list file")
		self.params['stackid'] = apStack.getStackIdFromRecon(self.params['reconid'])
		if self.params['stackname'][-4:] != ".hed":
			s = os.path.splitext(self.params['stackname'])[0]
			s += ".hed"
			self.params['stackname'] = s
		apDisplay.printMsg("Stack name: "+self.params['stackname'])

	#=====================
	def setRunDir(self):
		reconid = self.params['reconid']
		refinerundata = appionData.ApRefinementRunData.direct_query(reconid)
		if not refinerundata:
			apDisplay.printError("reconid "+str(reconid)+" does not exist in the database")
		self.params['rundir'] = os.path.join(refinerundata['path']['path'], 'satavg')

	#=====================
	def start(self):
		self.rootname = self.params['stackname'].split(".")[0]
		self.params['outputstack'] = os.path.join(self.params['rundir'], self.params['stackname'])
		
		if os.path.isfile(self.params['outputstack']):
			apFile.removeStack(self.params['outputstack'])
		if self.params['eotest'] is True:
			self.params['evenstack'] = os.path.splitext(self.params['outputstack'])[0]+'.even.hed'
			if os.path.isfile(self.params['evenstack']):
				apFile.removeStack(self.params['evenstack'])
			self.params['oddstack'] = os.path.splitext(self.params['outputstack'])[0]+'.odd.hed'
			if os.path.isfile(self.params['oddstack']):
				apFile.removeStack(self.params['oddstack'])

		classes = self.getClassData(self.params['reconid'], self.params['iter'])
		stackid = apStack.getStackIdFromRecon(self.params['reconid'])
		stackdata = apStack.getOnlyStackData(stackid)
		stackpath = os.path.join(stackdata['path']['path'], stackdata['name'])

		classkeys = classes.keys()
		classkeys.sort()

		classnum=0
		keeplist = self.procKeepList()
		finallist = []
		apDisplay.printMsg("Processing "+str(len(classes))+" classes")
		#loop through classes
		for key in classkeys:
			classnum+=1
			if classnum%10 == 1:
				sys.stderr.write("\b\b\b\b\b\b\b\b\b\b\b\b\b\b")
				sys.stderr.write(str(classnum)+" of "+(str(len(classkeys))))

			# loop through particles in class
			classfile = self.rootname+"-class.lst"
			classf = open(classfile, 'w')
			classf.write('#LST\n')
			nptcls=0
			for ptcl in classes[key]['particles']:
				# translate DB into EMAN
				partnum = ptcl['particle']['particleNumber'] - 1
				if partnum in keeplist:
					if ptcl['mirror']:
						mirror=1
					else:
						mirror=0
					rot = ptcl['euler3']*math.pi/180.0
					classf.write(
						"%d\t%s\t%f,\t%f,%f,%f,%d\n" % 
						(partnum, stackpath, ptcl['quality_factor'], 
						rot, ptcl['shiftx'], ptcl['shifty'], mirror))
					nptcls+=1
					finallist.append(partnum)
			classf.close()

			if nptcls<1:
				continue
			self.makeClassAverages(classfile, self.params['outputstack'], classes[key], self.params['mask'])
			if self.params['eotest'] is True:
				self.makeEvenOddClasses(classfile, self.params['outputstack'], classes[key], self.params['mask'])

			apFile.removeFile(classfile)

		sys.stderr.write("\n")
		finalfilename = self.rootname+"-keep.lst"
		finalf = open(finalfilename, 'w')
		finallist.sort()
		for partnum in finallist:
			finalf.write('%d\n' % (partnum,) )
		finalf.close()
		stackstr = str(stackdata.dbid)
		reconstr = str(self.params['reconid'])

		### recon 3d volumes
		threedname = os.path.join(self.params['rundir'], self.rootname+"."+str(self.params['iter'])+"a.mrc")
		emancmd = ( "make3d "+self.params['outputstack']+" out="
			+threedname+" hard=25 sym=d7 pad=240 mask="+str(self.params['mask'])+"; echo ''" )
		#print emancmd
		apEMAN.executeEmanCmd(emancmd, verbose=False, showcmd=True, logfile=self.rootname+"-eman.log")
		threednameb = os.path.join(self.params['rundir'], self.rootname+"."+str(self.params['iter'])+"b.mrc")
		emancmd = ( "proc3d "+threedname+" "+threednameb
			+" apix=1.63 norm=0,1 lp=6 origin=0,0,0 mask="+str(self.params['mask'])+"; echo '' " )
		apEMAN.executeEmanCmd(emancmd, verbose=False, showcmd=True, logfile=self.rootname+"-eman.log")
		if self.params['eotest'] is True:
			# even 
			evenname = os.path.join(self.params['rundir'], self.rootname+"-even."+str(self.params['iter'])+"a.mrc")
			if os.path.isfile(self.params['evenstack']):
				evenemancmd = ( "make3d "+self.params['evenstack']+" out="
					+evenname+" hard=25 sym=d7 pad=240 mask=70; echo ''" )
				#print evenemancmd
				apEMAN.executeEmanCmd(evenemancmd, verbose=False, showcmd=True, logfile=self.rootname+"-eveneman.log")
			else:
				apDisplay.printWarning("file "+self.params['evenstack']+" does not exist")

			# odd
			oddname = os.path.join(self.params['rundir'], self.rootname+"-odd."+str(self.params['iter'])+"a.mrc")
			if os.path.isfile(self.params['oddstack']):
				oddemancmd = ( "make3d "+self.params['oddstack']+" out="
					+oddname+" hard=25 sym=d7 pad=240 mask=70; echo ''" )
				#print oddemancmd
				apEMAN.executeEmanCmd(oddemancmd, verbose=False, showcmd=True, logfile=self.rootname+"-oddeman.log")
			else:
				apDisplay.printWarning("file "+self.params['oddstack']+" does not exist")

			#eotest
			fscout = os.path.join(self.params['rundir'], self.rootname+"-fsc.eotest")
			if os.path.isfile(oddname) and os.path.isfile(evenname):
				eotestcmd = "proc3d "+oddname+" "+evenname+" fsc="+fscout
				apEMAN.executeEmanCmd(eotestcmd, verbose=True, showcmd=True)
			else:
				apDisplay.printWarning("could not perform eotest")

			if os.path.isfile(fscout):
				res = apRecon.getResolutionFromFSCFile(fscout, 160.0, 1.63)
				apDisplay.printColor( ("resolution: %.5f" % (res)), "cyan")
				resfile = self.rootname+"-res.txt"
				f = open(resfile, 'a')
				f.write("[ %s ]\nresolution: %.5f\n" % (time.asctime(), res))
				f.close()

#=====================
#=====================
if __name__ == '__main__':
	satavg = satAverageScript()
	satavg.start()
	satavg.close()

