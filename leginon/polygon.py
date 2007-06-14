#!/usr/bin/env python

import numpy
import Image
import ImageDraw
import numextension

def insidePolygon(points, polygon):
	return numextension.pointsInPolygon(points, polygon)

def filledPolygon(shape, vertices):
	points = numpy.array(numpy.transpose(numpy.indices(shape), (1,2,0)))
	points.shape=(-1,2)
	inside = insidePolygon(points, vertices)
	final = numpy.array(inside)
	final.shape = shape
	return final

def pointsInPolygon(inputpoints, vertices):
	inside = insidePolygon(inputpoints, vertices)

	#temporary fix for compress change in numpy
	inside2 = []
	for i in inside:
		inside2.append(i)
		inside2.append(i)
	outputpoints = numpy.compress(inside, inputpoints)
	outputpoints2=[]
	for i in range(0,len(outputpoints)/2):
		outputpoints2.append((outputpoints[2*i],outputpoints[2*i+1]))
	return outputpoints2

def polygonSegments(polygon):
	a = numpy.transpose(polygon)
	b = numpy.concatenate((a[:,1:],a[:,:1]),1)
	return a,b

def distancePointsToPolygon(points, polygon):
	a,b = polygonSegments(polygon)
	evectors = b-a
	elengths = numpy.hypot(*evectors)
	eunitvectors = evectors / elengths
	pdists = []
	for p in points:
		pvectors = numpy.array((p[0]-a[0],p[1]-a[1]))
		dotprods = numpy.sum(evectors*pvectors)
		scalerproj = dotprods / elengths
		elengths2 = numpy.clip(scalerproj, 0, elengths)
		epoints = elengths2 * eunitvectors
		d = epoints - pvectors
		dists = numpy.hypot(*d)
		pdists.append(min(dists))
	return numpy.array(pdists)

def getPolygonArea(polygon, signed=False):
	a,b = polygonSegments(polygon)
	area = numpy.sum(a[0]*b[1]-a[1]*b[0]) / 2.0
	if not signed:
		area = numpy.abs(area)
	return area

def getPolygonCenter(polygon):
	a,b = polygonSegments(polygon)
	area = getPolygonArea(polygon, signed=True)
	c = (a[0]*b[1]-b[0]*a[1]) / 6.0 / area
	cx = numpy.sum((a[0]+b[0])*c)
	cy = numpy.sum((a[1]+b[1])*c)
	return (cx,cy)

if __name__ == '__main__':
	if 0:
		from pyami import mrc
		im = filledPolygon((256,256), ((20,20), (40,40), (20,40),(40,20)))
		mrc.write(im.astype(numpy.int16), 'test.mrc')

	if 1:
		pointsInPolygon( ((1,1),(2,2),(2,3),(3,2),(3,3),(8,8),(12,12)), ((2,2),(2,10),(10,10),(10,2)))
		points= ((1,1),(2,2),(2,3),(3,3),(3,0),)
		print points
		print getPolygonCenter(points)

def polygons_tuples2arrays(polygons_tuples):
	polygons_arrays=[]
	for p in polygons_tuples:
		polygon=[]
		for i,point in enumerate(p):
			polygon.append(list(point))
		polygon_array = numpy.array(polygon,dtype=numpy.float32)
		polygons_arrays.append(polygon_array)
	return polygons_arrays	
	
def polygons_arrays2tuples(polygons_arrays):
	# Input 'polygons' is a list of polygon vertices array
	polygons_tuples=[]
	for p in polygons_arrays:
		plist =p.tolist()
		polygon_tuples=[]
		for i,point in enumerate(plist):
			polygon_tuples.append(tuple(point))
		polygons_tuples.append(polygon_tuples)
	return polygons_tuples	

def plotPolygons(shape,polygons):
	# Input 'polygons' is a list of polygon vertices array
	zeros = numpy.zeros(shape,dtype=numpy.int8)
	img=Image.new('L',shape)
	draw=ImageDraw.Draw(img)
	try:
		polygons = polygons_arrays2tuples(polygons)
	except:
		pass
	for p in polygons:
		
		if len(p) > 2:
			draw.polygon(p,fill=1)	  
	seq=list(img.getdata())
	polygon_image=numpy.array(seq,dtype=numpy.int8)
	
	# The data sequence coverted this way is transposed in contrast to
	# the ndarray that generates it
	polygon_image=numpy.reshape(polygon_image,(shape[1],shape[0]))
	polygon_image=numpy.transpose(polygon_image)
	return polygon_image
