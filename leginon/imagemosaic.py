import watcher
import data
import event
import Numeric
import fftengine
import correlator
import peakfinder
import LinearAlgebra
import threading
from Tkinter import *
import ImageViewer

class ImageMosaic(watcher.Watcher):
	def __init__(self, id, nodelocations, watchfor = event.ImageTilePublishEvent, **kwargs):
		# needs own event?
		lockblocking = 1
		watcher.Watcher.__init__(self, id, nodelocations, watchfor, lockblocking, **kwargs)

		self.imagemosaic = {}

		self.correlator = correlator.Correlator(fftengine.fftNumeric())
		self.peakfinder = peakfinder.PeakFinder()

		### some things for the pop-up viewer
		self.iv = None
		self.viewer_ready = threading.Event()

		self.defineUserInterface()
		#self.start()

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

	def processData(self, idata):
		tileimage = idata.content['image']
		neighbors = idata.content['neighbor tiles']
		if len(neighbors) == 0:
			self.imagemosaic = {}
			self.imagemosaic[idata.id] = {'image': tileimage, 'position': (0, 0)}
		else:
			positionvotes = ({}, {})
			# calculate the tile's position based on shift from each of the neighbors
			for neighbor in neighbors:
				if neighbor not in self.imagemosaic:
					# we don't know about its neighbors, wait for them?
					self.printerror('unknown neighbor %s' % str(neighbor))
					break
				neighborimage = self.imagemosaic[neighbor]['image']
				neighborposition = self.imagemosaic[neighbor]['position']

				# phase correlate the tile image with the neighbors
				self.correlator.setImage(0, tileimage)
				self.correlator.setImage(1, neighborimage)
				pcimage = self.correlator.phaseCorrelate()
				self.peakfinder.setImage(pcimage)
				self.peakfinder.pixelPeak()
				peak = self.peakfinder.getResults()

				# determine which of the shifts is valid
				unwrappedshift = peak['pixel peak']
				wrappedshift = correlator.wrap_coord(peak['pixel peak'], pcimage.shape)
				shift = self.compareShifts(unwrappedshift, wrappedshift,
						tileimage, neighborimage)

				# use the shift and the neighbor position to get tile position
				tileposition = (neighborposition[0] + shift[0],
										neighborposition[1] + shift[1])
				peakvalue = peak['pixel peak value']

				# add a vote for this position
				positionvotes = self.votePosition(positionvotes,
													tileposition, peakvalue)

			# add the tile image and position to the mosaic
			self.imagemosaic[idata.id] = {}
			self.imagemosaic[idata.id]['image'] = tileimage
			self.imagemosaic[idata.id]['position'] = self.bestPosition(positionvotes)
		print idata.id, "position =", self.imagemosaic[idata.id]['position']

	def makeImage(self, mosaic):
		# could be Inf
		mincoordinate = [0, 0]
		maxcoordinate = [0, 0]
		for tileid in mosaic:
			for i in [0, 1]:
				min = mosaic[tileid]['position'][i]
				max = mosaic[tileid]['position'][i] + mosaic[tileid]['image'].shape[i]
				if min < mincoordinate[i]:
					mincoordinate[i] = min
				if max > maxcoordinate[i]:
					maxcoordinate[i] = max
		imageshape = (maxcoordinate[0] - mincoordinate[0], 
									maxcoordinate[1] - mincoordinate[1]) 
		image = Numeric.zeros(imageshape, Numeric.UnsignedInt16)
		for tileid in mosaic:
			row = mosaic[tileid]['position'][0] - mincoordinate[0]
			column = mosaic[tileid]['position'][1] - mincoordinate[1]
			iti = mosaic[tileid]['image']
			image[row:row + iti.shape[0], column:column + iti.shape[1]] = iti.astype(Numeric.UnsignedInt16)
		return image

	def OLDuiShow(self):
		i = self.makeImage(self.imagemosaic)
		import Image
		Image.fromstring('L', (i.shape[1], i.shape[0]), i.tostring()).show()
		return ''

	def uiShow(self):
		self.displayNumericArray(self.makeImage(self.imagemosaic))

	def start_viewer_thread(self):
		if self.iv is not None:
			return
		self.viewerthread = threading.Thread(name=`self.id`, target=self.open_viewer)
		self.viewerthread.setDaemon(1)
		self.viewerthread.start()

	def open_viewer(self):
		root = self.root = Toplevel()
		root.wm_geometry('=450x400')

		self.iv = ImageViewer.ImageViewer(root, bg='#488')
		self.iv.pack()

		self.viewer_ready.set()
		root.mainloop()

		##clean up if window destroyed
		self.viewer_ready.clear()
		self.iv = None

	def displayNumericArray(self, numarray):
		self.start_viewer_thread()
		self.viewer_ready.wait()
		if numarray is not None:
			self.iv.import_numeric(numarray)
			self.iv.update()

	def uiPublishMosaicImage(self):
		odata = data.ImageData(self.ID(), self.makeImage(self.imagemosaic))
		self.publish(odata, event.ImagePublishEvent)
		return ''

	def uiClearMosaic(self):
		self.imagemosaic = {}

	def defineUserInterface(self):
		watcherspec = watcher.Watcher.defineUserInterface(self)
		showspec = self.registerUIMethod(self.uiShow, 'Show Image', ())
		publishspec = self.registerUIMethod(self.uiPublishMosaicImage,
										'Publish Image', ())
		clearspec = self.registerUIMethod(self.uiClearMosaic, 'Clear', ())
		imagespec = self.registerUIContainer('Image',
																					(showspec, publishspec, clearspec))
		self.registerUISpec('Image Mosaic', (watcherspec, imagespec))

class StateImageMosaic(ImageMosaic):
	def __init__(self, id, nodelocations,
								watchfor = event.StateImageTilePublishEvent, **kwargs):
		self.calibration = None
		self.methods = ['calibration', 'correlation']
		self.method = self.methods[0]
		ImageMosaic.__init__(self, id, nodelocations, watchfor, **kwargs)

		self.addEventInput(event.CalibrationPublishEvent, self.setCalibration)
		self.start()

	def setCalibration(self, ievent):
		print 'setting calibration'
		idata = self.researchByDataID(ievent.content)
		self.calibration = idata.content

	def setProcessingMethod(self, processingmethod):
		if method in self.methods:
			self.method = method
		else:
			raise ValueError

	def processData(self, idata):
		print 'processData, state for idata =', idata.content['state']
		if self.method == 'correlation':
			self.processDataByCorrelation(idata)
		elif self.method == 'calibration':
			self.processDataByCalibration(idata)
		else:
			self.printerror('invalid processing method specified')
			raise ValueError
		self.imagemosaic[idata.id]['state'] = idata.content['state']

	def pixelLocation(self, row, column):
		print 'pixelLocation args =', row, column
		matrix = self.calibration2matrix()
		print 'pixelLocation matrix =', matrix
#		determinant = LinearAlgebra.determinant(matrix)
#		print 'pixelLocation determinant =', determinant
#		x = (matrix[1,1] * column - matrix[1,0] * row) / determinant
#		y = (matrix[0,0] * row - matrix[0,1] * column) / determinant
		x = (column * matrix[0, 0] + row * matrix[1, 0])/4
		y = (column * matrix[0, 1] + row * matrix[1, 1])/4
		print 'pixelLocation x, y =', x, y
		return (int(round(x)), int(round(y)))

	def calibration2matrix(self):
		matrix = Numeric.array([[self.calibration['x pixel shift']['x'],
														self.calibration['x pixel shift']['y']],
													[self.calibration['y pixel shift']['x'],
														self.calibration['y pixel shift']['y']]])
		matrix[0] /= self.calibration['x pixel shift']['value']
		matrix[1] /= self.calibration['y pixel shift']['value']
		return matrix

	def processDataByCalibration(self, idata):
		#tileimage = idata.content['image']
		neighbors = idata.content['neighbor tiles']
		if len(neighbors) == 0:
			self.imagemosaic = {}

		if self.calibration is None:
			self.printerror(
				'unable to process data %s by calibration, no calibration available'
					% str(idata.id))
			return
		# hardcode for now
		self.imagemosaic[idata.id] = {}
		self.imagemosaic[idata.id]['image'] = idata.content['image']
		self.imagemosaic[idata.id]['position'] = \
			self.pixelLocation(idata.content['state']['stage position']['y'],
														idata.content['state']['stage position']['x']) 
		print idata.id, "position =", self.imagemosaic[idata.id]['position']

	def processDataByCorrelation(self, idata):
		ImageMosaic.processData(self, idata)

	def uiPublishMosaicImage(self):
		#ImageMosaic.uiPublishMosaicImage(self)

		odata = data.ImageData(self.ID(), self.makeImage(self.imagemosaic))
		self.publish(odata, event.ImagePublishEvent)

		statedata = {'image data ID': odata.id}
		for dataid in self.imagemosaic:
			statedata[dataid] = {}
			statedata[dataid]['position'] = self.imagemosaic[dataid]['position']
			statedata[dataid]['state'] = self.imagemosaic[dataid]['state']
		self.publish(data.StateMosaicData(self.ID(), statedata),
			event.StateMosaicPublishEvent)

		return ''

