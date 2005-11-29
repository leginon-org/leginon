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

if __name__ == '__main__':
	if 0:
		import Mrc
		im = filledPolygon((256,256), ((20,20), (40,40), (20,40),(40,20)))
		Mrc.numeric_to_mrc(im.astype(numarray.Int16), 'test.mrc')

	if 1:
		pointsInPolygon( ((1,1),(2,2),(2,3),(3,2),(3,3),(8,8),(12,12)), ((2,2),(2,10),(10,10),(10,2)))
