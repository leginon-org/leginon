#!/usr/bin/python -O

import EMAN
import appionData
import apDB
import os
import math
import numpy
from scipy import ndimage
import sys
import apParam
import apDisplay
import apEulerCalc
from optparse import OptionParser

apdb=apDB.apdb

def parseCommandLine():
	usage = ("Usage: %prog --reconid=<DEF_id> --stackname=<name> --outdir=<path> --mask=<radius> "
		 +"--iter=<iter> --avgjump=<avg> --sigma=<sigma> <--eotest>")
	parser = OptionParser(usage=usage)

	parser.add_option("-r", "--reconid", dest="reconid", type="int",
			  help="primary key of reconstruction from db", metavar="INT")
	parser.add_option("-m", "--mask", dest="mask", type="int",
			  help="mask radius in pixels", metavar="INT")
	parser.add_option("-i", "--iter", dest="iter", type="int",
			  help="Final eulers applied to particles will come from this iteration", metavar="INT")
	parser.add_option("-s", "--sigma", dest="sigma", type="float",
			  help="num of std devs greater than the mean quality factor to include", metavar="FLOAT")
	parser.add_option("-j", "--avgjump", dest="avgjump", type="float",
			  help="throw away ptcls with median euler jumps greater than this", metavar="FLOAT")
	parser.add_option("--rejectlst", dest="rejectlst",
			  help="throw away ptcls in the specified text file. One particle per line with particle # from db", metavar="TEXT")
	parser.add_option("-n", "--stackname", dest="stackname", default="goodavgs.hed",
			  help="name of the stack to which the averages will be written", metavar="TEXT")
	parser.add_option("-o", "--outdir", dest="outdir",
			  help="Location of new class files", metavar="PATH")
	parser.add_option("--eotest", dest="eotest", default=False,
			  action="store_true", help="make even and odd averages")

	params = apParam.convertParserToParams(parser)
	return params
			  
def checkConflicts(params):
	if params['reconid'] is None:
		apDisplay.printError("enter a reconstruction ID from the database")
	if params['mask'] is None:
		apDisplay.printError("enter a mask radius")
	if params['iter'] is None:
		apDisplay.printError("enter an iteration for the final Eulers")

def getReconPath(reconid):
	"""Get the path of a given reconstruction"""
	refinerundata=apdb.direct_query(appionData.ApRefinementRunData, reconid)
	if not refinerundata:
		apDisplay.printError("reconid "+str(reconid)+" does not exist in the database")
	return refinerundata['path']['path']
	
def getParticleInfo(reconid,iteration):
	"""Get all particle data for given recon and iteration"""
	refinerundata=apdb.direct_query(appionData.ApRefinementRunData, reconid)
	
	refineq=appionData.ApRefinementData()
	refineq['refinementRun']=refinerundata
	refineq['iteration']=iteration
	refinedata=apdb.query(refineq,results=1)
	
	refineparticleq=appionData.ApParticleClassificationData()
	refineparticleq['refinement']=refinedata[0]
	print "Getting particles"
	refineparticledata=apdb.query(refineparticleq)
	return (refineparticledata)

def determineClasses(particles):
	"""Takes refineparticledata and returns a dictionary of classes"""
	print "Determining classes"
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
	print "Quality factor stats:"
	print "mean =", class_stats['meanquality']
	print "std =",class_stats['stdquality']
	print "max =",class_stats['max']
	print "min =",class_stats['min']
	return classes,class_stats

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
	e=EMAN.Euler()
	alt=classdata['euler']['euler1']*math.pi/180
	az=classdata['euler']['euler2']*math.pi/180
	phi=classdata['euler']['euler3']*math.pi/180
	e.setAngle(alt,az,phi)
	avg.setRAlign(e)
	avg.setNImg(len(images))
	avg.applyMask(params['mask'],0)
	avg.writeImage(outputstack,-1)
	
def makeEvenOddClasses(lst,classdata,params):
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
	evenstack=os.path.splitext(params['outputstack'])[0]+'.even.hed'
	oddstack=os.path.splitext(params['outputstack'])[0]+'.odd.hed'
	
	if neven>0:
		makeClassAverages('even.lst',evenstack,classdata,params)
	if nodd>0:
		makeClassAverages('odd.lst',oddstack,classdata,params)
	os.remove('even.lst')
	os.remove('odd.lst')

def getEMANPcmp(ref,img):
	"""returns EMAN quality factor for pcmp properly scaled"""
	dot=ref.pcmp(img)
	return((2.0-dot)*500.0)

def getCC(ref,img):
	"""returns straight up correlation coefficient"""
 	npix=ref.xSize()*ref.ySize()
	avg1=ref.Mean()
	avg2=img.Mean()
	
	var1=ref.Sigma()
	var1=var1*var1
	var2=img.Sigma()
	var2=var2*var2
	
	cc=ref.dot(img)
	cc=cc/npix
	cc=cc-(avg1*avg2)
	cc=cc/math.sqrt(var1*var2)
	return(cc)

def henryMult(m1,m2):
	c=numpy.zeros((m1.shape[0],m2.shape[1]))
	for i in range(0,c.shape[0]):
		for j in range(0,c.shape[1]):
			tot=0
			for k in range(0,m1.shape[1]):
				tot+=m1[i,k]*m2[k,j]
			c[i,j]=tot
	return c

def getEulersForParticle(particlenum,reconid):
	"""returns all classdata for a particular particle and refinement"""
	refinerundata=apdb.direct_query(appionData.ApRefinementRunData, reconid)

	stack=refinerundata['stack']
	stackparticlesq=appionData.ApStackParticlesData()
	stackparticlesq['stack']=stack
	stackparticlesq['particleNumber']=particlenum
	stackparticlesdata=apdb.query(stackparticlesq)
	
	refinementq=appionData.ApRefinementData()
	refinementq['refinementRun']=refinerundata

	particledata=stackparticlesdata[0]
	ptclclassq=appionData.ApParticleClassificationData()
	ptclclassq['particle']=particledata
	ptclclassq['refinement']=refinementq
	ptclclassdata = apdb.query(ptclclassq)
	
	#for cls in ptclclassdata:
		#print cls['refinement']['iteration'], cls['eulers']
	return ptclclassdata

def sortEulersByIteration(a, b):
	if a['refinement']['iteration'] > b['refinement']['iteration']:
		return 1
	else:
		return -1

def removePtclsByQualityFactor(particles,rejectlst,cutoff,params):
	stack=os.path.join(particles[0]['particle']['stack']['path']['path'],particles[0]['particle']['stack']['name'])
	
	for ptcl in particles:
		if ptcl['quality_factor'] < cutoff:
			rejectlst.append(ptcl['particle']['particleNumber'])
	return rejectlst

def removePtclsByJumps(particles,rejectlst,params):
	nptcls=len(particles)
	apDisplay.printMsg("Finding Euler jumps for "+str(nptcls)+" particles")
	stackdata = particles[0]['particle']['stack']
	stack = os.path.join(stackdata['path']['path'], stackdata['name'])
	f=open('jumps.txt','w')
	for ptcl in range(1,nptcls+1):
		f.write('%d\t' % ptcl)
		eulers=getEulersForParticle(ptcl, params['reconid'])
		eulers.sort(sortEulersByIteration)
		distances = numpy.zeros((len(eulers)-1), dtype=numpy.float32)
		for i range(len(eulers)-1):
			#calculate distance (in degrees) for D7 symmetry
			dist = eulerCalculateDistanceSym(eulers[i]['eulers'], eulers[i+1]['eulers'], sym='d7')
			distances[i] = dist
			f.write('%3.5f\t' % dist*math.pi/180.0)
		median = numpy.median(distances)
		if median > params['avgjump']:
			rejectlst.append(ptcl)
		f.write('%f\t%f\t%f\n' % (distances.mean(), median, distances.std()))
		if ptcl%100 == 0:
			print "particle=",ptcl,"; median jump=",median
		#print distances
		#print distances.mean()
	return rejectlst

def removePtclsByLst(rejectlst,params):
	"""Removes particles by reading a list of particle numbers generated externally. 
	The only requirements are that the input file has one particle per line and the first piece of data is the particle number from the db"""
	f=open(params['rejectlst'],'r')
	lines=f.readlines()
	f.close()
	for n in lines:
		words=n.split()
		rejectlst.append(int(words[0]))
	return rejectlst

if __name__=='__main__':
	params=parseCommandLine()
	checkConflicts(params)
	
	if params['outdir'] is None:
		# auto set the output directory
		params['outdir'] = getReconPath(params['reconid'])+'/eulers'
		
	#create the output directory, if needed
	apDisplay.printMsg("Out directory: "+params['outdir'])
	apParam.createDirectory(params['outdir'])			

	os.chdir(params['outdir'])
	apParam.writeFunctionLog(sys.argv)
	
	params['outputstack']=os.path.join(params['outdir'],params['stackname'])
	particles=getParticleInfo(params['reconid'],params['iter'])
	stack=os.path.join(particles[0]['particle']['stack']['path']['path'],particles[0]['particle']['stack']['name'])
	classes,cstats=determineClasses(particles)
	
	rejectlst=[]
	if params['sigma'] is not None:
		cutoff=cstats['meanquality']+params['sigma']*cstats['stdquality']
		print "Cutoff =",cutoff
		rejectlst=removePtclsByQualityFactor(particles,rejectlst,cutoff,params)
	if params['avgjump'] is not None:
		rejectlst=removePtclsByJumps(particles,rejectlst,params)
	if params['rejectlst']:
		rejectlst=removePtclsByLst(rejectlst,params)

	classkeys=classes.keys()
	classkeys.sort()
	classnum=0
	totalptcls=0
	
	reject=open('reject.lst','w')
	reject.write('#LST\n')
	print "Processing class"
	#loop through classes
	for key in classkeys:
		classnum+=1
		print classnum
		images=EMAN.EMData()

		#loop through particles in class
		f=open('tmp.lst','w')
		f.write('#LST\n')
		nptcls=0
		for ptcl in classes[key]['particles']:
			if ptcl['mirror']:
				mirror=1
			else:
				mirror=0
			rot=ptcl['inplane_rotation']
			rot=rot*math.pi/180
			if ptcl['particle']['particleNumber'] not in rejectlst:
				f.write('%d\t%s\t%f,\t%f,%f,%f,%d\n' % (ptcl['particle']['particleNumber']-1,stack,ptcl['quality_factor'],rot,ptcl['shiftx'],ptcl['shifty'],mirror))
				totalptcls+=1
				nptcls+=1
			else:
				reject.write('%d\t%s\t%f,\t%f,%f,%f,%d\n' % (ptcl['particle']['particleNumber']-1,stack,ptcl['quality_factor'],rot,ptcl['shiftx'],ptcl['shifty'],mirror))
			#if ptcl['quality_factor']>cstats['meanquality']+3*cstats['stdquality']:
			#	high.write('%d\t%s\t%f,\t%f,%f,%f,%d\n' % (ptcl['particle']['particleNumber']-1,stack,ptcl['quality_factor'],rot,ptcl['shiftx'],ptcl['shifty'],mirror))
		f.close()
		
		if nptcls<1:
			continue
		
		makeClassAverages('tmp.lst',params['outputstack'], classes[key], params)
		
		if params['eotest']:
			makeEvenOddClasses('tmp.lst',classes[key],params)
		os.remove('tmp.lst')
	reject.close()
	
	print
	print "Total particles included =",totalptcls
	print "Done!"
