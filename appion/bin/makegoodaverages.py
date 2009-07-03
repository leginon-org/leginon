#!/usr/bin/env python

#python
import os
import math
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
import appionData
import apDisplay
import apStack
import apEulerCalc
import apEulerJump
import apEMAN

def getParticleInfo(reconid, iteration):
	"""
	Get all particle data for given recon and iteration
	"""
	refinerundata = appionData.ApRefinementRunData.direct_query(reconid)
	if not refinerundata:
		apDisplay.printError("Could not find refinerundata for reconrun id="+str(reconid))

	refineq = appionData.ApRefinementData()
	refineq['refinementRun']=refinerundata
	refineq['iteration']=iteration
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

def determineClasses(particles):
	"""Takes refineparticledata and returns a dictionary of classes"""
	apDisplay.printMsg("sorting refineparticledata into classes")
	t0 = time.time()
	classes={}
	class_stats={}
	quality=numpy.zeros(len(particles))
	# group the particles by euler angle
	for ptcl in range(0,len(particles)):
		quality[ptcl]=particles[ptcl]['quality_factor']
		key=str(particles[ptcl]['euler1'])+','+str(particles[ptcl]['euler2'])
		if key not in classes.keys():
			classes[key]={}
			classes[key]['particles']=[]
		classes[key]['euler1']=particles[ptcl]['euler1']
		classes[key]['euler2']=particles[ptcl]['euler2']
		classes[key]['euler3']=particles[ptcl]['euler3']
		classes[key]['particles'].append(particles[ptcl])
	class_stats['meanquality']=quality.mean()
	class_stats['stdquality']=quality.std()
	class_stats['max']=quality.max()
	class_stats['min']=quality.min()
	### print stats
	apDisplay.printMsg("-- quality factor stats --")
	apDisplay.printMsg("mean/std :: "+str(round(class_stats['meanquality'],2))+" +/- "
		+str(round(class_stats['stdquality'],2)))
	apDisplay.printMsg("min/max  :: "+str(round(class_stats['min'],2))+" <> "
		+str(round(class_stats['max'],2)))
	apDisplay.printMsg("finished sorting in "+apDisplay.timeString(time.time()-t0))
	return classes, class_stats

def makeClassAverages(lst, outputstack, classdata, params):
	#align images in class
	images=EMAN.readImages(lst,-1,-1,0)
	for image in images:
		image.rotateAndTranslate()
		if image.isFlipped():
			image.hFlip()

	#make class average
	avg=EMAN.EMData()
	avg.makeMedian(images)
	
	#write class average
	e = EMAN.Euler()
	alt = classdata['euler1']*math.pi/180
	az = classdata['euler2']*math.pi/180
	phi = 0.0
	e.setAngle(alt,az,phi)
	avg.setRAlign(e)
	avg.setNImg(len(images))
	avg.applyMask(params['mask'],0)
	avg.writeImage(outputstack,-1)
	

def removePtclsByLst(rejectlst, params):
	"""
	Removes particles by reading a list of particle numbers generated externally.

	Requirements:
		the input file has one particle per line 
		the first piece of data is the particle number from the db
	"""
	f=open(params['rejectlst'],'r')
	lines=f.readlines()
	f.close()
	for n in lines:
		words = n.split()
		rejectlst.append(int(words[0]))
	return rejectlst


#=====================
#=====================
class makeGoodAveragesScript(appionScript.AppionScript):

	#=====================
	def makeEvenOddClasses(self,lst,classdata):
		f=open(lst,'r')
		f.readline()
		lines=f.readlines()
		f.close()
		even=open('even.lst','w')
		odd=open('odd.lst','w')
		even.write("#LST\n")
		odd.write("#LST\n")
		neven=0
		nodd=0
		for line in range(0,len(lines)):
			if line%2:
				nodd+=1
				odd.write(lines[line])
			else:
				neven+=1
				even.write(lines[line])
		even.close()
		odd.close()
		self.params['evenstack']=os.path.splitext(self.params['outputstack'])[0]+'.even.hed'
		self.params['oddstack']=os.path.splitext(self.params['outputstack'])[0]+'.odd.hed'
		
		if neven>0:
			makeClassAverages('even.lst',self.params['evenstack'],classdata,self.params)
		if nodd>0:
			makeClassAverages('odd.lst',self.params['oddstack'],classdata,self.params)
		os.remove('even.lst')
		os.remove('odd.lst')

	#=====================
	def removePtclsByJumps(self, particles, rejectlst):
		eulerjump = apEulerJump.ApEulerJump()
		numparts = len(particles)
		apDisplay.printMsg("finding euler jumps for "+str(numparts)+" particles")

		### check symmetry
		symmetry = eulerjump.getSymmetry(self.params['reconid'], msg=True)
		if not re.match("^[cd][0-9]+$", symmetry.lower()) and not re.match("^icos", symmetry.lower()):
			apDisplay.printError("Cannot calculate euler jumps for symmetry: "+symmetry)
			return
		self.params['sym']=symmetry.lower()

		### prepare file
		f = open('jumps.txt','w', 0666)
		f.write("#pnum\t")
		headerlist = ('mean', 'median', 'stdev', 'min', 'max')
		for key in headerlist:
			f.write(key+"\t")
		f.write("\n")

		### get stack particles
		stackid = apStack.getStackIdFromRecon(self.params['reconid'], msg=True)
		stackparts = apStack.getStackParticlesFromId(stackid)

		### start loop
		t0 = time.time()
		medians = []
		count = 0
		apDisplay.printMsg("processing euler jumps for recon run="+str(self.params['reconid']))
		for stackpart in stackparts:
			count += 1
			partnum = stackpart['particleNumber']
			f.write('%d\t' % partnum)
			jumpdata = eulerjump.getEulerJumpData(self.params['reconid'], stackpartid=stackpart.dbid, stackid=stackid, sym=symmetry)
			medians.append(jumpdata['median'])
			if (jumpdata['median'] > self.params['avgjump']) and partnum not in rejectlst:
				rejectlst.append(partnum)
			for key in headerlist:
				f.write("%.3f\t" % (jumpdata[key]))
			f.write("\n")
			if count % 1000 == 0:
				timeremain = (time.time()-t0)/(count+1)*(numparts-count)
				apDisplay.printMsg("particle=% 5d; median jump=% 3.2f, remain time= %s" % (partnum, jumpdata['median'],
					apDisplay.timeString(timeremain)))
				#f.flush()
		### print stats
		apDisplay.printMsg("-- median euler jumper stats --")
		medians = numpy.asarray(medians, dtype=numpy.float32)
		apDisplay.printMsg("mean/std :: "+str(round(medians.mean(),2))+" +/- "
			+str(round(medians.std(),2)))
		apDisplay.printMsg("min/max  :: "+str(round(medians.min(),2))+" <> "
			+str(round(medians.max(),2)))

		perrej = round(100.0*float(numparts-len(rejectlst))/float(numparts),2)
		apDisplay.printMsg("keeping "+str(numparts-len(rejectlst))+" of "+str(numparts)
			+" particles ("+str(perrej)+"%) so far "
			+" in "+apDisplay.timeString(time.time()-t0))

		return rejectlst

	#=====================
	def removePtclsByQualityFactor(self, particles, rejectlst, cutoff):
		t0 = time.time()
		for ptcl in particles:
			if ptcl['quality_factor'] < cutoff:
				rejectlst.append(ptcl['particle']['particleNumber'])
		numparts = len(particles)
		perrej = round(100.0*float(numparts-len(rejectlst))/float(numparts),2)
		apDisplay.printMsg("keeping "+str(numparts-len(rejectlst))+" of "+str(numparts)
			+" particles ("+str(perrej)+"%) so far "
			+" in "+apDisplay.timeString(time.time()-t0))
		return rejectlst

	#######################################################
	#### ITEMS BELOW CAN BE SPECIFIED IN A NEW PROGRAM ####
	#######################################################

	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --reconid=<DEF_id> --iter=<iter> --mask=<radius>\n\t "
			+"[ --stackname=<name> "
			+" --avgjump=<avg> --sigma=<sigma> --eotest ]")
		self.parser.add_option("-r", "--reconid", dest="reconid", type="int",
			help="reconstruction run id", metavar="#")
		self.parser.add_option("-m", "--mask", dest="mask", type="int",
			help="Mask radius in pixels", metavar="INT")
		self.parser.add_option("-i", "--iter", dest="iter", type="int",
			help="Final eulers applied to particles will come from this iteration", metavar="#")
		self.parser.add_option("-s", "--sigma", dest="sigma", type="float",
			help="Number of std devs greater than the mean quality factor to include", metavar="FLOAT")
		self.parser.add_option("-j", "--avgjump", dest="avgjump", type="float",
			help="Throw away ptcls with median euler jumps greater than this", metavar="FLOAT")
		self.parser.add_option("--rejectlst", dest="rejectlst",
			help="Throw away ptcls in the specified text file. DB style 1,2,...", metavar="LIST")
		self.parser.add_option("--stackname", dest="stackname", default="goodavgs.hed",
			help="Name of the stack to write the averages", metavar="NAME")
		self.parser.add_option("--eotest", dest="eotest", default=False,
			action="store_true", help="make even and odd averages")
		self.parser.add_option("--skip-avg", dest="skipavg", default=False,
			action="store_true", help="skip class averaging step")
		self.parser.add_option("--hard", dest="hard", type="int",
			help="specifies how well the class averages must match the model to be included")
		self.parser.add_option("--mode", dest="mode", type="int", default=2,
			help="specifies the interpolation size")
		self.parser.add_option("--make3d", dest="make3d", metavar="NAME",
			help="name of output density file")
	
	#=====================
	def checkConflicts(self):
		if self.params['reconid'] is None:
			apDisplay.printError("enter a reconstruction ID from the database")
		if self.params['mask'] is None:
			apDisplay.printError("enter a mask radius")
		if self.params['iter'] is None:
			apDisplay.printError("enter an iteration for the final Eulers")
		self.params['stackid'] = apStack.getStackIdFromRecon(self.params['reconid'])

	#=====================
	def setRunDir(self):
		reconid = self.params['reconid']
		refinerundata=appionData.ApRefinementRunData.direct_query(reconid)
		if not refinerundata:
			apDisplay.printError("reconid "+str(reconid)+" does not exist in the database")
		self.params['rundir'] = os.path.join(refinerundata['path']['path'], 'eulers',self.params['runname'])

	#=====================
	def start(self):
		self.params['outputstack'] = os.path.join(self.params['rundir'], self.params['stackname'])
		particles = getParticleInfo(self.params['reconid'], self.params['iter'])
		stackdata = particles[0]['particle']['stack']
		stack = os.path.join(stackdata['path']['path'], stackdata['name'])
		classes,cstats = determineClasses(particles)
		
		rejectlst=[]
		if self.params['sigma'] is not None:
			cutoff=cstats['meanquality']+self.params['sigma']*cstats['stdquality']
			apDisplay.printMsg("Cutoff = "+str(cutoff))
			rejectlst = self.removePtclsByQualityFactor(particles, rejectlst, cutoff)
		if self.params['avgjump'] is not None:
			rejectlst = self.removePtclsByJumps(particles, rejectlst)
		if self.params['rejectlst']:
			rejectlst = removePtclsByLst(rejectlst, self.params)

		classkeys=classes.keys()
		classkeys.sort()
		classnum=0
		totalptcls=0

		keepfile=open('keep.lst','w')
		keepfile.write('#LST\n')
		reject=open('reject.lst','w')
		reject.write('#LST\n')
		apDisplay.printMsg("Processing classes")
		#loop through classes
		for key in classkeys:

			# file to hold particles of this class
			clsfile=open('clstmp.lst','w')
			clsfile.write('#LST\n')

			classnum+=1
			if classnum%10 == 1:
				apDisplay.printMsg(str(classnum)+" of "+(str(len(classkeys))))
			images=EMAN.EMData()

			#loop through particles in class
			nptcls=0
			for ptcl in classes[key]['particles']:
				if ptcl['mirror']:
					mirror=1
				else:
					mirror=0
				rot=ptcl['euler3']
				rot=rot*math.pi/180
				if ptcl['particle']['particleNumber'] not in rejectlst:
					l = '%d\t%s\t%f,\t%f,%f,%f,%d\n' % (ptcl['particle']['particleNumber']-1,
						stack,ptcl['quality_factor'],rot,ptcl['shiftx'],ptcl['shifty'],mirror)
					keepfile.write(l)
					clsfile.write(l)
					totalptcls+=1
					nptcls+=1
				else:
					reject.write('%d\t%s\t%f,\t%f,%f,%f,%d\n' % (ptcl['particle']['particleNumber']-1,
						stack,ptcl['quality_factor'],rot,ptcl['shiftx'],ptcl['shifty'],mirror))
				#if ptcl['quality_factor']>cstats['meanquality']+3*cstats['stdquality']:
				#	high.write('%d\t%s\t%f,\t%f,%f,%f,%d\n' % (ptcl['particle']['particleNumber']-1,
				#		stack,ptcl['quality_factor'],rot,ptcl['shiftx'],ptcl['shifty'],mirror))
					
			clsfile.close()	

			if nptcls<1:
				continue
			if self.params['skipavg'] is False:
				makeClassAverages('clstmp.lst', self.params['outputstack'], classes[key], self.params)
			
			if self.params['eotest'] is True:
				self.makeEvenOddClasses('clstmp.lst',classes[key])

		apDisplay.printMsg("\n")
		reject.close()
		keepfile.close()
		os.remove('clstmp.lst')

		# make 3d density file if specified:
		if self.params['make3d'] is not None:
			apEMAN.make3d(self.params['stackname'], self.params['make3d'], sym=self.params['sym'], mode=self.params['mode'], hard=self.params['hard'])
			if self.params['eotest'] is True:
				apEMAN.make3d(self.params['oddstack'],"odd.mrc", sym=self.params['sym'],mode=self.params['mode'],hard=self.params['hard'])
				apEMAN.make3d(self.params['evenstack'],"even.mrc", sym=self.params['sym'],mode=self.params['mode'],hard=self.params['hard'])
				apEMAN.executeEmanCmd("proc3d odd.mrc even.mrc fsc=fsc.eotest")

		stackstr = str(stackdata.dbid)
		reconstr = str(self.params['reconid'])
		apDisplay.printColor("Make a new stack with only non-jumpers:\n"
			+"subStack.py --projectid="+str(self.params['projectid'])+" -s "+stackstr+" \\\n "
			+" -k "+os.path.join(self.params['rundir'],"keep.lst")+" \\\n "
			+" -d 'recon "+reconstr+" sitters' -n sitters"+reconstr+" -C ", "purple")

#=====================
#=====================
if __name__ == '__main__':
	makegood = makeGoodAveragesScript()
	makegood.start()
	makegood.close()
