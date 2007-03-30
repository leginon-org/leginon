#region finding functions called by makeMask.py

import apDatabase
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
		return testlog
	apImage.arrayToJpeg(array,jpgname)
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
	regions,clabels=nd.label(bimage)
	region_objs=nd.find_objects(regions,max_label=clabels)
	l=0
	one_region=bimage[region_objs[l]]
	starts=(region_objs[l][0].start,region_objs[l][1].start)
	region_dim=numarray.shape(one_region)
	gpoints=[]
	for x in range(region_dim[0]):
		for y in range(region_dim[1]):
			if one_region[x][y]:
				gpoints.append((x+starts[0],y+starts[1]))
	return gpoints

def findConvexHullsFromLabeledImage(regions,clabels):
	gpolygons=[]
	# individual region is masked to avoid problem of overlapped of region_obj slices
	for l in range(1,clabels+1):
		region=ma.masked_outside(regions,l,l)
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

def convexHullUnion(regions,clabels,testlog):
	shape=numarray.shape(regions)
	gpolygons=[]
	print "making convex hulls"
	while clabels != len(gpolygons):
		gpolygons=findConvexHullsFromLabeledImage(regions,clabels)
	
		print "merging from %d convex hulls" % len(gpolygons)
		gpolygons=mergePolygonPoints(gpolygons)
		print "merged to %d convex hulls" % len(gpolygons)

		#fill polygons and make a labeled image
		polygon_image=polygon.plotPolygons(shape,gpolygons)
		regions,clabels=nd.label(polygon_image)
		if clabels !=len(gpolygons):
			print "some polygons just touched, REDO!!"

	testlog=outputImage(regions,'region_labelp','Convex hull union labeled polygons',testlog)
	return regions,clabels,gpolygons,testlog
	

def getRealLabeledMeanStdev(image,labeled_image,indices,info):
	print "Getting real mean and stdev"
	mean=nd.mean(image,labels=labeled_image,index=indices)
	stdev=nd.standard_deviation(image,labels=labeled_image,index=indices)
	ll=0
	try:
		len(mean)
	except:
		mean=[mean]
		stdev=[stdev]
		try:
			len(indices)
		except:
			indices=[indices]
	try:
		info.keys()
	except:
		offset=1
	else:
		offset=0
	for l in indices:
		info[l-offset][1]=mean[ll]
		info[l-offset][2]=stdev[ll]
		ll += 1
	return info
	
def getRealLabeledPerimeter(image,edge_mask,labeled_image,indices,info,testlog):
	print "Getting real perimeter length"
	edgeimage,testlog=findEdgeSobel(edge_mask,0,0.5,1.0,False,testlog)
	mask=ma.getmask(edgeimage)
	length=nd.sum(mask,labels=labeled_image,index=indices)

	ll=0
	try:
		len(length)
	except:
		length=[length]
		try:
			len(indices)
		except:
			indices=[indices]
	try:
		info.keys()
	except:
		offset=1
	else:
		offset=0
	for l in indices:
		info[l-offset][3]=length[ll]
		ll += 1
	return info	

def getRealLabeledAreaCenter(image,labeled_image,indices,info):
	print "Getting real area and center"
	shape=numarray.shape(image)
	ones=numarray.ones(shape)
	area=nd.sum(ones,labels=labeled_image,index=indices)
	center=nd.center_of_mass(ones,labels=labeled_image,index=indices)

	ll=0
	try:
		len(area)
	except:
		area=[area]
		center=[center]
		try:
			len(indices)
		except:
			indices=[indices]
	try:
		info.keys()
	except:
		offset=1
	else:
		offset=0
	for l in indices:
		info[l-offset][0]=area[ll]
		info[l-offset][4]=center[ll]
		ll += 1
	return info	

def makeDefaultInfo(ltotal):
	info={}
	# info[l]=[area,avg,stdev,length,center]
	for l in range(1,ltotal+1):
		info[l]=[None,None,None,None,(None,None)]
	return info

def getLabeledInfo(image,alledgemask,labeled_image,indices,fast,info,testlog):
	try:
		ltotal=len(indices)
	except:
		ltotal=1
		
	print "getting region info"
	if len(info) != ltotal:
		info=makeDefaultInfo(ltotal)	
	
	imageshape=numarray.shape(labeled_image)
	if not fast:
		if (info[1][3] is None):
			info=getRealLabeledPerimeter(image,alledgemask,labeled_image,indices,info,testlog)
		if (info[1][1] is None):
			info=getRealLabeledMeanStdev(image,labeled_image,indices,info)
		if (info[1][0] is None):
			info=getRealLabeledAreaCenter(image,labeled_image,indices,info)
	else:
		objs = nd.find_objects(labeled_image)
		for l in indices:
			## use the bounding box perimeter as fast perimeter estimate
			## objs does not include the background
			lengthRow=(objs[l-1][0].stop - objs[l-1][0].start)
			lengthCol=(objs[l-1][1].stop - objs[l-1][1].start)
			info[l][3] = 2*(lengthRow+lengthCol)
	return info,testlog

def getPolygonInfo(polygons,info,testlog):
	print "get polygon area and center info"
	if len(info) != len(polygons):
		info=makeDefaultInfo(len(polygons))	
	polygons_arrays = polygon.polygons_tuples2arrays(polygons)
	for l,p in enumerate(polygons_arrays):
		length = 2*(p[:,0].max()-p[:,0].min())+2*(p[:,1].max()-p[:,1].min())
		if len(p) >=3:
			area = polygon.getPolygonArea(p)
			center = polygon.getPolygonCenter(p)
		else:
			## only a line
			area = length
			center = ((p[:,0].max()+p[:,0].min())/2,(p[:,1].max()+p[:,1].min())/2)
		info[l+1][0]=area
		info[l+1][4]=center
	return info,testlog
		
def pruneByLength(info,length_min,length_max,goodregions_in):
	print "pruning by edge length"
	goodregions=[]
	for l in range(1,len(info)+1):
		length=info[l][3]
		if (length > length_min and length < length_max):
			if l-1 in goodregions_in:
				goodregions.append(l-1)
	print "pruned to %d region" %len(goodregions)
	return goodregions


def pruneByArea(info,area_min,area_max,goodregions_in):
	print "pruning by area"
	goodregions=[]
	for l in range(1,len(info)+1):
		area=info[l][0]
		if (area > area_min and area < area_max):
			if l-1 in goodregions_in:
				goodregions.append(l-1)
	print "pruned to %d region" %len(goodregions)
	return goodregions

def pruneByStdev(info,stdev_min,goodregions_in):
	print "pruning by stdev"
	goodregions=[]
	for l in range(1,len(info)+1):
		stdev=info[l][2]
		if (stdev > stdev_min):
			if l-1 in goodregions_in:
				goodregions.append(l-1)
	print "pruned to %d region" %len(goodregions)
	return goodregions
	
def makePrunedLabels(imagename,labeled_image,ltotal,info,goodlabels):
	print "remaking %d labeled image after pruning" % len(goodlabels)
	new_labeled_image = makeImageFromLabels(labeled_image,ltotal,goodlabels)

	goodinfos=[]
	for i,l1 in enumerate(goodlabels):
		# output: centerx centery area average stdev length
		l=l1+1
		goodinfos.append(info[l])

	return new_labeled_image,len(goodlabels),goodinfos

def makeImageFromLabels(labeled_image,ltotal,goodlabels):
	imageshape=numarray.shape(labeled_image)
	new_labeled_image=numarray.zeros(imageshape,numarray.Int8)
	if len(goodlabels)==0:
		return new_labeled_image
	else:
		if len(goodlabels)==ltotal:
			return labeled_image
	if len(goodlabels)*2 < ltotal:
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
			numarray.putmask(tmp_labeled_image,region,0)
		new_labeled_image,resultlabels = nd.label(tmp_labeled_image)
		print 'makeImageFromLabels', len(goodlabels),resultlabels
	return new_labeled_image

def makePrunedPolygons(imagename,gpolygons,imageshape,info,goodlabels):
	print "remaking %d polygons after pruning" % len(goodlabels)
	goodpolygons=[]
	goodinfos=[]
	if len(goodlabels)==0:
		new_labeled_image=numarray.zeros(imageshape,numarray.Int8)
		return new_labeled_image,len(goodlabels),goodinfos
	for l1 in goodlabels:
		l=l1+1
		goodinfos.append(info[l])
		goodpolygons.append(gpolygons[l1])
	equalregions = polygon.plotPolygons(imageshape,goodpolygons)
	regions,clabels=nd.label(equalregions)
	if clabels != len(goodpolygons):
		print "ERROR: making %d labeled region from %d good polygons" % (clabels,len(goodpolygons))
	return regions,len(goodpolygons),goodinfos

def writeRegionInfo(imagename,path,infos):
	# infos is a list of information or a dictionary using non-zero index as keys
	# area,avg,stdev,length,(centerRow,centerColumn)
	if len(infos)==0:
		return
	regionlines=""
	try:
		infos.keys()
	except:
		offset=0
	else:
		offset=1
	for l1 in range(0,len(infos)):
		
		l=l1+offset
		info=infos[l]
		regionline=" %s.mrc %d %d %.1f %.1f %.1f %d\n" %(imagename,int(info[4][1]),int(info[4][0]),info[0],info[1],info[2],int(info[3]))
		regionlines=regionlines+regionline
	regionfile=open(path+imagename+".region",'w')
	regionfile.write(regionlines+"\n")
	regionfile.close()

def writeRegionInfoToDB(imagename,infos):
	# infos is a list of information or a dictionary using non-zero index as keys
	# area,avg,stdev,length,(centerRow,centerColumn)
	if len(infos)==0:
		return
	regionlines=""
	try:
		infos.keys()
	except:
		offset=0
	else:
		offset=1
	for l1 in range(0,len(infos)):
		
		l=l1+offset
		info=infos[l]
#		"READY FOR DATABASE INSERT HERE

def writeMaskImage(imagename,path,mask):
	# remove old mask file if it exists
	maskfile=path+"/"+imagename+"_mask.png"
	if (os.path.exists(maskfile)):
		os.remove(maskfile)
	if mask is not None:
		apImage.arrayToPng(mask,maskfile)

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

def makeMask(params,imagename):
	filelog="\nTEST OUTPUT IMAGES\n----------------------------------------\n"
	print "Processing %s.mrc" % (imagename,)
	run_dir=params["outdir"]+"/"+params["runid"]+"/"
	# create "run" directory if doesn't exist
	if not (os.path.exists(run_dir)):
		os.mkdir(run_dir)

	# create "regioninfo" directory if doesn't exist
	info_dir=run_dir+"/regions/"
	if not (os.path.exists(info_dir)):
		os.mkdir(info_dir)

	# remove region info file if it exists
	if (os.path.exists(info_dir+imagename+".region")):
		os.remove(info_dir+imagename+".region")
	
	
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

# selexon factors to expand the threshold
#	pm = 2.0
#	am = 3.0
# new values so that cdiam makes physical sense
	pm = 0.667
	am = 1.0
	
	list_t=pm*3.14159*cdiam
	pradius = diam/2.0	
	cradius=cdiam/2.0
	area_t=am*3.1415926*cradius*cradius
	regioninfo=""
#	image=Mrc.mrc_to_numeric(imagename+".mrc")
	image = apDatabase.getImageData(imagename)['image']
	image=imagefun.bin(image,bin)
	shape=numarray.shape(image)
	cutoff=8.0
	# remove spikes in the image first
	image=prepImage(image,cutoff)
	garea,gavg,gstdev=maskImageStats(image)
	allinfos={}
	regioninfos=[]

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

	print 'scaled regionhi= %.4f regionlo= %.4f' %(high,low)

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
		regioninfo=""
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
		
		labeled_regions,clabels=nd.label(mask)
		print "starting with",clabels, "regions"
		testlog=outputImage(labeled_regions,'region_label','Segmented labeled image',testlog)

		#pruning by length of the perimeters of the labeled regions.
		if (do_prune_by_length):
			allinfos,testlog=getLabeledInfo(image,mask,labeled_regions,range(1,clabels+1),True,allinfos,testlog)
			goodregions=range(clabels)
			goodregions=pruneByLength(allinfos,list_t,garea*0.5,goodregions)
			labeled_regions,clabels,goodinfo=makePrunedLabels(imagename,labeled_regions,clabels,allinfos,goodregions)
		
		#create convex hulls and merge overlapped or inside regions
		if do_convex_hulls:
			labeled_regions,clabels,gpolygons,testlog=convexHullUnion(labeled_regions,clabels,testlog)
				
		else:
			if do_cv:
				polygonregions,dummyimage=libCV.FindRegions(mask,area_t,0.2,1,0,1,0)
				gpolygons = reduceRegions(polygonregions,100)
				clabels = len(gpolygons)
				goodareas = range(clabels)

		if (clabels > 0):
			testlog[0]=False
			if do_convex_hulls or do_cv:
				if stdev_t < 0.001:
					allinfos,testlog=getPolygonInfo(gpolygons,allinfos,testlog)
				else:
					mask = polygon.plotPolygons(shape,gpolygons)
					labeled_regions,clabels=nd.label(mask)
					allinfos,testlog=getLabeledInfo(image,mask,labeled_regions,range(1,clabels+1),False,{},testlog)
			else:				
				allinfos,testlog=getLabeledInfo(image,mask,labeled_regions,range(1,clabels+1),False,allinfos,testlog)
			saved_labeled_regions=labeled_regions
			saved_clabels=clabels
			testlog[0]=test
			goodregions=range(clabels)
			if not do_cv:
				#pruning by area as in selexon
				goodareas=pruneByArea(allinfos,area_t,garea*0.5,goodregions)
				goodregions=goodareas

			if (len(goodregions)>0):
				#pruning by standard deviation in the regions
				if (stdev_t > 0):
					stdev_limit=stdev_t*gstdev
					goodstdevs=pruneByStdev(allinfos,stdev_limit,goodareas)
					goodregions=goodstdevs

			if do_convex_hulls or do_cv and stdev_t < 0.01:
				labeled_regions,clabels,regioninfos=makePrunedPolygons(imagename,gpolygons,shape,allinfos,goodregions)
			else:
				labeled_regions,clabels,regioninfos=makePrunedLabels(imagename,labeled_regions,clabels,allinfos,goodregions)

			
#		create final region mask
		if (clabels >0):
			int32regions=labeled_regions.astype(numarray.Int32)
			equalregions=ma.masked_greater_equal(int32regions,1)
			equalregions=equalregions.filled(1)
			regioninfos,testlog=getLabeledInfo(image,equalregions,labeled_regions,range(1,clabels+1),False,regioninfos,testlog)
			
		else:
			equalregions=None
	
		if test:
			try:
				good=len(goodareas)
			except:
				good=0
			if (good > 0):
				temp_regions,temp_clabels,goodinfos=makePrunedLabels(imagename,saved_labeled_regions,saved_clabels,allinfos,goodareas)
				testlog=outputImage(temp_regions,'region_labela','Area pruned labeled image',testlog)

			try:
				good=len(goodstdevs)
			except:
				good=0
			if (good>0):
				temp_regions,temp_clabels,goodinfos=makePrunedLabels(imagename,saved_labeled_regions,saved_clabels,allinfos,goodstdevs)
				testlog=outputImage(temp_regions,'region_labels','Stdev pruned labeled image',testlog)
			
			if (clabels>0):
				testlog=outputImage(equalregions,'finalregions','Final Mask image',testlog)
				regionedges,testlog=findEdgeSobel(equalregions,0,0.5,1.0,False,testlog)
				masklabel=1-ma.getmask(regionedges)
			else:
				masklabel=numarray.ones(shape)
			superimage=image*masklabel
			testlog=outputImage(superimage,'output','Final Mask w/ image',testlog)
			print testlog[2]
	
			writeRegionInfo(imagename,info_dir,regioninfos)
	
	if not test:
		writeRegionInfoToDB(imagename,regioninfos)
		writeMaskImage(imagename,run_dir,equalregions)
	
	return equalregions

def piksNotInMask(params,mask,piklines):
	bin = int(params["bin"])
	shape = numarray.shape(mask)
	piklinesNotInMask=[]
	for pikline in piklines:
		bits=pikline.split(' ')
		pik=(int(bits[1]),int(bits[2]))
		binpik = (int(pik[0]/bin),int(pik[1]/bin))
		if binpik[0] in range(0,shape[0]) and binpik[1] in range(0,shape[1]):
			if mask[binpik]==0:
				piklinesNotInMask.append(pikline)
	return piklinesNotInMask
	
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
	
def removeMaskedPiks(params,file):
	print "Start Removing Piks in Masks"
	pikfile = "pikfiles/"+file+".a.pik"
	piklines = readPiksFile(pikfile)
	regionmask=makeMask(params,file)
	print "Removing Bad Picks"
	piklinesgood = piksNotInMask(params,regionmask,piklines)
	writePiksFile(pikfile,'.nonmask',piklinesgood)
