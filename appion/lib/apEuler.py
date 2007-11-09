#!/usr/bin/python -O

import MySQLdb
import math
import numpy
from scipy import ndimage
import Image
import ImageDraw
import ImageFont
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


def fillDataDict(radlist, anglelist, freqlist):
	d = {}

	freqnumpy = numpy.asarray(freqlist, dtype=numpy.int32)
	d['minf'] = float(ndimage.minimum(freqnumpy))
	d['maxf'] = float(ndimage.maximum(freqnumpy))
	if ndimage.sum(freqnumpy) < 10:
		apDisplay.printWarning("not enough eulers to draw a map")
		return
	d['rangef'] = d['maxf']-d['minf']+1

	angnumpy = numpy.asarray(anglelist, dtype=numpy.float32)
	d['mina'] = float(ndimage.minimum(angnumpy))
	d['maxa'] = float(ndimage.maximum(angnumpy))
	d['rangea'] = d['maxa']-d['mina']

	radnumpy = numpy.asarray(radlist, dtype=numpy.float32)
	d['minr'] = float(ndimage.minimum(radnumpy))
	d['maxr'] = float(ndimage.maximum(radnumpy))
	d['ranger'] = d['maxr']-d['minr']

	x1, y1 = polarToCart(d['maxr'], d['rangea'])
	x2, y2 = polarToCart(d['minr'], 0)
	x3, y3 = polarToCart(d['maxr'], 0)
	d['minx'] = min(x1,x2,x3)
	d['maxx'] = max(x1,x2,x3)
	d['miny'] = min(y1,y2,y3)
	d['maxy'] = max(y1,y2,y3)
	d['rangex'] = d['maxx']-d['minx']
	d['rangey'] = d['maxy']-d['miny']

	return d

def makeImage(radlist, anglelist, freqlist, 
		imgname="temp.png", imgdim=650, crad=8, frame=30):
	d = {}
	#'L' -> grayscale
	#'RGB' -> color
	img = Image.new("RGB", (imgdim, imgdim), color="#ffffff")
	draw = ImageDraw.Draw(img)

	d = fillDataDict(radlist, anglelist, freqlist)

	drawAxes(draw, imgdim, crad, img, d)
	drawLegend(draw, imgdim, crad, d['minf'], d['maxf'])
	for i in range(len(radlist)):
		#frequency
		freq = freqlist[i]
		fgray = freqToColor(freq, d['maxf'], d['rangef'])
		fcolor = grayToColor(fgray)

		#direct polar
		rad = radlist[i]			
		ang = anglelist[i]
		#ax = float(imgdim-2*frame)*(ang-d['mina'])/d['rangea']+frame
		#ry = float(imgdim-2*frame)*(rad-d['minr'])/d['ranger']+frame
		#polarcoord = (ax-crad, ry-crad, ax+crad, ry+crad)

		#polar -> cartesian
		x, y = polarToCart(rad, ang-d['mina'])
		ys = float(imgdim-2*frame)*(x-d['minx'])/d['rangex']+frame
		xs = float(imgdim-2*frame)*(y-d['miny'])/d['rangey']+frame
		cartcoord = (xs-crad, ys-crad, xs+crad, ys+crad)

		draw.ellipse(cartcoord, fill=fcolor)
	try:
		img.save(imgname, "PNG")
	except:
		apDisplay.printWarning("could not save file: "+imgname)

	return

def freqToColor(freq, maxf, rangef):
	fgray = 255.0*((maxf-freq)/rangef)**2
	return fgray

def drawAxes(draw, imgdim, crad, img, d):
	#Coords
	start = 2*crad
	mid = imgdim/2
	end = imgdim - 2*crad
	#Axes
	coord = (start, start, start, end)
	draw.line(coord, fill="black", width=2)
	coord = (start, end, end, end)
	draw.line(coord, fill="black", width=2)
	#Axis Labels
	txt = "Latitude / Altitude"
	shifty = draw.textsize(txt)[0]/2.0
	shiftx = draw.textsize(txt)[1]
	coord = (start-shiftx, mid-shifty)
	addRotatedText(img, txt, coord, 90, color="black")
	txt = "Longitude / Azimuthal"
	shiftx = draw.textsize(txt)[0]/2.0
	shifty = draw.textsize(txt)[1]/2.0
	coord = (mid-shiftx, end)
	draw.text(coord, txt, fill="black")
	#Min/Max Numbers for Latitude / Altitude
	txt = str(round(d['minr']*90.0,1))
	shifty = draw.textsize(txt)[0]
	shiftx = draw.textsize(txt)[1]
	coord = (start-shiftx, start)
	addRotatedText(img, txt, coord, 90, color="black")
	txt = str(round(d['maxr']*90.0,1))
	shifty = draw.textsize(txt)[0]
	shiftx = draw.textsize(txt)[1]
	coord = (start-shiftx, end-shifty)
	addRotatedText(img, txt, coord, 90, color="black")
	#Min/Max Numbers for Longitude / Azimuthal
	txt = str(round(d['mina']*180.0/math.pi,1))
	shiftx = draw.textsize(txt)[0]/2.0
	shifty = draw.textsize(txt)[1]/2.0
	coord = (start, end)
	draw.text(coord, txt, fill="black")
	txt = str(round(d['maxa']*180.0/math.pi,1))
	shiftx = draw.textsize(txt)[0]
	shifty = draw.textsize(txt)[1]/2.0
	coord = (end-shiftx, end)
	draw.text(coord, txt, fill="black")

def drawLegend(draw, imgdim, crad=10, minf=0, maxf=100, gap=4, numsc=10):
	rangef = maxf - minf
	xs = imgdim-crad*numsc*gap-crad*2
	ys = crad*(gap+1)
	mult = 1.0/(numsc-1.0)
	for i in range(numsc):
		xt = crad*gap*i
		cartcoord = (xs-crad+xt, ys-crad, xs+crad+xt, ys+crad)
		freq = maxf - math.sqrt(1.0-mult*float(i))*rangef
		fgray = freqToColor(freq, maxf, rangef)
		fcolor = grayToColor(fgray)
		draw.ellipse(cartcoord, fill=fcolor)
		mystr = str(int(freq))
		xv = draw.textsize(mystr)[0]/2.0
		cartcoord2 = (xs+xt-xv, ys+2*crad)
		draw.text(cartcoord2, mystr, fill="black")
	cartcoord = (xs-crad*(gap/2.0), ys-crad*(gap/2.0), xs+crad*gap*(numsc-1)+crad*(gap/2.0), ys+crad*6, )
	draw.rectangle(cartcoord, outline="black")
	mystr = "number of particles"
	xv = draw.textsize(mystr)[0]/2.0
	cartcoord2 = ((cartcoord[0]+cartcoord[2])/2.0-xv, ys+crad*4 )
	draw.text(cartcoord2, "number of particles", fill="black")
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

def addRotatedText(im, text, where, rotation, color = "black", maxSize = None):
	"""
	stolen from http://mail.python.org/pipermail/image-sig/2000-July/001141.html
	"""
	anchor = (0.0,0.0)
	draw = ImageDraw.Draw(im)
	textsize = draw.textsize(text)
	del(draw)
	# do the math to figure out how big the text box will be after rotation
	rotationRadians = (math.pi/180.0) * rotation
	rotatedWidth = int(float(textsize[0]) * abs(math.cos(rotationRadians)) + float(textsize[1]) * abs(math.sin(rotationRadians)) + 0.5)
	rotatedHeight = int(float(textsize[0]) * abs(math.sin(rotationRadians)) + float(textsize[1]) * abs(math.cos(rotationRadians)) + 0.5)
	rotatedtextsize = (rotatedWidth, rotatedHeight)
	# make the text box big enough for the original text in any rotation
	if textsize[0] > textsize[1]:
		largetextsize = (textsize[0], textsize[0])
	else:
		largetextsize = (textsize[1], textsize[1])
	xOffset = int((float(largetextsize[0] - textsize[0])/2.0)+0.5)
	textIm = Image.new("L", largetextsize, (0))
	# draw a mask of the text unrotated
	draw = ImageDraw.Draw(textIm)
	draw.text((xOffset, (textIm.size[1]/2) - (textsize[1]/2)), text, fill="white")
	# rotate the text mask
	textIm = textIm.rotate(rotation)
	# crop it down to the real used area
	xOffset = int((float(textIm.size[0] - rotatedtextsize[0])/2.0) + 0.5)
	yOffset = int((float(textIm.size[1] - rotatedtextsize[1])/2.0) + 0.5)
	textIm = textIm.crop((xOffset, yOffset, xOffset + rotatedtextsize[0], yOffset + rotatedtextsize[1]))
	# fit it in MaxSize if specified and valid
	if maxSize != None and type(maxSize) == type(("tuple", "tuple")) and len(maxSize) == 2:
		if textIm.size[0] > maxSize[0] or textIm.size[1] > maxSize[1]:
			textIm.thumbnail(maxSize)
	# create an image mask the size of the whole image that you're putting the text on
	mask = Image.new("L", im.size, (0))
	# place the text mask in the proper place
	where = (where[0] - int(float(textIm.size[0])*anchor[0] + 0.5), where[1] - int(float(textIm.size[1])*anchor[1] + 0.5))
	mask.paste(textIm, where)
	del(textIm)
	# create an image the full size of the supplied image, in the color of the text you want to apply
	colorIm = Image.new(im.mode, im.size, color)
	# paste the color onto the image, using the text mask as a mask
	im.paste(colorIm, (0,0), mask)
	del(colorIm)
	del(mask)

	return im


if __name__ == "__main__":
	t0 = time.time()
	#radlist, anglelist, freqlist, freqgrid = getEulersForIteration(181, 4)
	radlist, anglelist, freqlist, freqgrid = getEulersForIteration(173, 12)
	makeImage(radlist,anglelist,freqlist,imgname="recon173.png")
	radlist, anglelist, freqlist, freqgrid = getEulersForIteration(158, 4)
	makeImage(radlist,anglelist,freqlist,imgname="recon158.png")
	#radlist, anglelist, freqlist, freqgrid = getEulersForIteration(158, 2)
	radlist, anglelist, freqlist, freqgrid = getEulersForIteration(118, 2)
	makeImage(radlist,anglelist,freqlist,imgname="recon118.png")
	radlist, anglelist, freqlist, freqgrid = getEulersForIteration(159, 1)
	makeImage(radlist,anglelist,freqlist,imgname="recon159.png")
	#freqmap = getEulersForIteration(158, 4)
	#makePlot(radlist,anglelist,freqlist,freqgrid)
	#makePlot(freqmap)
	apDisplay.printColor("Finished in "+apDisplay.timeString(time.time()-t0), "cyan")



