#!/usr/bin/env python

import sys
import time
import math
import numpy
import random
from appionlib.apCtf import ctftools
from pyami import ellipse

def ellipseRANSAC(edgeMap, ellipseThresh=2.0, minPercentGoodPoints=0.001, certainProb=0.9, maxiter=10000):
	"""
	takes 2D edge map from image and trys to find a good ellipse in the data
	"""
	## make a list of edges, with x, y radii
	bottomEdgeMap = numpy.copy(edgeMap)
	bottomEdgeMap[:edgeMap.shape[0]/2,:] = 0
	topEdgeMap = numpy.copy(edgeMap)
	topEdgeMap[edgeMap.shape[0]/2:,:] = 0
	rightEdgeMap = numpy.copy(edgeMap)
	rightEdgeMap[:,:edgeMap.shape[1]/2] = 0
	leftEdgeMap = numpy.copy(edgeMap)
	leftEdgeMap[:,edgeMap.shape[1]/2:] = 0
	
	center = numpy.array(edgeMap.shape, dtype=numpy.float64)/2.0 - 0.5
	edgeList = numpy.array(numpy.where(edgeMap), dtype=numpy.float64).transpose() - center
	bottomEdgeList = numpy.array(numpy.where(bottomEdgeMap), dtype=numpy.float64).transpose() - center
	topEdgeList = numpy.array(numpy.where(topEdgeMap), dtype=numpy.float64).transpose() - center
	rightEdgeList = numpy.array(numpy.where(rightEdgeMap), dtype=numpy.float64).transpose() - center
	leftEdgeList = numpy.array(numpy.where(leftEdgeMap), dtype=numpy.float64).transpose() - center



	#might be better to sort edges into quadrants and choose that way

	numEdges = edgeMap.sum()
	if numEdges != len(edgeList):
		print "something weird in array sizes"
		return None

	numSamples = 4
	mostGoodPoints = 0
	maxDistFromCenter = math.hypot(edgeMap.shape[0], edgeMap.shape[1])/10.0
	inscribedCircleArea = edgeMap.shape[0] * edgeMap.shape[1] / 4
	iternum = 0
	bestEllipseParams = None # {'center':(x,y), 'a':a, 'b':b, 'alpha':radians}
	areaReject = 0
	distReject = 0
	minGoodPoints = minPercentGoodPoints*numEdges
	t0 = time.time()
	while iternum <= maxiter:
		iternum += 1

		currentProb = 1.0 - math.exp( math.log(1.0-certainProb)/iternum )
		currentProb = currentProb**(1.0/numSamples)

		## check to see if we can stop
		if mostGoodPoints > currentProb*numEdges:
			currentProb = mostGoodPoints/float(numEdges)
			successProb = 1.0 - math.exp( iternum * math.log(1.0 - currentProb**numSamples) )
			print "\nRANSAC SUCCESS"
			break

		if currentProb < minPercentGoodPoints:
			print "\nRANSAC FAILURE"
			break

		if iternum >= maxiter:
			print "\nRANSAC GAVE UP"
			break

		#choose random edges
		#might be better to sort edges into quadrants and choose that way
		currentEdges = []
		currentEdges.append(random.choice(bottomEdgeList))
		currentEdges.append(random.choice(topEdgeList))
		currentEdges.append(random.choice(leftEdgeList))
		currentEdges.append(random.choice(rightEdgeList))
		currentEdges = numpy.array(currentEdges)

		# solve centered ellipse, fixed center
		centeredParams = ellipse.solveEllipseOLS(currentEdges)
		if centeredParams is None:
			sys.stderr.write("c")
			continue
		## check to see if ellipse has a area smaller than circle inscribed in image
		area = centeredParams['a'] * centeredParams['b']
		if area > inscribedCircleArea:
			areaReject += 1
			sys.stderr.write("A%d"%(areaReject))
			continue
		ratio = centeredParams['a']/float(centeredParams['b'])
		if ratio > 6 or ratio < 0.16:
			sys.stderr.write("R%d"%(areaReject))
			continue	

		## check to see if ellipse has a circumference smaller than something

		# solve general ellipse, floating center
		## only three points, can use other Ellipse fit
		#generalParams = ellipse.solveEllipseB2AC(currentEdges)
		generalParams = ellipse.solveEllipseGander(currentEdges)
		if generalParams is None:
			sys.stderr.write("g")
		else:
			## check center to see if its reasonably close to center
			distFromCenter = math.hypot(generalParams['center'][0], generalParams['center'][1])
			if distFromCenter > maxDistFromCenter:
				distReject += 1
				sys.stderr.write("D%d"%(distReject))
				continue
			## check to see if ellipse has a area smaller than circle inscribed in image
			area = math.pi * centeredParams['a'] * centeredParams['b']
			if area > inscribedCircleArea:
				areaReject += 1
				sys.stderr.write("A%d"%(areaReject))
				continue
		
		## create a larger and smaller ellipse intersect them to create a fit area
		ellipseMap = generateEllipseRangeMap(centeredParams, ellipseThresh, edgeMap.shape)

		## take overlap of edges and fit area to determine number of good points
		goodPoints = numpy.logical_and(edgeMap, ellipseMap).sum()

		if goodPoints > mostGoodPoints or iternum%100 == 0:
			print ("\ngood points=%d (best=%d; need=%d, bestProb=%.1f, iter=%d, timePer=%.3f)"
				%(goodPoints, mostGoodPoints, currentProb*numEdges, 
					mostGoodPoints/float(numEdges)*100, iternum, (time.time()-t0)/float(iternum)))

		if goodPoints < minGoodPoints or goodPoints < mostGoodPoints:
			sys.stderr.write("F")
			continue

		if goodPoints > mostGoodPoints:
			bestEllipseParams = centeredParams
			mostGoodPoints = goodPoints

	### end loop and do stuff
	return bestEllipseParams

#=================
def drawFilledEllipse(shape, a, b, alpha):
	'''
	Generate a zero initialized image array with a filled ellipse
	drawn by setting pixels to 1.

	see also imagefun.filled_circle
	'''
	ellipratio = a/float(b)
	### this step is TOO SLOW
	radial = ctftools.getEllipticalDistanceArray(ellipratio, math.degrees(alpha), shape)
	meanradius = math.sqrt(a*b)
	filledEllipse = numpy.where(radial > meanradius, False, True)
	return filledEllipse

#=================
def generateEllipseRangeMap(ellipseParams, ellipseThresh, shape):
	"""
	make an elliptical ring of width ellipseThresh based on ellipseParams
	"""
	largeEllipse = drawFilledEllipse(shape, ellipseParams['a']+ellipseThresh, 
		ellipseParams['b']+ellipseThresh, ellipseParams['alpha'])
	smallEllipse = drawFilledEllipse(shape, ellipseParams['a']-ellipseThresh, 
		ellipseParams['b']-ellipseThresh, ellipseParams['alpha'])
	ellipseRange = numpy.logical_and(largeEllipse, -smallEllipse)
	return ellipseRange

#=================
#=================
if __name__ == "__main__":
	from scipy.misc import lena
	from matplotlib import pyplot
	from appionlib.apCtf import canny
	lena = lena()

	edgeMap = canny.canny_edges(lena, 5, 0.25, 0.75)
	edgeMapInv = numpy.flipud(numpy.fliplr(edgeMap))
	edgeMap = numpy.logical_or(edgeMap,edgeMapInv)

	t0 = time.time()
	ellipseParams = ellipseRANSAC(edgeMap)
	print time.time()-t0, "seconds"

	filled = generateEllipseRangeMap(ellipseParams, 2, edgeMap.shape)
	filled = 2*edgeMap + filled
	pyplot.imshow(filled)
	pyplot.gray()
	pyplot.show()




