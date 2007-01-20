#!/usr/bin/env python

import sys
import os
import Mrc
import imagefun
import numarray
import numarray.nd_image
import Image
import ImageDraw
import numextension
import string
import math

def findPeaks2(params,file):
	#Does NOT use viewit
	#Resulting in a 5-fold speed up over findPeaks()

	threshold = float(params["thresh"])
	numtempl =  len(params['templatelist'])
	bin =       int(params["bin"])
	diam =      float(params["diam"])
	apix =      float(params["apix"])

	blobs = []
	for i in range(numtempl):
		blobs.append(findPeaksInMap(file,i+1,threshold,bin))

	mergePikFiles(file,blobs,diam,bin,apix)

	return

def findPeaksInMap(file,num,threshold,bin):

	infile="cccmaxmap"+str(num)+"00.mrc"
	outfile="pikfiles/"+file+"."+str(num)+".pik"
	if (os.path.exists(outfile)):
		os.remove(outfile)
		print "...removed existing file:",outfile

	cc=Mrc.mrc_to_numeric(infile)
	cc2=imagefun.threshold(cc,threshold)

	#Mrc.numeric_to_mrc(cc2,"threshold.mrc")

	#for i in range(30):
	#	thresh = threshold + float(i-15)*0.01
	#	cc2=imagefun.threshold(cc,thresh)
	#	blobs = imagefun.find_blobs(cc,cc2,6,3000,60,1)
	#	print thresh," ",len(blobs)

	blobs = imagefun.find_blobs(cc,cc2,6,100,int(250/bin**2+1),0)
	#find_blobs(image,mask,border,maxblobs,maxblobsize,minblobsize)
	print "Template "+str(num)+": Found",len(blobs),"peaks"

	blobs.sort(blob_compare)

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

	return blobs

def blob_compare(x,y):
	if float(x.stats['mean']) < float(y.stats['mean']):
		return 1
	else:
		return -1

def mergePikFiles(file,blobs,diam,bin,apix):
	print "Merging #.pik files into a.pik file"
	outfile="pikfiles/"+file+"-2.a.pik"
	if (os.path.exists(outfile)):
		os.remove(outfile)
		print "...removed existing file:",outfile

	#distance in pixels for two blobs to be too close together
	cutoff = 1.5*diam*0.5/float(bin)/apix	#1.5x particle radius in pixels
	print "... distance cutoff:",cutoff,"pixels"
	cutsq = cutoff**2+1

	allblobs = []
	for i in range(len(blobs)):
		allblobs.extend(blobs[i])
		#for j in range(len(blobs[i])):
		#	allblobs.append((blobs[i])[j])

	initblobs = len(allblobs)

	allblobs.sort(blob_compare)
	
	i=0
	while i < len(allblobs):
		j=0
		while j < i:
			distsq = blob_distsq((allblobs)[i],(allblobs)[j])
			if(distsq < cutsq):
				#print j,i,math.sqrt(distsq)
				del allblobs[i]
				i=i-1
				j=j-1
			j=j+1
		i=i+1

	postblobs = len(allblobs)

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
				f.write(str(out)+"\n")
	f.close()
		
	print "Kept",postblobs,"of",initblobs,"particles"	
	return


def blob_distsq(x,y):
	row1 = x.stats['center'][0]
	col1 = x.stats['center'][1]
	row2 = y.stats['center'][0]
	col2 = y.stats['center'][1]
	return (row1-row2)**2+(col1-col2)**2


def createJPG2(params,file):
	#Does NOT use viewit
	#Resulting in a 2-fold speed up over createJPG()
	#With more features!!!

	mrcfile = file+".mrc"
	count =   len(params['templatelist'])
	bin =     int(params["bin"])
	diam =    float(params["diam"])
	apix =    float(params["apix"])

	if not (os.path.exists("jpgs")):
		os.mkdir("jpgs")

	#print "Reading MRC: ",mrcfile
	numer=Mrc.mrc_to_numeric(mrcfile)
	numer=numextension.bin(numer,bin)

	#print "Image: ",numer.getshape()
	numer=normalizeImage(numer)
	image2 = array2image(numer)
	image2 = image2.convert("RGB")

	pikfile="pikfiles/"+file+"-2.a.pik"
	print "Reading Pik: ",pikfile
	draw = ImageDraw.Draw(image2)
	#blend(image1,image2,0.5)
	draw = readPikFile(pikfile,draw,diam,bin,apix) 
	del draw

	
	outfile="jpgs/"+file+".prtl-2.jpg"
	print "Writing JPEG: ",outfile
	image2.save(outfile, "JPEG", quality=95)


def normalizeImage(a):
    screenLevels = 240.0
    print "Normalizing image..."
    #b=numarray.ravel(a)
    devlimit=5

    avg1=numarray.nd_image.mean(a)
    #print "Average: ",avg1

    stdev1=numarray.nd_image.standard_deviation(a)
    #print "Stdev:   ",stdev1

    min1=numarray.nd_image.minimum(a) #b[numarray.argmin(b)]
    #print "Min:     ",min1
    if(min1 < avg1-devlimit*stdev1):
	#print "BIG MIN"
    	min1 = avg1-devlimit*stdev1

    max1=numarray.nd_image.maximum(a)
    #print "Max:     ",max1
    if(max1 > avg1+devlimit*stdev1):
	#print "BIG MAX"
    	max1 = avg1+devlimit*stdev1

    c = (a - min1)/(max1 - min1)*screenLevels

    #print "done"
    return c


def array2image(a):
    #print "Converting image..."
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
    #print "done"
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





def readPikFile(file,draw,diam,bin,apix):
	print "Making circles..."

	circle_colors = [ \
		"#ff4040","#3df23d","#3d3df2", \
		"#f2f23d","#3df2f2","#f23df2", \
		"#f2973d","#3df297","#973df2", \
		"#97f23d","#3d97f2","#f23d97", ]
	ps=int(1.5*diam*0.5/float(bin)/apix) #1.5x particle radius
	ps=float(1.5*diam*0.5/float(bin)/apix) #1.5x particle radius
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
			num = int(bits[6])
		else:
			num = 0
		draw.ellipse(coord,outline=circle_colors[num])
		#draw.rectangle(coord,outline=color1)
	f.close()
	return draw
