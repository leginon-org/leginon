#!/usr/bin/env python

import EMAN
import appionData
import apDB
import os
import math
import numpy
import sys

apdb=apDB.apdb

def createDefaults():
	params={}
	params['nsig']=False
	params['avgerr']=False
	params['stackname']='goodavgs.hed'
	params['eotest'] = False
	return params

def parseParams(args,params):
	for arg in args:
		elements=arg.split('=')
		if elements[0]=='reconid':
			params['reconid'] = int(elements[1])
		elif elements[0]=='mask':
			params['mask'] = int(elements[1])
		elif elements[0]=='iter':
			params['iter'] = int(elements[1])
		elif elements[0]=='nsig':
			params['nsig'] = float(elements[1])
		elif elements[0]=='stackname':
			params['stackname'] = elements[1]
		elif elements[0]=='eotest':
			params['eotest'] = True
		elif elements[0]=='avgerr':
			params['avgerr'] = float(elements[1])
		else:
			print elements[0], 'is not recognized as a valid parameter'
			sys.exit()
	return params

def checkParams(params):
	pass

def printHelp():
	print "Usage:"
	print "makegoodaverages.py reconid=<DEF_id> iter=<n> mask=<n> nsig=<n> stackname=<stackfile> <eotest>"
	print "--------------------------------------------------------------------------------------"
	print "reconid         : primary key from db"
	print "iter            : iteration to process"
	print "mask            : mask radius in pixels"
	print "nsig            : number of standard deviations greater than the mean quality factor"
	print "                  to include"
	print "avgerr          : throw away ptcls with error greater than this"
	print "stackname       : name of the stack to which the averages will be written"
	print "eotest          : make even and odd volumes"
	sys.exit()

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

def makeClassAverages(lst, stackname, classdata, params):
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
	avg.writeImage(stackname,-1)
	
def makeEvenOddClasses(lst,params):
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
	evenstack=os.path.splitext(params['stackname'])[0]+'.even.hed'
	oddstack=os.path.splitext(params['stackname'])[0]+'.odd.hed'
	
	if neven>0:
		makeClassAverages('even.lst',evenstack,params)
	if nodd>0:
		makeClassAverages('odd.lst',oddstack,params)

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

def getMatrix3(eulerdata):
	#math from http://mathworld.wolfram.com/EulerAngles.html
	#appears to conform to EMAN conventions - could use more testing
	#tested by independently rotating object with EMAN eulers and with the
	#matrix that results from this function
	phi=eulerdata['euler2']*math.pi/180 #eman az
	theta=eulerdata['euler1']*math.pi/180 #eman alt
	psi=eulerdata['euler3']*math.pi/180 #eman phi

	m=numpy.zeros((3,3))
	m[0,0]=math.cos(psi)*math.cos(phi)-math.cos(theta)*math.sin(phi)*math.sin(psi)
	m[0,1]=math.cos(psi)*math.sin(phi)+math.cos(theta)*math.cos(phi)*math.sin(psi)
	m[0,2]=math.sin(psi)*math.sin(theta)
	m[1,0]=-math.sin(psi)*math.cos(phi)-math.cos(theta)*math.sin(phi)*math.cos(psi)
	m[1,1]=-math.sin(psi)*math.sin(phi)+math.cos(theta)*math.cos(phi)*math.cos(psi)
	m[1,2]=math.cos(psi)*math.sin(theta)
	m[2,0]=math.sin(theta)*math.sin(phi)
	m[2,1]=-math.sin(theta)*math.cos(phi)
	m[2,2]=math.cos(theta)
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

def calculateDistanceOld(eulerdata1,eulerdata2):
	m1=getMatrix3(eulerdata1)
	m2=getMatrix3(eulerdata2)
	#print m1
	#print m2
	tot=0
	for i in range(0,m1.shape[0]):
		for j in range(0,m1.shape[1]):	
			tot+=(m1[i,j]-m2[i,j])**2
	#print 'd',tot
	return tot
	
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
	particledata=stackparticlesdata[0]
	ptclclassq=appionData.ApParticleClassificationData()
	ptclclassq['particle']=particledata
	ptclclassdata=apdb.query(ptclclassq)
	
	#for cls in ptclclassdata:
		#print cls['refinement']['iteration'], cls['eulers']
	return ptclclassdata

def removePtclsByQualityFactor(particles,params):
	stack=os.path.join(particles[0]['particle']['stack']['stackPath'],particles[0]['particle']['stack']['name'])
	classes,cstats=determineClasses(particles)
	
	print params['nsig']
	cutoff=cstats['meanquality']+params['nsig']*cstats['stdquality']
	#cutoff=0
	print "Cutoff =",cutoff

	classkeys=classes.keys()
	classkeys.sort()
	classnum=0
	totalptcls=0
	high=open("high.lst",'w')
	high.write("#LST\n")
	
	low=open("low.lst",'w')
	low.write("#LST\n")
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
			if ptcl['quality_factor']>cutoff:
				f.write('%d\t%s\t%f,\t%f,%f,%f,%d\n' % (ptcl['particle']['particleNumber']-1,stack,ptcl['quality_factor'],rot,ptcl['shiftx'],ptcl['shifty'],mirror))
				totalptcls+=1
				nptcls+=1
			else:
				low.write('%d\t%s\t%f,\t%f,%f,%f,%d\n' % (ptcl['particle']['particleNumber']-1,stack,ptcl['quality_factor'],rot,ptcl['shiftx'],ptcl['shifty'],mirror))
			if ptcl['quality_factor']>cstats['meanquality']+3*cstats['stdquality']:
				high.write('%d\t%s\t%f,\t%f,%f,%f,%d\n' % (ptcl['particle']['particleNumber']-1,stack,ptcl['quality_factor'],rot,ptcl['shiftx'],ptcl['shifty'],mirror))
		f.close()
		
		if nptcls<1:
			continue
		
		makeClassAverages('tmp.lst',params['stackname'], classes[key], params)
		
		if params['eotest']:
			makeEvenOddClasses('tmp.lst',params)
		#break
	low.close()
	high.close()
	return totalptcls

def removePtclsByErr(nptcls,params):
	errdict={}
	sumerr=0
	total=0
	f=open('err.txt','w')
	for ptcl in range(1,nptcls+1):
		eulers=getEulersForParticle(ptcl,params['reconid'])
		e0=eulers[0]['eulers']
		distances=numpy.zeros((len(eulers)-1))
		f.write('%d\t' % ptcl)
		for n in range(1,len(eulers)):
			# first get all equivalent Eulers given symmetry
			eqEulers=calculateEquivSym(eulers[n]['eulers'])

			# calculate the distances between the original Euler and all the equivalents
			mat0=getMatrix3(e0)
			mat1=getMatrix3(eulers[n]['eulers'])

			d=[]
			for e1 in eqEulers:
				d.append(calculateDistance(mat0,mat1))
			mind=min(d)
			distances[n-1]=mind*180/math.pi
			f.write('%f\t' % distances[n-1])
			e0=eulers[n]['eulers']
			sumerr+=distances[n-1]
			total+=1
		if not ptcl%100:
			print "particle",ptcl
		f.write('%f\t%f\n' % (distances.mean(),distances.std()))
		#print distances
		#print distances.mean()
	print total, sumerr/total
	return total

def calcXRot(a):
	m=numpy.zeros((3,3))
	m[0,0]=1
	m[0,1]=0
	m[0,2]=0
	m[1,0]=0
	m[1,1]=math.cos(a)
	m[1,2]=-(math.sin(a))
	m[2,0]=0
	m[2,1]=math.sin(a)
	m[2,2]=math.cos(a)
	return m

def calcYRot(a):
	m=numpy.zeros((3,3))
	m[0,0]=math.cos(a)
	m[0,1]=0
	m[0,2]=math.sin(a)
	m[1,0]=0
	m[1,1]=1
	m[1,2]=0
	m[2,0]=-(math.sin(a))
	m[2,1]=0
	m[2,2]=math.cos(a)
	return m

def calcZRot(a):
	m=numpy.zeros((3,3))
	m[0,0]=math.cos(a)
	m[0,1]=-(math.sin(a))
	m[0,2]=0
	m[1,0]=math.sin(a)
	m[1,1]=math.cos(a)
	m[1,2]=0
	m[2,0]=0
	m[2,1]=0
	m[2,2]=1
	return m

def calculateEquivSym(eulers):
	f=open('matrices.txt','w')
	eqEulers=[]
	m=getMatrix3(eulers)
	eqEulers.append(m)
	# 180 degree rotation around x axis
	x1 = calcXRot(math.pi)
	# calculate each of 7 rotations around z axis
	z1 = calcZRot(2*math.pi/7)
	z2 = calcZRot(4*math.pi/7)
	z3 = calcZRot(6*math.pi/7)
	z4 = calcZRot(8*math.pi/7)
	z5 = calcZRot(10*math.pi/7)
	z6 = calcZRot(12*math.pi/7)
	# combine each of 7 rotations with x axis rotation
	xz1 = numpy.dot(x1,z1)
	xz2 = numpy.dot(x1,z2)
	xz3 = numpy.dot(x1,z3)
	xz4 = numpy.dot(x1,z4)
	xz5 = numpy.dot(x1,z5)
	xz6 = numpy.dot(x1,z6)

	eqEulers.append(numpy.dot(m,x1))
	eqEulers.append(numpy.dot(m,z1))
	eqEulers.append(numpy.dot(m,z2))
	eqEulers.append(numpy.dot(m,z3))
	eqEulers.append(numpy.dot(m,z4))
	eqEulers.append(numpy.dot(m,z5))
	eqEulers.append(numpy.dot(m,z6))
	eqEulers.append(numpy.dot(m,xz1))
	eqEulers.append(numpy.dot(m,xz2))
	eqEulers.append(numpy.dot(m,xz3))
	eqEulers.append(numpy.dot(m,xz4))
	eqEulers.append(numpy.dot(m,xz5))
	eqEulers.append(numpy.dot(m,xz6))
	n=1
## 	for e in eqEulers:
## 		f.write('REMARK 290    SMTRY1  %2d   %5.2f %5.2f %5.2f     0.0\n' % (n, e[0,0], e[0,1], e[0,2]))
## 		f.write('REMARK 290    SMTRY2  %2d   %5.2f %5.2f %5.2f     0.0\n' % (n, e[1,0], e[1,1], e[1,2]))
## 		f.write('REMARK 290    SMTRY3  %2d   %5.2f %5.2f %5.2f     0.0\n' % (n, e[2,0], e[2,1], e[2,2]))
## 		n+=1
## 	f.close()
## 	sys.exit()
	return eqEulers

if __name__=='__main__':
	
	params=createDefaults()
	if len(sys.argv) < 2:
		printHelp()
	
	params=parseParams(sys.argv[1:],params)
	
	checkParams(params)
	
	particles=getParticleInfo(params['reconid'],params['iter'])
	
	if params['nsig']:
		totalptcls=removePtclsByQualityFactor(particles,params)
	elif params['avgerr']:
		nptcls=len(particles)
		totalptcls=removePtclsByErr(nptcls,params)
	print
	print "Total particles included =",totalptcls
	print "Done!"
