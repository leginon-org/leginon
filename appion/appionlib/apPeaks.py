
#pythonlib
import os
import math
import numpy
#PIL
import Image
import ImageDraw
#import ImageOps
#appion
import apImage
import apFile
import apDisplay
import apParam
#leginon
from pyami import imagefun

def findPeaks(imgdict, maplist, params, maptype="ccmaxmap"):
	peaktreelist = []
	count = 0

	imgname = imgdict['filename']
	mapdir = os.path.join(params['rundir'], "maps")
	thresh =    float(params["thresh"])
	bin =       int(params["bin"])
	diam =      float(params["diam"])
	apix =      float(params["apix"])
	olapmult =  float(params["overlapmult"])
	maxpeaks =  int(params["maxpeaks"])
	maxthresh = params["maxthresh"]
	maxsizemult = float(params["maxsize"])
	peaktype =  params["peaktype"]
	msg =       not params['background']
	pixdiam =   diam/apix/float(bin)
	pixrad =    diam/apix/2.0/float(bin)
	tmpldbid =  None
	mapdiam =   None

	for imgmap in maplist:
		count += 1

		if 'templateIds' in params:
			#template correlator
			tmpldbid =  params['templateIds'][count-1]
		elif 'diamarray' in params:
			#dogpicker
			mapdiam = params['diamarray'][count-1]

		#find peaks
		peaktree = findPeaksInMap(imgmap, thresh, pixdiam, count, olapmult, 
			maxpeaks, maxsizemult, msg, tmpldbid, mapdiam, bin=bin, peaktype=peaktype)

		#remove border peaks
		peaktree = removeBorderPeaks(peaktree, pixdiam, imgdict['image'].shape[1], imgdict['image'].shape[0])

		#write map to jpeg with highlighted peaks
		outfile = os.path.join(mapdir, imgname+"."+maptype+str(count)+".jpg")
		createPeakMapImage(peaktree, imgmap, outfile, pixrad, bin, msg)

		#write pikfile
		peakTreeToPikFile(peaktree, imgname, count, params['rundir'])

		#append to complete list of peaks
		peaktreelist.append(peaktree)

	peaktree = mergePeakTrees(imgdict, peaktreelist, params, msg)

	#max threshold
	if maxthresh is not None:
		precount = len(peaktree)
		peaktree = maxThreshPeaks(peaktree, maxthresh)
		postcount = len(peaktree)
		#if precount != postcount:
		apDisplay.printMsg("Filtered %d particles above threshold %.2f"%(precount-postcount,maxthresh))

	return peaktree

def printPeakTree(peaktree):
	print "peaktree="
	for i,p in enumerate(peaktree):
		print "  ",i,":",int(p['xcoord']),int(p['ycoord'])

def findPeaksInMap(imgmap, thresh, pixdiam, count=1, olapmult=1.5, maxpeaks=500, 
		maxsizemult=1.0, msg=True, tmpldbid=None, mapdiam=None, bin=1, peaktype="maximum"):

	pixrad = pixdiam/2.0

	#MAXPEAKSIZE ==> 1x AREA OF PARTICLE
	partarea = 4*math.pi*(pixrad**2)
	maxsize = int(round(maxsizemult*partarea,0))+1

	#VARY PEAKS FROM STATS
	if msg is True:
		varyThreshold(imgmap, thresh, maxsize)

	#GET FINAL PEAKS
	blobtree, percentcov = findBlobs(imgmap, thresh, maxsize=maxsize,
		maxpeaks=maxpeaks, summary=msg)
	#convert
	peaktree = convertBlobsToPeaks(blobtree, bin, tmpldbid, count, mapdiam, peaktype)

	#warnings
	if msg is True:
		apDisplay.printMsg("Found "+str(len(peaktree))+" peaks ("+str(percentcov)+"% coverage)")
	if(percentcov > 25):
		apDisplay.printWarning("thresholding covers more than 25% of image;"
			+" you should increase the threshold")

	#remove overlaps
	cutoff = olapmult*pixrad #1.5x particle radius in pixels
	removeOverlappingPeaks(peaktree, cutoff, msg)

	#max peaks
	if(len(peaktree) > maxpeaks):
		#orders peaks from biggest to smallest
		peaktree.sort(_peakCompareBigSmall)
		apDisplay.printWarning("more than maxpeaks ("+str(maxpeaks)+" peaks), selecting only top peaks")
		apDisplay.printMsg("Corr best=%.3f, worst=%.3f"
			%(peaktree[0]['correlation'], peaktree[len(peaktree)-1]['correlation']))
		peaktree = peaktree[0:maxpeaks]

	return peaktree


def createPeakMapImage(peaktree, ccmap, imgname="peakmap.jpg", pixrad="10.0", bin=1.0, msg=True, masxthresh=None):
	### drop all values below zero
	ccmap = numpy.where(ccmap<0, 0.0, ccmap)

	### create bar at bottom
	ccshape = (ccmap.shape[0]+50, ccmap.shape[1])
	bigmap = numpy.resize(ccmap, ccshape)
	bigmap[ccshape[0]+1:,:] = 0
	minval = ccmap.min()
	maxval = ccmap.max()

	#print minval,maxval
	grad = numpy.linspace(minval, maxval, bigmap.shape[1])
	bigmap[ccmap.shape[0]:bigmap.shape[0],:] = grad
	#print ccmap.shape, "-->",  bigmap.shape

	image = apImage.arrayToImage(bigmap, stdevLimit=8.0)
	image = image.convert("RGB")

	### color stuff below threshold
	#threshmap = imagefun.threshold(ccmap, threshold)
	#filtmap = numpy.where(threshmap > 0, -3.0, ccmap)
	#imagefilt = apImage.arrayToImage(filtmap)
	#imagefilt = imagefilt.convert("RGB")
	#imagefilt = ImageOps.colorize(imagefilt, "black", "green")
	#image = Image.blend(image, imagefilt, 0.2) 

	### color peaks in map
	image2 = image.copy()
	peakdraw = ImageDraw.Draw(image2)
	drawPeaks(peaktree, peakdraw, bin, pixrad, fill=True)
	### add text
	image3 = image.copy()
	textdraw = ImageDraw.Draw(image3)
	addMinMaxTextToMap(textdraw, bigmap.shape[1], minval, maxval)
	### merge
	image = Image.blend(image, image3, 0.9)
	image = Image.blend(image, image2, 0.2)

	if msg is True:
		apDisplay.printMsg("writing summary JPEG: "+imgname)
	image.save(imgname, "JPEG", quality=80)


def addMinMaxTextToMap(draw, imgdim, minval, maxval):
	### add text
	#print "adding text"
	midval = (maxval + minval)/2.0
	midlval = (maxval + minval)/4.0
	midrval = 3.0*(maxval + minval)/4.0
	crad = 10
	start = 2*crad
	midl = imgdim/4
	mid = imgdim/2
	midr = 3*imgdim/4
	end = imgdim - 2*crad
	### left
	txt = str(round(minval,3))
	shiftx = draw.textsize(txt)[0]/2.0
	shifty = draw.textsize(txt)[1]/2.0
	coord = (start-shiftx, end+40)
	draw.text(coord, txt, fill="white")
	### mid left
	txt = str(round(midlval,3))
	shiftx = draw.textsize(txt)[0]/2.0
	shifty = draw.textsize(txt)[1]/2.0
	coord = (midl-shiftx, end+40)
	draw.text(coord, txt, fill="blue")
	### mid
	txt = str(round(midval,3))
	shiftx = draw.textsize(txt)[0]/2.0
	shifty = draw.textsize(txt)[1]/2.0
	coord = (mid-shiftx, end+40)
	draw.text(coord, txt, fill="blue")
	### mid right
	txt = str(round(midrval,3))
	shiftx = draw.textsize(txt)[0]/2.0
	shifty = draw.textsize(txt)[1]/2.0
	coord = (midr-shiftx, end+40)
	draw.text(coord, txt, fill="blue")
	### right
	txt = str(round(maxval,3))
	shiftx = draw.textsize(txt)[0]/2.0
	shifty = draw.textsize(txt)[1]/2.0
	coord = (end-shiftx, end+40)
	draw.text(coord, txt, fill="black")
	return


def maxThreshPeaks(peaktree, maxthresh):
	newpeaktree = []
	for i in range(len(peaktree)):
		if peaktree[i]['correlation'] < maxthresh:
			newpeaktree.append(peaktree[i])
	return newpeaktree

def mergePeakTrees(imgdict, peaktreelist, params, msg=True):
	if msg is True:
		apDisplay.printMsg("Merging individual picked peaks into one set")
	bin =         int(params["bin"])
	diam =        float(params["diam"])
	apix =        float(params["apix"])
	maxpeaks =    int(params["maxpeaks"])
	olapmult =    float(params["overlapmult"])
	pixrad =      diam/apix/2.0
	binpixrad =   diam/apix/2.0/float(bin)
	imgname =     imgdict['filename']
	doubles =     params['doubles']

	#PUT ALL THE PEAKS IN ONE ARRAY
	mergepeaktree = []
	for peaktree in peaktreelist:
		mergepeaktree.extend(peaktree)
	#REMOVE OVERLAPPING PEAKS
	cutoff   = olapmult*pixrad	#1.5x particle radius in pixels
	mergepeaktree = removeOverlappingPeaks(mergepeaktree, cutoff, msg, doubles)

	bestpeaktree = []
	for peaktree in peaktreelist:
		for peakdict in peaktree:
			if peakdict in mergepeaktree:
				bestpeaktree.append(peakdict)

	if(len(bestpeaktree) > maxpeaks):
		apDisplay.printWarning("more than maxpeaks ("+str(maxpeaks)+" peaks), selecting only top peaks")
		#orders peaks from biggest to smallest
		bestpeaktree.sort(_peakCompareBigSmall)
		apDisplay.printMsg("Corr best=%.3f, worst=%.3f"
			%(peaktree[0]['correlation'], peaktree[len(peaktree)-1]['correlation']))
		bestpeaktree = bestpeaktree[0:maxpeaks]

	peakTreeToPikFile(bestpeaktree, imgname, 'a', params['rundir'])

	return bestpeaktree

def removeOverlappingPeaks(peaktree, cutoff, msg=True, doubles=False):
	#distance in pixels for two peaks to be too close together
	if msg is True:
		apDisplay.printMsg("overlap distance cutoff: "+str(round(cutoff,1))+" pixels")
	cutsq = cutoff**2 + 1

	initpeaks = len(peaktree)
	#orders peaks from smallest to biggest
	peaktree.sort(_peakCompareSmallBig)
	doublepeaktree = []
	i=0
	while i < len(peaktree):
		j = i+1
		while j < len(peaktree):
			distsq = peakDistSq(peaktree[i], peaktree[j])
			if(distsq < cutsq):
				doublepeaktree.append(peaktree[j])
				del peaktree[i]
				i -= 1
				j = len(peaktree)
			j += 1
		i += 1

	if doubles is True:
		peaktree = removeOverlappingPeaks(doublepeaktree, cutoff, False, False)

	numpeaks = len(peaktree)
	if msg is True:
		apDisplay.printMsg("kept "+str(numpeaks)+" non-overlapping peaks of "
			+str(initpeaks)+" total peaks")

	return peaktree

def removeBorderPeaks(peaktree, diam, xdim, ydim):
	#remove peaks that are less than 1/2 diam from a border
	r=diam/2
	xymin=r
	xmax=xdim-r
	ymax=ydim-r
	newpeaktree=[]
	for peak in peaktree:
		x = peak['xcoord']
		y = peak['ycoord']
		if x>xymin and y>xymin and x<xmax and y<ymax:
			newpeaktree.append(peak)
	return newpeaktree
	
def _peakCompareSmallBig(a, b):
	if float(a['correlation']) > float(b['correlation']):
		return 1
	else:
		return -1

def _peakCompareBigSmall(a, b):
	if float(a['correlation']) < float(b['correlation']):
		return 1
	else:
		return -1

def peakDistSq(a,b):
	row1 = a['ycoord']
	col1 = a['xcoord']
	row2 = b['ycoord']
	col2 = b['xcoord']
	return (row1-row2)**2 + (col1-col2)**2

def varyThreshold(ccmap, threshold, maxsize):
	for i in numpy.array([-0.05,-0.02,0.00,0.02,0.05]):
		thresh      = threshold + float(i)
		blobtree, percentcov = findBlobs(ccmap, thresh, maxsize=maxsize)
		tstr  = "%.2f" % thresh
		lbstr = "%4d" % len(blobtree)
		pcstr = "%.2f" % percentcov
		if(thresh == threshold):
			apDisplay.printMsg("*** selected threshold: "+tstr+" gives "
				+lbstr+" peaks ("+pcstr+"% coverage ) ***")
		else:
			apDisplay.printMsg("    varying threshold: "+tstr+" gives "
				+lbstr+" peaks ("+pcstr+"% coverage )")

def convertListToPeaks(peaks, params):
	if peaks is None or len(peaks) == 0:
		return []
	bin = params['bin']
	peaktree = []
	peak = {}
	for i in range(peaks.shape[0]):
		peak['xcoord'] = int(round( float(peaks[i,0]) * float(bin) ))
		peak['ycoord'] = int(round( float(peaks[i,1]) * float(bin) ))
		peak['peakarea'] = 1
		peaktree.append(peak.copy())
	return peaktree

def convertBlobsToPeaks(blobtree, bin=1, tmpldbid=None, tmplnum=None, diam=None, peaktype="maximum"):
	peaktree = []
	#if tmpldbid is not None:
	#	print "TEMPLATE DBID:",tmpldbid
	for blobclass in blobtree:
		peakdict = {}
		if peaktype == "maximum":
			peakdict['ycoord']      = int(round( float(blobclass.stats['maximum_position'][0])*float(bin) ))
			peakdict['xcoord']      = int(round( float(blobclass.stats['maximum_position'][1])*float(bin) ))
		else:
			peakdict['ycoord']      = int(round( float(blobclass.stats['center'][0])*float(bin) ))
			peakdict['xcoord']      = int(round( float(blobclass.stats['center'][1])*float(bin) ))
		peakdict['correlation'] = blobclass.stats['mean']
		peakdict['peakmoment']  = blobclass.stats['moment']
		peakdict['peakstddev']  = blobclass.stats['stddev']
		peakdict['peakarea']    = blobclass.stats['n']
		peakdict['tmplnum']     = tmplnum
		peakdict['template']    = tmpldbid
		peakdict['diameter']    = diam
		peaktree.append(peakdict)
	return peaktree

def findBlobs(ccmap, thresh, maxsize=500, minsize=1, maxpeaks=1500, border=10, 
	  maxmoment=6.0, elim= "highest", summary=False):
	"""
	calls leginon's imagefun.find_blobs
	"""
	totalarea = (ccmap.shape)[0]*(ccmap.shape)[1]
	ccthreshmap = imagefun.threshold(ccmap, thresh)
	percentcov  =  round(100.0*float(ccthreshmap.sum())/float(totalarea),2)
	#imagefun.find_blobs(image,mask,border,maxblobs,maxblobsize,minblobsize,maxmoment,method)
	if percentcov > 15:
		apDisplay.printWarning("too much coverage in threshold: "+str(percentcov))
		return [],percentcov
	#apImage.arrayToJpeg(ccmap, "dogmap2.jpg")
	#apImage.arrayToJpeg(ccthreshmap, "threshmap2.jpg")
	blobtree = imagefun.find_blobs(ccmap, ccthreshmap, border, maxpeaks*4,
	  maxsize, minsize, maxmoment, elim, summary)
	return blobtree, percentcov

def peakTreeToPikFile(peaktree, imgname, tmpl, rundir="."):
	outpath = os.path.join(rundir, "pikfiles")
	apParam.createDirectory(outpath, warning=False)
	outfile = os.path.join(outpath, imgname+"."+str(tmpl)+".pik")
	apFile.removeFile(outfile, warn=True)
	#WRITE PIK FILE
	f=open(outfile, 'w')
	f.write("#filename x y mean stdev corr_coeff peak_size templ_num angle moment diam\n")
	for peakdict in peaktree:
		row = peakdict['ycoord']
		col = peakdict['xcoord']
		if 'corrcoeff' in peakdict:
			rho = peakdict['corrcoeff']
		else:
			rho = 1.0
		size = peakdict['peakarea']
		mean_str = "%.4f" % peakdict['correlation']
		std_str = "%.4f" % peakdict['peakstddev']
		mom_str = "%.4f" % peakdict['peakmoment']
		if peakdict['diameter'] is not None:
			diam_str = "%.2f" % peakdict['diameter']
		else:
			diam_str = "0"
		if 'template' in peakdict:
			tmplnum = peakdict['template']
		else:
			tmplnum = tmpl
		#filename x y mean stdev corr_coeff peak_size templ_num angle moment
		out = imgname+".mrc "+str(int(col))+" "+str(int(row))+ \
			" "+mean_str+" "+std_str+" "+str(rho)+" "+str(int(size))+ \
			" "+str(tmplnum)+" 0 "+mom_str+" "+diam_str
		f.write(str(out)+"\n")
	f.close()

def createPeakJpeg(imgdata, peaktree, params, procimgarray=None):
	if 'templatelist' in params:
		count =   len(params['templatelist'])
	else: count = 1
	bin =     int(params["bin"])
	diam =    float(params["diam"])
	apix =    float(params["apix"])
	binpixrad  = diam/apix/2.0/float(bin)
	imgname = imgdata['filename']

	jpegdir = os.path.join(params['rundir'],"jpgs")
	apParam.createDirectory(jpegdir, warning=False)

	if params['uncorrected']:
		imgarray = apImage.correctImage(imgdata, params)
	else:
		imgarray = imgdata['image']

	if procimgarray is not None:
		#instead of re-processing image use one that is already processed...
		imgarray = procimgarray
	else:
		imgarray = apImage.preProcessImage(imgarray, bin=bin, planeReg=False, params=params)

	outfile = os.path.join(jpegdir, imgname+".prtl.jpg")
	msg = not params['background']
	subCreatePeakJpeg(imgarray, peaktree, binpixrad, outfile, bin, msg)

	return

def subCreatePeakJpeg(imgarray, peaktree, pixrad, imgfile, bin=1, msg=True):
	image = apImage.arrayToImage(imgarray)
	image = image.convert("RGB")
	image2 = image.copy()
	draw = ImageDraw.Draw(image2)
	if len(peaktree) > 0:
		drawPeaks(peaktree, draw, bin, pixrad)
	if msg is True:
		apDisplay.printMsg("writing peak JPEG: "+imgfile)
	image = Image.blend(image, image2, 0.9) 
	image.save(imgfile, "JPEG", quality=95)

def createTiltedPeakJpeg(imgdata1, imgdata2, peaktree1, peaktree2, params, procimg1=None, procimg2=None):
	if 'templatelist' in params:
		count =   len(params['templatelist'])
	else: count = 1
	bin =     int(params["bin"])
	diam =    float(params["diam"])
	apix =    float(params["apix"])
	binpixrad  = diam/apix/2.0/float(bin)
	imgname1 = imgdata1['filename']
	imgname2 = imgdata2['filename']

	jpegdir = os.path.join(params['rundir'],"jpgs")
	apParam.createDirectory(jpegdir, warning=False)

	if procimg1 is not None:
		imgarray1 = procimg1
	else:
		imgarray1 = apImage.preProcessImage(imgdata1['image'], bin=bin, planeReg=False, params=params)
	if procimg2 is not None:
		imgarray2 = procimg2
	else:
		imgarray2 = apImage.preProcessImage(imgdata2['image'], bin=bin, planeReg=False, params=params)
	imgarray = numpy.hstack((imgarray1,imgarray2))

	image = apImage.arrayToImage(imgarray)
	image = image.convert("RGB")
	image2 = image.copy()
	draw = ImageDraw.Draw(image2)
	#import pprint
	if len(peaktree1) > 0:
		#pprint.pprint(peaktree1)
		drawPeaks(peaktree1, draw, bin, binpixrad)
	if len(peaktree2) > 0:
		peaktree2adj = []
		for peakdict in peaktree2:
			peakdict2adj = {}
			#pprint.pprint(peakdict)
			peakdict2adj['xcoord'] = peakdict['xcoord'] + imgdata1['image'].shape[1]
			peakdict2adj['ycoord'] = peakdict['ycoord']
			peakdict2adj['peakarea'] = 1
			peakdict2adj['tmplnum'] = 2
			peaktree2adj.append(peakdict2adj.copy())
		#pprint.pprint(peaktree2adj)
		drawPeaks(peaktree2adj, draw, bin, binpixrad)
	image = Image.blend(image, image2, 0.9) 

	outfile1 = os.path.join(jpegdir, imgname1+".prtl.jpg")
	apDisplay.printMsg("writing peak JPEG: "+outfile1)
	image.save(outfile1, "JPEG", quality=95)
	outfile2 = os.path.join(jpegdir, imgname2+".prtl.jpg")
	apDisplay.printMsg("writing peak JPEG: "+outfile2)
	image.save(outfile2, "JPEG", quality=95)

	return

def drawPeaks(peaktree, draw, bin, binpixrad, circmult=1.0, numcircs=None, circshape="circle", fill=False):
	"""	
	Takes peak list and draw circles around all the peaks
	"""
	circle_colors = [ \
		"#ff4040","#3df23d","#3d3df2", \
		"#f2f23d","#3df2f2","#f23df2", \
		"#f2973d","#3df297","#973df2", \
		"#97f23d","#3d97f2","#f23d97", ]
	"""	
	Order: 	Red, Green, Blue, Yellow, Cyan, Magenta,
		Orange, Teal, Purple, Lime-Green, Sky-Blue, Pink
	"""
	if numcircs is None and fill is False:
		numcircs = int( round(binpixrad/8.0,0) )+1
	elif fill is True:
		numcircs = 1
	#CIRCLE SIZE:
	ps=float(circmult*binpixrad) #1.5x particle radius

	#00000000 1 2 3333 44444 5555555555 666666666 777777777
	#filename x y mean stdev corr_coeff peak_size templ_num angle moment
	for peakdict in peaktree:
		x1=float(peakdict['xcoord'])/float(bin)
		y1=float(peakdict['ycoord'])/float(bin)
		if 'tmplnum' in peakdict and peakdict['tmplnum'] is not None:
			#GET templ_num
			num = int(peakdict['tmplnum']-1)%12
		elif 'template' in peakdict and peakdict['template'] is not None:
			#GET templ_dbid
			num = int(peakdict['template'])%12
		elif 'peakarea' in peakdict and peakdict['peakarea'] > 1:
			#GET templ_num
			num = int(peakdict['peakarea']*255)%12
		else:
			num = 0
		#Draw (numcircs) circles of size (circmult*binpixrad)
		for count in range(numcircs):
			tps = ps + count
			coord = (x1-tps, y1-tps, x1+tps, y1+tps)
			if circshape is "square":
				if fill is True:
					draw.rectangle(coord,fill=circle_colors[num])
				else:
					draw.rectangle(coord,outline=circle_colors[num])
			else:
				if fill is True:
					draw.ellipse(coord,fill=circle_colors[num])
				else:
					draw.ellipse(coord,outline=circle_colors[num])
	return 
