
#pythonlib
import os
import math
import numarray
import numarray.nd_image as nd_image
#PIL
import Image
import ImageDraw
import ImageOps
#appion
import apImage
import apDisplay
import apParam
#leginon
import imagefun


def findPeaks(imgdict, ccmaplist, params, maptype="ccmaxmap"):

	peaktreelist = []
	count = 0
	for ccmap in ccmaplist:
		count += 1
		peaktree = findPeaksInMap(ccmap, imgdict, count, params, maptype)
		peaktreelist.append(peaktree)

	peaktree = mergePeakTrees(imgdict, peaktreelist, params)

	return peaktree

def findPeaksInMap(ccmap, imgdict, tmplnum, params, maptype):
	threshold = float(params["thresh"])
	bin =       int(params["bin"])
	diam =      float(params["diam"])
	apix =      float(params["apix"])
	olapmult =  float(params["overlapmult"])
	maxpeaks =  int(params["maxpeaks"])
	imgname =   imgdict['filename']
	pixrad =    diam/apix/2.0
	binpixrad = diam/apix/2.0/float(bin)
	if 'ogTmpltInfo' in params:
		tmpldbid =  params['ogTmpltInfo'][tmplnum-1].dbid
	else:
		tmpldbid = None
	mapdir = os.path.join(params['rundir'],maptype+"s")

	#MAXPEAKSIZE ==> 1x AREA OF PARTICLE
	maxsize =   int(round(math.pi*(binpixrad**2),0))+1

	#VARY PEAKS FROM STATS
	varyThreshold(ccmap, threshold, maxsize)
	#GET FINAL PEAKS
	blobtree, percentcov = findBlobs(ccmap, threshold, maxsize=maxsize, maxpeaks=maxpeaks, summary=True)
	peaktree = convertBlobsToPeaks(blobtree, tmpldbid, tmplnum, bin)
	print "Template "+str(tmplnum)+": Found",len(peaktree),"peaks ("+\
		str(percentcov)+"% coverage)"
	if(percentcov > 10):
		apDisplay.printWarning("thresholding covers more than 10% of image; you should increase the threshold")

	cutoff = olapmult*pixrad #1.5x particle radius in pixels
	removeOverlappingPeaks(peaktree, cutoff)

	if(len(peaktree) > maxpeaks):
		apDisplay.printWarning("more than maxpeaks ("+str(maxpeaks)+" peaks), selecting only top peaks")
		peaktree.sort(_peakCompare)
		peaktree = peaktree[0:maxpeaks]
	else:
		peaktree.sort(_peakCompare)

	apParam.createDirectory(mapdir, warning=False)

	image = apImage.arrayToImage(ccmap)
	image = image.convert("RGB")

	### color stuff below threshold
	#threshmap = imagefun.threshold(ccmap, threshold)
	#filtmap = numarray.where(threshmap > 0, -3.0, ccmap)
	#imagefilt = apImage.arrayToImage(filtmap)
	#imagefilt = imagefilt.convert("RGB")
	#imagefilt = ImageOps.colorize(imagefilt, "black", "green")
	#image = Image.blend(image, imagefilt, 0.2) 

	### color peaks in map
	image2 = image.copy()
	draw = ImageDraw.Draw(image2)
	drawPeaks(peaktree, draw, bin, binpixrad, fill=True)
	image = Image.blend(image, image2, 0.3) 

	outfile = os.path.join(mapdir, imgname+"."+maptype+str(tmplnum)+".jpg")
	print " ... writing JPEG: ",outfile
	image.save(outfile, "JPEG", quality=90)

	peakTreeToPikFile(peaktree, imgname, tmplnum, params['rundir'])

	return peaktree


def mergePeakTrees(imgdict, peaktreelist, params):
	print "Merging individual template peaks into one set"
	bin =         int(params["bin"])
	diam =        float(params["diam"])
	apix =        float(params["apix"])
	olapmult =    float(params["overlapmult"])
	pixrad =      diam/apix/2.0
	binpixrad =   diam/apix/2.0/float(bin)
	imgname =     imgdict['filename']

	#PUT ALL THE PEAKS IN ONE ARRAY
	mergepeaktree = []
	for peaktree in peaktreelist:
		mergepeaktree.extend(peaktree)

	#REMOVE OVERLAPPING PEAKS
	cutoff   = olapmult*pixrad	#1.5x particle radius in pixels
	mergepeaktree = removeOverlappingPeaks(mergepeaktree, cutoff)

	bestpeaktree = []
	for peaktree in peaktreelist:
		for peakdict in peaktree:
			if peakdict in mergepeaktree:
				bestpeaktree.append(peakdict)

	peakTreeToPikFile(bestpeaktree, imgname, 'a', params['rundir'])

	return bestpeaktree

def removeOverlappingPeaks(peaktree, cutoff):
	#distance in pixels for two peaks to be too close together
	print " ... overlap distance cutoff:",round(cutoff,1),"pixels"
	cutsq = cutoff**2 + 1

	initpeaks = len(peaktree)
	peaktree.sort(_peakCompare)
	i=0
	while i < len(peaktree):
		j=0
		while j < i:
			distsq = peakDistSq(peaktree[i], peaktree[j])
			if(distsq < cutsq):
				del peaktree[i]
				i=i-1
				j=j-1
			j=j+1
		i=i+1
	postpeaks = len(peaktree)
	apDisplay.printMsg("kept "+str(postpeaks)+" non-overlapping peaks of "+str(initpeaks)+" total peaks")

	return peaktree

def _peakCompare(a, b):
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
	for i in numarray.array([-0.05,-0.02,0.00,0.02,0.05]):
		thresh      = threshold + float(i)
		blobtree, percentcov = findBlobs(ccmap, thresh, maxsize=maxsize)
		tstr  = "%.2f" % thresh
		lbstr = "%4d" % len(blobtree)
		pcstr = "%.2f" % percentcov
		if(thresh == threshold):
			print " ... *** selected threshold: "+tstr+" gives "+lbstr+" peaks ("+\
				pcstr+"% coverage ) ***"
		else:
			print " ...      varying threshold: "+tstr+" gives "+lbstr+" peaks ("+\
				pcstr+"% coverage )"

def convertBlobsToPeaks(blobtree, tmpldbid, tmplnum, bin):
	peaktree = []
	if tmpldbid is not None:
		print "TEMPLATE DBID:",tmpldbid
	for blobclass in blobtree:
		peakdict = {}
		peakdict['ycoord']      = float(blobclass.stats['center'][0]*float(bin))
		peakdict['xcoord']      = float(blobclass.stats['center'][1]*float(bin))
		peakdict['correlation'] = blobclass.stats['mean']
		peakdict['peakmoment']  = blobclass.stats['moment']
		peakdict['peakstddev']  = blobclass.stats['stddev']
		peakdict['peakarea']    = blobclass.stats['n']
		peakdict['tmplnum']     = tmplnum
		peakdict['template']    = tmpldbid
		peaktree.append(peakdict)
	return peaktree

def findBlobs(ccmap, thresh, maxsize=500, minsize=1, maxpeaks=1500, border=10, 
	  maxmoment=4.0, elim= "highest", summary=False):
	"""
	calls leginon's find_blobs
	"""
	totalarea = (ccmap.shape)[0]**2
	ccthreshmap = imagefun.threshold(ccmap, thresh)
	percentcov  =  round(100.0*float(ccthreshmap.sum())/float(totalarea),2)
	#find_blobs(image,mask,border,maxblobs,maxblobsize,minblobsize,maxmoment,method)
	if percentcov > 15:
		apDisplay.printWarning("too much coverage in threshold: "+str(percentcov))
		return [],percentcov
	try:
		blobtree = imagefun.find_blobs(ccmap, ccthreshmap, border, maxpeaks*4,
		  maxsize, minsize, maxmoment, elim, summary)
	except:
		blobtree = imagefun.find_blobs(ccmap, ccthreshmap, border, maxpeaks*4,
		  maxsize, minsize, maxmoment, elim)
	return blobtree, percentcov

def peakTreeToPikFile(peaktree, imgname, tmpl, rundir="."):
	outpath = os.path.join(rundir, "pikfiles")
	apParam.createDirectory(outpath, warning=False)
	outfile = os.path.join(outpath, imgname+"."+str(tmpl)+".pik")
	if (os.path.isfile(outfile)):
		os.remove(outfile)
		print " ... removed existing file:", outfile
	#WRITE PIK FILE
	f=open(outfile, 'w')
	f.write("#filename x y mean stdev corr_coeff peak_size templ_num angle moment\n")
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
		if 'template' in peakdict:
			tmplnum = peakdict['template']
		else:
			tmplnum = tmpl
		#filename x y mean stdev corr_coeff peak_size templ_num angle moment
		out = imgname+".mrc "+str(int(col))+" "+str(int(row))+ \
			" "+mean_str+" "+std_str+" "+str(rho)+" "+str(int(size))+ \
			" "+str(tmplnum)+" 0 "+mom_str
		f.write(str(out)+"\n")
	f.close()

def createPeakJpeg(imgdata, peaktree, params):
	if 'templatelist' in params:
		count =   len(params['templatelist'])
	else: count = 1
	bin =     int(params["bin"])/2
	diam =    float(params["diam"])
	apix =    float(params["apix"])
	if bin < 1: 
		bin = 1
	binpixrad  = diam/apix/2.0/float(bin)
	imgname = imgdata['filename']

	jpegdir = os.path.join(params['rundir'],"jpgs")
	apParam.createDirectory(jpegdir, warning=False)

	imgarray = nd_image.median_filter(imgdata['image'], size=3)
	imgarray = apImage.preProcessImage(imgarray, bin=bin, params=params)
	image = apImage.arrayToImage(imgarray)
	image = image.convert("RGB")

	image2 = image.copy()
	draw = ImageDraw.Draw(image2)
	drawPeaks(peaktree, draw, bin, binpixrad)
	outfile = os.path.join(jpegdir,imgname+".prtl.jpg")
	print " ... writing JPEG: ",outfile
	image = Image.blend(image, image2, 0.9) 
	image.save(outfile, "JPEG", quality=95)

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
		print "BINPEAKRAD",binpixrad/8.0
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
		elif 'peakarea' in peakdict and peakdict['peakarea'] != 0:
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
