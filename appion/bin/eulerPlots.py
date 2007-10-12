#!/usr/bin/python -O

import MySQLdb
import math
import numpy
import pylab
import random
import time
import pprint
import apDisplay

# connect
db = MySQLdb.connect(host="cronus4.scripps.edu", user="usr_object", passwd="", db="dbappiondata")
# create a cursor
cursor = db.cursor()


def getEulersForIteration(reconid, iteration=1):
	"""
	returns all classdata for a particular refinement iteration
	"""
	t0 = time.time()
	query = (
		"SELECT e.euler1, e.euler2, pc.`inplane_rotation` "
			+"FROM `ApEulerData` AS e "
			+"LEFT JOIN `ApParticleClassificationData` AS pc "
			+"ON pc.`REF|ApEulerData|eulers` = e.`DEF_id` "
			+"LEFT JOIN `ApRefinementData` AS rd "
			+"ON pc.`REF|ApRefinementData|refinement` = rd.`DEF_id` "
			+"WHERE rd.`REF|ApRefinementRunData|refinementRun` = "+str(reconid)+" "
			+"AND rd.`iteration` = "+str(iteration)+" "
		)
	print query
	cursor.execute(query)
	numrows = int(cursor.rowcount)
	print "Found ",numrows," rows"

	result = cursor.fetchall()
	apDisplay.printMsg("Fetched data in "+apDisplay.timeString(time.time()-t0))
	r0 = resToEuler(result[int( float(len(result)) * random.random() )])
	r1 = resToEuler(result[int( float(len(result)) * random.random() )])
	print r0
	print r1
	mat0 = getMatrix3(r0)
	mat1 = getMatrix3(r1)
	dist = calculateDistance(mat0, mat1)
	print mat0
	print mat1
	print "dist=",dist
	radlist = []
	anglelist = []
	freqlist = []
	#pprint.pprint(result[0:100])
	freqmap = calcFreqEqualArea(result)
	for i,val in freqmap.items():
		radlist.append(val[0]/90.0)
		anglelist.append(val[1]/180.0*math.pi)
		freqlist.append(math.log10(val[2]))		
	return radlist,anglelist,freqlist

	for i in range(1000):
		index = int( float(len(result)) * random.random() )
		record = result[index]
		radlist.append(record[2])
		anglelist.append(record[3])
		#print record[2] , ",", record[3], ",", record[5]
	return radlist,anglelist,[]


def resToEuler(res):
	euler = {}
	euler['euler1'] = float(res[2])
	euler['euler2'] = float(res[3])
	euler['euler3'] = float(res[5])
	return euler

def getMatrix3(eulerdata):
	#math from http://mathworld.wolfram.com/EulerAngles.html
	#appears to conform to EMAN conventions - could use more testing
	#tested by independently rotating object with EMAN eulers and with the
	#matrix that results from this function
	phi = round(eulerdata['euler2']*math.pi/180,2) #eman az,  azimuthal
	the = round(eulerdata['euler1']*math.pi/180,2) #eman alt, altitude
	psi = round(eulerdata['euler3']*math.pi/180,2) #eman phi, inplane_rotation

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

def calcFreqGrid(points, xystep=0.1):
	indexmap = {}
	rstep = 9.0
	rlen = int(90.0/rstep)
	area = rstep*180.0
	tsteps = []
	xlist = [x*xystep for x in range(10)]
	print xlist

	for point in points:
		rad = point[2]
		theta = point[3]
		if rad > maxrad:
			maxrad = rad
		elif rad < minrad:
			minrad = rad
		if theta > maxtheta:
			maxtheta = theta
		elif theta < mintheta:
			mintheta = theta
		rbox = int(rad / rstep)
		tstep = area / (rbox*rstep + rstep/2.0)
		#tstep = 360.0 / float(rbox+1.0)**1.7
		tbox = int(theta / tstep)
		rval = rbox*rstep
		tval = (tbox*tstep+tstep/2.0) % 360.0
		index = int(rbox + tbox*rlen)
		if index in indexmap:
			oldcounts = indexmap[index][2]
			indexmap[index] = [rval, tval, oldcounts+1]
		else:
			print "newdata=",rval,",",tval
			indexmap[index] = [rval,tval,1]
	print minrad,maxrad
	print mintheta,maxtheta
	#pprint.pprint(indexmap)
	return indexmap


def calcFreqEqualArea(points, rstep=9.0):
	indexmap = {}
	rlen = int(90.0/rstep)
	area = rstep*180.0
	tsteps = []

	for rbox in range(rlen):
		tstep = area / float(rbox*rstep + rstep/2.0)
		#tstep = 360.0 / 2*float(rbox+1.0)**1.7
		tsteps.append(tstep)
		tlen = int(360.0/tstep)
		#print rbox, tlen
		for tbox in range(tlen):
			rval = rbox*rstep
			tval = tbox*tstep+tstep/2.0
			index = int(rbox + tbox*rlen)
			#print "box=",rbox,tbox,rval,tval
			indexmap[index] = [rval,tval,1]
	#print tsteps
	#pprint.pprint(indexmap)
	minrad = 100
	maxrad = -100
	mintheta = 360
	maxtheta = -360
	for point in points:
		rad = point[2]
		theta = point[3]
		if rad > maxrad:
			maxrad = rad
		elif rad < minrad:
			minrad = rad
		if theta > maxtheta:
			maxtheta = theta
		elif theta < mintheta:
			mintheta = theta
		rbox = int(rad / rstep)
		tstep = area / (rbox*rstep + rstep/2.0)
		#tstep = 360.0 / float(rbox+1.0)**1.7
		tbox = int(theta / tstep)
		rval = rbox*rstep
		tval = (tbox*tstep+tstep/2.0) % 360.0
		index = int(rbox + tbox*rlen)
		if index in indexmap:
			oldcounts = indexmap[index][2]
			indexmap[index] = [rval, tval, oldcounts+1]
		else:
			print "newdata=",rval,",",tval
			indexmap[index] = [rval,tval,1]
	print minrad,maxrad
	print mintheta,maxtheta
	#pprint.pprint(indexmap)
	return indexmap


def makePlot(radlist,anglelist,freqlist):
	# radar green, solid grid lines
	pylab.rc('grid', color='#316931', linewidth=1, linestyle='-')
	pylab.rc('xtick', labelsize=16)
	pylab.rc('ytick', labelsize=16)

	# square figure and square axes looks better for polar plots
	pylab.figure(figsize=(4,4))
	ax = pylab.axes([0.1, 0.1, 0.8, 0.8], polar=True, axisbg='#d5de9c')

	#SPIRAL
	# r = pylab.arange(0,1,0.001)
	# theta = 2*2*math.pi*r
	# pylab.polar(theta, r, color='#ee8d18', lw=3)
	#p = pylab.polar(anglelist, radlist, color='#ee8d18', lw=1)
	#p.set_alpha(0.2)

	#ax = pylab.subplot(111, polar=True)
	#c = pylab.scatter(radlist, anglelist, c='#ee8d18', s=100)
	#pprint.pprint( radlist)
	#pprint.pprint( anglelist)
	#pprint.pprint( freqlist)
	c = pylab.contour(anglelist, radlist, freqlist)
	#c = pylab.scatter(anglelist, radlist, c=freqlist, s=900, marker='o')
	#c.set_alpha(0.5)
	pylab.setp(ax.thetagridlabels, y=1.075) # the radius of the grid labels

	pylab.title("Euler plot", fontsize=24)
	#pylab.savefig('polar_test2')
	pylab.show()


if __name__ == "__main__":
	radlist, anglelist, freqlist = getEulersForIteration(158, 4)
	#radlist, anglelist, freqlist = getEulersForIteration(158, 2)
	#radlist, anglelist, freqlist = getEulersForIteration(118, 1)
	#radlist, anglelist, freqlist = getEulersForIteration(159, 1)
	#freqmap = getEulersForIteration(158, 4)
	makePlot(radlist,anglelist,freqlist)
	#makePlot(freqmap)




