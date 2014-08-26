#!/usr/bin/env python

'''
from:
http://en.wikipedia.org/wiki/Ramer%E2%80%93Douglas%E2%80%93Peucker_algorithm

function DouglasPeucker(PointList[], epsilon)
 //Find the point with the maximum distance
 dmax = 0
 index = 0
 for i = 2 to (length(PointList) - 1)
  d = PerpendicularDistance(PointList[i], Line(PointList[1], PointList[end])) 
  if d > dmax
   index = i
   dmax = d
  end
 end
 
 //If max distance is greater than epsilon, recursively simplify
 if dmax >= epsilon
  //Recursive call
  recResults1[] = DouglasPeucker(PointList[1...index], epsilon)
  recResults2[] = DouglasPeucker(PointList[index...end], epsilon)
  
  // Build the result list
  ResultList[] = {recResults1[1...end-1] recResults2[1...end]}
 else
  ResultList[] = {PointList[1], PointList[end]}
 end
 
 //Return the result
 return ResultList[]
end
'''

import numpy

def pointToLineDistance(linepta, lineptb, point):
	normalLength = numpy.sqrt((lineptb[0] - linepta[0]) * (lineptb[0] - linepta[0]) + (lineptb[1] - linepta[1]) * (lineptb[1] - linepta[1]))
	if normalLength < 0.00000001:
		return numpy.sqrt((point[0] - linepta[0]) * (point[0] - linepta[0]) + (point[1] - linepta[1]) * (point[1] - linepta[1]))
	return numpy.absolute((point[0] - linepta[0]) * (lineptb[1] - linepta[1]) - (point[1] - linepta[1]) * (lineptb[0] - linepta[0])) / normalLength

def douglas_peucker(points, epsilon):
	dmax = 0.0
	index = 0
	for i in range(1,len(points)-2):
		d = pointToLineDistance(points[0], points[-1], points[i])
		if d > dmax:
		 index = i
		 dmax = d
	# If max distance is greater than epsilon, recursively simplify
	if dmax >= epsilon:
		# Recursive call
		recResults1 = douglas_peucker(points[:index+1], epsilon)
		recResults2 = douglas_peucker(points[index:], epsilon)
  
		# Build the result list
		result = numpy.vstack((recResults1[:-1], recResults2))
	else:
		result = numpy.vstack((points[0], points[-1]))
 
	# Return the result
	return result

def test1():
	for testargs in (((0,0),(1,0),(5,5)), ((0,0),(0,1),(5,5))):
		print 'ARGS', testargs
		print ' -> ', pointToLineDistance(*testargs)

def test2():
	points = ((0,0), (1,1), (2,2), (3,3), (3,2), (3,1), (3,0))
	print 'ORIGINAL', points
	print 'NEW', douglas_peucker(points, 1)

if __name__ == '__main__':
	test2()
