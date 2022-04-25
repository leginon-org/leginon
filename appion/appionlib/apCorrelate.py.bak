#Future home of cross-correlation functions

import numpy
import scipy.ndimage as nd_image
#import numpy.convolve as convolve
#import numpy.fft as fft
import numpy.random as random_array
#import numpy.linear_algebra as linear_algebra

def runCrossCorr(params,file):
	# Run Neil's version of FindEM
	#imagefile = file+".mrc"
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

		strt=float(params["startang"+str(classavg)])
		end=float(params["endang"+str(classavg)])
		incr=float(params["incrang"+str(classavg)])

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

def getOverSize(image,template):
	shape     = image.shape
	kshape    = template.shape
	oversized = (numarray.array(shape) + numarray.array(kshape)).copy()
	return oversized
	#return numarray.array(shape) +numarray.array([1,1])

#########################################################

def crossCorrelate(image,template):	
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

def calcTemplateFft(template, oversized):
	#CALCULATE FOURIER TRANSFORMS
	templatefft = fft.real_fft2d(template, s=oversized)
	#templatefft = fft.fft2d(template, s=oversized)

	return templatefft

#########################################################

def calcImageFft(image, oversized):
	#EXPAND IMAGE TO BIGGER SIZE
	avg=nd_image.mean(image)
	image2 = convolve.iraf_frame.frame(image, oversized, mode="constant", cval=avg)

	#CALCULATE FOURIER TRANSFORMS
	imagefft = fft.real_fft2d(image2, s=oversized)
	#imagefft = fft.fft2d(image2, s=oversized)
	del image2

	return imagefft

#########################################################

def crossCorrelateFft(imagefft, templatefft, imshape, tmplshape):
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

def calcNormConvMap(image, imagefft, tmplmask, oversized, pixrad):
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

def convolutionFft(afft,bfft,oversized):
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

def phaseCorrelate(image, template):	
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
	absfft = numarray.absolute(newfft.copy())
	phasefft = numarray.where(absfft>0, newfft/absfft, 0)
	#phasefft = newfft / numarray.absolute(newfft)
	del newfft
	print "d"

	#INVERSE TRANSFORM TO GET RESULT
	correlation = fft.inverse_real_fft2d(phasefft, s=oversized)
	#correlation = fft.inverse_fft2d(phasefft, s=oversized)
	del phasefft

	#RETURN CENTRAL PART OF IMAGE (SIDES ARE JUNK)
	return correlation[ kshape[0]/2-1:shape[0]+kshape[0]/2-1, kshape[1]/2-1:shape[1]+kshape[1]/2-1 ]
