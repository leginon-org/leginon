import math
import os
import sys
import numpy
import random
import time
import pprint
from appionlib import apDisplay

#==================
#==================
#==================
def eulerCalculateDistance(e1, e2, inplane=False):
	"""
	given two euler as dicts
	calculate distance between euler values
	value in degrees
	"""
	mat0 = getEmanEulerMatrix(e1, inplane=inplane)
	mat1 = getEmanEulerMatrix(e2, inplane=inplane)
	dist = computeDistance(mat0, mat1)
	#convert to degrees
	return dist

#==================
def eulerCalculateDistanceSym(e1, e2, sym='d7', inplane=False):
	"""
	given two euler as dicts in degrees
	calculate distance between euler values
	value in degrees

	euler1 = alt
	euler2 = az
	euler3 = in plane rotation
	"""
	e1mat = getEmanEulerMatrix(e1, inplane=inplane)
	#print e1mat
	#get list of equivalent euler matrices
	if len(sym) > 3 and sym.lower()[:4] == "icos":
		e2equivMats = calculateEquivIcos(e2, inplane=inplane)
	else:
		e2equivMats = calculateEquivSym(e2, sym=sym, inplane=inplane)
	#print e2equivMats[0]

	# calculate the distances between the original Euler and all the equivalents
	mindist = 360.0
	distlist = []
	for e2mat in e2equivMats:
		dist = computeDistance(e1mat, e2mat)
		distlist.append(dist)
		if dist < mindist:
			mindist = dist
	"""
	if mindist > 91.0:
		print round(mindist,4),"<--",numpy.around(distlist,2)
		pprint.pprint(e1)
		pprint.pprint(e2)
		print ""
	"""

	#convert to degrees
	return mindist

#==================
def calculateEquivSym(euler, sym='d7', symout=False, inplane=False):
	"""
	rotates eulers about any c and d symmetry group

	input:
		individual euler dict
	output:
		list of equiv. euler matrices
	"""
	symMats = []

	# calculate each of the rotations around z axis
	numrot = int(sym[1:])
	for i in range(numrot):
		symMats.append( calcZRot(2.0*math.pi*float(i)/float(numrot)) )

	# if D symmetry, combine each rotations with x axis rotation
	if sym[0] == 'd':
		x1 = calcYRot(math.pi)
		for i in range(numrot):
			symMats.append( numpy.dot(x1, symMats[i]) )

	#calculate new euler matices
	eulerMat = getEmanEulerMatrix(euler, inplane=inplane)
	equivMats=[]
	for symMat in symMats:
		equivMats.append(numpy.dot(eulerMat, symMat))

	if symout is True:
		f=open('matrices.txt','w')
		for n,e in enumerate(equivMats):
			f.write('REMARK 290    SMTRY1  %2d   %5.2f %5.2f %5.2f     0.0\n' % (n+1, e[0,0], e[0,1], e[0,2]))
			f.write('REMARK 290    SMTRY2  %2d   %5.2f %5.2f %5.2f     0.0\n' % (n+1, e[1,0], e[1,1], e[1,2]))
			f.write('REMARK 290    SMTRY3  %2d   %5.2f %5.2f %5.2f     0.0\n' % (n+1, e[2,0], e[2,1], e[2,2]))
		f.close()
	return equivMats

#==================
def calculateEquivIcos(euler, symout=False, inplane=False):
	"""
	rotates eulers about icosahedral symmetry group

	input:
		individual euler dict
	output:
		list of equiv. euler matrices
	"""
	symMats = []

	### first 5 rotations
	for i in range(5):
		symMats.append( calcZRot(2.0*math.pi*float(i)/float(5)) )
	### second 5 are rotated 180 out of phase
	x1 = calcYRot(math.pi)
	for i in range(5):
		symMats.append( numpy.dot(x1, symMats[i]) )
	### next 25 include a y rotation duplicated 5 times with another z rotation
	y1 = calcYRot(296.56505*math.pi/180.0)
	for i in range(5):
		mysym = numpy.dot(y1, calcZRot(2.0*math.pi*float(i)/5.0+36.0))
		symMats.append( mysym )
		for i in range(4):
			z2 = calcZRot(2.0*math.pi*float(i+1)/5.0)
			symMats.append( numpy.dot(z2, mysym) )
	### final 25 include a y rotation duplicated 5 times with another z rotation
	y1 = calcYRot(243.43495*math.pi/180.0)
	for i in range(5):
		mysym = numpy.dot(y1, calcZRot(2.0*math.pi*float(i)/5.0))
		symMats.append( mysym )
		for i in range(4):
			z2 = calcZRot(2.0*math.pi*float(i+1)/5.0+36.0)
			symMats.append( numpy.dot(z2, mysym) )

	#calculate new euler matices
	eulerMat = getEmanEulerMatrix(euler, inplane=inplane)
	equivMats=[]
	for symMat in symMats:
		equivMats.append(numpy.dot(eulerMat, symMat))

	if symout is True:
		f=open('matrices.txt','w')
		for n,e in enumerate(equivMats):
			f.write('REMARK 290    SMTRY1  %2d   %5.2f %5.2f %5.2f     0.0\n' % (n+1, e[0,0], e[0,1], e[0,2]))
			f.write('REMARK 290    SMTRY2  %2d   %5.2f %5.2f %5.2f     0.0\n' % (n+1, e[1,0], e[1,1], e[1,2]))
			f.write('REMARK 290    SMTRY3  %2d   %5.2f %5.2f %5.2f     0.0\n' % (n+1, e[2,0], e[2,1], e[2,2]))
		f.close()
	return equivMats

#==================
def getEmanEulerMatrix(eulerdata, inplane=True):
	return getMatrix3(eulerdata, inplane=inplane)

#==================
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

#==================
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

#==================
def getMatrix3(eulerdata, inplane=False):
	"""
	math from http://mathworld.wolfram.com/EulerAngles.html
	appears to conform to EMAN conventions - could use more testing
	tested by independently rotating object with EMAN eulers and with the
	matrix that results from this function
	"""
	#theta is a rotation about the x-axis, i.e. latitude
	# 0 <= theta <= 180 degrees
	the = eulerdata['euler1']*math.pi/180.0 #eman alt, altitude
	#phi is a rotation in the xy-plane, i.e. longitude
	# 0 <= phi <= 360 degrees
	phi = eulerdata['euler2']*math.pi/180.0 #eman az, azimuthal
	if inplane is True:
		psi = eulerdata['euler3']*math.pi/180.0 #eman phi, inplane_rotation
	else:
		psi = 0.0

	if 'mirror' in eulerdata and eulerdata['mirror'] == 1:
		"""
		using mirror function
		see: http://blake.bcm.tmc.edu/emanwiki/EMAN2/Symmetry
		for documentation
		"""
		#theta flips to the back
		the = math.pi - the
		#phi is rotated 180 degrees
		phi += math.pi
		#this works without in_plane
		if inplane is False:
			#psi is rotated 180 degrees
			psi += math.pi

	m = numpy.zeros((3,3), dtype=numpy.float32)
	m[0,0] =  math.cos(psi)*math.cos(phi) - math.cos(the)*math.sin(phi)*math.sin(psi)
	m[0,1] =  math.cos(psi)*math.sin(phi) + math.cos(the)*math.cos(phi)*math.sin(psi)
	m[0,2] =  math.sin(psi)*math.sin(the)
	m[1,0] = -math.sin(psi)*math.cos(phi) - math.cos(the)*math.sin(phi)*math.cos(psi)
	m[1,1] = -math.sin(psi)*math.sin(phi) + math.cos(the)*math.cos(phi)*math.cos(psi)
	m[1,2] =  math.cos(psi)*math.sin(the)
	m[2,0] =  math.sin(the)*math.sin(phi)
	m[2,1] = -math.sin(the)*math.cos(phi)
	m[2,2] =  math.cos(the)
	return m

#==================
def computeDistance(m1,m2):
	r = numpy.dot(m1.transpose(),m2)
	#print r
	trace = r.trace()
	s = (trace-1.0)/2.0
	if int(round(abs(s),7)) == 1:
		"""
		Either:
		 (1) Vectors are the same , i.e. 0 degrees
		 (2) Vectors are opposite, i.e. 180 degrees
		"""
		diff = numpy.sum(pow((m1-m2),2))
		#apDisplay.printWarning("overflow return, diff="+str(diff)+" m1="+str(m1)+" m2="+str(m2))
		if diff < 1.0e-6:
			return 0.0
		return 180.0
	else:
		#print "calculating"
		theta = math.acos(s)
		#print 'theta',theta
		t1 = abs(theta/(2*math.sin(theta)))
		#print 't1',t1
		t2 = math.sqrt(pow(r[0,1]-r[1,0],2)+pow(r[0,2]-r[2,0],2)+pow(r[1,2]-r[2,1],2))
		#print 't2',t2, t2*180/math.pi
		dist = t1 * t2
		dist *= 180.0/math.pi
		#print 'dist=',dist
		return dist

#==================
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

#==================
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

#==================
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

#==================
def henryMult(m1,m2):
	c=numpy.zeros((m1.shape[0],m2.shape[1]))
	for i in range(0,c.shape[0]):
		for j in range(0,c.shape[1]):
			tot=0
			for k in range(0,m1.shape[1]):
				tot+=m1[i,k]*m2[k,j]
			c[i,j]=tot
	return c


