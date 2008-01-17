#!/usr/bin/python -O

import EMAN
import appionData
import apDB
import os
import math
import numpy
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

def getMatrix(eulerdata):
	a=eulerdata['euler3']*math.pi/180
	b=eulerdata['euler1']*math.pi/180
	c=eulerdata['euler2']*math.pi/180
	m=numpy.zeros((3,3))
	m[0,0]=math.cos(c)*math.cos(a)-math.cos(b)*math.sin(a)*math.sin(c)
	m[0,1]=math.cos(c)*math.sin(a)+math.cos(b)*math.cos(a)*math.sin(c)
	m[0,2]=math.sin(c)*math.sin(b)
	m[1,0]=-math.sin(c)*math.cos(a)-math.cos(b)*math.sin(a)*math.cos(c)
	m[1,1]=-math.sin(c)*math.sin(a)+math.cos(b)*math.cos(a)*math.cos(c)
	m[1,2]=math.cos(c)*math.sin(b)
	m[2,0]=math.sin(b)*math.sin(a)
	m[2,1]=-math.sin(b)*math.cos(a)
	m[2,2]=math.cos(b)
	return m

def getMatrix2(eulerdata):
	alpha=eulerdata['euler1']*math.pi/180
	beta=eulerdata['euler2']*math.pi/180
	gamma=eulerdata['euler3']*math.pi/180

	alpham=numpy.zeros((3,3))
	betam=numpy.zeros((3,3))
	gammam=numpy.zeros((3,3))
	
	gammam[0,0]=math.cos(gamma)
	gammam[0,1]=math.sin(gamma)
	gammam[1,0]=-math.sin(gamma)
	gammam[1,1]=math.cos(gamma)
	gammam[2,2]=1.0
	
	betam[0,0]=1.0
	betam[1,1]=math.cos(beta)
	betam[1,2]=math.sin(beta)
	betam[2,1]=-math.sin(beta)
	betam[2,2]=math.cos(beta)
	
	alpham[0,0]=math.cos(alpha)
	alpham[0,1]=math.sin(alpha)
	alpham[1,0]=-math.sin(alpha)
	alpham[1,1]=math.cos(alpha)
	alpham[2,2]=1.0
	
	m=numpy.dot(gammam,betam)
	m=numpy.dot(m,alpham)
	m2=numpy.dot(alpham,betam)
	m2=numpy.dot(m2,gammam)
	
	return(m)

def calculateDistance(m1,m2):
	r=numpy.dot(m1.transpose(),m2)
	#print r
	trace=r.trace()
	s=(trace-1)/2.0
	if int(round(abs(s),7)) == 1:
		#print "here"
		return 0
	else:
		#print "calculating"
		theta=math.acos(s)
		#print 'theta',theta
		t1=abs(theta/(2*math.sin(theta)))
		#print 't1',t1 
		t2 = math.sqrt(pow(r[0,1]-r[1,0],2)+pow(r[0,2]-r[2,0],2)+pow(r[1,2]-r[2,1],2))
		#print 't2',t2, t2*180/math.pi
		d = t1 * t2
		#print 'd',d
		return d

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
	ptclclassdata=apdb.query(ptclclassq)
	
	#for cls in ptclclassdata:
		#print cls['refinement']['iteration'], cls['eulers']
	return ptclclassdata

def sortEulers(a, b):
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
	#errdict={}
	print "Finding Euler jumps"
	nptcls=len(particles)
	stack=os.path.join(particles[0]['particle']['stack']['path']['path'],particles[0]['particle']['stack']['name'])
	f=open('jumps.txt','w')
	for ptcl in range(1,nptcls+1):
		eulers=getEulersForParticle(ptcl,params['reconid'])
		eulers.sort(sortEulers)
		e0=eulers[0]['eulers']
		distances=numpy.zeros((len(eulers)-1))
		f.write('%d\t' % ptcl)
		for n in range(1,len(eulers)):
			# first get all equivalent Eulers given symmetry
			eqEulers=apEulerCalc.calculateEquivD7Sym(eulers[n]['eulers'])
			# calculate the distances between the original Euler and all the equivalents
			mat0=apEulerCalc.getMatrix3(e0)
			mat1=apEulerCalc.getMatrix3(eulers[n]['eulers'])

			d=[]
			for e1 in eqEulers:
				d.append(apEulerCalc.calculateDistance(mat0,mat1))
			mind=min(d)
			distances[n-1]=mind*180/math.pi
			f.write('%f\t' % distances[n-1])
			e0=eulers[n]['eulers']
		if numpy.median(distances) > params['avgjump']:
			rejectlst.append(ptcl)
		if not ptcl%100:
			print "particle",ptcl
		f.write('%f\t%f\t%f\n' % (distances.mean(),numpy.median(distances),distances.std()))
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
