#
# COPYRIGHT:
#       The Leginon software is Copyright under
#       Apache License, Version 2.0
#       For terms of the license agreement
#       see  http://leginon.org
#
import numpy
import scipy
from pyami import correlator, convolver, peakfinder, imagefun
import math
from leginon import leginondata

class Tile(object):
	def __init__(self, image, position, imagedata):
		self.image = image
		self.position = position
		self.imagedata = imagedata

class Mosaic(object):
	def __init__(self):
		# This will be set to a float number once getMosaicImage is called
		# with maxdimension is input
		self.scale = None

		self.targetlist = []

		self.correlator = correlator.Correlator()
		self.peakfinder = peakfinder.PeakFinder()
		self.convolver = convolver.Convolver()

		self.tiles = []

		self.positionmethods = {}
		self.positionmethods['correlation'] = self.positionByCorrelation
		self.positionmethods['automatic'] = self.automaticPosition
		self.automaticpriority = ['correlation']
		#self.positionmethod = self.positionmethods.keys()[0]
		self.positionmethod = 'automatic'
		self.boundaries = {'min':(0,0),'max':(1,1)}

	def clear(self):
		self.tiles = []

	def hasTile(self, tile):
		if tile in self.tiles:
			return True
		else:
			return False

	def getTilePosition(self, tile):
		for i in self.tiles:
			if i == tile:	
				return tile.position

	def getTileShape(self, tile):
		for i in self.tiles:
			if i == tile:	
				return tile.image.shape

	def getMosaicImageBoundaries(self):
		mosaicmin = None
		mosaicmax = None
		for tile in self.tiles:
			position = self.getTilePosition(tile)
			shape = self.getTileShape(tile)
			min = position
			max = (position[0] + shape[0], position[1] + shape[1])
			for i in [0, 1]:
				if mosaicmin is None:
					mosaicmin = list(min)
				elif min[i] < mosaicmin[i]:
					mosaicmin[i] = min[i]
				if mosaicmax is None:
					mosaicmax = list(max)
				elif max[i] > mosaicmax[i]:
					mosaicmax[i] = max[i]
		return {'min': (int(round(mosaicmin[0])), int(round(mosaicmin[1]))), 
						'max': (int(round(mosaicmax[0])), int(round(mosaicmax[1])))}

	def getMosaicImage(self, maxdimension=None, numtype=numpy.uint16, make_edge=False):
		if not self.tiles:
			return None
		bbox = self.getMosaicImageBoundaries()
		self.boundaries = bbox
		imageshape = [bbox['max'][0] - bbox['min'][0], 
									bbox['max'][1] - bbox['min'][1]]
		### scale the mosaic shape
		scale = 1.0
		scaleoffset = [0, 0]
		if maxdimension is not None:
			for value in imageshape:
				newscale = float(maxdimension)/float(value)
				if newscale < scale:
					scale = newscale

			for i, value in enumerate(imageshape):
				imageshape[i] = int(numpy.ceil(scale*value))
		self.scale = scale
		### create mosaic image
		if self.tiles:
			numtype = self.tiles[0].image.dtype
		if make_edge:
			numtype = numpy.bool
		mosaicimage = numpy.zeros(imageshape, numtype)
		### scale and insert tiles
		for tile in self.tiles:
			position = self.getTilePosition(tile)
			shape = self.getTileShape(tile)
			offset = (position[0] - bbox['min'][0], position[1] - bbox['min'][1])
			offset = (int(round(offset[0] * scale + scaleoffset[0])),
									int(round(offset[1] * scale + scaleoffset[1])))

			image = imagefun.scale(tile.image, scale)
			if make_edge:
				# fill mosaic with flat tiles with values of one
				image = numpy.ones(image.shape,numtype)
			else:
				image = numpy.asarray(image, numtype)
			mosaicimage[offset[0]:offset[0] + image.shape[0],
									offset[1]:offset[1] + image.shape[1]] = image
		if make_edge:
			### Make sure the edge of the mosaic canvas are treated as tile edge.
			# set first and last column and rows to zero
			mosaicimage[:,0]=0
			mosaicimage[:,shape[1]-1]=0
			mosaicimage[0,:]=0
			mosaicimage[shape[0]-1,:]=0
			mosaicimage = scipy.ndimage.generic_gradient_magnitude(mosaicimage, derivative=scipy.ndimage.sobel)
			# convert to boolean to save space
			mosaicimage = mosaicimage.astype(numpy.bool)
		return mosaicimage

	def addTile(self, image, neighbors):
		position = self.positionmethods[self.positionmethod](image, neighbors)
		if image is None:
			raise ValueError('invalid image for tile')
		tile = Tile(image, position)
		self.tiles.append(tile)
		return tile

	def automaticPosition(self, image, neighbors):
		for positionmethod in self.automaticpriority:
			return self.positionmethods[positionmethod](image, neighbors)
		raise RuntimeError('cannot position tile')

	def getPeak(self, image1, image2):
		self.correlator.setImage(0, image1)
		self.correlator.setImage(1, image2)
		pcimage = self.correlator.phaseCorrelate()
		self.peakfinder.setImage(pcimage)
		self.peakfinder.pixelPeak()
		peak = self.peakfinder.getResults()
		return peak['pixel peak value']

	def compareShifts(self, unwrappedshift, wrappedshift, image1, image2):
		# if both shift values disagree, we must check all four of the possible
		# correct shift pairs
		if unwrappedshift[0] != wrappedshift[0] \
											and unwrappedshift[1] != wrappedshift[1]:
			# holds peak values for the four cases for comparison at the end
			peakmatrix = numpy.zeros((2,2), numpy.float32)

			# tests if both unwrapped shift values are valid
			peakmatrix[0, 0] = self.getPeak(
				image2[unwrappedshift[0]:, unwrappedshift[1]:],
				image1[:image2.shape[0] - unwrappedshift[0],
								:image2.shape[1] - unwrappedshift[1]])

			# tests if unwrappedshift[0] is valid and wrappedshift[1] is valid 
			peakmatrix[0, 1] = self.getPeak(
				image2[unwrappedshift[0]:, :image1.shape[1] + wrappedshift[1]],
				image1[:image2.shape[0] - unwrappedshift[0], -wrappedshift[1]:])

			# tests if wrappedshift[0] is valid and unwrappedshift[1] is valid 
			peakmatrix[1, 0] = self.getPeak(
				image2[:image1.shape[0] + wrappedshift[0], unwrappedshift[1]:],
				image1[-wrappedshift[0]:, :image2.shape[1] - unwrappedshift[1]])

			# tests if both wrapped shift values are valid
			peakmatrix[1, 1] = self.getPeak(
				image2[:image1.shape[0] + wrappedshift[0],
								:image1.shape[1] + wrappedshift[1]],
				image1[-wrappedshift[0]:, -wrappedshift[1]:])

			# finds the biggest peak in the matrix
			maxvalue = 0.0
			for i in range(len(peakmatrix)):
				for j in range(len(peakmatrix[i])):
					if peakmatrix[i, j] > maxvalue:
						maxvalue = peakmatrix[i, j]
						maxpeak = (i, j)

			# assigns the correct shift based on the matrix
			if maxpeak[0] == 1:
				shift0 = wrappedshift[0]
			else:
				shift0 = unwrappedshift[0]
			if maxpeak[1] == 1:
				shift1 = wrappedshift[1]
			else:
				shift1 = unwrappedshift[1]

		# unwrappedshift[1] and wrappedshift[1] agree,
		# unwrappedshift[0] and wrappedshift[0] do not
		elif unwrappedshift[0] != wrappedshift[0]:
			unwrappedshiftpeak = self.getPeak(
				image2[unwrappedshift[0]:, unwrappedshift[1]:],
				image1[:image2.shape[0] - unwrappedshift[0],
								:image2.shape[1] - unwrappedshift[1]])
			wrappedshiftpeak = self.getPeak(
				image2[:image1.shape[0] + wrappedshift[0], wrappedshift[1]:],
				image1[-wrappedshift[0]:, :image2.shape[1] - wrappedshift[1]])

			# use the shift[0] with the biggest peak
			if unwrappedshiftpeak < wrappedshiftpeak:
				shift0 = wrappedshift[0]
			else:
				shift0 = unwrappedshift[0]
			shift1 = unwrappedshift[1]

		# unwrappedshift[0] and wrappedshift[0] agree,
		# unwrappedshift[1] and wrappedshift[1] do not
		elif unwrappedshift[1] != wrappedshift[1]:
			unwrappedshiftpeak = self.getPeak(
				image2[unwrappedshift[0]:, unwrappedshift[1]:],
				image1[:image2.shape[0]-unwrappedshift[0],
								:image2.shape[1]-unwrappedshift[1]])
			wrappedshiftpeak = self.getPeak(
				image2[wrappedshift[0]:, :image1.shape[1] + wrappedshift[1]],
				image1[:image2.shape[0] - wrappedshift[0], -wrappedshift[1]:])

			shift0 = unwrappedshift[0]
			# use the shift[1] with the biggest peak
			if unwrappedshiftpeak < wrappedshiftpeak:
				shift1 = wrappedshift[1]
			else:
				shift1 = unwrappedshift[1]
		else:
			# unwrappedshift and wrappedshift agree, no need to check
			shift0 = unwrappedshift[0]
			shift1 = unwrappedshift[1]

		return (shift0, shift1)

	def votePosition(self, positionvotes, tileposition, peakvalue):
		# add a vote for this position per axis
		# add the peak value to the sum of peak values for the position per axis
		for i in [0, 1]:
			if tileposition[i] in positionvotes[i]:
				positionvotes[i][tileposition[i]]['votes'] += 1
				positionvotes[i][tileposition[i]]['peaks value'] += peakvalue
			else:
				positionvotes[i][tileposition[i]] = {'votes': 1,
					'peaks value': peakvalue}
		return positionvotes

	def bestPosition(self, positionvotes):
		# which ever position has the most votes wins per axis
		# the sum of the peak values for the position breaks ties
		position = [0, 0]
		for i in [0, 1]:
			maxvotes = 0
			maxpeakvalue = 0.0
			for p in positionvotes[i]:
				if positionvotes[i][p]['votes'] > maxvotes:
					position[i] = p
					maxvotes = positionvotes[i][p]['votes']
					maxpeakvalue = positionvotes[i][p]['peaks value']
				elif positionvotes[i][p]['votes'] == maxvotes:
					if positionvotes[i][p]['peaks value'] > maxpeakvalue:
						position[i] = p
						maxvotes = positionvotes[i][p]['votes']
						maxpeakvalue = positionvotes[i][p]['peaks value']
		return tuple(position)

	def positionByCorrelation(self, image, neighbors):
		if not self.tiles:
			return (0, 0)
		positionvotes = ({}, {})
		for neighbor in neighbors:
			if self.hasTile(neighbor):
				neighborposition = self.getTilePosition(neighbor)

				# phase correlate the tile image with the neighbors
				self.correlator.setImage(0, image)
				self.correlator.setImage(1, neighbor.image)
				pcimage = self.correlator.phaseCorrelate()
				self.peakfinder.setImage(pcimage)
				self.peakfinder.pixelPeak()
				peak = self.peakfinder.getResults()

				# determine which of the shifts is valid
				unwrappedshift = peak['pixel peak']
				wrappedshift = correlator.wrap_coord(peak['pixel peak'],
																										pcimage.shape)
				shift = self.compareShifts(unwrappedshift, wrappedshift,
																		image, neighbor.image)

				# use the shift and the neighbor position to get tile position
				position = (neighborposition[0] + shift[0],
												neighborposition[1] + shift[1])
				peakvalue = peak['pixel peak value']

				# add a vote for this position
				positionvotes = self.votePosition(positionvotes, position, peakvalue)

		return self.bestPosition(positionvotes)

	def getNearestTile(self, x, y):
		row = y
		column = x

		bbox = self.getMosaicImageBoundaries()
		imageshape = (bbox['max'][0] - bbox['min'][0], 
									bbox['max'][1] - bbox['min'][1])

		maxmagnitude = math.sqrt(imageshape[0]**2 + imageshape[1]**2)
		nearestdelta = (0,0)
		nearesttile = None
		for tile in self.tiles:
			position = self.getTilePosition(tile)
			tileshape = self.getTileShape(tile)
			offset = (-bbox['min'][0], -bbox['min'][1])
			offsetposition = (position[0] + offset[0], position[1] + offset[1])
			location = ((row - offsetposition[0]), (column - offsetposition[1]))
			deltaposition = ((location[0] - tileshape[0]/2.0),
												(location[1] - tileshape[1]/2.0))
			magnitude = math.sqrt((deltaposition[0])**2 + (deltaposition[1])**2)
			if magnitude < maxmagnitude:
				maxmagnitude = magnitude
				nearestdelta = deltaposition
				nearesttile = tile
		return nearesttile, nearestdelta, location

class EMTile(Tile):
	def __init__(self, imagedata):
		image = imagedata['image']
		Tile.__init__(self, image, position=None, imagedata=imagedata)

class EMMosaic(object):
	def __init__(self, calibrationclient):
		# This will be set to a float number once getMosaicImage is called
		# with maxdimension is input
		self.scale = None
		self.edge_width = None
		self.convolver = convolver.Convolver()
		self.setCalibrationClient(calibrationclient)
		self.clear()

	def hasTiles(self):
		if self.tiles:
			return True
		else:
			return False

	def clear(self):
		self.tiles = []

	def setCalibrationClient(self, calibrationclient):
		self.calibrationclient = calibrationclient

	def addTile(self, imagedata):
		tile = EMTile(imagedata)
		self.tiles.append(tile)
		return tile

	def round(self, f):
		try:
			return int(round(f))
		except:
			return int(round(f[0])), int(round(f[1]))

	def calculateMosaicImage(self):
		'''
		calculates (but does not generate) an unscaled mosaic image
		'''
		if not self.tiles:
			return
		param = self.calibrationclient.parameter()
		## calculate parameter center of final mosaic image
		center = {'x': 0.0, 'y': 0.0}
		for tile in self.tiles:
			tileparam = tile.imagedata['scope'][param]
			center['x'] += tileparam['x']
			center['y'] += tileparam['y']
		n = len(self.tiles)
		# float math here
		center['x'] /= n
		center['y'] /= n
		# center of the mosaic in scope parameter such as stage position.
		self.center = center

		## Calculate pixel vector on final image to center of 
		## each tile.
		## To use calibrationclient's itransform method, we need
		## a fake image from which to calculate a pixel vector
		## Maybe could use an actual final image leginondata.
		someimage = self.tiles[0].imagedata
		self.fakescope = leginondata.ScopeEMData(initializer=someimage['scope'])
		self.fakescope[param] = dict(someimage['scope'][param])
		self.fakescope[param].update(center)
		## assume the final fake image has same binning as first tile
		self.fakecamera = leginondata.CameraEMData(initializer=someimage['camera'])
		tile0 = self.tiles[0]
		mosaic0 = mosaic1 = None
		for tile in self.tiles:
			tileparam = {}
			## calculate the parameter shift from center of 
			## mosaic image to center of tile
			for axis in ('x','y'):
				tileparam[axis] = tile.imagedata['scope'][param][axis]
			## calculate corresponding pixel shift (float)
			center2center = self.positionByCalibration(tileparam)
			## for targeting, until it's fixed
			tile.position = center2center

			## pixel shift mosaic center to tile center (int)
			center2center = self.round(center2center)
			tile.center_vect = center2center

			## pixel shift from center of mosaic to corners of tile
			shape = tile.image.shape
			# These are integer math
			corner_vect = center2center[0]-shape[0]//2, center2center[1]-shape[1]//2
			corner1_vect = corner_vect[0]+shape[0], corner_vect[1]+shape[1]
			tile.corner_vect = corner_vect
			## check if this is a min or max in the mosaic
			if mosaic0 is None:
				mosaic0 = [corner_vect[0], corner_vect[1]]
				mosaic1 = [corner1_vect[0], corner1_vect[1]]
			for axis in (0,1):
				if corner_vect[axis] < mosaic0[axis]:
					mosaic0[axis] = corner_vect[axis]
				if corner1_vect[axis] > mosaic1[axis]:
					mosaic1[axis] = corner1_vect[axis]
		## mosaic shape at full scale
		self.mosaicshape = mosaic1[0]-mosaic0[0], mosaic1[1]-mosaic0[1]

		## position of corner and center
		for tile in self.tiles:
			corner_pos = tile.corner_vect[0]-mosaic0[0], tile.corner_vect[1]-mosaic0[1]
			center_pos = tile.center_vect[0]-mosaic0[0], tile.center_vect[1]-mosaic0[1]
			tile.corner_pos = corner_pos
			tile.center_pos = center_pos

	def scaled(self, coord):
		scoord = self.scale*coord[0], self.scale*coord[1]
		intcoord = self.round(scoord)
		return intcoord

	def unscaled(self, coord):
		newcoord = float(coord[0])/self.scale, float(coord[1])/self.scale
		return newcoord

	def getMosaicImage(self, maxdimension=None, make_edge=False):
		self.calculateMosaicImage()

		### scale the mosaic shape
		if maxdimension is None:
			scale = 1.0
		else:
			maxdim = max(self.mosaicshape)
			## restore old stupid patch. It avoids rounding problem
			## and misaligned matrices errors
			scale = float(maxdimension-1) / float(maxdim)
		self.scale = scale

		numtype = self.tiles[0].image.dtype

		### find shape of final mosaic
		### optimize me
		maxrow = maxcol = 0
		for tile in self.tiles:
			scaled_tile = imagefun.scale(tile.image, scale)
			scaled_tile = numpy.asarray(scaled_tile, numtype)
			scaled_shape = scaled_tile.shape
			scaled_pos = self.scaled(tile.corner_pos)
			rowslice1 = scaled_pos[0],scaled_pos[0]+scaled_shape[0]
			colslice1 = scaled_pos[1],scaled_pos[1]+scaled_shape[1]
			rowslice = slice(scaled_pos[0],scaled_pos[0]+scaled_shape[0])
			colslice = slice(scaled_pos[1],scaled_pos[1]+scaled_shape[1])
			if rowslice1[1] > maxrow:
				maxrow = rowslice1[1]
			if colslice1[1] > maxcol:
				maxcol = colslice1[1]
		### mosaic image shape
		mshape = (maxrow,maxcol)

		### create mosaic image
		if make_edge:
			numtype = numpy.bool
		mosaicimage = numpy.zeros(mshape, numtype)

		### scale and insert tiles
		for tile in self.tiles:
			# TODO: This part duplicates the code above. Keeping it for now
			# since mshape is not equal to self.mosaicshape.
			scaled_tile = imagefun.scale(tile.image, scale)
			scaled_tile = numpy.asarray(scaled_tile, numtype)
			scaled_shape = scaled_tile.shape
			scaled_pos = self.scaled(tile.corner_pos)
			rowslice = slice(scaled_pos[0],scaled_pos[0]+scaled_shape[0])
			colslice = slice(scaled_pos[1],scaled_pos[1]+scaled_shape[1])
			if make_edge:
				# fill mosaic with flat tiles with values of one
				scaled_tile = numpy.ones(scaled_tile.shape, numtype)
			mosaicimage[rowslice, colslice] = scaled_tile
		if make_edge:
			### Make sure the edge of the mosaic canvas are treated as tile edge.
			# set first and last column and rows to zero
			mosaicimage[:,0]=0
			mosaicimage[:,mshape[1]-1]=0
			mosaicimage[0,:]=0
			mosaicimage[mshape[0]-1,:]=0
			# edge finding
			mosaicimage = scipy.ndimage.generic_gradient_magnitude(mosaicimage, derivative=scipy.ndimage.sobel)
			# convert to boolean to save space
			mosaicimage = mosaicimage.astype(numpy.bool)
		return mosaicimage

	def getEdgeMosaicImage(self, maxdimension=None, width=None):
		'''
		Return a binary image of the outer edge of the mosaic atlas.
		This is used to eliminate targets auto-selected near the edge.
		width defines a convolution kernel to make the edge to returned
		at the given width.
		'''
		mosaicimage = self.getMosaicImage(maxdimension, make_edge=True)
		if width is None:
			# default to 15 percent of the tile size based on typical gr images.
			t0 = self.tiles[0]
			t0_half_shape = t0.center_pos[0]-t0.corner_pos[0],t0.center_pos[1]-t0.corner_pos[1]
			width = int(max(self.scaled(t0_half_shape))*0.3)
		self.edge_width = width
		kernel = numpy.ones(width*width)
		kernel = kernel.reshape((width,width))
		self.convolver.setKernel(kernel)
		mosaicimage = numpy.greater(self.convolver.convolve(image=mosaicimage),numpy.ones(mosaicimage.shape))
		return mosaicimage

	def distanceToTile(self, tile, row, col):
		tilepos = tile.center_pos
		rdist = tilepos[0] - row
		cdist = tilepos[1] - col
		dist = numpy.hypot(rdist, cdist)
		return dist

	def getNearestTile(self, row, col):
		if not self.tiles:
			return 
		nearest = self.tiles[0]
		nearestdist = self.distanceToTile(nearest, row, col)
		for tile in self.tiles[1:]:
			dist = self.distanceToTile(tile, row, col)
			if dist < nearestdist:
				nearest = tile
				nearestdist = dist
		return nearest

	def tile2mosaic(self, tile, tilepos):
		'''
		return an unscaled mosaic position given a tile and a position
		on the unscaled tile image
		'''
		mos = tile.corner_pos[0] + tilepos[0], tile.corner_pos[1] + tilepos[1]
		return mos

	def mosaic2tile(self, mosaic_pos):
		'''
		given a mosaic position
		return a tile and a position on that tile
		'''
		tile = self.getNearestTile(mosaic_pos[0], mosaic_pos[1])

		pos = mosaic_pos[0]-tile.corner_pos[0], mosaic_pos[1]-tile.corner_pos[1]
		return tile, pos

	def getFakeParameter(self):
		param = self.calibrationclient.parameter()
		return self.fakescope[param]

	def positionByCalibration(self, value):
		'''
		calculate a pixel vector which corresponds to
		the given parameter value from the same of the fakeimage.
		'''
		position = self.calibrationclient.itransform(value, self.fakescope, self.fakecamera)
		if position is None:
			return None
		# this makes it work with calibration
		position['row'] *= -1
		position['col'] *= -1
		return (position['row'], position['col'])
