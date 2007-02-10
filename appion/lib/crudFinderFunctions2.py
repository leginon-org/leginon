#!/usr/bin/env python

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
#import libCV
from selexonFunctions2 import *


######################################################################
# Convexhull related functions Starts
######################################################################

"""Taken from internet serach
   , strip down to needed parts and add Colinear test and complete the polygon
   with the initial point if lacked
Anchi"""

"""convexhull.py

Calculate the convex hull of a set of n 2D-points in O(n log n) time.  
Taken from Berg et al., Computational Geometry, Springer-Verlag, 1997.

Usage:

	convexhull.py <numPoints> <squareLength> <outFile>

Dinu C. Gherman
"""

def _myDet(p, q, r):
	"""Calc. determinant of a special matrix with three 2D points.

	The sign, "-" or "+", determines the side, right or left,
	respectivly, on which the point r lies, when measured against
	a directed vector from p to q.
	"""

	# We use Sarrus' Rule to calculate the determinant.
	# (could also use the Numeric package...)
	sum1 = q[0]*r[1] + p[0]*q[1] + r[0]*p[1]
	sum2 = q[0]*p[1] + r[0]*q[1] + p[0]*r[1]

	return sum1 - sum2


def _isRightTurn((p, q, r)):
	"Do the vectors pq:qr form a right turn, or not?"

	assert p != q and q != r and p != r
			
	if _myDet(p, q, r) < 0:
		return 1
	else:
		return 0

def _isRightTurnOrColinear((p, q, r)):
	"Do the vectors pq:qr form a right turn, or not?"
	assert p != q and q != r and p != r
	if _myDet(p, q, r) < 0:
		return 1
	else:
		if _myDet(p, q, r) > 0:
			return 0
		if _myDet(p, q, r) == 0:
			if ((p[0]<= q[0] and r[0]>=q[0]) or (p[0]>= q[0] and r[0]<=q[0])) and ((p[1]<= q[1] and r[1]>=q[1]) or (p[1]>= q[1] and r[1]<=q[1])):
				return 1
			else:
				return 0

def _isPointInPolygon(r, P0):
	"Is point r inside a given polygon P?"
	# We assume the polygon is a list of points, listed clockwise!
	P=list(P0)
	if (P[0] !=P[-1]):
		P.append(P[0])
	for i in xrange(len(P[:-1])):
		p, q = P[i], P[i+1]
		if not (r==p or r==q):
			if not _isRightTurnOrColinear((p, q, r)):
				return 0 # Out!		   
	return 1 # It's within or on!

def _isPointOnlyInPolygon(r, P0):
	"Is point r inside a given polygon P?"
	# We assume the polygon is a list of points, listed clockwise!
	P=list(P0)
	if (P[0] !=P[-1]):
		P.append(P[0])
	for i in xrange(len(P[:-1])):
		p, q = P[i], P[i+1]
		if (r==p or r==q):
			return 1 # It's on
		else:
			if not _isRightTurn((p, q, r)):
				return 0 # Out!		   

	return 1 # It's within!

def convexHull(P):
	"Calculate the convex hull of a set of points."

	# Get a local list copy of the points and sort them lexically.
	points = map(None, P)
	points.sort()

	# Build upper half of the hull.
	upper = [points[0], points[1]]
	for p in points[2:]:
		upper.append(p)
		while len(upper) > 2 and not _isRightTurnOrColinear(upper[-3:]):
			del upper[-2]

	# Build lower half of the hull.
	points.reverse()
	lower = [points[0], points[1]]
	for p in points[2:]:
		lower.append(p)
		while len(lower) > 2 and not _isRightTurnOrColinear(lower[-3:]):
			del lower[-2]

	# Remove duplicates.
	del lower[0]
	del lower[-1]

	# Concatenate both halfs and return.
	return tuple(upper + lower)
######################################################################
# Convexhull related functions Ends
######################################################################

def image2array(im, convertType='UInt8'):
    """
    Convert PIL image to Numarray array
    copied and modified from http://mail.python.org/pipermail/image-sig/2005-September/003554.html
    """
    if im.mode == "L":
        a = numarray.fromstring(im.tostring(), N.UInt8)
        a = numarray.reshape(a, (im.size[1], im.size[0]))
        #a.shape = (im.size[1], im.size[0], 1)  # alternate way
    elif (im.mode=='RGB'):
        a = numarray.fromstring(im.tostring(), N.UInt8)
        a.shape = (im.size[1], im.size[0], 3)
    else:
        raise ValueError, im.mode+" mode not considered"

    if convertType == 'Float32':
        a = a.astype(N.Float32)
    return a

def prepimage(image,cutoff=5.0):
	shape=numarray.shape(image)
	garea,gavg,gstdev=masked_stats(image)
	print 'image mean= %.1f stdev= %.1f' %(gavg,gstdev)
	cleanimage=ma.masked_outside(image,gavg-cutoff*gstdev,gavg+cutoff*gstdev)
	carea,cavg,cstdev=masked_stats(cleanimage)
	
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

def outputimage(array,name,description,testlog):
	width=25
	if testlog[0]:
		mrcname="tests/%02d%s.mrc" %(testlog[1],name)
		space=(width-len(mrcname))*' '
		testlog[2]+= "%s:%s%s\n" % (mrcname,space,description)
		testlog[1] += 1
		if array.type()==numarray.Bool:
			array=array.astype(numarray.Int8)
		Mrc.numeric_to_mrc(array,mrcname)
	return testlog

def find_edge(image,sigma,amin,amax,output,testlog):
	if (output):
		testlog=outputimage(image,'input','input image',testlog)
	if (sigma > 0):
		smooth=nd.gaussian_filter(image,sigma)
		if (output):
			testlog=outputimage(smooth,'smooth','filtered image',testlog)
	else:
		smooth=image

	edges=nd.generic_gradient_magnitude(smooth, derivative=nd.sobel)
	if (output):
		testlog=outputimage(edges,'edge','edge image',testlog)

	edgemax=edges.max()
	tedges=ma.masked_inside(edges,edgemax*amin,edgemax*amax)
	return tedges,testlog

def fill_mask(mask_image,iteration):
	base=nd.generate_binary_structure(2,2)
	mask_image=nd.binary_dilation(mask_image,structure=base,iterations=iteration)
	mask_image=nd.binary_erosion(mask_image,structure=base,iterations=iteration)
	if (numarray.__version__ >= '1.5'):
		mask_image=nd.binary_fill_holes(mask_image,structure=base)
	else:
		print "fill_holes function not available in numarray version %s, do dilation/erosion only" %numarray.__version__
	return mask_image
	

def makedisk(radius):
	#make  disk mask
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

def masked_stats(mimage):
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

def convolve_disk(bimage,radius,convolve_t,testlog):
	#make  disk binaray image
	disk = makedisk(radius)
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
	testlog=outputimage(cmask,'maskc','Convolved filled edge mask',testlog)
	
	# Thresholding to binary mask
	cmax=cref.max()*convolve_t
	masked_cmask=ma.masked_greater(cmask,cmax)
	mask=ma.getmask(masked_cmask)
	testlog=outputimage(mask,'maskct','Thresholded Convolved mask',testlog)
	return mask,testlog
		
def find_convex_hulls_from_points(points):
	polygons=[]
	if (len(points) >3):
		polygon=convexHull(points)
		polygon=list(polygon)
	else:
		polygon=points
	return polygon		

def one_obj_bimage_to_gpoints(bimage):
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

def find_convex_hulls_from_labeled_image(bimage,cruds,clabels):
	gpolygons=[]
	# individual crud is masked to avoid problem of overlapped of crud_obj slices
	for l in range(1,clabels+1):
		region=ma.masked_outside(cruds,l,l)
		mask=1-ma.getmask(region)
		gpoints=one_obj_bimage_to_gpoints(mask)
		gpolygon=find_convex_hulls_from_points(gpoints)
		gpolygons.append(gpolygon)
	return gpolygons
		
def plot_polygons(shape,gpolygons):
	zeros=numarray.zeros(shape,type=numarray.Int8)
	img=Image.new('L',shape)
	draw=ImageDraw.Draw(img)
	for p in gpolygons:
		if len(p) > 2:
			draw.polygon(p,fill=1)	  
	seq=list(img.getdata())
	polygon_image=numarray.array(seq)
	polygon_image=numarray.reshape(polygon_image,shape)
	polygon_image=numarray.transpose(polygon_image)
	return polygon_image

def do_points_overlap(p1,p2):
	is_overlapped=False
	if len(p2) >= 2:
		for point in p1:
			overlapped=_isPointInPolygon(point,p2)
			if overlapped==1:
				return True
	else:
		for point in p1:
			if point==p2[0]:
				return True
	if len(p1) >= 2:
		for point in p2:
			overlapped=_isPointInPolygon(point,p1)
			if overlapped==1:
				return True
	else:
		for point in p2:
			if point==p1[0]:
				return True
	return False

def include_one_in_another(p1,p2):
	for point in p1:
		if point not in p2:
			p2.append(point)
	return p2

def merge_polygon_points(points):
	p1=0
	result=list(points)
	while p1 in range(len(result)):
		p2=p1+1
		has_overlap=False
		while p2 in range(len(result)):
			overlap=do_points_overlap(points[p1],points[p2])
			if not overlap:
				p2=p2+1
			else:

				points[p2]=include_one_in_another(points[p1],points[p2])
				has_overlap=True
				p2=p2+1

		if has_overlap==False:
			results=list(points)
			p1=p1+1
		else:
			points.pop(p1)
			result=list(points)
	#create new convex hulls
	for p in range(len(result)):
		checked=[]
		for point in points[p]:
			if point not in checked:
				checked.append(point)
		points[p]=checked
		new_polygon=find_convex_hulls_from_points(points[p])
		result[p]=new_polygon
	return result		  

def make_global_polygons(shape,crud_objs,polygons):
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

def make_local_polygons(gpolygons):
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

def merge_polygons(shape,crud_objs,polygons):
	gpolygons=make_global_polygons(shape,crud_objs,polygons)
	gpolygons=merge_polygon_points(gpolygons)
	new_crud_objs,new_polygons=make_local_polygons(gpolygons)
	return new_crud_objs,new_polygons	


def convex_hull_union(bimage,cruds,clabels,testlog):
	shape=numarray.shape(bimage)
	gpolygons=find_convex_hulls_from_labeled_image(bimage,cruds,clabels)
	print "made %d convex hulls" % len(gpolygons)
	
	gpolygons=merge_polygon_points(gpolygons)
	print "merge to %d convex hulls" % len(gpolygons)

	#fill polygons and make a labeled image
	polygon_image=plot_polygons(shape,gpolygons)
	cruds,clabels=nd.label(polygon_image)

	testlog=outputimage(cruds,'crud_labelp','Convex hull union labeled polygons',testlog)
	return cruds,clabels,testlog
	
def get_labeled_info(image,alledgemask,labeled_image,ltotal,testlog):
	info={}
	imageshape=numarray.shape(labeled_image)
	edgeimage,testlog=find_edge(alledgemask,0,-1,0.0,False,testlog)
	mask=1-ma.getmask(edgeimage)
	mask=nd.binary_dilation(mask,iterations=1)
	testlog=outputimage(mask,'labeledge','Edges of the image labels',testlog)
	ones=numarray.ones(imageshape)
	# individual crud is masked to avoid problem of overlapped of crud_obj slices
	for l in range(1,ltotal+1):
		length=nd.sum(mask,labels=labeled_image,index=l)
		area=nd.sum(ones,labels=labeled_image,index=l)
		avg=nd.mean(image,labels=labeled_image,index=l)
		stdev=nd.standard_deviation(image,labels=labeled_image,index=l)
		center=nd.center_of_mass(ones,labels=labeled_image,index=l)
		info[l]=(area,avg,stdev,length,center)
	return info,testlog 

def prune_by_length(info,length_min,length_max,goodcruds_in):
	print "pruning by edge length"
	goodcruds=[]
	for l in range(1,len(info)+1):
		length=info[l][3]
		if (length > length_min and length < length_max):
			if l-1 in goodcruds_in:
				goodcruds.append(l-1)
	print "pruned to %d region" %len(goodcruds)
	return goodcruds


def prune_by_area(info,area_min,area_max,goodcruds_in):
	print "pruning by area"
	goodcruds=[]
	for l in range(1,len(info)+1):
		area=info[l][0]
		if (area > area_min and area < area_max):
			if l-1 in goodcruds_in:
				goodcruds.append(l-1)
	print "pruned to %d region" %len(goodcruds)
	return goodcruds

def prune_by_stdev(info,stdev_min,goodcruds_in):
	print "pruning by stdev"
	goodcruds=[]
	for l in range(1,len(info)+1):
		stdev=info[l][2]
		if (stdev > stdev_min):
			if l-1 in goodcruds_in:
				goodcruds.append(l-1)
	print "pruned to %d region" %len(goodcruds)
	return goodcruds

def make_pruned_labels(file,labeled_image,ltotal,info,goodlabels):
	imageshape=numarray.shape(labeled_image)
	goodinfo=""
	goodl=0
	new_labeled_image=numarray.zeros(imageshape,numarray.Int8)
	base=numarray.ones(imageshape)
	for l in range(1,ltotal+1):
		region=ma.masked_outside(labeled_image,l,l)
		if (l-1 in goodlabels):
			goodl=goodl+1
			region=region/l+goodl-1
			one_region=region.filled(0)
			new_labeled_image=new_labeled_image+one_region
			# output: center area average stdev
			goodcrudline=file+".mrc "+str(int(info[l][4][1]))+" "+str(int(info[l][4][0]))+" "+str(info[l][0])+" "+str(info[l][1])+" "+str(info[l][2])+" "+str(info[l][3])+"\n"
			goodinfo=goodinfo+goodcrudline
	return new_labeled_image,goodl,goodinfo

#def findCrud_Craig(bimage,area_t):
#		print "try FindRegions",area_t
#		result=libCV.FindRegions(mask,area_t,0.05,1,0,1,0,1)

def findCrud2(params,file):
	filelog="\nTEST OUTPUT IMAGES\n----------------------------------------\n"
	# create "jpgs" directory if doesn't exist
	if not (os.path.exists("mrcs")):
		os.mkdir("mrcs")

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

	list_t=3.14159*diam
	radius=diam/2
	area_t=3.1415926*cdiam*cdiam/4
	crudinfo=""
	
	
	image=Mrc.mrc_to_numeric(file+".mrc")
	image=imagefun.bin(image,bin)
	shape=numarray.shape(image)

	cutoff=8.0
	# remove spikes in the image first
	image=prepimage(image,cutoff)
	garea,gavg,gstdev=masked_stats(image)

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

	#binary edge
	edgeimage,testlog=find_edge(image,sigma,low,high,True,testlog)

	nedge=ma.count(edgeimage)
	# If the area not within the threshold is too large or zero, no further calculation is necessary
	if (nedge <image.size()*0.1 or nedge ==image.size()):
		superimage=image
		crudinfo=""
	else:
		mask=ma.getmask(edgeimage)
		maskedimage=ma.masked_array(image,mask=mask,fill_value=0)
		testlog=outputimage(mask,'mask','Thresholded edge binary image mask',testlog)

		#fill
		iteration=3
		mask=fill_mask(mask,iteration)
		testlog=outputimage(mask,'maskf','Hole filled edge mask',testlog)

		if (convolve_t > 0):
			#convolve with the disk image of the particle
			mask,testlog=convolve_disk(mask,radius,convolve_t,testlog)
		

		#segmentation
		
		cruds,clabels=nd.label(mask)
		print "starting with",clabels, "cruds"
		testlog=outputimage(cruds,'crud_label','Segmented labeled image',testlog)

		#pruning by length of the perimeters of the labeled regions.
		# Caution, it will be slow because the need to reconstruct the labeled image
		if (do_prune_by_length):
			allinfo,testlog=get_labeled_info(image,mask,cruds,clabels,testlog)
			goodcruds=range(clabels)
			goodcruds=prune_by_length(allinfo,list_t,garea*0.5,goodcruds)
			cruds,clabels,goodinfo=make_pruned_labels(file,cruds,clabels,allinfo,goodcruds)
		
		#create convex hulls and merge overlapped or inside cruds
		if (do_convex_hulls):
			cruds,clabels,testlog=convex_hull_union(mask,cruds,clabels,testlog)		

		if (clabels > 0):
			testlog[0]=False
			allinfo,testlog=get_labeled_info(image,mask,cruds,clabels,testlog)
			testlog[0]=test
			goodcruds=range(clabels)
			#pruning by area as in selexon
			goodcruds=prune_by_area(allinfo,area_t,garea*0.5,goodcruds)
			if (test):
				temp_cruds,temp_clabels,goodinfo=make_pruned_labels(file,cruds,clabels,allinfo,goodcruds)
				testlog=outputimage(temp_cruds,'crud_labela','Area pruned labeled image',testlog)

			if (len(goodcruds)>0):
				#pruning by standard deviation in the cruds
				if (stdev_t > 0):
					stdev_limit=stdev_t*gstdev
					goodcruds=prune_by_stdev(allinfo,stdev_limit,goodcruds)

					if (test):
						temp_cruds,temp_clabels,goodinfo=make_pruned_labels(file,cruds,clabels,allinfo,goodcruds)
						testlog=outputimage(temp_cruds,'crud_labels','Stdev pruned labeled image',testlog)

			if (test):
				cruds,clabels,crudinfo=temp_cruds,temp_clabels,goodinfo
			else:
				cruds,clabels,crudinfo=make_pruned_labels(file,cruds,clabels,allinfo,goodcruds)

#		create edge image of the cruds for display
		if (clabels >0):
			equalcruds=ma.masked_greater_equal(cruds,1)
			equalcruds=equalcruds.filled(100)
			crudedges,testlog=find_edge(equalcruds,1,0.5,1.0,False,testlog)
			masklabel=1-ma.getmask(crudedges)
		else:
			masklabel=numarray.ones(numarray.shape(image))
		superimage=image*masklabel
	
	Mrc.numeric_to_mrc(superimage,"mrcs/"+file+".crud.mrc")
	testlog=outputimage(superimage,'output','Final Crud w/ image',testlog)
	
	if (test):
		print testlog[2]
	
	crudfile=open("crudfiles/"+file+".crud",'w')
	crudfile.write(crudinfo+"\n")
	crudfile.close()

		
