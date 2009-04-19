#!/usr/bin/env python

import numpy
import Image
import ImageDraw

try:
	import numextension
	def insidePolygon(points, polygon):
		return numextension.pointsInPolygon(points, polygon)
except:
	def insidePolygon(points, polygon):
		truthlist = []
		for point in points:
			inside = point_inside_polygon(point[0], point[1], polygon)
			truthlist.append(inside)
		return truthlist

def point_inside_polygon(x, y, poly):
	"""
	taken from http://www.ariel.com.au/a/python-point-int-poly.html

	determine if a point is inside a given polygon or not
	Polygon is a list of (x,y) pairs.
	"""
	n = len(poly)
	inside = False
	p1x,p1y = poly[0]
	for i in range(n+1):
		p2x,p2y = poly[i % n]
		if y > min(p1y,p2y):
			if y <= max(p1y,p2y):
				if x <= max(p1x,p2x):
					if p1y != p2y:
						xinters = (y-p1y)*(p2x-p1x)/(p2y-p1y)+p1x
					if p1x == p2x or x <= xinters:
						inside = not inside
		p1x,p1y = p2x,p2y
	return inside

def indicesInsidePolygon(shape, vertices):
	points = numpy.array(numpy.transpose(numpy.indices(shape), (1,2,0)))
	points.shape=(-1,2)
	inside = pointsInPolygon(points, vertices)
	return inside

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
	outputpoints = numpy.compress(inside2, inputpoints)
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
