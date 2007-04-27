
import os
import math
import apImage
import apDisplay
import ImageDraw
import numarray
import imagefun


def findPeaks(imgdict, ccmaplist, params):
	numtempl =    len(params['templatelist'])
	bin =         int(params["bin"])
	diam =        float(params["diam"])
	apix =        float(params["apix"])

	blobtreelist = []
	count = 0
	for ccmap in ccmaplist:
		count += 1
		blobtree = findPeaksInMap(ccmap, imgdict, count, params)
		blobtreelist.append(blobtree)

	blobtree = mergeBlobTrees(imgdict,blobtreelist,params)

	return blobtree

def findPeaksInMap(ccmap, imgdict, num, params):
	threshold = float(params["thresh"])
	bin =       int(params["bin"])
	diam =      float(params["diam"])
	apix =      float(params["apix"])
	olapmult =  float(params["overlapmult"])
	maxblobs =  int(params["maxpeaks"])
	imgname =   imgdict['filename']
	pixrad =    diam/apix/2.0/float(bin)
	#MAXBLOBSIZE ==> 1x AREA OF PARTICLE
	maxsize =   int(round(math.pi*(apix*diam/float(bin))**2/4.0,0))+1

	#VARY PEAKS FROM STATS
	varyThreshold(ccmap, threshold, maxsize)
	#GET FINAL PEAKS
	blobtree, percentcov = findBlobs(ccmap, threshold, maxsize=maxsize)

	#find_blobs(image,mask,border,maxblobs,maxblobsize,minblobsize,maxmoment,method)
	print "Template "+str(num)+": Found",len(blobtree),"peaks ("+\
		str(percentcov)+"% coverage)"
	if(percentcov > 10):
		apDisplay.printWarning("thresholding covers more than 10% of image")

	cutoff = olapmult*pixrad	#1.5x particle radius in pixels
	removeOverlappingBlobs(blobtree, cutoff)

	if(len(blobtree) > maxblobs):
		apDisplay.printWarning("more than maxpeaks ("+str(maxblobs)+" peaks), selecting only top peaks")
		blobtree.sort(_blobCompare)
		blobtree = blobtree[0:maxblobs]
	else:
		blobtree.sort(_blobCompare)

	if not (os.path.exists("ccmaxmaps")):
		os.mkdir("ccmaxmaps")

	image = apImage.arrayToImage(ccmap)
	draw = ImageDraw.Draw(image)
	drawBlobsBW(blobtree, draw, bin, pixrad)
	outfile="ccmaxmaps/"+file+".ccmaxmap"+str(num)+".jpg"
	print " ... writing JPEG: ",outfile
	image.save(outfile, "JPEG", quality=90)

	return blobs

def _blobCompare(x,y):
	if float(x.stats['mean']) < float(y.stats['mean']):
		return 1
	else:
		return -1

def mergeBlobTrees(imgdict, blobtreelist, params):
	print "Merging individual template peaks into one set"
	bin =         int(params["bin"])
	diam =        float(params["diam"])
	apix =        float(params["apix"])
	olapmult =    float(params["overlapmult"])
	pixrad =      diam/apix/2.0/float(bin)
	imgname =     imgdict['filename']

	#PUT ALL THE BLOBS IN ONE ARRAY
	allblobtree = []
	for blobtree in blobtreelist:
		allblobtree.extend(blobtree)

	#REMOVE OVERLAPPING BLOBS
	cutoff   = olapmult*pixrad	#1.5x particle radius in pixels
	allblobtree = removeOverlappingBlobs(allblobtree, cutoff)

	bestblobtree = []
	for blobtree in blobtreelist:
		for blobdict in blobtree:
			if blobdict in allblobs:
				bestblobtree.append(blobdict)

	outfile="pikfiles/"+imgname+".a.pik"
	blobTreeToPikFile(bestblobtree, outfile)

	return count

def removeOverlappingBlobs(blobtree, cutoff):
	#distance in pixels for two blobs to be too close together
	print " ... overlap distance cutoff:",round(cutoff,1),"pixels"
	cutsq = cutoff**2+1

	initblobs = len(blobtree)
	blobtree.sort(_blobCompare)
	i=0
	while i < len(blobtree):
		j=0
		while j < i:
			distsq = blobDistSq(blobtree[i],blobtree[j])
			if(distsq < cutsq):
				del blobtree[i]
				i=i-1
				j=j-1
			j=j+1
		i=i+1
	postblobs = len(blobtree)
	apDisplay.printMsg("kept"+str(postblobs)+" non-overlapping particles of "+str(initblobs)+" total particles")

	return blobtree

def blobDistSq(x,y):
	row1 = x.stats['center'][0]
	col1 = x.stats['center'][1]
	row2 = y.stats['center'][0]
	col2 = y.stats['center'][1]
	return (row1-row2)**2+(col1-col2)**2

def varyThreshold(ccmap, threshold, maxsize):
	for i in numarray.array([-0.05,-0.02,0.00,0.02,0.05]):
		thresh      = threshold + float(i)
		blobs,percentcov = findBlobs(ccmap, thresh, maxsize=maxsize)
		tstr  = "%.2f" % thresh
		lbstr = "%4d" % len(blobs)
		pcstr = "%.2f" % percentcov
		if(thresh == threshold):
			print " ... *** selected threshold: "+tstr+" gives "+lbstr+" peaks ("+\
				pcstr+"% coverage ) ***"
		else:
			print " ...      varying threshold: "+tstr+" gives "+lbstr+" peaks ("+\
				pcstr+"% coverage )"

def findBlobs(ccmap, thresh, maxsize=500, minsize=2, maxblobs=1500, border=6, maxmoment=5.0, elim= "highest"):
	totalarea = (ccmap.shape)[0]**2
	ccthreshmap = imagefun.threshold(ccmap, thresh)
	percentcov  =  round(100.0*float(ccthreshmap.sum())/float(totalarea),2)
	blobs = imagefun.find_blobs(ccmap, ccthreshmap, border, maxblobs*4,
		maxsize, minsize, maxmoment, elim)
	return blobs,percentcov

def blobTreeToPikFile(blobtree, outfile):
	outfile="pikfiles/"+imgname+"."+str(num)+".pik"
	if (os.path.exists(outfile)):
		os.remove(outfile)
		print " ... removed existing file:", outfile

	#WRITE PIK FILE
	f=open(outfile, 'w')
	f.write("#filename x y mean stdev corr_coeff peak_size templ_num angle moment\n")
	for blob in blobtree:
		row = blob.stats['center'][0]
		col = blob.stats['center'][1]
		mean = blob.stats['mean']
		std = blob.stats['stddev']
		mom = blob.stats['moment']
		#HACK BELOW
		blob.stats['corrcoeff']  = 1.0
		rho = blob.stats['corrcoeff']
		size = blob.stats['n']
		mean_str = "%.4f" % mean
		std_str = "%.4f" % std
		mom_str = "%.4f" % mom
		#filename x y mean stdev corr_coeff peak_size templ_num angle moment
		out = file+".mrc "+str(int(col)*bin)+" "+str(int(row)*bin)+ \
			" "+mean_str+" "+std_str+" "+str(rho)+" "+str(int(size))+ \
			" "+str(num)+" 0 "+mom_str
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

	jpegdir = os.path.join(params['rundir'],"jpgs")
	if not (os.path.exists(jpegdir)):
		os.mkdir(jpegdir,0777)

	numer = apImage.preProcessImageParams(imgdict['image'],params)
	image = apImage.arrayToImage(numer)
	image = image.convert("RGB")

	draw = ImageDraw.Draw(image)

	drawBlobs(peaktree, draw, bin, pixrad)

	outfile = os.path.join(jpegdir,img['filename']+".prtl.jpg")
	print " ... writing JPEG: ",outfile

	image.save(outfile, "JPEG", quality=95)

	del image,numer,draw

	return

def drawBlobs(blobtree, draw, bin, pixrad, circmult=1.0, numcircs=2, circshape="circle"):
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
	for blobdict in blobtree:
		x1=float(blobdict['xcoord'])/float(bin)
		y1=float(blobdict['ycoord'])/float(bin)

		if 'template' in blobdict:
			#GET templ_num
			num = int(blobdict['template'])%12
		elif 'size' in blobdict and blobdict['size'] != 0:
			#GET templ_num
			num = int(blobdict['size']*255)%12
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

def drawBlobsBW(blobtree, draw, bin, pixrad)
def drawCCMaxMapBlobs(ccmaxmap,blobs,file,num,bin,pixrad):


	ps=float(pixrad) #1x particle radius
	psp = ps+1
	psn = ps-1
	for blobdict in blobtree:
		x1 = float(blobdict['xcoord'])
		y1 = float(blobdict['ycoord'])
		m1 = float(blobdict['moment'])
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
