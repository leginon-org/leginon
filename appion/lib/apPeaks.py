import os
import math
import apImage
import apDisplay
import ImageDraw
import numarray
import imagefun


def findPeaks(imgdict, ccmaplist, params):

	peaktreelist = []
	count = 0
	for ccmap in ccmaplist:
		count += 1
		peaktree = findPeaksInMap(ccmap, imgdict, count, params)
		peaktreelist.append(peaktree)

	peaktree = mergePeakTrees(imgdict, peaktreelist, params)

	return peaktree

def findPeaksInMap(ccmap, imgdict, tmplnum, params):
	threshold = float(params["thresh"])
	bin =       int(params["bin"])
	diam =      float(params["diam"])
	apix =      float(params["apix"])
	olapmult =  float(params["overlapmult"])
	maxpeaks =  int(params["maxpeaks"])
	imgname =   imgdict['filename']
	pixrad =    diam/apix/2.0/float(bin)
	#MAXPEAKSIZE ==> 1x AREA OF PARTICLE
	maxsize =   int(round(math.pi*(apix*diam/float(bin))**2/4.0,0))+1

	#VARY PEAKS FROM STATS
	varyThreshold(ccmap, threshold, maxsize)
	#GET FINAL PEAKS
	blobtree, percentcov = findBlobs(ccmap, threshold, maxsize=maxsize, maxpeaks=maxpeaks)
	peaktree = convertBlobsToPeaks(blobtree, tmplnum, bin)

	print "Template "+str(tmplnum)+": Found",len(peaktree),"peaks ("+\
		str(percentcov)+"% coverage)"
	if(percentcov > 10):
		apDisplay.printWarning("thresholding covers more than 10% of image; you should increase the threshold")

	cutoff = olapmult*pixrad	#1.5x particle radius in pixels
	removeOverlappingPeaks(peaktree, cutoff)

	if(len(peaktree) > maxpeaks):
		apDisplay.printWarning("more than maxpeaks ("+str(maxpeaks)+" peaks), selecting only top peaks")
		peaktree.sort(_peakCompare)
		peaktree = peaktree[0:maxpeaks]
	else:
		peaktree.sort(_peakCompare)

	if not (os.path.exists("ccmaxmaps")):
		os.mkdir("ccmaxmaps")

	image = apImage.arrayToImage(ccmap)
	draw = ImageDraw.Draw(image)
	drawPeaksBW(peaktree, draw, bin, pixrad)
	outfile = "ccmaxmaps/"+imgname+".ccmaxmap"+str(tmplnum)+".jpg"
	print " ... writing JPEG: ",outfile
	image.save(outfile, "JPEG", quality=90)

	return peaktree


def mergePeakTrees(imgdict, peaktreelist, params):
	print "Merging individual template peaks into one set"
	bin =         int(params["bin"])
	diam =        float(params["diam"])
	apix =        float(params["apix"])
	olapmult =    float(params["overlapmult"])
	pixrad =      diam/apix/2.0/float(bin)
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

	peakTreeToPikFile(bestpeaktree, imgname, 'a')

	return bestpeaktree

def removeOverlappingPeaks(peaktree, cutoff):
	#distance in pixels for two peaks to be too close together
	print " ... overlap distance cutoff:",round(cutoff,1),"pixels"
	cutsq = cutoff**2+1

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
	return (row1-row2)**2+(col1-col2)**2

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

def convertBlobsToPeaks(blobtree, tmplnum, bin):
	peaktree = []
	for blobclass in blobtree:
		peakdict = {}
		peakdict['ycoord']      = blobclass.stats['center'][0]*bin
		peakdict['xcoord']      = blobclass.stats['center'][1]*bin
		peakdict['correlation'] = blobclass.stats['mean']
		peakdict['peakmoment']  = blobclass.stats['moment']
		peakdict['peakstddev']  = blobclass.stats['stddev']
		peakdict['peakarea']    = blobclass.stats['n']
		peakdict['template']    = tmplnum
		peaktree.append(peakdict)
	return peaktree

def findBlobs(ccmap, thresh, maxsize=500, minsize=2, maxpeaks=1500, border=6, maxmoment=5.0, elim= "highest"):
	totalarea = (ccmap.shape)[0]**2
	ccthreshmap = imagefun.threshold(ccmap, thresh)
	percentcov  =  round(100.0*float(ccthreshmap.sum())/float(totalarea),2)
	#find_blobs(image,mask,border,maxblobs,maxblobsize,minblobsize,maxmoment,method)
	blobtree = imagefun.find_blobs(ccmap, ccthreshmap, border, maxpeaks*4,
		maxsize, minsize, maxmoment, elim)
	return blobtree, percentcov

def peakTreeToPikFile(peaktree, imgname, tmplnum):
	outfile="pikfiles/"+imgname+"."+str(tmplnum)+".pik"
	if (os.path.exists(outfile)):
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
		tmplnum = peakdict['template']
		#filename x y mean stdev corr_coeff peak_size templ_num angle moment
		out = imgname+".mrc "+str(int(col))+" "+str(int(row))+ \
			" "+mean_str+" "+std_str+" "+str(rho)+" "+str(int(size))+ \
			" "+str(tmplnum)+" 0 "+mom_str
		f.write(str(out)+"\n")
	f.close()

def createPeakJpeg(imgdict, peaktree, params):
	count =   len(params['templatelist'])
	bin =     int(params["bin"])/2
	diam =    float(params["diam"])
	apix =    float(params["apix"])
	if bin < 1: 
		bin = 1
	pixrad  = diam/apix/2.0/float(bin)
	imgname = imgdict['filename']

	jpegdir = os.path.join(params['rundir'],"jpgs")
	if not (os.path.exists(jpegdir)):
		os.mkdir(jpegdir,0777)

	numer = apImage.preProcessImageParams(imgdict['image'],params)
	image = apImage.arrayToImage(numer)
	image = image.convert("RGB")

	draw = ImageDraw.Draw(image)

	drawPeaks(peaktree, draw, bin, pixrad)

	outfile = os.path.join(jpegdir,imgname+".prtl.jpg")
	print " ... writing JPEG: ",outfile

	image.save(outfile, "JPEG", quality=95)

	del image,numer,draw

	return

def drawPeaks(peaktree, draw, bin, pixrad, circmult=1.0, numcircs=2, circshape="circle"):
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
	ps=float(circmult*pixrad) #1.5x particle radius

	#00000000 1 2 3333 44444 5555555555 666666666 777777777
	#filename x y mean stdev corr_coeff peak_size templ_num angle moment
	for peakdict in peaktree:
		x1=float(peakdict['xcoord'])/float(bin)
		y1=float(peakdict['ycoord'])/float(bin)

		if 'template' in peakdict:
			#GET templ_num
			num = int(peakdict['template'])%12
		elif 'peakarea' in peakdict and peakdict['peakarea'] != 0:
			#GET templ_num
			num = int(peakdict['peakarea']*255)%12
		else:
			num = 0
		#Draw (numcircs) circles of size (circmult*pixrad)
		count = 0
		while(count < numcircs):
			tps = ps + count
			coord=(x1-tps, y1-tps, x1+tps, y1+tps)
			if(circshape == "square"):
				draw.rectangle(coord,outline=circle_colors[num])
			else:
				draw.ellipse(coord,outline=circle_colors[num])
			count = count + 1

	return 

def drawPeaksBW(peaktree, draw, bin, pixrad):
	ps=float(pixrad) #1x particle radius
	psp = ps+1
	psn = ps-1
	for peakdict in peaktree:
		x1 = float(peakdict['xcoord'])
		y1 = float(peakdict['ycoord'])
		m1 = float(peakdict['peakmoment'])
		if(m1 < 2.2):
			coord=(x1-ps, y1-ps, x1+ps, y1+ps)
			draw.ellipse(coord,outline="white")
			coord=(x1-psp, y1-psp, x1+psp, y1+psp)
			draw.ellipse(coord,outline="black")
			coord=(x1-psn, y1-psn, x1+psn, y1+psn)
			draw.ellipse(coord,outline="black")
		else:
			coord=(x1-ps, y1-ps, x1+ps, y1+ps)
			draw.rectangle(coord,outline="white")
			coord=(x1-psp, y1-psp, x1+psp, y1+psp)
			draw.rectangle(coord,outline="black")
			coord=(x1-psn, y1-psn, x1+psn, y1+psn)
			draw.rectangle(coord,outline="black")
		#draw.ellipse(coord,outline="white")

	return
