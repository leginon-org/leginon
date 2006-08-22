#!/usr/bin/env python

import numarray

def insidePolygon(indices, polygon):
	'''
	test which points in indices are inside polygon
	'''
	intersections = numarray.zeros(indices.shape[1:])
	p0,p1 = indices
	## test each edge intersection with ray originating at each point in indices
	for v in range(len(polygon)):
		a0,a1 = polygon[v-1]
		b0,b1 = float(polygon[v][0]), float(polygon[v][1])
		if a0 != b0:
			intersection = numarray.logical_and(
					numarray.logical_or(
						numarray.logical_and(b0 < p0, a0 >= p0),
						numarray.logical_and(b0 >= p0, a0 < p0)),
					((b1 - a1) / (b0 - a0) * (p0 - a0) + a1) > p1)
			intersections += intersection
	## if only 1 intersection, then point is inside polygon
	inside = intersections % 2 == 1
	return inside

def filledPolygon(shape, vertices):
	indices = numarray.indices(shape)
	return insidePolygon(indices, vertices)

def pointsInPolygon(inputpoints, vertices):
	indices = numarray.array(inputpoints)
	indices.transpose()
	inside = insidePolygon(indices, vertices)
	outputpoints = numarray.compress(inside, inputpoints)
	outputpoints = map(tuple, outputpoints)
	return outputpoints

def getPolygonArea(polygon):
	area=0.0
	N = len(polygon)
	for i in range(N):
		j = (i+1) % N
		ax,ay = polygon[i]
		bx,by = polygon[j]
		area += ax * by
		area -= ay * bx
	area /= 2.0
	if area<0:
		return -area
	return area

def getPolygonCenter(polygon):
	N = len(polygon)
	A = getPolygonArea(polygon)
	if not A:
		return ()
	cx = cy = factor = 0.0
	for i in range(N):
		j = (i+1) % N
		ax,ay = polygon[i]
		bx,by = polygon[j]
		factor = ax*by - bx*ay
		cx += (ax + bx) * factor
		cy -= (ay + by) * factor
	A *= 6.0
	factor = 1/A
	cx *= factor
	cy *= factor
	return (cx,cy,)

if __name__ == '__main__':
	if 0:
		import Mrc
		im = filledPolygon((256,256), ((20,20), (40,40), (20,40),(40,20)))
		Mrc.numeric_to_mrc(im.astype(numarray.Int16), 'test.mrc')

	if 1:
		pointsInPolygon( ((1,1),(2,2),(2,3),(3,2),(3,3),(8,8),(12,12)), ((2,2),(2,10),(10,10),(10,2)))
		points= ((1,1),(2,2),(2,3),(3,3),(3,0),)
		print points
		print getPolygonCenter(points)

