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
import convolver
import numarray
import numarray.nd_image as nd_image
import numarray.convolve as convolve
import numarray.fft as fft
import numarray.random_array as random_array
import numarray.linear_algebra as linear_algebra
import threading
#import numextension
#import mem

def runCrossCorr(params,file):
	# Run Neil's version of FindEM
	imagefile = file+".mrc"
	tmplt     =params["template"]

	image = process_image(imagefile,params)
	#print "Processed image Stats:"
	#imageinfo(image)

	#CYCLE OVER EACH TEMPLATE
	classavg=1
	blobs = []
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
		blobs.append(getCrossCorrPeaks(image,file,templfile,classavg,strt,end,incr,params))

		classavg+=1
	
	numpeaks = mergePikFiles(file,blobs,params)

	del blobs

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
	image    = bin_img(image,bin)

	#NORMALIZE
	#image    = normStdev(image)
	image    = PlaneRegression(image)
	#image    = normStdev(image)/2.0
	#image    = normRange(image)-0.5
	#numeric_to_jpg(image,"normimage.jpg")

	#LOW PASS FILTER
	image    = filterImg(image,apix,bin,lowpass)

	#image    = (image-6990.0)/316.0
	#image = image + 8.0

	#BLACK OUT DARK AREAS, LESS THAN 2 STDEVS
	#image = removeCrud(image,imagefile,-2.0,params)

	#IMAGE MUST HAVE NORMALIZED RANGE OR THE WHOLE THING BREAKS
	# AND BE POSSITIVE EVERYWHERE
	image = 5.0*normRange(image)+0.000001

	return image

#########################################################

def getCrossCorrPeaks(image,file,templfile,classavg,strt,end,incr,params):
	bin     = int(params["bin"])
	apix    = float(params["apix"])
	diam    = float(params["diam"])
	pixrad  = int(diam/apix/2.0/float(bin) + 0.5)
	err     = 0.00001

	#PROCESS TEMPLATE
	template = Mrc.mrc_to_numeric(templfile)
	templatebin = bin_img(template,bin) #FAKE FOR SIZING
	template = normRange(template)-0.5

	#MASK IF YOU WANT
	tmplmask = circ_mask(template,pixrad*float(bin))
	template = normStdev(template)*tmplmask.sum()/((tmplmask.shape)[0]**2)
	tmplmaskbin = circ_mask(templatebin,diam/apix/2.0/float(bin))
	#tmplmaskbin = bin_img(tmplmask,bin)
	nmask = float(tmplmaskbin.sum())

	#TRANSFORM IMAGE
	oversized = get_oversize(image,templatebin).copy()
	ccmaxmap  = numarray.zeros(image.shape)-1.0
	anglemap  = numarray.zeros(image.shape)
	imagefft  = calc_imagefft(image,oversized) #SAVE SOME CPU CYCLES

	#GET FINDEM NORMALIZATION FUNCTION
	normconvmap = calc_normconvmap(image, imagefft, tmplmaskbin, oversized, pixrad)

	totalrots = int( (end - strt) / incr + 0.999)
	sys.stderr.write("Doing "+str(totalrots)+" rotations ")
	ang = strt
	i = 1
	while(ang < end):
		#print " ... rotation:",i,"of",totalrots,"  \tangle =",ang
		sys.stderr.write(".")
		#ROTATE
		template2   = nd_image.rotate(template,ang,reshape=False,mode="wrap").copy()
		#MASK
		template2   = template2*tmplmask
		#BIN
		template2   = bin_img(template2,bin)
		#NORMALIZE
		template2   = normStdev2(template2,nmask)
		#TRANSFORM
		templatefft = calc_templatefft(template2,oversized)

		#CROSS CORRELATE
		ccmap       = cross_correlate_fft(imagefft,templatefft,image.shape,template2.shape)
		ccmap       = ccmap / nmask
		#imageinfo(ccmap)
		del template2
		del templatefft

		#GET MAXIMUM VALUES
		ccmaxmap    = numarray.where(ccmap>ccmaxmap, ccmap, ccmaxmap)
		anglemap    = numarray.where(ccmap==ccmaxmap,  ang, anglemap)
		del ccmap

		#INCREMENT
		ang = ang + incr
		i = i + 1

		#sys.exit(1)
	print ""
	#NORMALIZE
	#print "NormConvMap Stats:"
	#imageinfo(normconvmap)
	#print normconvmap[511,511],normconvmap[512,512],normconvmap[513,513]
	#numeric_to_jpg(normconvmap,str(classavg)+"anormconvmap.jpg")
	#print "CCMaxMap Stats:"
	#imageinfo(ccmaxmap)
	#print ccmaxmap[511,511],ccmaxmap[512,512],ccmaxmap[513,513]
	#numeric_to_jpg(ccmaxmap,str(classavg)+"bccmaxmap.jpg")

	ccmaxmap = numarray.where(normconvmap != 0.0, ccmaxmap/normconvmap, ccmaxmap)

	#REMOVE OUTSIDE AREA
	cshape = ccmaxmap.shape
	#SET BLACK TO -1.2 FOR MORE EXACT FINDEM MAPS
	black1 = -0.1
 	ccmaxmap[ 0:pixrad*2, 0:cshape[1] ] = black1
	ccmaxmap[ 0:cshape[0], 0:pixrad*2 ] = black1
 	ccmaxmap[ cshape[0]-pixrad*2:cshape[0], 0:cshape[1] ] = black1
	ccmaxmap[ 0:cshape[0], cshape[1]-pixrad*2:cshape[1] ] = black1

	print "NormCCMaxMap Stats:"
	imageinfo(ccmaxmap)
	#print ccmaxmap[511,511],ccmaxmap[512,512],ccmaxmap[513,513]
	#numeric_to_jpg(ccmaxmap,str(classavg)+"cnormccmaxmap.jpg")

	#print "Normalized CCMaxMap Stats:"
	#ccmaxmap = ccmaxmap/4.0
	ccmaxmap = numarray.where(ccmaxmap > 1.0, 1.0, ccmaxmap)
	ccmaxmap = numarray.where(ccmaxmap < 0.0, 0.0, ccmaxmap)
	#ccmaxmap = normStdev(ccmaxmap)/5.0
	#numeric_to_jpg(ccmaxmap,"editccmaxmap.jpg")
	#imageinfo(ccmaxmap)

	#OUTPUT FILE
	#Mrc.numeric_to_mrc(ccmaxmap,outfile)

	#sys.exit(1)

	blobs = findPeaksInMapPlus(ccmaxmap,file,classavg,params,template,tmplmask,anglemap)

	del ccmaxmap,tmplmask,anglemap

	return blobs

#########################################################

def normStdev2(map,n):
	"""
	normalizes mean and stdev of image inside mask only
	"""
	lsum  = map.sum()
	mean  = nd_image.mean(map)
	sumsq = (map*map).sum()
	a = n*sumsq
	b = lsum*lsum
	sq = (a - b)/(n*n)
	if (sq < 0): 
		print " !!! BAD NORMALIZATION: sq > 0:",sq
		sys.exit(1)

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

class findemjob(threading.Thread):
   def __init__ (self, feed):
      threading.Thread.__init__(self)
      self.feed = feed
   def run(self):
		fin=''
		fin=os.popen('${FINDEM_EXE}','w')
		fin.write(self.feed)
		print "running findem.exe"
		fin.flush
		fin.close()

#########################################################

def threadFindEM(params,file):
	tmplt=params["template"]
	numcls=len(params['templatelist'])
	pixdwn=str(params["apix"]*params["bin"])
	d=str(params["diam"])
	if (params["multiple_range"]==False):
		strt=str(params["startang"])
		end=str(params["endang"])
		incr=str(params["incrang"])
	bw=str(int((1.5 * params["diam"]/params["apix"]/params["bin"])/2))
	joblist = []

	classavg=1
	while classavg<=len(params['templatelist']):
		cccfile="./cccmaxmap%i00.mrc" % classavg
		if (os.path.exists(cccfile)):
			os.remove(cccfile)

		if (params["multiple_range"]==True):
			strt=str(params["startang"+str(classavg)])
			end=str(params["endang"+str(classavg)])
			incr=str(params["incrang"+str(classavg)])

		feed = file+".dwn.mrc\n"
		if (len(params['templatelist'])==1 and not params['templateIds']):
			feed = feed+tmplt+".dwn.mrc\n"
		else:
			feed = feed+tmplt+str(classavg)+".dwn.mrc\n"
		feed = feed+"-200.0\n"+pixdwn+"\n"+d+"\n"
		feed = feed+str(classavg)+"00\n"
		feed = feed+strt+','+end+','+incr+"\n"
		feed = feed+bw+"\n"
		current = findemjob(feed)
		joblist.append(current)
		current.start()
		classavg+=1

	for job in joblist:
		job.join()
	return

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
	image    = bin_img(image,bin)

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
	del leftmat,rightmat
	print " ... plane_regress: x-slope:",round(resvec[0]*size,5),\
		", y-slope:",round(resvec[1]*size,5),", xy-intercept:",round(resvec[2],5)
	newarray = sqarray - xarray*resvec[0] - yarray*resvec[1] - resvec[2]
	del sqarray,xarray,yarray,resvec
	return newarray

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
		ccmaxmap = Mrc.mrc_to_numeric(infile)
		blobs.append(findPeaksInMap(ccmaxmap,file,i+1,params))

	del ccmaxmap

	numpeaks = mergePikFiles(file,blobs,params)
	del blobs

	return numpeaks

#########################################################

def findPeaksInMap(ccmaxmap,file,num,params):
	threshold =   float(params["thresh"])
	bin =         int(params["bin"])
	diam =        float(params["diam"])
	apix =        float(params["apix"])
	olapmult =    float(params["overlapmult"])
	maxpeaks =    int(params["maxpeaks"])
	pixrad =      diam/apix/2.0/float(bin)
	#MAXBLOBSIZE ==> 1x AREA OF PARTICLE
	maxblobsize = int(round(math.pi*(apix*diam/float(bin))**2/4.0,0))+1
	totalarea =   (ccmaxmap.shape)[0]**2

	print " ... threshold",threshold

	outfile="pikfiles/"+file+"."+str(num)+".pik"
	if (os.path.exists(outfile)):
		os.remove(outfile)
		print " ... removed existing file:",outfile

	for i in range(5):
		thresh      = threshold + float(i-2)*0.05
		ccthreshmap = imagefun.threshold(ccmaxmap,thresh)
		percentcover =  round(100.0*float(ccthreshmap.sum())/float(totalarea),2)
		blobs       = imagefun.find_blobs(ccmaxmap,ccthreshmap,6,maxpeaks*2,maxblobsize,2)
		tstr  = "%.2f" % thresh
		lbstr = "%4d" % len(blobs)
		pcstr = "%.2f" % percentcover
		if(thresh == threshold):
			print " ... *** selected threshold: "+tstr+" gives "+lbstr+" peaks ("+\
				pcstr+"% coverage ) ***"
		else:
			print " ...      varying threshold: "+tstr+" gives "+lbstr+" peaks ("+\
				pcstr+"% coverage )"

	ccthreshmap = imagefun.threshold(ccmaxmap,threshold)
	percentcover =  round(100.0*float(ccthreshmap.sum())/float(totalarea),3)

	blobs = imagefun.find_blobs(ccmaxmap, ccthreshmap, 6, maxpeaks*2, maxblobsize, 2)
	if(len(blobs) > maxpeaks):
		print " !!! more than maxpeaks ("+str(maxpeaks)+") peaks, selecting only top peaks"
		blobs.sort(blob_compare)
		blobs = blobs[0:maxpeaks]

	del ccthreshmap

	#find_blobs(image,mask,border,maxblobs,maxblobsize,minblobsize)
	print "Template "+str(num)+": Found",len(blobs),"peaks ("+\
		str(percentcover)+"% coverage)"
	if(percentcover > 10):
		print " !!! WARNING: thresholding covers more than 10% of image"

	cutoff = olapmult*pixrad	#1.5x particle radius in pixels
	removeOverlappingBlobs(blobs,cutoff)

	blobs.sort(blob_compare)

	#WRITE PIK FILE
	f=open(outfile, 'w')
	f.write("#filename x y mean stdev corr_coeff peak_size templ_num angle\n")
	for blob in blobs:
		row = blob.stats['center'][0]
		col = blob.stats['center'][1]
		mean = blob.stats['mean']
		std = blob.stats['stddev']
		#HACK BELOW
		blob.stats['corrcoeff']  = 1.0
		rho = blob.stats['corrcoeff']
		size = blob.stats['n']
		mean_str = "%.4f" % mean
		std_str = "%.4f" % std
		#filename x y mean stdev corr_coeff peak_size templ_num angle
		out = file+".mrc "+str(int(col)*bin)+" "+str(int(row)*bin)+ \
			" "+mean_str+" "+std_str+" "+str(rho)+" "+str(int(size))+ \
			" "+str(num)
		f.write(str(out)+"\n")
	f.close()

	drawBlobs(ccmaxmap,blobs,file,num,bin,pixrad)

	return blobs

#########################################################

def findPeaksInMapPlus(ccmaxmap,file,num,params,template,tmplmask,anglemap):
	threshold =   float(params["thresh"])
	bin =         int(params["bin"])
	diam =        float(params["diam"])
	apix =        float(params["apix"])
	olapmult =    float(params["overlapmult"])
	maxpeaks =    int(params["maxpeaks"])
	pixrad =      diam/apix/2.0/float(bin)
	#MAXBLOBSIZE ==> 2x AREA OF PARTICLE
	maxblobsize = int(round(math.pi*(apix*diam/float(bin))**2/2.0,0))+1
	totalarea =   (ccmaxmap.shape)[0]**2

	print " ... threshold",threshold

	outfile="pikfiles/"+file+"."+str(num)+".pik"
	if (os.path.exists(outfile)):
		os.remove(outfile)
		print " ... removed existing file:",outfile

	for i in range(5):
		thresh      = threshold + float(i-2)*0.05
		ccthreshmap = imagefun.threshold(ccmaxmap,thresh)
		percentcover =  round(100.0*float(ccthreshmap.sum())/float(totalarea),3)
		blobs       = imagefun.find_blobs(ccmaxmap,ccthreshmap,6,maxpeaks*2,maxblobsize,2)
		tstr  = "%.2f" % thresh
		lbstr = "%4d" % len(blobs)
		pcstr = "%.2f" % percentcover
		if(thresh == threshold):
			print " ... *** selected threshold: "+tstr+" gives "+lbstr+" peaks ("+\
				pcstr+"% coverage ) ***"
		else:
			print " ...      varying threshold: "+tstr+" gives "+lbstr+" peaks ("+\
				pcstr+"% coverage )"

	ccthreshmap = imagefun.threshold(ccmaxmap,threshold)
	percentcover =  round(100.0*float(ccthreshmap.sum())/float(totalarea),2)

	#numeric_to_jpg(ccthreshmap,"ccthreshmap.jpg")
	blobs = imagefun.find_blobs(ccmaxmap, ccthreshmap, 6, maxpeaks*2, maxblobsize, 2)
	if(len(blobs) > maxpeaks):
		print " !!! more than maxpeaks ("+str(maxpeaks)+") peaks, selecting only top peaks"
		blobs.sort(blob_compare)
		blobs = blobs[0:maxpeaks]

	del ccthreshmap

	#find_blobs(image,mask,border,maxblobs,maxblobsize,minblobsize)
	print "Template "+str(num)+": Found",len(blobs),"peaks ("+\
		str(percentcover)+"% coverage)"
	if(percentcover > 10):
		print " !!! WARNING: thresholding covers more than 10% of image"

	cutoff = olapmult*pixrad	#1.5x particle radius in pixels
	removeOverlappingBlobs(blobs,cutoff)

	blobs.sort(blob_compare)

	#blobs = calc_corrcoeffs(blobs,file,bin,template,tmplmask,anglemap)
	blobs = fake_corrcoeffs(blobs,file,bin,template,tmplmask,anglemap)

	#WRITE PIK FILE
	f=open(outfile, 'w')
	f.write("#filename x y mean stdev corr_coeff peak_size templ_num angle\n")
	for blob in blobs:
		row = blob.stats['center'][0]
		col = blob.stats['center'][1]
		mean = blob.stats['mean']
		std = blob.stats['stddev']
		rho = blob.stats['corrcoeff']
		size = blob.stats['n']
		mean_str = "%.4f" % mean
		std_str = "%.4f" % std
		rho_str = "%.4f" % rho

		#filename x y mean stdev corr_coeff peak_size templ_num angle
		out = file+".mrc "+str(int(col)*bin)+" "+str(int(row)*bin)+ \
			" "+mean_str+" "+std_str+" "+rho_str+" "+str(int(size))+ \
			" "+str(num)
		f.write(str(out)+"\n")
	f.close()

	drawBlobs(ccmaxmap,blobs,file,num,bin,pixrad)

	return blobs

#########################################################

def calc_corrcoeffs(blobs,imfile,bin,template,tmplmask,anglemap):
	print "Processing correlation coefficients"
	t1 = time.time()
	image    = Mrc.mrc_to_numeric(imfile+".mrc")
	image    = bin_img(image,2)
	tmplmask = bin_img(tmplmask,2)
	tx = (template.shape)[0]/4
	ty = (template.shape)[1]/4
	ix = (image.shape)[0] - tx
	iy = (image.shape)[1] - ty
	for blob in blobs:
		x = int(blob.stats['center'][1])
		y = int(blob.stats['center'][0])
		if(x > tx and y > ty and x < ix and y < iy):
			smimage = image[ x-tx:x+tx, y-ty:y+ty ]
			angle = anglemap[x/bin,y/bin]
			template2 = nd_image.rotate(template, angle, reshape=False, mode="wrap")
			template2 = bin_img(template2,2)
			rho = corr_coeff(smimage,template2,tmplmask)
			blob.stats['corrcoeff'] = rho
		else:
			blob.stats['corrcoeff'] = -1.0
	initblobs = len(blobs)
	blobs.sort(blob_compare)
	i=0
	while i < len(blobs):
		rho = float(blobs[i].stats['corrcoeff'])
		if(rho <= 0.1):
			del blobs[i]
			i=i-1
		i=i+1
	postblobs = len(blobs)
	print " ... time %.2f sec" % float(time.time()-t1)
	print " ... kept",postblobs,"correlating particles of",initblobs,"total particles"

	

	return blobs

#########################################################

def fake_corrcoeffs(blobs,imfile,bin,template,tmplmask,anglemap):
	print "Faking correlation coefficients"

	for blob in blobs:
		blob.stats['corrcoeff'] = 1.0

	return blobs

#########################################################

def corr_coeff(x,y,mask):
	tot = float(mask.sum())
	x = normStdev(x)
	y = normStdev(y)
	z = x*y
	z = z*mask
	sm  = float(z.sum())
	return sm/tot

#########################################################

def drawBlobs(ccmaxmap,blobs,file,num,bin,pixrad):
	if not (os.path.exists("ccmaxmaps")):
		os.mkdir("ccmaxmaps")

	ccmaxmap = whiteNormalizeImage(ccmaxmap)
	image    = array2image(ccmaxmap)

	draw = ImageDraw.Draw(image)

	ps=float(pixrad) #1x particle radius
	psp = ps+1
	psn = ps-1
	for blob in blobs:
		x1=blob.stats['center'][1]
		y1=blob.stats['center'][0]
		coord=(x1-ps, y1-ps, x1+ps, y1+ps)
		draw.rectangle(coord,outline="white")
		coord=(x1-psp, y1-psp, x1+psp, y1+psp)
		draw.rectangle(coord,outline="black")
		coord=(x1-psn, y1-psn, x1+psn, y1+psn)
		draw.rectangle(coord,outline="black")
		#draw.ellipse(coord,outline="white")

	outfile="ccmaxmaps/"+file+".ccmaxmap"+str(num)+".jpg"
	print " ... writing JPEG: ",outfile
	image.save(outfile, "JPEG", quality=90)

	del image,draw

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
	f.write("#filename x y mean stdev corr_coeff peak_size templ_num angle\n")
	for i in range(len(blobs)):
		for blob in (blobs[i]):
			if blob in allblobs:
				row = blob.stats['center'][0]
				col = blob.stats['center'][1]
				mean = blob.stats['mean']
				std = blob.stats['stddev']
				rho = blob.stats['corrcoeff']
				size = blob.stats['n']
				mean_str = "%.4f" % mean
				std_str = "%.4f" % std
				rho_str = "%.4f" % rho
				#filename x y mean stdev corr_coeff peak_size templ_num angle
				out = file+".mrc "+str(int(col)*bin)+" "+str(int(row)*bin)+ \
					" "+mean_str+" "+std_str+" "+rho_str+" "+str(int(size))+ \
					" "+str(i)
				count = count + 1
				f.write(str(out)+"\n")
	f.close()
	
	del allblobs,f

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
	numer = Mrc.mrc_to_numeric(mrcfile)
	numer = bin_img(numer,bin)

	numer = whiteNormalizeImage(numer)
	image = array2image(numer)
	image = image.convert("RGB")

	pikfile="pikfiles/"+file+".a.pik"

	draw = ImageDraw.Draw(image)
	#blend(image1,image2,0.5)

	circmult = 1.0
	drawPikFile(pikfile,draw,bin,pixrad,circmult)

	outfile="jpgs/"+mrcfile+".prtl.jpg"
	print " ... writing JPEG: ",outfile

	image.save(outfile, "JPEG", quality=95)

	del image,numer,draw

	return

#########################################################

def drawPikFile(file,draw,bin,pixrad,circmult):
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
	ps=float(circmult*pixrad) #1.5x particle radius

	#print " ... reading Pik file: ",file
	f=open(file, 'r')
	#00000000 1 2 3333 44444 5555555555 666666666 777777777
	#filename x y mean stdev corr_coeff peak_size templ_num angle
	psm1 = ps - 1
	for line in f:
		if(line[0] != "#"):
			line=string.rstrip(line)
			bits=line.split(' ')
			x1=float(bits[1])/float(bin)
			y1=float(bits[2])/float(bin)
			coord=(x1-ps, y1-ps, x1+ps, y1+ps)
			coord2=(x1-psm1, y1-psm1, x1+psm1, y1+psm1)
			if(len(bits) > 7):
				#GET templ_num
				num = int(bits[7])%12
			else:
				num = 0
			draw.ellipse(coord,outline=circle_colors[num])
			draw.ellipse(coord2,outline=circle_colors[num])
			#draw.rectangle(coord,outline=color1)
	f.close()
	del f

	return

#########################################################
#########################################################

def whiteNormalizeImage(a):
	"""	
	Normalizes numarray to fit into an image format
	that is values between 0 and 255.
	"""
	#Minimum image value, i.e. how black the image can get
	minlevel = 55.0
	#Maximum image value, i.e. how white the image can get
	maxlevel = 255.0
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

	a = (a - min1)/(max1 - min1)*imrange + minlevel
	a = numarray.where(a > maxlevel,255.0,a)
	a = numarray.where(a < minlevel,45.0,a)

	return a

#########################################################

def blackNormalizeImage(a):
	"""	
	Normalizes numarray to fit into an image format
	that is values between 0 and 255.
	"""
	#Minimum image value, i.e. how black the image can get
	minlevel = 0.0
	#Maximum image value, i.e. how white the image can get
	maxlevel = 200.0
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

	a = (a - min1)/(max1 - min1)*imrange + minlevel
	a = numarray.where(a > maxlevel,215.0,a)
	a = numarray.where(a < minlevel,0.0,a)

	return a

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

	a = (a - min1)/(max1 - min1)*imrange + minlevel
	a = numarray.where(a > maxlevel,255.0,a)
	a = numarray.where(a < minlevel,0.0,a)

	return a

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
	numer = normalizeImage(numer)
	image = array2image(numer)
	#image = image.convert("RGB")
	print " ... writing JPEG: ",file
	image.save(file, "JPEG", quality=85)
	del image
	return

#########################################################

def numeric_to_jpg2(numer,file):
	numer = numer*255.0
	image = array2image(numer)
	#image = image.convert("RGB")
	print " ... writing JPEG: ",file
	image.save(file, "JPEG", quality=85)
	del image
	return

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
	#print " ... size: ",im.shape
	#print " ... sum:  ",im.sum()

	avg1=nd_image.mean(im)
	stdev1=nd_image.standard_deviation(im)
	print " ... avg:  ",round(avg1,6),"+-",round(stdev1,6)

	min1=nd_image.minimum(im)
	max1=nd_image.maximum(im)
	print " ... range:",round(min1,6),"<>",round(max1,6)

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
	#return numarray.array(shape) +numarray.array([1,1])

#########################################################

def cross_correlate(image,template):	
	#CALCULATE BIGGER MAP SIZE
	shape = image.shape
	kshape = template.shape
	oversized = (numarray.array(shape) + numarray.array(kshape))

	#EXPAND IMAGE TO BIGGER SIZE
	image2 = convolve.iraf_frame.frame(image, oversized, mode="wrap", cval=0.0)

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
	#templatefft = fft.fft2d(template, s=oversized)

	return templatefft

#########################################################

def calc_imagefft(image, oversized):
	#EXPAND IMAGE TO BIGGER SIZE
	avg=nd_image.mean(image)
	image2 = convolve.iraf_frame.frame(image, oversized, mode="constant", cval=avg)

	#CALCULATE FOURIER TRANSFORMS
	imagefft = fft.real_fft2d(image2, s=oversized)
	#imagefft = fft.fft2d(image2, s=oversized)
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
	#corr = fft.inverse_fft2d(newfft, s=oversized)
	#corr = corr.astype(numarray.Float64)
	del newfft

	#ROTATION AND SHIFT

	#ROTATE 180 DEGREES, NEIL STYLE
	#corr = numarray.transpose(corr)
	#corr = corr[(corr.shape)[0]::-1,:]
	#corr = numarray.transpose(corr)
	#corr = corr[(corr.shape)[0]::-1,:]

	#ROTATE 180 DEGREES, CRAIG STYLE
	corrshape = corr.shape
	corr = numarray.ravel(corr)
	corr = numarray.reshape(corr[(corr.shape)[0]::-1],corrshape)

	corr = nd_image.shift(corr, tmplshape[0], mode='wrap', order=0)

	#print " ... ... rot time %.2f sec" % float(time.time()-t1)

	#RETURN CENTRAL PART OF IMAGE (SIDES ARE JUNK)
	return corr[ tmplshape[0]-1:imshape[0]+tmplshape[0]-1, tmplshape[1]-1:imshape[1]+tmplshape[1]-1 ]

#########################################################

def calc_normconvmap(image, imagefft, tmplmask, oversized, pixrad):
	t1 = time.time()
	print " ... computing FindEM's norm_conv_map"

	#print " IMAGE"
	#imageinfo(image)
	#numeric_to_jpg(image,"image.jpg")
	#print " TMPLMASK"
	#imageinfo(tmplmask)
	#numeric_to_jpg(tmplmask,"tmplmask.jpg")

	if(nd_image.minimum(image) < 0.0 or nd_image.minimum(tmplmask) < 0.0):
		print " !!! WARNING image or mask is less than zero"

	tmplsize = (tmplmask.shape)[1]
	nmask = tmplmask.sum()
	tmplshape  = tmplmask.shape
	imshape  = image.shape

	shift = int(-1*tmplsize/2.0)
	#tmplmask2 = nd_image.shift(tmplmask, shift, mode='wrap', order=0)
	#tmplmask2 = tmplmask

	err = 0.000001

	#print " IMAGESQ"
	#imageinfo(image*image)

	#print " CNV2 = convolution(image**2, mask)"
	tmplmaskfft = fft.real_fft2d(tmplmask, s=oversized)
	imagesqfft = fft.real_fft2d(image*image, s=oversized)
	cnv2 = convolution_fft(imagesqfft, tmplmaskfft, oversized)
	cnv2 = cnv2 + err
	del imagesqfft
	#SHIFTING CAN BE SLOW
	#cnv2 = nd_image.shift(cnv2, shift, mode='wrap', order=0)
	#imageinfo(cnv2)
	#print cnv2[499,499],cnv2[500,500],cnv2[501,501]
	#numeric_to_jpg(cnv2,"cnv2.jpg")

	#print " CNV1 = convolution(image, mask)"
	cnv1 = convolution_fft(imagefft, tmplmaskfft, oversized)
	cnv1 = cnv1 + err
	del tmplmaskfft
	#SHIFTING CAN BE SLOW
	cnv1 = nd_image.shift(cnv1, shift, mode='wrap', order=0)
	#imageinfo(cnv1)
	#print cnv1[499,499],cnv1[500,500],cnv1[501,501]
	#numeric_to_jpg(cnv1*cnv1,"cnv1.jpg")

	#print " V2 = ((nm*cnv2)-(cnv1*cnv1))/(nm*nm)"
	a1 = nmask*cnv2
	a1 = a1[ tmplshape[0]/2-1:imshape[0]+tmplshape[0]/2-1, tmplshape[1]/2-1:imshape[1]+tmplshape[1]/2-1 ]
	#imageinfo(a1)
	#print a1[499,499],a1[500,500],a1[501,501]
	b1 = cnv1*cnv1
	b1 = b1[ tmplshape[0]/2-1:imshape[0]+tmplshape[0]/2-1, tmplshape[1]/2-1:imshape[1]+tmplshape[1]/2-1 ]
	del cnv2
	del cnv1
	#imageinfo(b1)
	#print b1[499,499],b1[500,500],b1[501,501]

	#print (a1[500,500]-b1[500,500])
	#print nmask**2

	#cross = cross_correlate(a1,b1)
	#print numarray.argmax(numarray.ravel(cross))
	#cross = normRange(cross)
	#cross = numarray.where(cross > 0.8,cross,0.7)
	#cross = nd_image.shift(cross, (cross.shape)[0]/2, mode='wrap', order=0)
	#numeric_to_jpg(cross,"cross.jpg")
	#phase = phase_correlate(a1[128:896,128:896],b1[128:896,128:896])
	#print numarray.argmax(numarray.ravel(phase))
	#phase = normRange(phase)
	#phase = numarray.where(phase > 0.7,phase,0.6)
	#phase = nd_image.shift(phase, (phase.shape)[0]/2, mode='wrap', order=0)
	#numeric_to_jpg(phase,"phase.jpg")

	v2= (a1 - b1)
	v2 = v2/(nmask**2)

	#REMOVE OUTSIDE AREA
	cshape = v2.shape
	white1 = 0.01
 	v2[ 0:pixrad*2, 0:cshape[1] ] = white1
	v2[ 0:cshape[0], 0:pixrad*2 ] = white1
 	v2[ cshape[0]-pixrad*2:cshape[0], 0:cshape[1] ] = white1
	v2[ 0:cshape[0], cshape[1]-pixrad*2:cshape[1] ] = white1

	xn = (v2.shape)[0]/2
	#IMPORTANT TO CHECK FOR ERROR
	if(v2[xn-1,xn-1] > 1.0 or v2[xn,xn] > 1.0 or v2[xn+1,xn+1] > 1.0 \
		or nd_image.mean(v2[xn/2:3*xn/2,xn/2:3*xn/2]) > 1.0):
		print " !!! MAJOR ERROR IN NORMALIZATION CALCUATION (values > 1)"
		imageinfo(v2)
		print " ... VALUES: ",v2[xn-1,xn-1],v2[xn,xn],v2[xn+1,xn+1],nd_image.mean(v2)
		numeric_to_jpg(a1,"a1.jpg")
		numeric_to_jpg(b1,"b1.jpg")
		numeric_to_jpg(b1,"v2.jpg")
		sys.exit(1)
	if(v2[xn-1,xn-1] < 0.0 or v2[xn,xn] < 0.0 or v2[xn+1,xn+1] < 0.0 \
		or nd_image.mean(v2[xn/2:3*xn/2,xn/2:3*xn/2]) < 0.0):
		print " !!! MAJOR ERROR IN NORMALIZATION CALCUATION (values < 0)"
		imageinfo(v2)
		print " ... VALUES: ",v2[xn-1,xn-1],v2[xn,xn],v2[xn+1,xn+1],nd_image.mean(v2)
		numeric_to_jpg(a1,"a1.jpg")
		numeric_to_jpg(b1,"b1.jpg")
		numeric_to_jpg(b1,"v2.jpg")
		sys.exit(1)
	del a1
	del b1
	#numeric_to_jpg(v2,"v2.jpg")

	#print " Normconvmap = sqrt(v2)"
	v2 = numarray.where(v2 < err, err, v2)
	normconvmap = numarray.sqrt(v2)
	#numeric_to_jpg(normconvmap,"normconvmap-zero.jpg")
	#normconvmap = numarray.where(v2 > err, numarray.sqrt(v2), 0.0)
	del v2

	#imageinfo(normconvmap)
	#print normconvmap[499,499],normconvmap[500,500],normconvmap[501,501]
	#numeric_to_jpg(normconvmap,"normconvmap-big.jpg")
	print " ... ... time %.2f sec" % float(time.time()-t1)

	#RETURN CENTER
	return normconvmap

#########################################################

def convolution_fft(afft,bfft,oversized):
	#THIS IS:
	# fft1 x fft2
	nx = (afft.shape)[0]
	#ny = (afft.shape)[1]
	cfft = afft * bfft
	c = fft.inverse_real_fft2d(cfft, s=oversized)
	#c = fft.inverse_fft2d(cfft, s=oversized)
	#c = c.astype(numarray.Float64)

	del cfft
	#c=c
	return c

#########################################################

def phase_correlate(image, template):	
	#CALCULATE BIGGER MAP SIZE
	shape = image.shape
	kshape = template.shape
	oversized = (numarray.array(shape) + numarray.array(kshape))

	#EXPAND IMAGE TO BIGGER SIZE
	avg=nd_image.mean(image)
	image2 = convolve.iraf_frame.frame(image, oversized, mode="wrap", cval=avg)

	#CALCULATE FOURIER TRANSFORMS
	imagefft = fft.real_fft2d(image2, s=oversized)
	templatefft = fft.real_fft2d(template, s=oversized)
	#imagefft = fft.fft2d(image2, s=oversized)
	#templatefft = fft.fft2d(template, s=oversized)

	#MULTIPLY FFTs TOGETHER
	newfft = (templatefft * numarray.conjugate(imagefft)).copy()
	del templatefft

	#NORMALIZE CC TO GET PC
	print "d"
	phasefft = newfft / numarray.absolute(newfft)
	del newfft
	print "d"

	#INVERSE TRANSFORM TO GET RESULT
	correlation = fft.inverse_real_fft2d(phasefft, s=oversized)
	#correlation = fft.inverse_fft2d(phasefft, s=oversized)
	del phasefft

	#RETURN CENTRAL PART OF IMAGE (SIDES ARE JUNK)
	return correlation[ kshape[0]/2-1:shape[0]+kshape[0]/2-1, kshape[1]/2-1:shape[1]+kshape[1]/2-1 ]

#########################################################

def bin_img(image,bin):
	""" zoom does a bad job of binning """
	#return nd_image.zoom(img,1.0/float(binning),order=1)
	""" numextension used to cause mem leaks """
	return imagefun.bin(image,bin)

