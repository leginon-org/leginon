import Numeric
import fftengine
import correlator
import peakfinder
import math

class Tile(object):
	def __init__(self, image, position):
		self.image = image
		self.position = position

class Mosaic(object):
	def __init__(self):
		self.targetlist = []

		self.correlator = correlator.Correlator(fftengine.fftNumeric())
		self.peakfinder = peakfinder.PeakFinder()

		self.tiles = []

		self.positionmethods = {}
		self.positionmethods['correlation'] = self.positionByCorrelation
		self.positionmethods['automatic'] = self.automaticPosition
		self.automaticpriority = ['correlation']
		#self.positionmethod = self.positionmethods.keys()[0]
		self.positionmethod = 'automatic'

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

	def getMosaicImage(self, astype=Numeric.Int16):
		bbox = self.getMosaicImageBoundaries()
		imageshape = (bbox['max'][0] - bbox['min'][0], 
									bbox['max'][1] - bbox['min'][1])
		mosaicimage = Numeric.zeros(imageshape, astype)
		for tile in self.tiles:
			position = self.getTilePosition(tile)
			shape = self.getTileShape(tile)
			offset = (position[0] - bbox['min'][0], position[1] - bbox['min'][1])
			limit = (offset[0] + shape[0], offset[1] + shape[1])
			mosaicimage[int(round(offset[0])):int(round(limit[0])),
									int(round(offset[1])):int(round(limit[1]))] \
																					= tile.image.astype(astype)
		return mosaicimage

	def addTile(self, image, neighbors):
		position = self.positionmethods[self.positionmethod](image, neighbors)
		self.tiles.append(Tile(image, position))

	def automaticPosition(self, image, neighbors):
		for positionmethod in self.automaticpriority:
#			try:
			return self.positionmethods[positionmethod](image, neighbors)
#			except:
#				pass
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
			peakmatrix = Numeric.zeros((2,2), Numeric.Float32)

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
	def __init__(self, image, state, position):
		Tile.__init__(self, image, position)
		self.state = state

class EMMosaic(Mosaic):
	def __init__(self, calibrationclients):
		self.calibrationclients = calibrationclients
		self.setCalibrationParameter('stage position')

		Mosaic.__init__(self)

		self.positionmethods['calibration'] = self.positionByCalibration
		self.automaticpriority = ['calibration', 'correlation']
		self.positionmethod = 'calibration'

	def getCalibrationParameters(self):
		return self.calibrationclients.keys()

	def getCalibrationParameter(self):
		return self.calibration

	def setCalibrationParameter(self, parameter):
		if parameter in self.getCalibrationParameters():
			self.calibration = parameter
		else:
			raise ValueError('invalid calibration parameter')

	def addTile(self, imagedata):
		image = imagedata['image']
		state = {}
		state['scope'] = imagedata['scope']
		state['camera'] = imagedata['camera']
		position = self.positionmethods[self.positionmethod](imagedata)

		self.tiles.append(EMTile(image, state, position))

	def positionByCalibration(self, state):
		if self.calibration == 'all':
			parameters = self.calibrationclients.values()
		else:
			calibrations = [self.calibrationclients[self.calibration]]
		position = {'row': 0.0, 'col': 0.0}
		for calibration in calibrations:
			parameterposition = calibration.itransform(
																			state['scope'][calibration.parameter()],
																			state['scope'], state['camera'])
			if parameterposition is None:
				self.printerror('calibration positioning error')
				return None
			position['row'] += parameterposition['row']
			position['col'] += parameterposition['col']
		# this makes it work with calibration
		position['row'] *= -1
		position['col'] *= -1
		return (position['row'], position['col'])

	def getTargetInfo(self, x, y):
		tile, deltaposition, location = self.getNearestTile(x, y)
		return {'delta row': deltaposition[0],
						'delta column': deltaposition[1],
						'scope': tile.state['scope'],
						'camera': tile.state['camera']}

