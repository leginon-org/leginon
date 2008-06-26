#!/usr/bin/python -O

#python
import os
import math
import sys
import time
import re
import cPickle
#scipy
import numpy
#eman
import EMAN
#db
import sinedon
import MySQLdb
#appion
import appionScript
import apDB
import appionData
import apDisplay
import apStack
import apEMAN
import apFile
apdb=apDB.apdb



#=====================
#=====================
class satAverageScript(appionScript.AppionScript):

	#=====================
	def makeEvenOddClasses(self, listfile, outputstack, classdata, maskrad):
		f=open(listfile,'r')
		f.readline()
		lines = f.readlines()
		f.close()
		evenf=open('even.lst','w')
		oddf=open('odd.lst','w')
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
		self.params['evenstack'] = os.path.splitext(outputstack)[0]+'.even.hed'
		self.params['oddstack'] = os.path.splitext(outputstack)[0]+'.odd.hed'

		if neven>0:
			self.makeClassAverages('even.lst', self.params['evenstack'], classdata, maskrad)
		if nodd>0:
			self.makeClassAverages('odd.lst', self.params['oddstack'], classdata, maskrad)
		apFile.removeFile('even.lst')
		apFile.removeFile('odd.lst')

	#=====================
	def getParticleInfo(self, reconid, iteration):
		"""
		Get all particle data for given recon and iteration
		"""
		refinerundata = apdb.direct_query(appionData.ApRefinementRunData, reconid)
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
		t0 = time.time()
		apDisplay.printMsg("querying particles on "+time.asctime())
		refineparticledata = refinepartq.query()
		apDisplay.printMsg("received "+str(len(refineparticledata))+" particles in "+apDisplay.timeString(time.time()-t0))
		return (refineparticledata)

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
		az = classdata['euler']['euler2']*math.pi/180
		phi = classdata['euler']['euler3']*math.pi/180
		e.setAngle(alt,az,phi)
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
		self.parser.add_option("-n", "--stackname", dest="stackname", default="goodavgs.hed",
			help="Name of the stack to write the averages", metavar="TEXT")
		self.parser.add_option("--keep-list", dest="keeplist",
			help="Keep particles in the specified text file, EMAN style 0,1,...", metavar="TEXT")
		self.parser.add_option("-o", "--outdir", dest="outdir",
			help="Location of new class files", metavar="PATH")
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

	#=====================
	def setOutDir(self):
		reconid = self.params['reconid']
		refinerundata=apdb.direct_query(appionData.ApRefinementRunData, reconid)
		if not refinerundata:
			apDisplay.printError("reconid "+str(reconid)+" does not exist in the database")
		self.params['outdir'] = os.path.join(refinerundata['path']['path'], 'satavg')

	#=====================
	def start(self):
		rootname = self.params['stackname'].split(".")[0]
		self.params['outputstack'] = os.path.join(self.params['outdir'], self.params['stackname'])
		particles = self.getParticleInfo(self.params['reconid'], self.params['iter'])
		stackdata = particles[0]['particle']['stack']
		stack = os.path.join(stackdata['path']['path'], stackdata['name'])
		classes, cstats = self.determineClasses(particles)

		classkeys=classes.keys()
		classkeys.sort()
		classnum=0
		totalptcls=0
		
		keeplist = self.procKeepList()
		finallist = []
		apDisplay.printMsg("Processing classes")
		#loop through classes
		for key in classkeys:
			classnum+=1
			if classnum%10 == 1:
				sys.stderr.write("\b\b\b\b\b\b\b\b\b\b\b\b\b\b")
				sys.stderr.write(str(classnum)+" of "+(str(len(classkeys))))
			images=EMAN.EMData()

			#loop through particles in class
			classlist=open('class.lst', 'w')
			classlist.write('#LST\n')
			nptcls=0
			for ptcl in classes[key]['particles']:
				if ptcl['mirror']:
					mirror=1
				else:
					mirror=0
				rot=ptcl['inplane_rotation']
				rot=rot*math.pi/180
				if ptcl['particle']['particleNumber'] in keeplist:
					classlist.write(
						"%d\t%s\t%f,\t%f,%f,%f,%d\n" % 
						(ptcl['particle']['particleNumber']-1, stack, ptcl['quality_factor'], 
						rot, ptcl['shiftx'], ptcl['shifty'], mirror))
					totalptcls+=1
					nptcls+=1
					finallist.append(ptcl['particle']['particleNumber']-1)
			classlist.close()

			
			if nptcls<1:
				continue
			self.makeClassAverages('class.lst', self.params['outputstack'], classes[key], self.params['mask'])
			if self.params['eotest'] is True:
				self.makeEvenOddClasses('class.lst', self.params['outputstack'], classes[key], self.params['mask'])

			apFile.removeFile('class.lst')

		sys.stderr.write("\n")
		finalfilename = rootname+"-keep.lst"
		finalf = open(finalfilename, 'w')
		finallist.sort()
		for partnum in finallist:
			finalf.write('%d\n' % (partnum,) )
		finalf.close()
		stackstr = str(stackdata.dbid)
		reconstr = str(self.params['reconid'])

		### recon 3d volumes
		threedname = os.path.join(self.params['outdir'], rootname+".a.mrc")
		emancmd = ( "make3d "+self.params['outputstack']+" out="
			+threedname+" hard=25 sym=d7 pad=240 mask=70; echo ''" )
		#print emancmd
		apEMAN.executeEmanCmd(emancmd, verbose=False, showcmd=True)
		if self.params['eotest'] is True:
			# even 
			evenname = os.path.join(self.params['outdir'], rootname+"-even.a.mrc")
			evenemancmd = ( "make3d "+self.params['evenstack']+" out="
				+evenname+" hard=25 sym=d7 pad=240 mask=70; echo ''" )
			#print evenemancmd
			apEMAN.executeEmanCmd(evenemancmd, verbose=False, showcmd=True)

			# odd
			oddname = os.path.join(self.params['outdir'], rootname+"-odd.a.mrc")
			oddemancmd = ( "make3d "+self.params['oddstack']+" out="
				+oddname+" hard=25 sym=d7 pad=240 mask=70; echo ''" )
			#print oddemancmd
			apEMAN.executeEmanCmd(oddemancmd, verbose=False, showcmd=True)

			#eotest
			fscout = os.path.join(self.params['outdir'], rootname+"-fsc.eotest")
			eotestcmd = "proc3d "+oddname+" "+evenname+" fsc="+fscout
			apEMAN.executeEmanCmd(oddemancmd, verbose=True, showcmd=True)

#=====================
#=====================
if __name__ == '__main__':
	satavg = satAverageScript()
	satavg.start()
	satavg.close()

