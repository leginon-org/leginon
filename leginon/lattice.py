#!/usr/bin/env python

import numpy

class Lattice(object):
	def __init__(self, firstpoint, spacing, tolerance):
		self.points = []
		self.lattice_points = {}
		self.lattice_points_err = {}
		self.center = None

		self.tolerance = tolerance
		self.spacing = spacing
		self.t00 = None
		self.matrix = None
		self.add_first_point(firstpoint)

	def raster(self, shape=None, layers=None):
		# generate raster using lattice params
		if shape is None and layers is None:
			raise RuntimeError('lattice raster requires shape and/or layers')
		if shape is None:
			maxn = layers
		else:
			maxdist = numpy.hypot(*shape)
			maxn = int(numpy.ceil(maxdist / self.spacing))
		if layers is not None:
			maxn = min(maxn,layers)
		points = [self.center]
		for i in range(-maxn, maxn+1):
			iv0 = i * self.matrix[0,0]
			iv1 = i * self.matrix[0,1]
			for j in range(-maxn, maxn+1):
				if i == 0 and j == 0:
					continue
				jv0 = j * self.matrix[1,0]
				jv1 = j * self.matrix[1,1]
				v0 = self.center[0] + iv0 + jv0
				v1 = self.center[1] + iv1 + jv1
				if v0 >=0 and v0 <= shape[0]-1 and v1 >= 0 and v1 <= shape[1]-1:
					points.append((v0,v1))
		return points

	def add_point(self, newpoint):
		num = len(self.points)
		if num == 0:
			self.add_first_point(newpoint)
		elif num == 1:
			self.add_second_point(newpoint)
		else:
			self.add_any_point(newpoint)

	def add_first_point(self, firstpoint):
		self.points.append(firstpoint)
		self.lattice_points[(0,0)] = firstpoint
		self.lattice_points_err[(0,0)] = 0.0
		self.center = firstpoint

	def add_second_point(self, secondpoint):
		'''
		If the lattice transition matrix still needs to be determined,
		see if this point is at proper spacing, then add it
		and calculate matrix.

		If the lattice matrix is already known, treat this point
		like any other.
		'''
		## check if matrix is known
		if self.matrix is None:
			## check if spacing is within tolerance
			v0 = secondpoint[0] - self.center[0]
			v1 = secondpoint[1] - self.center[1]
			dist = numpy.hypot(v0,v1)
			nf = dist / self.spacing
			n = int(round(nf))
			if n == 0:
				## we can only have one point at (0,0)
				return
			err = numpy.absolute(nf - n)
			if err < self.tolerance:
				point = (n,0)
				m = numpy.array(((v0/n, v1/n),(v1/n, -v0/n)), numpy.float32)
				self.matrix = m
				tmatrix = numpy.linalg.inv(m)
				self.t00 = tmatrix[0,0]
				self.t01 = tmatrix[0,1]
				self.t10 = tmatrix[1,0]
				self.t11 = tmatrix[1,1]
				self.angle = numpy.arctan2(v1,v0)
				self.spacing = dist
				self.lattice_points[point] = secondpoint
				## I am trusting that my new calculated
				## vector is more reliable than the first
				## guess for spacing, otherwise I could set
				## error to be err instead of 0.0
				self.lattice_points_err[point] = 0.0
				self.points.append(secondpoint)
		else:
			self.add_any_point(secondpoint)

	def add_any_point(self, point):
		'''
		this checks to see if a point falls on a lattice
		point, within a certain tolerance
		'''

		p0 = point[0] - self.center[0]
		p1 = point[1] - self.center[1]
		c0 = p0 * self.t00 + p1 * self.t01
		c1 = p0 * self.t10 + p1 * self.t11
		cint0 = round(c0)
		cint1 = round(c1)
		err0 = c0 - cint0
		err1 = c1 - cint1
		err = numpy.sqrt(err0*err0+err1*err1)

		if err < self.tolerance:
			## if already have point at this lattice point,
			## use the one with least error
			closest = int(cint0), int(cint1)
			if closest in self.lattice_points_err:
				closestpoint = self.lattice_points[closest]
				closesterr = self.lattice_points_err[closest]
				if closesterr > err:
					## replace existing point
					self.points.remove(closestpoint)
					self.points.append(point)
					self.lattice_points[closest] = point
					self.lattice_points_err[closest] = err
			else:
				self.lattice_points[closest] = point
				self.lattice_points_err[closest] = err
				self.points.append(point)

def pointsToLattice(points, spacing, tolerance, first_is_center=False):
	# create a lattice for every point, or if centerfirst, then only
	# create a lattice with first point as center
	if first_is_center:
		lattices = [Lattice(points[0], spacing, tolerance)]
	else:
		lattices = []
		for point in points:
			lattices.append(Lattice(point, spacing, tolerance))
	# see which points fit in which lattices
	for point in points:
		#found_lattice = False
		for lat in lattices:
			lat.add_point(point)
	if len(points) == 1:
		best_lattice = lattices[0]
	else:
		# find the best lattice
		maxpoints = 1
		best_lattice = None
		for lat in lattices:
			if len(lat.points) > maxpoints:
				maxpoints = len(lat.points)
				best_lattice = lat
	return best_lattice


if __name__ == '__main__':
	from numpy.random import randint
	import profile
	import pickle

	f = open('rand', 'r')

	#n = 50
	#points = randint(0, 512, (n,2))
	#pickle.dump(points, f)
	points = pickle.load(f)

	f.close()

	points = [(0,0)]
	#lat = profile.run('pointsToLattice(points, 2.0, 0.1)')
	lat = pointsToLattice(points, 2.0, 0.1)
	keys = lat.lattice_points.keys()
	keys.sort()
	for key in keys:
		print key, lat.lattice_points[key]
