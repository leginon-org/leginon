#!/usr/bin/python -O

import MySQLdb
import math
import os
import numpy
import pyami.quietscipy
from scipy import ndimage
import Image
import ImageDraw
import ImageFont
import random
import time
import pprint
from appionlib import apDisplay
import sinedon


#===========
def getEulersForIteration(reconid, iteration=1):
	"""
	returns all classdata for a particular refinement iteration

	this does NOT use sinedon because it goes
	from taking < 1 min for this method
	to taking several hours with sinedon
	"""
	# connect
	dbconf = sinedon.getConfig('appiondata')
	db = MySQLdb.connect(**dbconf)
	# create a cursor
	cursor = db.cursor()


	t0 = time.time()
	query = (
		"SELECT pc.euler1, pc.euler2, pc.`thrown_out`, pc.`coran_keep` "
			+"FROM `ApParticleClassificationData` AS pc "
			+"LEFT JOIN `ApRefinementData` AS rd "
			+"ON pc.`REF|ApRefinementData|refinement` = rd.`DEF_id` "
			+"WHERE rd.`REF|ApRefinementRunData|refinementRun` = "+str(reconid)+" "
			+"AND rd.`iteration` = "+str(iteration)+" "
		)
	#print query
	print "querying for euler values at "+time.asctime()
	cursor.execute(query)
	numrows = int(cursor.rowcount)
	apDisplay.printColor("Found "+str(numrows)+" euler values", "cyan")
	result = cursor.fetchall()
	apDisplay.printMsg("Fetched data in "+apDisplay.timeString(time.time()-t0))

	# sort eulers into classes
	alldict, eulerdict, corandict = calcDictNative(result)
	db.close()

	return alldict, eulerdict, corandict

#===========
def freqListStat(freqlist):
	freqnumpy = numpy.asarray(freqlist, dtype=numpy.int32)
	print "min=",   ndimage.minimum(freqnumpy)
	print "max=",   ndimage.maximum(freqnumpy)
	print "mean=",  ndimage.mean(freqnumpy)
	print "stdev=", ndimage.standard_deviation(freqnumpy)
	#print "median=",ndimage.median(freqnumpy)

#===========
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

#===========
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

#===========
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

#===========
def polarToCart(rad, thrad):
	#thrad = thdeg*math.pi/180.0
	x = rad*math.cos(thrad)
	y = rad*math.sin(thrad)
	return x,y

#===========
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

#===========
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

#===========
def calcDictNative(points):
	""" SELECT e.euler1, e.euler2, pc.`thrown_out`, pc.`coran_keep` """
	alldict = {}
	eulerdict = {}
	corandict = {}
	for point in points:
		### convert data
		#print point
		rad = float(point[0])
		theta = float(point[1])
		thrownout = bool(point[2])
		corankeep = bool(point[3])
		key = ( "%.3f,%.3f" % (rad, theta))
		#print thrownout,corankeep,key

		### sort points
		if key in alldict:
			alldict[key] += 1
		else:
			alldict[key] = 0
		if thrownout is False:
			if key in eulerdict:
				eulerdict[key] += 1
			else:
				eulerdict[key] = 0
		if corankeep is True:
			if key in corandict:
				corandict[key] += 1
			else:
				corandict[key] = 0
	#import pprint
	#pprint.pprint( alldict)
	return alldict, eulerdict, corandict


#===========
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

#===========
def fillDataDict(radlist, anglelist, freqlist):
	"""
	Get min/max statistics on data lists
	"""
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
	if d['maxa'] > 330.0*math.pi/180.0:
		d['maxa'] = 2.0*math.pi
	d['rangea'] = d['maxa']-d['mina']

	radnumpy = numpy.asarray(radlist, dtype=numpy.float32)
	d['minr'] = float(ndimage.minimum(radnumpy))
	d['maxr'] = float(ndimage.maximum(radnumpy))
	d['ranger'] = d['maxr']-d['minr']

	xnumpy = radnumpy * numpy.cos(angnumpy - d['mina'])
	ynumpy = radnumpy * numpy.sin(angnumpy - d['mina'])
	d['minx'] = float(ndimage.minimum(xnumpy))
	d['maxx'] = float(ndimage.maximum(xnumpy))
	d['miny'] = float(ndimage.minimum(ynumpy))
	d['maxy'] = float(ndimage.maximum(ynumpy))
	d['rangex'] = d['maxx']-d['minx']
	d['rangey'] = d['maxy']-d['miny']

	return d

#===========
def makeTriangleImage(eulerdict, imgname="temp.png",
		imgdim=640, crad=8, frame=30):
	"""
	Creates the classic triangle euler plot
	"""

	### convert to lists
	radlist   = []
	anglelist = []
	freqlist  = []
	for key,val in eulerdict.items():
		rad,ang = map(float, key.split(','))
		radlist.append(rad*math.pi/180.0*math.pi/180.0)
		anglelist.append(ang*math.pi/180.0*math.pi/180.0)
		freqlist.append(val)

	### find min/max data
	d = fillDataDict(radlist, anglelist, freqlist)
	#pprint.pprint(d)

	img = Image.new("RGB", (imgdim, imgdim), color="#ffffff")
	draw = ImageDraw.Draw(img)

	drawAxes(draw, imgdim, crad, img, d)
	drawLegend(draw, imgdim, crad, d['minf'], d['maxf'])
	for key,freq in eulerdict.items():
		#frequency
		fgray = freqToColor(freq, d['maxf'], d['rangef'])
		fcolor = grayToColor(fgray)

		#direct polar
		rad, ang = map(float, key.split(','))
		rad *= (math.pi/180.0)**2
		ang *= (math.pi/180.0)**2
		#polar -> cartesian
		x, y = polarToCart(rad, ang-d['mina'])
		ys = float(imgdim-2*frame)*(x-d['minx'])/d['rangex']+frame
		xs = float(imgdim-2*frame)*(y-d['miny'])/d['rangey']+frame
		cartcoord = (xs-crad, ys-crad, xs+crad, ys+crad)

		draw.ellipse(cartcoord, fill=fcolor)
	try:
		img.save(imgname, "PNG")
		apDisplay.printMsg("save euler image to file: "+imgname)
	except:
		apDisplay.printWarning("could not save file: "+imgname)

	return

#===========
def makePolarImage(eulerdict, imgname="temp.png",
		imgdim=640, crad=8, frame=60):
	"""
	make a round polar plot of euler angles
	"""

	### convert to lists
	radlist   = []
	anglelist = []
	freqlist  = []
	for key,val in eulerdict.items():
		rad,ang = map(float, key.split(','))
		radlist.append(rad*math.pi/180.0)
		anglelist.append(ang*math.pi/180.0)
		freqlist.append(val)

	### find min/max data
	d = fillDataDict(radlist, anglelist, freqlist)
	if d is None:
		apDisplay.printWarning("No rejected particles found!")
		return
	#pprint.pprint(d)

	img = Image.new("RGB", (imgdim, imgdim), color="#ffffff")
	draw = ImageDraw.Draw(img)

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
		xn = (x - d['minx'])/float(d['rangex'])
		yn = (y - d['miny'])/float(d['rangey'])
		xs = float(imgdim-2*frame)*xn+frame
		ys = float(imgdim-3*frame)*yn+2*frame
		if rad > 10.98:
			print round(rad,2), round(ang*180.0/math.pi,1), "\t-->", round(x,2), round(y,2), "\t-->", round(xn,2), round(yn,2)
		#print xs, ys
		cartcoord = (xs-crad, ys-crad, xs+crad, ys+crad)

		draw.ellipse(cartcoord, fill=fcolor)
	## end loop

	drawPolarAxes(draw, imgdim, frame, img, d)
	try:
		img.save(imgname, "PNG")
		apDisplay.printMsg("save euler image to file: "+imgname)
	except:
		apDisplay.printWarning("could not save file: "+imgname)

	return

#===========
def freqToColor(freq, maxf, rangef):
	fgray = 255.0*((maxf-freq)/rangef)**2
	return fgray

#===========
def drawAxes(draw, imgdim, crad, img, d):

	#pprint.pprint(d)
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
	txt = str(round(d['mina']*60.0*180.0/math.pi,1))
	shiftx = draw.textsize(txt)[0]/2.0
	shifty = draw.textsize(txt)[1]/2.0
	coord = (start, end)
	draw.text(coord, txt, fill="black")
	txt = str(round(d['maxa']*60.0*180.0/math.pi,1))
	shiftx = draw.textsize(txt)[0]
	shifty = draw.textsize(txt)[1]/2.0
	coord = (end-shiftx, end)
	draw.text(coord, txt, fill="black")

#===========
def drawPolarAxes(draw, imgdim, frame, img, d, overmult=1.02):
	#Axes 1
	x, y = polarToCart(d['minr'], 0.0)
	xn = (x - d['minx'])/float(d['rangex'])
	yn = (y - d['miny'])/float(d['rangey'])
	xs = float(imgdim-2*frame)*xn+frame
	ys = float(imgdim-3*frame)*yn+2*frame

	x, y = polarToCart(overmult*d['maxr'], 0.0)
	xn = (x - d['minx'])/float(d['rangex'])
	yn = (y - d['miny'])/float(d['rangey'])
	xf = float(imgdim-2*frame)*xn+frame
	yf = float(imgdim-3*frame)*yn+2*frame

	coord = (xs, ys, xf, yf)
	draw.line(coord, fill="black", width=2)
	#Axes 2
	#required integer degrees
	maxang = math.ceil(d['rangea']*180.0/math.pi)*math.pi/180.0
	x, y = polarToCart(d['minr'], maxang)
	xn = (x - d['minx'])/float(d['rangex'])
	yn = (y - d['miny'])/float(d['rangey'])
	xs = float(imgdim-2*frame)*xn+frame
	ys = float(imgdim-3*frame)*yn+2*frame

	x, y = polarToCart(overmult*d['maxr'], maxang)
	xn = (x - d['minx'])/float(d['rangex'])
	yn = (y - d['miny'])/float(d['rangey'])
	xf = float(imgdim-2*frame)*xn+frame
	yf = float(imgdim-3*frame)*yn+2*frame

	coord = (xs, ys, xf, yf)
	#print coord
	draw.line(coord, fill="black", width=2)

	#Outer arc circle
	x = -1.0*overmult*d['maxr']
	y = -1.0*overmult*d['maxr']
	xn = (x - d['minx'])/float(d['rangex'])
	yn = (y - d['miny'])/float(d['rangey'])
	xs = float(imgdim-2*frame)*xn+frame
	ys = float(imgdim-3*frame)*yn+2*frame

	x = overmult*d['maxr']
	y = overmult*d['maxr']
	xn = (x - d['minx'])/float(d['rangex'])
	yn = (y - d['miny'])/float(d['rangey'])
	xf = float(imgdim-2*frame)*xn+frame
	yf = float(imgdim-3*frame)*yn+2*frame

	#coord = (frame, frame, float(imgdim-frame), float(imgdim-frame))
	coord = (int(xs), int(ys), int(xf), int(yf))
	#coord = float(imgdim-2*frame)*numpy.array([0.0, 0.0, 1.0, 1.0])+frame
	arcmin = 0
	arcmax = int(math.ceil(180.0*d['rangea']/math.pi))
	#print coord, arcmin, arcmax
	#pprint.pprint(d)
	draw.arc(coord, arcmin, arcmax, "black")
	#draw.ellipse(coord, outline="black")

	#return

	#Min/Max Numbers for Longitude / Azimuthal
	txt = str(round(d['mina']*180.0/math.pi,1))
	shiftx = draw.textsize(txt)[0]/2.0
	shifty = draw.textsize(txt)[1]/2.0
	x, y = polarToCart(overmult*d['maxr'], 0.0)
	xn = (x - d['minx'])/float(d['rangex'])
	yn = (y - d['miny'])/float(d['rangey'])
	xf = float(imgdim-2*frame)*xn+frame
	yf = float(imgdim-3*frame)*yn+2*frame
	coord = (xf+5, yf-shifty)
	draw.text(coord, txt, fill="black")

	if(d['rangea'] < 2*math.pi):
		txt = str(round(d['maxa']*180.0/math.pi,1))
		shiftx = draw.textsize(txt)[0]
		shifty = draw.textsize(txt)[1]/2.0

		maxang = math.ceil(d['rangea']*180.0/math.pi)*math.pi/180.0
		x, y = polarToCart(overmult*d['maxr'], maxang)
		xn = (x - d['minx'])/float(d['rangex'])
		yn = (y - d['miny'])/float(d['rangey'])
		xf = float(imgdim-2*frame)*xn+frame
		yf = float(imgdim-3*frame)*yn+2*frame
		coord = (xf+5, yf+shifty)
		#addRotatedText(img, txt, coord, 90.0-maxang*180.0/math.pi, color="black")
		draw.text(coord, txt, fill="black")

	return
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

	return

#===========
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

#===========
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

#===========
def colorTupleToHex(r, g, b, scale=1):
	#print r,g,b
	ir = int(r*scale)
	ig = int(g*scale)
	ib = int(b*scale)
	hexcode = str(hex(ir*256**2 + ig*256 + ib))[2:]
	hexstr = "#"+apDisplay.leftPadString(hexcode, n=6, fill='0')
	return hexstr

#===========
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

#===========
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
	where = (int(where[0] - float(textIm.size[0])*anchor[0] + 0.5), int(where[1] - float(textIm.size[1])*anchor[1] + 0.5))
	mask.paste(textIm, where)
	del(textIm)
	# create an image the full size of the supplied image, in the color of the text you want to apply
	colorIm = Image.new(im.mode, im.size, color)
	# paste the color onto the image, using the text mask as a mask
	im.paste(colorIm, (0,0), mask)
	del(colorIm)
	del(mask)

	return im

#===========
def createEulerImages(recon=239, iternum=1, path=".", coran=False):
	### get data from database
	alldict, eulerdict, corandict = getEulersForIteration(recon, iternum)

	### create image in triangle form
	triangfile = os.path.join(path, "eulerTriangle-"+str(recon)+"_"+str(iternum)+".png")
	makeTriangleImage(eulerdict, imgname=triangfile)

	### create image in polar form
	polarfile = os.path.join(path, "eulerPolar-"+str(recon)+"_"+str(iternum)+".png")
	makePolarImage(eulerdict, imgname=polarfile)

	### create image of rejected particles
	rejectfile = os.path.join(path, "eulerPolarReject-"+str(recon)+"_"+str(iternum)+".png")
	rejectdict = alldict
	for key,val in eulerdict.items():
		rejectdict[key] -= val
	makePolarImage(rejectdict, imgname=rejectfile)

	if coran is True and corandict:
		### create image of coran keep particle
		coranfile = os.path.join(path, "eulerPolarCoran-"+str(recon)+"_"+str(iternum)+".png")
		makePolarImage(corandict, imgname=coranfile)

		### create image of coran difference
		corandiffdict = eulerdict
		for key,val in corandict.items():
			corandiffdict[key] -= val
		corandifffile = os.path.join(path, "eulerPolarCoranDiff-"+str(recon)+"_"+str(iternum)+".png")
		makePolarImage(corandiffdict, imgname=corandifffile)

#===========
#===========
if __name__ == "__main__":
	t0 = time.time()
	#createEulerImages(239, 4)  ## small groEL
	#createEulerImages(212, 4)  ## icos virus
	#createEulerImages(212, 8)  ## icos virus
	#createEulerImages(231, 3)  ## c6 virus tail
	#createEulerImages(231, 9)  ## c6 virus tail
	#createEulerImages(239, 8)  ## med groEL
	#createEulerImages(217, 1)  ## small assymmetric
	#createEulerImages(217, 12)  ## big assymmetric
	#createEulerImages(239, 20)  ## large groEL
	#createEulerImages(181, 4)
	#createEulerImages(173, 12) ## huge groEL, broken
	#createEulerImages(158, 1)  ## small assymmetric
	#createEulerImages(118, 2)
	#createEulerImages(159, 1)  ## small assymmetric
	#createEulerImages(158, 4, ".", True)
	#createEulerImages(110, 16, ".", True)
	for i in range(13,21):
		print i
		createEulerImages(110, i, ".", True)

	### coran
	#createEulerImages(296, 2, ".", True)
	#createEulerImages(305, 12, ".", True)
	apDisplay.printColor("Finished in "+apDisplay.timeString(time.time()-t0), "cyan")




