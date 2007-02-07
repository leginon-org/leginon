#!/usr/bin/python -O

import sys
import os
import string
import math
import time
import Image
import ImageDraw
import Mrc
import imagefun
import numextension
import convolver
import numarray
import numarray.nd_image as nd_image
import numarray.convolve as convolve
import numarray.fft as fft
import numarray.random_array as random_array
import numarray.linear_algebra as linear_algebra


def runCrossCorr(params,file):
	# Run Neil's version of FindEM
	imagefile = file+".mrc"
	tmplt     =params["template"]

	#CYCLE OVER EACH TEMPLATE
	classavg=1
	blobs = []

	image = process_image(imagefile,params)

	while classavg<=len(params['templatelist']):
		print "Template ",classavg
		outfile="cccmaxmap%i00.mrc" % classavg
		if (os.path.exists(outfile)):
			print " ... removing outfile:",outfile
			os.remove(outfile)

		if (params["multiple_range"]==True):
			strt=float(params["startang"+str(classavg)])
			end=float(params["endang"+str(classavg)])
			incr=float(params["incrang"+str(classavg)])
		else:
			strt=float(params["startang"])
			end=float(params["endang"])
			incr=float(params["incrang"])

		if (len(params['templatelist'])==1 and not params['templateIds']):
			templfile = tmplt+".mrc"
		else:
			templfile = tmplt+str(classavg)+".mrc"

		#MAIN FUNCTION HERE:
		ccmaxmap = createCrossCorr(image,templfile,classavg,strt,end,incr,params)

		#OUTPUT FILE
		#Mrc.numeric_to_mrc(ccmaxmap,outfile)

		blobs.append(findPeaksInMap(ccmaxmap,file,classavg,params))

		classavg+=1
	
	numpeaks = mergePikFiles(file,blobs,params)

	return numpeaks

#########################################################

def process_image(imagefile,params):
	bin     = int(params["bin"])
	apix    = float(params["apix"])
	diam    = float(params["diam"])
	lowpass	= float(params["lp"])
	pixrad  = int(math.ceil(diam/apix/2.0/float(bin)))

	#READ IMAGES
	image    = Mrc.mrc_to_numeric(imagefile)

	#BIN IMAGES
	image       = imagefun.bin(image,bin)

	#NORMALIZE
	image    = normStdev(image)
	image    = PlaneRegression(image)
	image    = normRange(image)-0.5

	#LOW PASS FILTER
	image    = filterImg(image,apix,bin,lowpass)

	#BLACK OUT DARK AREAS, LESS THAN 2 STDEVS
	#image = removeCrud(image,imagefile,-2.0,params)

	return image

#########################################################

def createCrossCorr(image,templfile,classavg,strt,end,incr,params):
	bin     = int(params["bin"])
	apix    = float(params["apix"])
	diam    = float(params["diam"])
	pixrad  = int(math.ceil(diam/apix/2.0/float(bin)))
	err     = 0.00001

	#PROCESS TEMPLATE
	template = Mrc.mrc_to_numeric(templfile)
	templatebin = imagefun.bin(template,bin) #FAKE FOR SIZING
	template = normRange(template)-0.5


	#MASK IF YOU WANT
	tmplmask = circ_mask(template,diam/apix)
	template = normStdev2(template,tmplmask.sum())
	tmplmaskbin = imagefun.bin(tmplmask,bin)
	nm = float(tmplmaskbin.sum())

	#TRANSFORM IMAGE
	oversized = get_oversize(image,templatebin).copy()
	ccmaxmap  = numarray.zeros(image.shape)-50.0
	imagefft  = calc_imagefft(image,oversized) #SAVE SOME CPU CYCLES

	#GET NORMALIZATION FUNCTION
	normconvmap = calc_norm_conv_map(image, imagefft, tmplmaskbin, oversized, bin)

	print "Starting rotations ... "
	ang = strt
	i = 1
	totalrots = int( (end - strt) / incr + 0.999)
	while(ang < end):
		print " ... rotation:",i,"of",totalrots,"  \tangle =",ang
		#ROTATE
		template2   = nd_image.rotate(template,ang,reshape=False,mode="wrap").copy()
		#MASK
		template2   = template2*tmplmask
		#BIN
		template2   = imagefun.bin(template2,bin)
		#NORMALIZE
		template2   = normStdev2(template2,nm)
		#TRANSFORM
		templatefft = calc_templatefft(template2,oversized)

		#CROSS CORRELATE
		ccmap       = cross_correlate_fft(imagefft,templatefft,image.shape,template2.shape)
		ccmap       = ccmap / nm
		del template2
		del templatefft
		#GET MAXIMUM VALUES
		ccmaxmap    = numarray.where(ccmap>ccmaxmap,ccmap,ccmaxmap)
		del ccmap
		#INCREMENT
		ang = ang + incr
		i = i + 1

	#NORMALIZE
	print "NormConvMap"
	imageinfo(normconvmap)
	print "CCMaxMap"
	imageinfo(ccmaxmap)
	ccmaxmap = numarray.where(normconvmap > err, ccmaxmap/normconvmap, 0.0)
	ccmaxmap = numarray.where(ccmaxmap > 1.0, 1.0, ccmaxmap)
	ccmaxmap = numarray.where(ccmaxmap < 0.0, 0.0, ccmaxmap)
	print "NormCCMaxMap"
	imageinfo(ccmaxmap)

	#WOW THIS IS A HACK:
	#ccmaxmap = normStdev(ccmaxmap)/4
	#print "NormCCMaxMap-Hacked"
	#imageinfo(ccmaxmap)

	#REMOVE OUTSIDE AREA
	cshape = ccmaxmap.shape
	black = -0.01
 	ccmaxmap[ 0:pixrad, 0:cshape[1] ] = black
	ccmaxmap[ 0:cshape[0], 0:pixrad ] = black
 	ccmaxmap[ cshape[0]-pixrad:cshape[0], 0:cshape[1] ] = black
	ccmaxmap[ 0:cshape[0], cshape[1]-pixrad:cshape[1] ] = black

	#NORMALIZE
	ccmaxmap   = normRange(ccmaxmap)

	return ccmaxmap

#########################################################

def normStdev2(map,n):
	"""
	normalizes mean and stdev of image inside mask only
	"""
	lsum = map.sum()
	mean=nd_image.mean(map)
	sum_sqs=(map*map).sum()
	sq = (n*sum_sqs - lsum*lsum)/(n*n)
	if (sq < 0): sys.exit(1)

	th=0.00001
	if (sq > th):
		sd  = math.sqrt(sq)
		map = (map-mean)/sd
		val = -mean/sd
	elif (sq < th):
		map = (map-mean)
		val = -mean/sd

	return map

#########################################################
#########################################################

def removeCrud(image,imagefile,stdev,params):
	print "Put noise in low density regions (crud remover)"

	bin     = int(params["bin"])
	apix    = float(params["apix"])
	diam    = float(params["diam"])
	lowpass	= float(params["lp"])
	pixrad  = diam/apix/2.0/float(bin)/4

	#BLACK OUT DARK AREAS, LESS THAN 2 STDEVS

	print " ... low pass filter"
	#imagemed = filterImg(image,apix*float(bin),int(pixrad+1))
	imagemed = filterImg(image,apix*float(bin),int(16*pixrad+1))

	print " ... max/min filters"
	#GROW
	print " ... ... grow filter"
	rad = int(pixrad/2+1)
	def distsq(x,y):
		return (x-rad)**2 + (y-rad)**2
	fp = numarray.fromfunction(distsq, (rad*2,rad*2))
	fp = numarray.where(fp < rad**2,1.0,0.0)
	imagemed = nd_image.minimum_filter(imagemed, \
		footprint=fp,mode="constant",cval=stdev)
	#SHRINK
	print " ... ... shrink filter"
	rad = int(pixrad+1)
	def distsq(x,y):
		return (x-rad)**2 + (y-rad)**2
	fp = numarray.fromfunction(distsq, (rad*2,rad*2))
	fp = numarray.where(fp < rad**2,1.0,0.0)
	imagemed = nd_image.maximum_filter(imagemed, \
		footprint=fp,mode="constant",cval=0.0)
	#GROW
	print " ... ... grow filter"
	rad = int(2*pixrad+1)
	def distsq(x,y):
		return (x-rad)**2 + (y-rad)**2
	fp = numarray.fromfunction(distsq, (rad*2,rad*2))
	fp = numarray.where(fp < rad**2,1.0,0.0)
	imagemed = nd_image.minimum_filter(imagemed, \
		footprint=fp,mode="constant",cval=stdev)

	#SHRINK
	print " ... ... shrink filter"
	rad = int(pixrad/2+1)
	def distsq(x,y):
		return (x-rad)**2 + (y-rad)**2
	fp = numarray.fromfunction(distsq, (rad*2,rad*2))
	fp = numarray.where(fp < rad**2,1.0,0.0)
	imagemed = nd_image.maximum_filter(imagemed, \
		footprint=fp,mode="constant",cval=0.0)

	imagemed = normStdev(imagemed)
	print " ... create mask"
	imagemask = numarray.where(imagemed>stdev,0.0,1.0)
	#numeric_to_jpg(imagemask,imagefile+"-mask.jpg")
	#image = numarray.where(imagemask<0.1,image,image-3)
	print " ... create random noise data"
	imagerand = random_array.normal(0.0, 1.0, shape=image.shape)
	print " ... replace crud with noise"
	image = numarray.where(imagemask<0.1,image,imagerand) #random.gauss(-1.0,1.0))
	#numeric_to_jpg(image,imagefile+"-modified.jpg")
	del imagemed
	del imagemask
	del imagerand
	return image

#########################################################

def tmpRemoveCrud(params,imagefile):
	bin     = int(params["bin"])
	apix    = float(params["apix"])
	diam    = float(params["diam"])
	lowpass	= float(params["lp"])
	pixrad  = diam/apix/2.0
	
	imagefile=imagefile+'.mrc'
	#READ IMAGES
	image    = Mrc.mrc_to_numeric(imagefile)

	#BIN IMAGES
	image    = imagefun.bin(image,bin)

	#NORMALIZE
	image    = normStdev(image)
#	image    = PlaneRegression(image)
#	image    = normStdev(image)

	#LOW PASS FILTER
	image    = selexonFunctions.filterImg(image,apix*float(bin),lowpass)

	#BLACK OUT DARK AREAS, LESS THAN 2 STDEVS
	image = removeCrud(image,imagefile,-1.0,params)
	Mrc.numeric_to_mrc(image,(imagefile.split('.')[0]+'.dwn.mrc'))
	return()

#########################################################
#########################################################

def filterImg(img,apix,bin,rad):
	# low pass filter image to res resolution
	if rad==0:
		print " ... skipping low pass filter"
		return(img)
	else:
		print " ... performing low pass filter"
		sigma=float(rad)/apix/3.0/float(bin)
		kernel=convolver.gaussian_kernel(sigma)
	c=convolver.Convolver()
	return(c.convolve(image=img,kernel=kernel))

#########################################################

def PlaneRegression(sqarray):
	print " ... calculate 2d linear regression"
	if ( (sqarray.shape)[0] != (sqarray.shape)[1] ):
		print "Array is NOT square"
		sys.exit(1)
	size = (sqarray.shape)[0]
	count = float((sqarray.shape)[0]*(sqarray.shape)[1])
	def retx(y,x):
		return x
	def rety(y,x):
		return y	
	xarray = numarray.fromfunction(retx, sqarray.shape)
	yarray = numarray.fromfunction(rety, sqarray.shape)
	xsum = float(xarray.sum())
	xsumsq = float((xarray*xarray).sum())
	ysum = xsum
	ysumsq = xsumsq
	xysum = float((xarray*yarray).sum())
	xzsum = float((xarray*sqarray).sum())
	yzsum = float((yarray*sqarray).sum())
	zsum = sqarray.sum()
	zsumsq = (sqarray*sqarray).sum()
	xarray = xarray.astype(numarray.Float64)
	yarray = yarray.astype(numarray.Float64)
	leftmat = numarray.array( [[xsumsq, xysum, xsum], [xysum, ysumsq, ysum], [xsum, ysum, count]] )
	rightmat = numarray.array( [xzsum, yzsum, zsum] )
	resvec = linear_algebra.solve_linear_equations(leftmat,rightmat)
	print " ... plane_regress: x-slope:",round(resvec[0]*size,5),\
		", y-slope:",round(resvec[1]*size,5),", xy-intercept:",round(resvec[2],5)
	return sqarray - xarray*resvec[0] - yarray*resvec[1] - resvec[2]
	sys.exit(1)

#########################################################
#########################################################

def findPeaks2(params,file):
	#Does NOT use viewit
	#Resulting in a 5-fold speed up over findPeaks()

	numtempl =    len(params['templatelist'])
	bin =         int(params["bin"])
	diam =        float(params["diam"])
	apix =        float(params["apix"])



	blobs = []
	for i in range(numtempl):
		infile="cccmaxmap"+str(i+1)+"00.mrc"
		ccmaxmap=Mrc.mrc_to_numeric(infile)
		blobs.append(findPeaksInMap(ccmaxmap,file,i+1,params))

	numpeaks = mergePikFiles(file,blobs,params)

	return numpeaks

#########################################################

def findPeaksInMap(ccmaxmap,file,num,params):
	threshold =   float(params["thresh"])
	bin =         int(params["bin"])
	diam =        float(params["diam"])
	apix =        float(params["apix"])
	olapmult =    float(params["overlapmult"])
	pixrad =      diam/apix/2.0/float(bin)
	#MAXBLOBSIZE ==> 1/8 AREA OF PARTICLE
	maxblobsize = int(round(math.pi*(apix*diam/float(bin))**2/32.0,0))+1

	print " ... threshold",threshold

	outfile="pikfiles/"+file+"."+str(num)+".pik"
	if (os.path.exists(outfile)):
		os.remove(outfile)
		print " ... removed existing file:",outfile

	for i in range(5):
		thresh      = threshold + float(i-2)*0.05
		ccthreshmap = imagefun.threshold(ccmaxmap,thresh)
		blobs       = imagefun.find_blobs(ccmaxmap,ccthreshmap,6,10000,60,1)
		if(thresh == threshold):
			print " ... selected threshold:",thresh,"gives",len(blobs),"peaks ***"
		else:
			print " ... varying  threshold:",thresh,"gives",len(blobs),"peaks"

	ccthreshmap=imagefun.threshold(ccmaxmap,threshold)
	blobs = imagefun.find_blobs(ccmaxmap, ccthreshmap, 6, 10000, maxblobsize, 0)
	if(len(blobs) > 9000):
		print " !!! more than 10000 peaks, selecting only top 1500 peaks"
		blobs.sort(blob_compare)
		blobs = blobs[0:1500]

	#find_blobs(image,mask,border,maxblobs,maxblobsize,minblobsize)
	print "Template "+str(num)+": Found",len(blobs),"peaks"

	cutoff = olapmult*pixrad	#1.5x particle radius in pixels
	removeOverlappingBlobs(blobs,cutoff)

	blobs.sort(blob_compare)

	#WRITE PIK FILE
	f=open(outfile, 'w')
	for blob in blobs:
		row = blob.stats['center'][0]
		column = blob.stats['center'][1]
		mean = blob.stats['mean']
		std = blob.stats['stddev']
		size = blob.stats['n']
		mean_str = "%.4f" % mean
		std_str = "%.4f" % std
		out = file+".mrc "+str(int(column)*bin)+" "+str(int(row)*bin)+ \
			" "+mean_str+" "+std_str+" "+str(int(size))
		f.write(str(out)+"\n")
	f.close()

	draw = drawBlobs(ccmaxmap,blobs,file,num,bin,pixrad)

	return blobs

#########################################################

def drawBlobs(ccmaxmap,blobs,file,num,bin,pixrad):
	if not (os.path.exists("ccmaxmaps")):
		os.mkdir("ccmaxmaps")

	ccmaxmap =  normalizeImage(ccmaxmap)
	image    = array2image(ccmaxmap)

	draw = ImageDraw.Draw(image)

	ps=float(1.5*pixrad) #1.5x particle radius
	for blob in blobs:
		x1=blob.stats['center'][1]
		y1=blob.stats['center'][0]
		coord=(x1-ps, y1-ps, x1+ps, y1+ps)
		#draw.ellipse(coord,outline="white")
		draw.rectangle(coord,outline="white")
	del draw

	outfile="ccmaxmaps/"+file+".ccmaxmap"+str(num)+".jpg"
	print " ... writing JPEG: ",outfile
	image.save(outfile, "JPEG", quality=90)

	return

#########################################################

def blob_compare(x,y):
	if float(x.stats['mean']) < float(y.stats['mean']):
		return 1
	else:
		return -1

#########################################################

def removeOverlappingBlobs(blobs,cutoff):
	#distance in pixels for two blobs to be too close together
	print " ... overlap distance cutoff:",round(cutoff,1),"pixels"
	cutsq = cutoff**2+1

	initblobs = len(blobs)
	blobs.sort(blob_compare)
	i=0
	while i < len(blobs):
		j=0
		while j < i:
			distsq = blob_distsq((blobs)[i],(blobs)[j])
			if(distsq < cutsq):
				del blobs[i]
				i=i-1
				j=j-1
			j=j+1
		i=i+1
	postblobs = len(blobs)
	print " ... kept",postblobs,"non-overlapping particles of",initblobs,"total particles"
	return blobs

#########################################################

def mergePikFiles(file,blobs,params):
	print "Merging #.pik files into a.pik file"
	bin =         int(params["bin"])
	diam =        float(params["diam"])
	apix =        float(params["apix"])
	olapmult =    float(params["overlapmult"])
	pixrad =      diam/apix/2.0/float(bin)

	outfile="pikfiles/"+file+".a.pik"
	if (os.path.exists(outfile)):
		os.remove(outfile)
		print " ... removed existing file:",outfile

	#PUT ALL THE BLOBS IN ONE ARRAY
	allblobs = []
	for i in range(len(blobs)):
		allblobs.extend(blobs[i])

	#REMOVE OVERLAPPING BLOBS
	cutoff   = olapmult*pixrad	#1.5x particle radius in pixels
	allblobs = removeOverlappingBlobs(allblobs,cutoff)

	#WRITE SELECTED BLOBS TO FILE
	count = 0
	f=open(outfile, 'w')
	for i in range(len(blobs)):
		for blob in (blobs[i]):
			if blob in allblobs:
				row = blob.stats['center'][0]
				column = blob.stats['center'][1]
				mean = blob.stats['mean']
				std = blob.stats['stddev']
				size = blob.stats['n']
				mean_str = "%.4f" % mean
				std_str = "%.4f" % std
				out = file+".mrc "+str(int(column)*bin)+" "+str(int(row)*bin)+ \
					" "+mean_str+" "+std_str+" "+str(int(size))+" "+str(i)
				count = count + 1
				f.write(str(out)+"\n")
	f.close()
	return count

#########################################################

def blob_distsq(x,y):
	row1 = x.stats['center'][0]
	col1 = x.stats['center'][1]
	row2 = y.stats['center'][0]
	col2 = y.stats['center'][1]
	return (row1-row2)**2+(col1-col2)**2

#########################################################
#########################################################

def createJPG2(params,file):
	#Does NOT use viewit
	#Resulting in a 2-fold speed up over createJPG()
	#With more features!!!

	mrcfile = file+".mrc"
	count =   len(params['templatelist'])
	bin =     int(params["bin"])/2
	diam =    float(params["diam"])
	apix =    float(params["apix"])
	if bin < 1: 
		bin = 1
	pixrad  = diam/apix/2.0/float(bin)

	if not (os.path.exists("jpgs")):
		os.mkdir("jpgs")

	#print "Reading MRC: ",mrcfile
	numer=Mrc.mrc_to_numeric(mrcfile)
	numer=numextension.bin(numer,bin)

	#print "Image: ",numer.getshape()
	numer=normalizeImage(numer)
	image2 = array2image(numer)
	image2 = image2.convert("RGB")

	pikfile="pikfiles/"+file+".a.pik"
	print " ... reading Pik: ",pikfile
	draw = ImageDraw.Draw(image2)
	#blend(image1,image2,0.5)

	draw = drawPikFile(pikfile,draw,bin,pixrad) 
	del draw

	outfile="jpgs/"+mrcfile+".prtl.jpg"
	print " ... writing JPEG: ",outfile
	image2.save(outfile, "JPEG", quality=97)

#########################################################

def drawPikFile(file,draw,bin,pixrad):
	"""	
	Reads a .pik file and draw circles around all the points
	in the .pik file
	"""
	circle_colors = [ \
		"#ff4040","#3df23d","#3d3df2", \
		"#f2f23d","#3df2f2","#f23df2", \
		"#f2973d","#3df297","#973df2", \
		"#97f23d","#3d97f2","#f23d97", ]
	"""	
	Order: 	Yellow, Cyan, Magenta, Red, Green, Blue,
		Orange, Teal, Purple, Lime-Green, Sky-Blue, Pink
	"""
	ps=float(1.5*pixrad) #1.5x particle radius
	f=open(file, 'r')
	for line in f:
		line=string.rstrip(line)
		bits=line.split(' ')
		#x1=int(bits[1])/bin
		#y1=int(bits[2])/bin
		x1=float(bits[1])/float(bin)
		y1=float(bits[2])/float(bin)
		coord=(x1-ps, y1-ps, x1+ps, y1+ps)
		if(len(bits) > 6):
			num = int(bits[6])%12
		else:
			num = 0
		draw.ellipse(coord,outline=circle_colors[num])
		#draw.rectangle(coord,outline=color1)
	f.close()
	return draw

#########################################################
#########################################################

def normalizeImage(a):
	"""	
	Normalizes numarray to fit into an image format
	that is values between 0 and 255.
	"""
	#Minimum image value, i.e. how black the image can get
	minlevel = 0.0
	#Maximum image value, i.e. how white the image can get
	maxlevel = 235.0
	#Maximum standard deviations to include, i.e. pixel > N*stdev --> white
	devlimit=5.0
 	imrange = maxlevel - minlevel

	avg1=nd_image.mean(a)

	stdev1=nd_image.standard_deviation(a)

	min1=nd_image.minimum(a)
	if(min1 < avg1-devlimit*stdev1):
		min1 = avg1-devlimit*stdev1

	max1=nd_image.maximum(a)
	if(max1 > avg1+devlimit*stdev1):
		max1 = avg1+devlimit*stdev1

	c = (a - min1)/(max1 - min1)*imrange + minlevel
	c = numarray.where(c > maxlevel,255.0,c)
	c = numarray.where(c < minlevel,0.0,c)

	return c

#########################################################

def array2image(a):
    """
    Converts array object (numarray) to image object (PIL).
    """
    h, w = a.shape[:2]
    int32 = numarray.Int32
    uint32 = numarray.UInt32
    float32 = numarray.Float32
    float64 = numarray.Float64

    if a.type()==int32 or a.type()==uint32 or a.type()==float32 or a.type()==float64:
        a = a.astype(numarray.UInt8) # convert to 8-bit
    if len(a.shape)==3:
        if a.shape[2]==3:  # a.shape == (y, x, 3)
            r = Image.fromstring("L", (w, h), a[:,:,0].tostring())
            g = Image.fromstring("L", (w, h), a[:,:,1].tostring())
            b = Image.fromstring("L", (w, h), a[:,:,2].tostring())
            return Image.merge("RGB", (r,g,b))
        elif a.shape[2]==1:  # a.shape == (y, x, 1)
            return Image.fromstring("L", (w, h), a.tostring())
    elif len(a.shape)==2:  # a.shape == (y, x)
        return Image.fromstring("L", (w, h), a.tostring())
    else:
        raise ValueError, "unsupported image mode"

#########################################################

def numeric_to_jpg(numer,file):
	numer=normalizeImage(numer)
	image = array2image(numer)
	#image = image.convert("RGB")
	print " ... writing JPEG: ",file
	image.save(file, "JPEG", quality=85)

#########################################################

def normRange(im):
	min1=nd_image.minimum(im)
	max1=nd_image.maximum(im)
	return (im - min1)/(max1 - min1)

#########################################################

def normStdev(im):
	avg1=nd_image.mean(im)
	std1=nd_image.standard_deviation(im)
	return (im - avg1)/std1

#########################################################

def imageinfo(im):
	avg1=nd_image.mean(im)
	stdev1=nd_image.standard_deviation(im)
	print " ... avg:  ",round(avg1,3),"+-",round(stdev1,3)

	min1=nd_image.minimum(im)
	max1=nd_image.maximum(im)
	print " ... range:",round(min1,3),"<>",round(max1,3)

	return

#########################################################
#########################################################

def circ_mask(numer,pixrad):
	indices = numarray.indices(numer.shape)
	x0, y0 = (numer.shape)[0]/2, (numer.shape)[1]/2
	dx, dy = indices[0]-y0,indices[1]-x0
	return numarray.sqrt(dx**2+dy**2)<pixrad

#########################################################

def get_oversize(image,template):
	shape     = image.shape
	kshape    = template.shape
	oversized = (numarray.array(shape) + numarray.array(kshape)).copy()
	return oversized

#########################################################

def cross_correlate(image,template):	
	#CALCULATE BIGGER MAP SIZE
	shape = image.shape
	kshape = template.shape
	oversized = (numarray.array(shape) + numarray.array(kshape))

	#EXPAND IMAGE TO BIGGER SIZE
	image2 = convolve.iraf_frame.frame(image, oversized, mode="constant", cval=0.0)

	#CALCULATE FOURIER TRANSFORMS
	imagefft = fft.real_fft2d(image2, s=oversized)
	del image2
	templatefft = fft.real_fft2d(template, s=oversized)

	#MULTIPLY FFTs TOGETHER
	newfft = imagefft * templatefft 
	del imagefft
	del templatefft

	#INVERSE TRANSFORM TO GET RESULT
	corr = fft.inverse_real_fft2d(newfft, s=oversized)
	del newfft

	#RETURN CENTRAL PART OF IMAGE (SIDES ARE JUNK)
	return corr[ kshape[0]-1:shape[0]+kshape[0]-1, kshape[1]-1:shape[1]+kshape[1]-1 ]

#########################################################

def calc_templatefft(template, oversized):
	#CALCULATE FOURIER TRANSFORMS
	templatefft = fft.real_fft2d(template, s=oversized)

	return templatefft

#########################################################

def calc_imagefft(image, oversized):
	#EXPAND IMAGE TO BIGGER SIZE
	avg=nd_image.mean(image)
	image2 = convolve.iraf_frame.frame(image, oversized, mode="constant", cval=avg)

	#CALCULATE FOURIER TRANSFORMS
	imagefft = fft.real_fft2d(image2, s=oversized)
	del image2

	return imagefft

#########################################################

def cross_correlate_fft(imagefft, templatefft, imshape, tmplshape):
	#CALCULATE BIGGER MAP SIZE
	oversized = (numarray.array(imshape) + numarray.array(tmplshape))

	#MULTIPLY FFTs TOGETHER
	newfft = (templatefft * numarray.conjugate(imagefft)).copy()
	del templatefft

	#INVERSE TRANSFORM TO GET RESULT
	corr = fft.inverse_real_fft2d(newfft, s=oversized)
	del newfft

	#ROTATION, NEGATE AND SHIFT:
	rot = numarray.array( [ [-1, 0], [0, -1] ] )
	corr = nd_image.affine_transform(corr, rot, offset=tmplshape[0]-1, mode='wrap', order=0)

	corr=corr*imshape[0]

	#RETURN CENTRAL PART OF IMAGE (SIDES ARE JUNK)
	return corr[ tmplshape[0]-1:imshape[0]+tmplshape[0]-1, tmplshape[1]-1:imshape[1]+tmplshape[1]-1 ]

#########################################################

def calc_norm_conv_map(image, imagefft, tmplmask, oversized, bin):
	t1 = time.time()
	print " ... computing FindEM's norm_conv_map"

	tmplsize = (tmplmask.shape)[1]
	nm = tmplmask.sum()
	tmplshape  = tmplmask.shape
	imshape  = image.shape
	shift = int(-1*tmplsize/float(bin)/2.0)
	err = 0.00001

	#print " ... ... compute ffts"
	tmplmaskfft = fft.real_fft2d(tmplmask, s=oversized)
	imagesqfft = fft.real_fft2d(image*image, s=oversized)
	del tmplmask

	#print " ... ... cnv2 = convolution(image**2, mask)"
	cnv2 = convolution_fft(imagesqfft, tmplmaskfft, oversized)
	del imagesqfft
	#SHIFTING CAN BE SLOW
	cnv2 = nd_image.shift(cnv2, shift, mode='wrap', order=0)
	cnv2 = cnv2 + err
	#numeric_to_jpg(cnv2,"cnv2.jpg")

	#print " ... ... cnv1 = convolution(image, mask)"
	cnv1 = convolution_fft(imagefft, tmplmaskfft, oversized)
	del tmplmaskfft
	#SHIFTING CAN BE SLOW
	cnv1 = nd_image.shift(cnv1, shift, mode='wrap', order=0)
	cnv1 = cnv1 + err
	#numeric_to_jpg(cnv1,"cnv1.jpg")

	#print " ... ... v2 = ((nm*cnv2)-(cnv1*cnv1))/(nm*nm)"
	v2=((-1*nm*cnv2)+(cnv1*cnv1))/(nm*nm) + err
	del cnv2
	del cnv1
	#numeric_to_jpg(v,"v.jpg")

	#print " ... ... normconvmap = sqrt(v2)"
	normconvmap = numarray.where(v2 > err, numarray.sqrt(v2), 0.0)
	del v2
	#numeric_to_jpg(v2,"v2.jpg")
	print " ... ... TIME: %.2f" % float(time.time()-t1)

	return normconvmap[ tmplshape[0]-1:imshape[0]+tmplshape[0]-1, tmplshape[1]-1:imshape[1]+tmplshape[1]-1 ]

#########################################################

def convolution_fft(afft,bfft,oversized):
	#THIS IS:
	# fft1 x fft2
	nx = (afft.shape)[0]
	#ny = (afft.shape)[1]
	cfft = afft * bfft
	c = fft.inverse_real_fft2d(cfft, s=oversized)
	del cfft
	c=c*nx
	return c

#########################################################

def phase_correlate(image, template):	
	#CALCULATE BIGGER MAP SIZE
	shape = image.shape
	kshape = template.shape
	oversized = (numarray.array(shape) + numarray.array(kshape))

	#EXPAND IMAGE TO BIGGER SIZE
	avg=nd_image.mean(image)
	image2 = convolve.iraf_frame.frame(image, oversized, mode="constant", cval=avg)

	#CALCULATE FOURIER TRANSFORMS
	imagefft = fft.real_fft2d(image2, s=oversized)
	templatefft = fft.real_fft2d(template, s=oversized)

	#MULTIPLY FFTs TOGETHER
	newfft = imagefft * templatefft 
	del templatefft

	#NORMALIZE CC TO GET PC
	phasefft = newfft / numarray.absolute(newfft)
	del newfft

	#INVERSE TRANSFORM TO GET RESULT
	correlation = fft.inverse_real_fft2d(phasefft, s=oversized)
	del phasefft

	#RETURN CENTRAL PART OF IMAGE (SIDES ARE JUNK)
	return correlation[ kshape[0]-1:shape[0]+kshape[0]-1, kshape[1]-1:shape[1]+kshape[1]-1 ]
