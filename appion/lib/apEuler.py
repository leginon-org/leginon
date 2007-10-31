#!/usr/bin/python -O

import MySQLdb
import math
import numpy
from scipy import ndimage
import Image
import ImageDraw
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

	this does NOT use sinedon because it goes
	from taking < 1 min for this method
	to taking several hours with sinedon
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
	#print query
	cursor.execute(query)
	numrows = int(cursor.rowcount)
	apDisplay.printColor("Found "+str(numrows)+" euler values", "cyan")
	result = cursor.fetchall()
	apDisplay.printMsg("Fetched data in "+apDisplay.timeString(time.time()-t0))
	#r0 = resToEuler(result[int( float(len(result)) * random.random() )])
	#r1 = resToEuler(result[int( float(len(result)) * random.random() )])
	#print r0
	#print r1
	#mat0 = getMatrix3(r0)
	#mat1 = getMatrix3(r1)
	#dist = calculateDistance(mat0, mat1)
	#print mat0
	#print mat1
	#print "dist=",dist
	radlist = []
	anglelist = []
	freqlist = []
	xlist = []
	ylist = []
	xlist = [ x*30.0 for x in range(-3, 3+1)]
	ylist = [ y*30.0 for y in range(-3, 3+1)]

	#freqmap = calcFreqEqualArea(result)
	indres = 1.0
	indmult = int(90.0/indres)
	indrange = len(range(-indmult, indmult+1))
	#freqmap = calcFreqGrid(result, indres)
	freqmap = calcFreqNative(result)
	#pprint.pprint(freqmap)
	#radlist = numpy.zeros((len(freqmap)), dtype=numpy.float32)
	#anglelist = numpy.zeros((len(freqmap)), dtype=numpy.float32)
	freqgrid = numpy.zeros((indrange,indrange), dtype=numpy.int32)
	items = freqmap.items()
	items.sort(sortFreqMapCart)
	freqsort = [value for key, value in items]
	#print freqsort

	for val in freqsort:
		radlist.append(val[0]/90.0)
		xlist.append(val[0])
		ylist.append(val[1])
		#radlist[val[3]] = val[0]/90.0
		anglelist.append(val[1]/180.0*math.pi)
		#anglelist[val[4]] = val[1]/180.0*math.pi
		freqlist.append(val[2])
		#freqgrid[val[3],val[4]] = val[2]
		#freqlist.append(math.log10(val[2]))
	xlist = [x*indres for x in range(-indmult, indmult+1) ]
	ylist = [y*indres for y in range(-indmult, indmult+1) ]

	freqnumpy = numpy.asarray(freqlist, dtype=numpy.int32)
	#print(freqlist)
	print "min=",ndimage.minimum(freqnumpy)
	print "max=",ndimage.maximum(freqnumpy)
	print "mean=",ndimage.mean(freqnumpy)
	print "stdev=",ndimage.standard_deviation(freqnumpy)
	#print "median=",ndimage.median(freqnumpy)

	return radlist,anglelist,freqlist,freqgrid

	for i in range(1000):
		index = int( float(len(result)) * random.random() )
		record = result[index]
		radlist.append(record[2])
		anglelist.append(record[3])
		#print record[2] , ",", record[3], ",", record[5]
	return radlist,anglelist,[],[]


def sortFreqMapCart(a, b):
	if a[1][3] > b[1][3]:
		return 1
	elif a[1][3] < b[1][3]:
		return -1
	elif a[1][4] > b[1][4]:
		return 1
	elif a[1][4] < b[1][4]:
		return -1
	else:
		return 0

def sortFreqMapPolar(a, b):
	ax,ay = polarToCart(a[1][3],a[1][4])
	bx,by = polarToCart(b[1][3],b[1][4])
	if ax > bx:
		return 1
	elif ax < bx:
		return -1
	elif ay > by:
		return 1
	elif ay < by:
		return -1
	else:
		return 0

def resToEuler(res):
	euler = {}
	euler['euler1'] = float(res[0])
	euler['euler2'] = float(res[1])
	euler['euler3'] = float(res[2])
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

def calcFreqGrid(points, indres=30.0):
	indmult = int(90.0/indres)
	indexmap = {}
	for ybox in range(-indmult, indmult+1):
		for xbox in range(-indmult, indmult+1):
			index = int(xbox + ybox*indmult*3)
			indexmap[index] = [xbox*indres, ybox*indres, 1, xbox, ybox]
	#items = indexmap.items()
	#items.sort(sortFreqMapCart)
	#freqsort = [value for key, value in items]
	#print freqsort
	for point in points:
		rad = point[0]
		theta = point[1]
		x, y = polarToCart(rad, theta)
		xbox = int(round(x/indres,0))
		ybox = int(round(y/indres,0))
		index = int(xbox + ybox*indmult*3)
		if index in indexmap:
			oldcounts = indexmap[index][2]
		else:
			oldcounts = 0
		indexmap[index] = [xbox*indres, ybox*indres, oldcounts+1, xbox, ybox]
	return indexmap

def polarToCart(rad, thdeg):
	thrad = thdeg*math.pi/180.0
	x = rad*math.cos(thrad)
	y = rad*math.sin(thrad)
	return x,y

def cartToPolar(x, y):
	r = math.hypot(x,y)
	if x > 0:
		if y < 0:
			th = math.atan2(y,x)
		else:
			th = math.atan2(y,x) + 2*math.pi
	elif x < 0:
		th = math.atan2(y,x) + math.pi
	else:
		#x = 0
		if y > 0:
			th = 3*math.pi/2.0
		elif y < 0:
			th = math.pi/2.0
		else:
			#x,y = 0
			th = 0
	return r, th*180.0/math.pi

def calcFreqNative(points):
	indres = 0.1
	indmult = int(90.0/indres)
	indexmap = {}
	for point in points:
		rad = point[0]
		theta = point[1]
		rbox = int(round(rad/indres,0))
		tbox = int(round(theta/indres,0))
		index = int(rbox + tbox*indmult)
		if index in indexmap:
			oldcounts = indexmap[index][2]
		else:
			oldcounts = 0
		indexmap[index] = [rad, theta, oldcounts+1, rbox, tbox]
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
			indexmap[index] = [rval,tval,1, rbox, tbox]
	#print tsteps
	#pprint.pprint(indexmap)
	minrad = 100
	maxrad = -100
	mintheta = 360
	maxtheta = -360
	for point in points:
		rad = point[0]
		theta = point[1]
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
			indexmap[index] = [rval, tval, oldcounts+1, rbox, tbox]
		else:
			print "newdata=",rval,",",tval
			indexmap[index] = [rval,tval,1, rbox, tbox]
	print minrad,maxrad
	print mintheta,maxtheta
	#pprint.pprint(indexmap)
	return indexmap


def makeImage(radlist, anglelist, freqlist, 
		imgname="temp.png", imgdim=1024, crad=10, frame=50):

	#'L' -> grayscale
	#'RGB' -> color
	img = Image.new("RGB", (imgdim, imgdim), color="#ffffff")
	draw = ImageDraw.Draw(img)

	freqnumpy = numpy.asarray(freqlist, dtype=numpy.int32)
	minf = float(ndimage.minimum(freqnumpy))
	maxf = float(ndimage.maximum(freqnumpy))
	if ndimage.sum(freqnumpy) < 10:
		apDisplay.printWarning("not enough eulers to draw a map")
		return
	rangef = maxf-minf+1

	angnumpy = numpy.asarray(anglelist, dtype=numpy.float32)
	mina = float(ndimage.minimum(angnumpy))
	maxa = float(ndimage.maximum(angnumpy))
	rangea = maxa-mina

	radnumpy = numpy.asarray(radlist, dtype=numpy.float32)
	minr = float(ndimage.minimum(radnumpy))
	maxr = float(ndimage.maximum(radnumpy))
	ranger = maxr-minr

	x1, y1 = polarToCart(maxr, rangea)
	x2, y2 = polarToCart(minr, 0)
	x3, y3 = polarToCart(maxr, 0)
	minx = min(x1,x2,x3)
	maxx = max(x1,x2,x3)
	miny = min(y1,y2,y3)
	maxy = max(y1,y2,y3)
	rangex = maxx-minx
	rangey = maxy-miny

	for i in range(len(radlist)):
		#frequency
		freq = freqlist[i]
		fgray = 255.0*((maxf-freq)/rangef)**2
		fcolor = grayToColor(fgray)

		#direct polar
		rad = radlist[i]			
		ang = anglelist[i]
		#ax = float(imgdim-2*frame)*(ang-mina)/rangea+frame
		#ry = float(imgdim-2*frame)*(rad-minr)/ranger+frame
		#polarcoord = (ax-crad, ry-crad, ax+crad, ry+crad)

		#polar -> cartesian
		x, y = polarToCart(rad, ang-mina)
		ys = float(imgdim-2*frame)*(x-minx)/rangex+frame
		xs = float(imgdim-2*frame)*(y-miny)/rangey+frame
		cartcoord = (xs-crad, ys-crad, xs+crad, ys+crad)

		draw.ellipse(cartcoord, fill=fcolor)
	try:
		img.save(imgname, "PNG")
	except:
		apDisplay.printWarning("could not save file: "+imgname)
	try:
		os.chmod(imgname, 0666)
	except:
		apDisplay.printWarning("could not modify file: "+imgname)

	return

def grayToColor(gray):
	b = 32
	if gray < 128:
		#green (0) 00ff00 -> yellow (128) ffff00
		r = gray*2
		g = 255
	else:
		#yellow (128) ffff00 -> red (255) ff0000
		r = 255
		g = 2*(255 - gray)
	return colorTupleToHex(r, g, b, scale=0.8)

def colorTupleToHex(r, g, b, scale=1):
	#print r,g,b
	ir = int(r*scale)
	ig = int(g*scale)
	ib = int(b*scale)
	hexcode = str(hex(ir*256**2 + ig*256 + ib))[2:]
	hexstr = "#"+apDisplay.leftPadString(hexcode, n=6, fill='0')
	return hexstr

def makePlot(radlist,anglelist,freqlist,freqgrid):
	import pylab
	from matplotlib import cm
	# radar green, solid grid lines
	pylab.rc('grid', color='#316931', linewidth=2, linestyle='-')
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
	print numpy.around(radlist,3)
	print numpy.around(anglelist,3)
	print numpy.around(freqgrid,3)
	#c = pylab.contourf(anglelist, radlist, freqgrid, cmap=cm.RdYlGn)
	c = pylab.scatter(anglelist, radlist, c=freqlist, s=100, marker='o', cmap=cm.RdYlGn)
	#c.set_alpha(0.5)
	#pylab.setp(ax.thetagridlabels, y=1.075) # the radius of the grid labels
	#pylab.RdYlGn()
	#pylab.autumn()
	pylab.title("Euler plot", fontsize=24)
	#pylab.savefig('polar_test2')
	pylab.show()


if __name__ == "__main__":
	t0 = time.time()
	#radlist, anglelist, freqlist, freqgrid = getEulersForIteration(181, 4)
	#radlist, anglelist, freqlist, freqgrid = getEulersForIteration(173, 12)
	#radlist, anglelist, freqlist, freqgrid = getEulersForIteration(158, 4)
	#radlist, anglelist, freqlist, freqgrid = getEulersForIteration(158, 2)
	radlist, anglelist, freqlist, freqgrid = getEulersForIteration(118, 1)
	#radlist, anglelist, freqlist, freqgrid = getEulersForIteration(159, 1)
	#freqmap = getEulersForIteration(158, 4)
	#makePlot(radlist,anglelist,freqlist,freqgrid)
	makeImage(radlist,anglelist,freqlist)
	#makePlot(freqmap)
	apDisplay.printColor("Finished in "+apDisplay.timeString(time.time()-t0), "cyan")



