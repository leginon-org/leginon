#!/usr/bin/env python

import math
from leginon import lattice,raster


class RasterIndexer(object):
	def __init__(self):
		'''
		points are list of tuples, and need to be approximately
		a rectangular extension of a square lattice
		'''
		self.points = []
		self.shape = None
		self.spacing_guess = None

	def setRasterShape(self,raster_shape):
		self.shape = raster_shape

	def setPoints(self,point_positions):
		self.points = point_positions

	def setSpacingGuess(self,spacing):
		self.spacing_guess = spacing

	def getPointsCenter(self):
		points = self.points
		xcenter = sum(map((lambda x: x[0]),points)) / float(len(points))
		ycenter = sum(map((lambda x: x[1]),points)) / float(len(points))
		return (xcenter,ycenter)

	def convertToFirstAxisAngle(self,angle):
		'''
		Convert the angle to be more generic. The two axes of the lattice
		are degenerate.  This conversion, however, makes it easier to
		index later.
		'''
		xangle = math.atan(math.tan(angle))
		if xangle > 0 and xangle > math.radians(50.0):
			xangle -= math.radians(90.0)
		if xangle < 0 and xangle < math.radians(-50.0):
			xangle += math.radians(90.0)
		return xangle

	def getLatticeMatrix(self,spacing_guess=100,tolerance=0.2):
		'''
		Obtain spacing and angle of the lattice best fit all the data
		'''
		best_lattice = lattice.pointsToLattice(self.points, spacing_guess, tolerance)
		self.matrix = best_lattice.matrix
		# Degenerated matrix angle
		self.angle = self.convertToFirstAxisAngle(best_lattice.angle)
		# Spacing is best obtained from the matrix
		diagonal = math.hypot(self.matrix[(0,0)]-self.matrix[(1,0)], self.matrix[(1,0)]-self.matrix[(1,1)])
		self.spacing = diagonal / math.sqrt(2)

	def makeRasterPoints(self,center=(0,0)):
		'''
		Make raster points as list of tuples
		'''
		ind = raster.createIndices(self.shape)
		rasterpoints = raster.createRaster3(self.spacing, -self.angle,ind)
		# offset the raster points to the center of all points
		rasterpoints = map((lambda x: (x[0]+center[0],x[1]+center[1])),rasterpoints)
		ind_offset = ind[0]
		ind = map((lambda x: (int(x[0]-ind_offset[0]),int(x[1]-ind_offset[1]))),ind)
		self.rasterindices = ind
		self.rasterpoints = rasterpoints

	def _calcBestIndex(self,point):
		'''
		Get Best Index for a point by looking for the one closest to it.
		'''
		best_i = None
		closest_dist = 100000.0
		for i in range(len(self.rasterindices)):
			dist = math.hypot(self.rasterpoints[i][0]-point[0],self.rasterpoints[i][1]-point[1])
			if dist < closest_dist:
				closest_dist = dist
				best_i = i
		return best_i	

	def _indexPoints(self):
		'''
		Get indices for all points.
		'''
		# 2d_index is a tuple such as (0,0) or (0,1)
		point_2d_indices = []
		# list indix is an integer for as index of self.rasterpoints
		# and self.rasterindices
		point_list_indices = []
		for point in self.points:
			best_list_index = self._calcBestIndex(point)
			point_2d_index = self.rasterindices[best_list_index]
			point_2d_indices.append(point_2d_index)
			point_list_indices.append(best_list_index)
			#print best_list_index, point_2d_index, point,'(%.0f,%.0f)' % (self.rasterpoints[best_list_index][0],self.rasterpoints[best_list_index][1])
		return point_2d_indices, point_list_indices

	def getSpacingGuess(self, center):
		'''
		Obtain the initial guess of lattice spacing.  This only works
		if no spots are missing close to the center.
		'''
		sorted_points = lattice.sortPointsByDistances(self.points,center)
		first_point = sorted_points[0]
		distances = []
		# use points closest to the geometry center to find 4 neighbors of
		# the most centered point 
		for point in sorted_points[1:10]:
			distances.append(math.hypot(point[0]-first_point[0],point[1]-first_point[1]))
		distances.sort()
		closest_distances = distances[:4]
		self.center_point = first_point
		return sum(closest_distances) / len(closest_distances)

	def run(self):
		'''
		Run indexing points with raster.
		'''
		center = self.getPointsCenter()
		# Guess spacing automatically if not set
		if not self.spacing_guess:
			self.spacing_guess = self.getSpacingGuess(center)
		self.getLatticeMatrix(self.spacing_guess,0.6)
		'''
		The rasterpoints may be offset from the best fit since there will
		be missing points, including ones intentionally left out as 
		negative fiducials
		'''
		best_offset = None
		unique_number = 0
		point_list_indices={}
		point_2d_indices={}
		# Do a search arround the center
		for i in range(-3,4):
			for j in range(-3,4):
				key = (i,j)
				test_center = (center[0]+i*0.2*self.spacing,center[1]+j*0.2*self.spacing)
				self.makeRasterPoints(test_center)
				point_2d_indices[key], point_list_indices[key] = self._indexPoints()
				# The best result has most unique indices
				if len(set(point_list_indices[key])) > unique_number:
					best_offset = key
					unique_number=len(set(point_list_indices[key]))
		# print the finale results
		#for i, point in enumerate(self.points):
		#	print i,point_2d_indices[best_offset][i],point
		print 'spacing', self.spacing
		print 'angle', self.angle
		return point_2d_indices[best_offset]

	def runRasterIndexer(self,raster_shape,point_positions):
		'''
		Run indexer with inputs.
		raster_shape and each point_position are tuples of (col,row)
		Returned 2d_indices is a list of tuples in (col_index, row_index) starts from (0,0)
		'''
		self.setRasterShape(raster_shape)
		self.setPoints(point_positions)
		return self.run()

if __name__=="__main__":
	shape = (3,5)
	points = [(155, 127), (221, 128), (289, 128), (153, 190), (214, 190), (288, 190), (153, 250), (216, 251), (290, 251), (154, 311), (217, 310), (289, 309), (151, 374), (217, 375), (291, 374)]
	app=RasterIndexer()
	app.setPoints(points)
	app.setRasterShape(shape)
	#app.setSpacingGuess(400)
	app.run()
