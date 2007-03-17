#crud functions called by crudFinder.py

import apImage
import apConvexHull
import os,sys
import math
import numarray
import numarray.ma as ma
import numarray.nd_image as nd
import Mrc
import convolver
import Image
import ImageDraw
import imagefun
import numextension
import polygon
import libCV
import selexonFunctions2
import string
import operator

def prepImage(image,cutoff=5.0):
	shape=numarray.shape(image)
	garea,gavg,gstdev=maskImageStats(image)
	print 'image mean= %.1f stdev= %.1f' %(gavg,gstdev)
	cleanimage=ma.masked_outside(image,gavg-cutoff*gstdev,gavg+cutoff*gstdev)
	carea,cavg,cstdev=maskImageStats(cleanimage)
	
	image=cleanimage.filled(cavg)
	return image


def medium(image):
	size=image.size()
	image1d=numarray.reshape(image,(image.size()))
	image1d.sort()
	medium=image1d[size/2]
	topquad=image1d[size*3/4]
	botquad=image1d[size/4]
	return medium,topquad,botquad

def outputImage(array,name,description,testlog):
	width=25
	if testlog[0]:
		jpgname="tests/%02d%s.jpg" %(testlog[1],name)
		space=(width-len(jpgname))*' '
		testlog[2]+= "%s:%s%s\n" % (jpgname,space,description)
		testlog[1] += 1
	else:
		if testlog[1] == -1:
			jpgname="jpgs/%s.crud.jpg" %(name,)
		else:
			return testlog
	if array.type()==numarray.Bool:
		array=array.astype(numarray.Int8)
	if array.type()==numarray.UInt8:
		array=array.astype(numarray.Int16)
	if array.type()==numarray.Int64:
		array=array.astype(numarray.Int32)
	if array.max()-array.min() >0.1:
		array = selexonFunctions2.whiteNormalizeImage(array)
	PILimage = selexonFunctions2.array2image(array)
	PILimage.save(jpgname, "JPEG", quality=95)
	return testlog

def findEdgeSobel(image,sigma,amin,amax,output,testlog):
	if (sigma > 0):
		smooth=nd.gaussian_filter(image,sigma)
		if (output):
			testlog=outputImage(smooth,'smooth','filtered image',testlog)
	else:
		smooth=image

	edges=nd.generic_gradient_magnitude(smooth, derivative=nd.sobel)
	if (output):
		testlog=outputImage(edges,'edge','edge image',testlog)

	edgemax=edges.max()
	tedges=ma.masked_inside(edges,edgemax*amin,edgemax*amax)
	return tedges,testlog

def findEdgeCanny(image,sigma,amin,amax,output,testlog):

	tedges,gradient = canny(image,sigma,5,True,amin,amax)

	if (output):
		testlog=outputImage(gradient,'grad','gradient magnitude image',testlog)
	
	return tedges,testlog

def canny(image, sigma=1.8, nonmaximawindow=7, hysteresis=True, tlow=0.3, thigh=0.9):
	edgeimage,grad_mag = numextension.cannyedge(image,sigma,tlow,thigh)
	edges = ma.masked_less(edgeimage,100,0)
	return edges, grad_mag

def fillMask(mask_image,iteration):
	base=nd.generate_binary_structure(2,2)
	mask_image=nd.binary_dilation(mask_image,structure=base,iterations=iteration)
	base=nd.generate_binary_structure(2,1)
	mask_image=nd.binary_erosion(mask_image,structure=base,iterations=iteration)
	return mask_image
	

def makeDisk(radius):
	#make  disk mask
	#This is copied from jahcfinderback.py and should be organized properly in pyleginon
	radius=int(radius)
	cutoff=[0.0,0.0]
	diskimageshape=(2*radius,2*radius)
	center=[radius,radius]
	lshift=[0.0,0.0]
	gshift=[0.0,0.0]
	minradsq=0
	maxradsq=radius*radius
	
	def circle(indices0,indices1):
		## this shifts and wraps the indices
		i0 = numarray.where(indices0<cutoff[0], indices0-center[0]+lshift[0], indices0-center[0]+gshift[0])
		i1 = numarray.where(indices1<cutoff[1], indices1-center[1]+lshift[1], indices1-center[1]+gshift[1])
		rsq = i0*i0+i1*i1
		c = numarray.where((rsq>=minradsq)&(rsq<=maxradsq), 1, 0)
		return c.astype(numarray.Int8)
	disk = numarray.fromfunction(circle,diskimageshape)
	return disk

def maskImageStats(mimage):
	n=ma.count(mimage)
	mimagesq=mimage*mimage
	sum1=ma.sum(mimage)
	sum2=ma.sum(sum1)
	sumsq1=ma.sum(mimagesq)
	sumsq2=ma.sum(sumsq1)
	avg=sum2/n
	if (n > 1):
		stdev=math.sqrt((sumsq2-sum2*sum2/n)/(n-1))
	else:
		stdev=2e20
	return n,avg,stdev

def convolveDisk(bimage,radius,convolve_t,testlog):
	#make  disk binaray image
	disk = makeDisk(radius)
	diskshape=numarray.shape(disk)

	# convolve
	c=convolver.Convolver()
	c.setImage(bimage)
	c.setKernel(disk)
	cmask=c.convolve()

	# convolve two disks to get maximum correlation
	c=convolver.Convolver()
	c.setImage(disk)
	c.setKernel(disk)
	cref=c.convolve()
	testlog=outputImage(cmask,'maskc','Convolved filled edge mask',testlog)
	
	# Thresholding to binary mask
	cmax=cref.max()*convolve_t
	masked_cmask=ma.masked_greater(cmask,cmax)
	mask=ma.getmask(masked_cmask)
	testlog=outputImage(mask,'maskct','Thresholded Convolved mask',testlog)
	return mask,testlog
		
def findConvexHullsFromPoints(points):
	polygons=[]
	if (len(points) >3):
		polygon=apConvexHull.convexHull(points)
		polygon=list(polygon)
	else:
		polygon=points
	return polygon		

def oneObjToGlobalPoints(bimage):
	cruds,clabels=nd.label(bimage)
	crud_objs=nd.find_objects(cruds,max_label=clabels)
	l=0
	one_crud=bimage[crud_objs[l]]
	starts=(crud_objs[l][0].start,crud_objs[l][1].start)
	crud_dim=numarray.shape(one_crud)
	gpoints=[]
	for x in range(crud_dim[0]):
		for y in range(crud_dim[1]):
			if one_crud[x][y]:
				gpoints.append((x+starts[0],y+starts[1]))
	return gpoints

def findConvexHullsFromLabeledImage(bimage,cruds,clabels):
	gpolygons=[]
	# individual crud is masked to avoid problem of overlapped of crud_obj slices
	for l in range(1,clabels+1):
		region=ma.masked_outside(cruds,l,l)
		mask=1-ma.getmask(region)
		gpoints=oneObjToGlobalPoints(mask)
		gpolygon=findConvexHullsFromPoints(gpoints)
		gpolygons.append(gpolygon)
	return gpolygons
		
def mergePolygonPoints(polygons):
	p1=0
	result=list(polygons)
	while p1 in range(len(result)):
		p2=p1+1
		has_overlap=False
		polygon1=polygons[p1]
		while p2 in range(len(result)):
			polygon2=polygons[p2]
			overlapped_points=polygon.pointsInPolygon(polygon1,polygon2)
			if len(overlapped_points) > 0:
				polygons[p2].extend(polygon1)
				has_overlap=True
			p2=p2+1

		if has_overlap==False:
			p1=p1+1
		else:
			polygons.pop(p1)
		result=list(polygons)
	#create new convex hulls
	for p in range(len(result)):
		pointset = list(set(polygons[p]))
		new_polygon=findConvexHullsFromPoints(pointset)
		result[p]=new_polygon

	return result		  

def makeGlobalPolygons(shape,crud_objs,polygons):
	gpolygons=[]
	ltotal=len(crud_objs)
	for l in range(ltotal):
		starts=(crud_objs[l][0].start,crud_objs[l][1].start)
		gpoints=[]
		for point in polygons[l]:
			gpoint=(point[0]+starts[0],point[1]+starts[1])
			gpoints.append(gpoint)
		gpolygons.append(gpoints)
	return gpolygons

def makeLocalPolygons(gpolygons):
	crud_objs=[]
	polygons=[]
	for l in range(len(gpolygons)):
		xs=[]
		ys=[]
		points=[]
		for point in gpolygons[l]:
			xs.append(point[0])
			ys.append(point[1])
		xs.sort()
		ys.sort()
		crud_obj=(slice(xs[0],xs[-1]+1),slice(ys[0],ys[-1]+1))
		crud_objs.append(crud_obj)
		for point in gpolygons[l]:
			point=(point[0]-xs[0],point[1]-ys[0])
			points.append(point)
		polygons.append(points)
	return crud_objs,polygons

def convexHullUnion(bimage,cruds,clabels,testlog):
	shape=numarray.shape(bimage)
	print "making convex hulls"
	gpolygons=findConvexHullsFromLabeledImage(bimage,cruds,clabels)
	
	print "merging from %d convex hulls" % len(gpolygons)
	gpolygons=mergePolygonPoints(gpolygons)
	print "merged to %d convex hulls" % len(gpolygons)

	#fill polygons and make a labeled image
	polygon_image=polygon.plotPolygons(shape,gpolygons)
	cruds,clabels=nd.label(polygon_image)

	testlog=outputImage(cruds,'crud_labelp','Convex hull union labeled polygons',testlog)
	return cruds,clabels,gpolygons,testlog
	
def getLabeledInfo(image,alledgemask,labeled_image,ltotal,fast,testlog):
	print "getting crud info"
	info={}
	imageshape=numarray.shape(labeled_image)
	if not fast:
		edgeimage,testlog=findEdgeSobel(alledgemask,0,-1,0.0,False,testlog)
		mask=1-ma.getmask(edgeimage)
		mask=nd.binary_dilation(mask,iterations=1)
		testlog=outputImage(mask,'labeledge','Edges of the image labels',testlog)
	else:
		objs = nd.find_objects(labeled_image)
	ones=numarray.ones(imageshape)
	# individual crud is masked to avoid problem of overlapped of crud_obj slices
	avgall = nd.mean(image)
	for l in range(1,ltotal+1):
		if not fast:
			length=nd.sum(mask,labels=labeled_image,index=l)
			area=nd.sum(ones,labels=labeled_image,index=l)
			avg=nd.mean(image,labels=labeled_image,index=l)
			stdev=nd.standard_deviation(image,labels=labeled_image,index=l)
			center=nd.center_of_mass(ones,labels=labeled_image,index=l)
		else:
			lengths = []
			lengths.append(objs[l-1][0].stop - objs[l-1][0].start)
			lengths.append(objs[l-1][1].stop - objs[l-1][1].start)
			length = 2*(lengths[0]+lengths[1])
			area = lengths[0]*lengths[1]
			avg = avgall
			stdev = 2
			center=(imageshape[0]/2,imageshape[1]/2)
		info[l]=(area,avg,stdev,length,center)
	return info,testlog 

def getPolygonInfo(polygons,testlog):
	print "get polygon info"
	polygons_arrays = polygon.polygons_tuples2arrays(polygons)
	info={}
	for l,p in enumerate(polygons_arrays):
		length = 2*(p[:,0].max()-p[:,0].min())+2*(p[:,1].max()-p[:,1].min())
		area = polygon.getPolygonArea(p)
		center = polygon.getPolygonCenter(p)
		avg = 100
		stdev = 2
		info[l+1]=(area,avg,stdev,length,center)
	return info,testlog 
		
def pruneByLength(info,length_min,length_max,goodcruds_in):
	print "pruning by edge length"
	goodcruds=[]
	for l in range(1,len(info)+1):
		length=info[l][3]
		if (length > length_min and length < length_max):
			if l-1 in goodcruds_in:
				goodcruds.append(l-1)
	print "pruned to %d region" %len(goodcruds)
	return goodcruds


def pruneByArea(info,area_min,area_max,goodcruds_in):
	print "pruning by area"
	goodcruds=[]
	for l in range(1,len(info)+1):
		area=info[l][0]
		if (area > area_min and area < area_max):
			if l-1 in goodcruds_in:
				goodcruds.append(l-1)
	print "pruned to %d region" %len(goodcruds)
	return goodcruds

def pruneByStdev(info,stdev_min,goodcruds_in):
	print "pruning by stdev"
	goodcruds=[]
	for l in range(1,len(info)+1):
		stdev=info[l][2]
		if (stdev > stdev_min):
			if l-1 in goodcruds_in:
				goodcruds.append(l-1)
	print "pruned to %d region" %len(goodcruds)
	return goodcruds
	
def makePrunedLabels(file,labeled_image,ltotal,info,goodlabels):
	print "remaking %d labeled image after pruning" % len(goodlabels)

	new_labeled_image = makeImageFromLabels(labeled_image,ltotal,goodlabels)

	goodinfo=""
	for i,l1 in enumerate(goodlabels):
		# output: centerx centery area average stdev length
		l=l1+1
		goodcrudline=file+".mrc "+str(int(info[l][4][1]))+" "+str(int(info[l][4][0]))+" "+str(info[l][0])+" "+str(info[l][1])+" "+str(info[l][2])+" "+str(info[l][3])+"\n"
		goodinfo=goodinfo+goodcrudline

	return new_labeled_image,len(goodlabels),goodinfo

def makeImageFromLabels(labeled_image,ltotal,goodlabels):
	imageshape=numarray.shape(labeled_image)
	if len(goodlabels)==0:
		return new_labeled_image
	else:
		if len(goodlabels)==ltotal:
			return labeled_image
	if len(goodlabels)*2 < ltotal:
		new_labeled_image=numarray.zeros(imageshape,numarray.Int8)
		for i,l1 in enumerate(goodlabels):
			l=l1+1
			region=numarray.where(labeled_image==l,1,0)
			numarray.putmask(new_labeled_image,region,i+1)
	else:
		tmp_labeled_image=labeled_image
		badset=set(range(ltotal))
		badset=badset.difference(set(goodlabels))
		for i,l1 in enumerate(badset):
			l=l1+1
			region=numarray.where(labeled_image==l,1,0)
			numarray.putmask(tmp_labeled_image,region,i+1)
		new_labeled_image,resultlabels = nd.label(tmp_labeled_image)
	return new_labeled_image

def makePrunedPolygons(file,gpolygons,imageshape,info,goodlabels):
	print "remaking %d polygons after pruning" % len(goodlabels)
	goodpolygons=[]
	goodinfo=""
	if len(goodlabels)==0:
		new_labeled_image=numarray.zeros(imageshape,numarray.Int8)
		return new_labeled_image,len(goodlabels),goodinfo
	for l1 in goodlabels:
		l=l1+1
		goodcrudline=file+".mrc "+str(int(info[l][4][1]))+" "+str(int(info[l][4][0]))+" "+str(info[l][0])+" "+str(info[l][1])+" "+str(info[l][2])+" "+str(info[l][3])+"\n"
		goodinfo=goodinfo+goodcrudline
		goodpolygons.append(gpolygons[l1])
	cruds = polygon.plotPolygons(imageshape,goodpolygons)
	return cruds,len(goodpolygons),goodinfo


def reduceRegions(regions,velimit):
	regionarrays = []
	regionellipses = []
	for i,region in enumerate(regions):
		regionpolygon = region['regionEllipse']
		regionaxismajor = regionpolygon[2]
		regionaxisminor = regionpolygon[3]
		overlap = False
		regionrow = int(regionpolygon[0])
		regioncol = int(regionpolygon[1])
		for j,regionellipse in enumerate(regionellipses):
			halfminor = 0.5*regionellipse[3]
			if regionrow > regionellipse[0]-halfminor and regionrow < regionellipse[0]+halfminor and regioncol > regionellipse[1]-halfminor and regioncol < regionellipse[1]+halfminor:
				overlap = True
				break
		if not overlap:
			regionellipse = region['regionEllipse']
			regionarray = region['regionBorder']
			## reduce to 20 points
			regionarray = libCV.PolygonVE(regionarray, velimit)
			regionarray.transpose()
			regionarrays.append(regionarray)
			regionellipses.append(regionellipse)
					
	return regionarrays
	

def findCrud(params,file):
	filelog="\nTEST OUTPUT IMAGES\n----------------------------------------\n"
	# create "jpgs" directory if doesn't exist
	if not (os.path.exists("jpgs")):
		os.mkdir("jpgs")

	# remove crud info file if it exists
	if (os.path.exists("crudfiles/"+file+".crud")):
		os.remove("crudfiles/"+file+".crud")
	
	
	bin=int(params["bin"])
	apix=float(params["apix"])
	scale=bin*apix

	diam=float(params["diam"]/scale)
	cdiam=float(params["cdiam"]/scale)
	if (params["cdiam"]==0):
		cdiam=diam
	else:
		cdiam=float(params["cdiam"]/scale)
	sigma=float(params["cblur"]) # blur amount for edge detection
	low_tn=float(params["clo"]) # low threshold for edge detection
	high_tn=float(params["chi"]) # upper threshold for edge detection
	scale_high=float(params["cschi"]) # hi threshold for scaling edge detection
	scale_low=float(params["csclo"]) # lower threshold for scaling edge detection
	stdev_t=float(params["stdev"]) # lower threshold for stdev pruning
	convolve_t=float(params["convolve"]) # convolved mask threshold
	do_convex_hulls=not params["no_hull"] # convex hull flag
	do_cv=params["cv"] # convex hull flag
	do_prune_by_length=not params["no_length_prune"] # convex hull flag
	test=params["test"] # test mode flag
	lognumber=0
	testlog=[test,lognumber,filelog]
	# create "tests" directory if doesn't exist
	if (test):
		if (os.path.exists("tests")):
			testfiles=os.listdir("tests")
			for testfilename in testfiles:
				os.remove("tests/"+testfilename)
		else:
			os.mkdir("tests")

	pm = 2.0
	am = 3.0
	
	list_t=pm*3.14159*cdiam
	pradius = diam/2.0	
	cradius=cdiam/2.0
	area_t=am*3.1415926*cradius*cradius
	crudinfo=""
		
	image=Mrc.mrc_to_numeric(file+".mrc")
	image=imagefun.bin(image,bin)
	shape=numarray.shape(image)

	cutoff=8.0
	# remove spikes in the image first
	image=prepImage(image,cutoff)
	garea,gavg,gstdev=maskImageStats(image)

	if (scale_high == 1):
		high=high_tn
		low=low_tn
	else:
		# scale the edge detection limits in the range of scale_high and scale_low
		# This creates an edge detection less sensitive to noise in images without particles
		delta_scale=scale_high-scale_low
		delta_stdev=gstdev-scale_low
		if (delta_stdev <= 0):
			low=1.0
			high=1.0
		else:
			if (delta_stdev >=delta_scale or delta_scale==0):
				low=low_tn
				high=high_tn
			else:
				low=(low_tn-1.0)*delta_stdev/delta_scale+1.0
				high=(high_tn-1.0)*delta_stdev/delta_scale+1.0

	print 'scaled crudhi= %.4f crudlo= %.4f' %(high,low)

	if (test):
		testlog=outputImage(image,'input','input image',testlog)

	#binary edge
	if convolve_t < 0.001:
		edgeimage,testlog=findEdgeCanny(image,sigma,low,high,True,testlog)
	else:
		edgeimage,testlog=findEdgeSobel(image,sigma,low,high,True,testlog)

	nedge=ma.count(edgeimage)
	# If the area not within the threshold is too large or zero, no further calculation is necessary
	if (nedge <image.size()*0.1 or nedge ==image.size()):
		superimage=image
		crudinfo=""
	else:
		mask=ma.getmask(edgeimage)
		maskedimage=ma.masked_array(image,mask=mask,fill_value=0)
		testlog=outputImage(mask,'mask','Thresholded edge binary image mask',testlog)

		#fill
		iteration=3
		mask=fillMask(mask,iteration)
		testlog=outputImage(mask,'maskf','Hole filled edge mask',testlog)

		if (convolve_t > 0):
			#convolve with the disk image of the particle
			mask,testlog=convolveDisk(mask,pradius,convolve_t,testlog)
		

		#segmentation
		
		cruds,clabels=nd.label(mask)
		print "starting with",clabels, "cruds"
		testlog=outputImage(cruds,'crud_label','Segmented labeled image',testlog)

		#pruning by length of the perimeters of the labeled regions.
		if (do_prune_by_length):
			allinfo,testlog=getLabeledInfo(image,mask,cruds,clabels,True,testlog)
			goodcruds=range(clabels)
			goodcruds=pruneByLength(allinfo,list_t,garea*0.5,goodcruds)
			cruds,clabels,goodinfo=makePrunedLabels(file,cruds,clabels,allinfo,goodcruds)
		
		#create convex hulls and merge overlapped or inside cruds
		if do_convex_hulls:
			cruds,clabels,gpolygons,testlog=convexHullUnion(mask,cruds,clabels,testlog)
		else:
			if do_cv:
				regions,dummyimage=libCV.FindRegions(mask,area_t,0.5,1,0,1,0)
				gpolygons = reduceRegions(regions,60)
				clabels = len(gpolygons)

		if (clabels > 0):
			testlog[0]=False
			if do_convex_hulls or do_cv:
				if stdev_t < 0.001:
					allinfo,testlog=getPolygonInfo(gpolygons,testlog)
				else:
					mask = polygon.plotPolygons(shape,gpolygons)
					cruds,clabels=nd.label(mask)
					allinfo,testlog=getLabeledInfo(image,mask,cruds,clabels,False,testlog)
			else:				
				allinfo,testlog=getLabeledInfo(image,mask,cruds,clabels,False,testlog)
			testlog[0]=test
			goodcruds=range(clabels)
			if not do_cv:
				#pruning by area as in selexon
				goodcruds=pruneByArea(allinfo,area_t,garea*0.5,goodcruds)
				if (test):
					temp_cruds,temp_clabels,goodinfo=makePrunedLabels(file,cruds,clabels,allinfo,goodcruds)
					testlog=outputImage(temp_cruds,'crud_labela','Area pruned labeled image',testlog)

			if (len(goodcruds)>0):
				#pruning by standard deviation in the cruds
				if (stdev_t > 0):
					stdev_limit=stdev_t*gstdev
					goodcruds=pruneByStdev(allinfo,stdev_limit,goodcruds)

					if (test):
						temp_cruds,temp_clabels,goodinfo=makePrunedLabels(file,cruds,clabels,allinfo,goodcruds)
						testlog=outputImage(temp_cruds,'crud_labels','Stdev pruned labeled image',testlog)

			if test and (not do_cv or stdev_t > 0):
				cruds,clabels,crudinfo=temp_cruds,temp_clabels,goodinfo
				goodcruds=range(clabels)

			if not test:
				if do_convex_hulls or do_cv and stdev_t < 0.01:
					cruds,clabels,crudinfo=makePrunedPolygons(file,gpolygons,shape,allinfo,goodcruds)
				else:
					cruds,clabels,crudinfo=makePrunedLabels(file,cruds,clabels,allinfo,goodcruds)

#		create edge image of the cruds for display
		if (clabels >0):
			int32cruds=cruds.astype(numarray.Int32)
			equalcruds=ma.masked_greater_equal(int32cruds,1)
			equalcruds=equalcruds.filled(100)
			if (test):
				testlog=outputImage(equalcruds,'finalcruds','Final Crud image',testlog)
			crudedges,testlog=findEdgeSobel(equalcruds,1,0.5,1.0,False,testlog)
			masklabel=1-ma.getmask(crudedges)
		else:
			masklabel=numarray.ones(shape)
			equalcruds=numarray.zeros(shape)
		superimage=image*masklabel
	
	testlog=outputImage(superimage,'output','Final Crud w/ image',testlog)
	
	if (test):
		print testlog[2]
	
	testlog[0]=False
	testlog[1]=-1
	testlog=outputImage(superimage,file,'Final Crud w/ image',testlog)
	
	crudfile=open("crudfiles/"+file+".crud",'w')
	crudfile.write(crudinfo+"\n")
	crudfile.close()
	
	return equalcruds
		
def piksNotInCrud(params,mask,piklines):
	bin = int(params["bin"])
	shape = numarray.shape(mask)
	print shape
	piklinesNotInCrud=[]
	for pikline in piklines:
		bits=pikline.split(' ')
		pik=(int(bits[1]),int(bits[2]))
		binpik = (int(pik[0]/bin),int(pik[1]/bin))
		if binpik[0] in range(0,shape[0]) and binpik[1] in range(0,shape[1]):
			if mask[binpik]==0:
				piklinesNotInCrud.append(pikline)
	return piklinesNotInCrud
	
def readPiksFile(file,extra=''):
	#print " ... reading Pik file: ",file
	f=open(file+extra, 'r')
	#00000000 1 2 3333 44444 5555555555 666666666 777777777
	#filename x y mean stdev corr_coeff peak_size templ_num angle moment
	piks = []
	piklines = []
	for line in f:
		if(line[0] != "#"):
			line.strip()
			piklines.append(line)
	return piklines
	
def writePiksFile(file,extra='',piklines=[]):
	pikstring=''.join(piklines)
	f=open(file+extra, 'w')
	f.write(pikstring)
	
def removeCrudPiks(params,file):
	print "Start Removing Piks in Cruds"
	pikfile = "pikfiles/"+file+".a.pik"
	piklines = readPiksFile(pikfile)
	crudmask=findCrud(params,file)
	print "Removing Bad Picks"
	piklinesgood = piksNotInCrud(params,crudmask,piklines)
	writePiksFile(pikfile,'.nocrud',piklinesgood)
