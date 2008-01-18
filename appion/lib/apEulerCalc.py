import math
import os
import numpy
import random
import time
import apDisplay

def eulerCalculateDistance(e1, e2):
	"""
	given two euler as dicts
	calculate distance between euler values
	value in degrees
	"""
	mat0 = getMatrix3(e1)
	mat1 = getMatrix3(e2)
	dist = computeDistance(mat0, mat1)
	#convert to degrees
	dist *= 180.0/math.pi
	return dist

def eulerCalculateDistanceforD7Sym(e1, e2):
	"""
	given two euler as dicts
	calculate distance between euler values
	value in degrees
	"""
	e1mat = getMatrix3(e1)
	#get list of equivalent euler matrices
	e2equivMats = calculateEquivD7Sym(e2)

	# calculate the distances between the original Euler and all the equivalents
	mindist = 180.0
	for e2mat in e2equivMats:
		dist = computeDistance(e1mat,e2mat)
		if dist < mindist:
			mindist = dist
	#convert to degrees
	dist *= 180.0/math.pi
	return dist

def getMatrix3(eulerdata):
	"""
	math from http://mathworld.wolfram.com/EulerAngles.html
	appears to conform to EMAN conventions - could use more testing
	tested by independently rotating object with EMAN eulers and with the
	matrix that results from this function
	"""
	phi = round(eulerdata['euler2']*math.pi/180,2) #eman az,  azimuthal
	the = round(eulerdata['euler1']*math.pi/180,2) #eman alt, altitude
	#psi = round(eulerdata['euler3']*math.pi/180,2) #eman phi, inplane_rotation
	psi = 0.0  #psi component is not working!!!

	m=numpy.zeros((3,3), dtype=numpy.float32)
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

def computeDistance(m1,m2):
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

def calculateEquivD7Sym(eulers, symout=False):
	"""
	rotates eulers about d7 symmetry

	input:
		individual euler dict
	output:
		list of equiv. euler matrices
	"""

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
	if symout:
		f=open('matrices.txt','w')
 		for e in eqEulers:
 			f.write('REMARK 290    SMTRY1  %2d   %5.2f %5.2f %5.2f     0.0\n' % (n, e[0,0], e[0,1], e[0,2]))
 			f.write('REMARK 290    SMTRY2  %2d   %5.2f %5.2f %5.2f     0.0\n' % (n, e[1,0], e[1,1], e[1,2]))
 			f.write('REMARK 290    SMTRY3  %2d   %5.2f %5.2f %5.2f     0.0\n' % (n, e[2,0], e[2,1], e[2,2]))
 			n+=1
 		f.close()
	return eqEulers



