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
import Mrc
import math
import calibrationclient
import xmlrpclib
#import xmlrpclib2 as xmlbinlib
xmlbinlib = xmlrpclib

class ImageMosaicInfo(object):
	def __init__(self):
		self.imageinfo = {}

	def addTile(self, dataid, image, position):
		self.imageinfo[dataid] = {}
		self.imageinfo[dataid]['image'] = image
		self.imageinfo[dataid]['position'] = position

	def hasTile(self, dataid):
		if dataid in self.getTileDataIDs():
			return True
		else:
			return False

	def hasTiles(self, dataids):
		for dataid in dataids:
			if not self.hasTile(dataid):
				return False
		return True

	def getTileImage(self, dataid):
		try:
			return self.imageinfo[dataid]['image']
		except KeyError:
			raise ValueError

	def getTilePosition(self, dataid):
		try:
			return self.imageinfo[dataid]['position']
		except KeyError:
			raise ValueError

	def getTileDataIDs(self):
		return self.imageinfo.keys()

	def getTileShape(self, dataid):
		return self.getTileImage(dataid).shape

	def getMosaicLimits(self):
		# could be Inf
		imagemin = [0, 0]
		imagemax = [0, 0]
		tiledataids = self.getTileDataIDs()
		for tiledataid in tiledataids:
			tileposition = self.getTilePosition(tiledataid)
			tileshape = self.getTileShape(tiledataid)
			tilemin = tileposition
			tilemax = (tileposition[0] + tileshape[0], tileposition[1] + tileshape[1])
			for i in [0, 1]:
				if tilemin[i] < imagemin[i]:
					imagemin[i] = tilemin[i]
				if tilemax[i] > imagemax[i]:
					imagemax[i] = tilemax[i]

		return {'min': (int(round(imagemin[0])), int(round(imagemin[1]))), 
						'max': (int(round(imagemax[0])), int(round(imagemax[1])))}

	def getMosaicImage(self, astype=Numeric.Int16):
		limits = self.getMosaicLimits()
		imageshape = (limits['max'][0] - limits['min'][0], 
									limits['max'][1] - limits['min'][1])

		mosaicimage = Numeric.zeros(imageshape, astype)

		tiledataids = self.getTileDataIDs()
		for tiledataid in tiledataids:
			tileposition = self.getTilePosition(tiledataid)
			tileshape = self.getTileShape(tiledataid)
			tileimage = self.getTileImage(tiledataid)
			tileoffset = (tileposition[0] - limits['min'][0],
										tileposition[1] - limits['min'][1])
			tilelimit = (tileoffset[0] + tileshape[0], tileoffset[1] + tileshape[1])
			mosaicimage[int(round(tileoffset[0])):int(round(tilelimit[0])),
									int(round(tileoffset[1])):int(round(tilelimit[1]))] \
																				= tileimage.astype(astype)

		return mosaicimage

class StateImageMosaicInfo(ImageMosaicInfo):
	def addTile(self, dataid, image, position, scope, camera):
		ImageMosaicInfo.addTile(self, dataid, image, position)
		self.imageinfo[dataid]['scope'] = scope
		self.imageinfo[dataid]['camera'] = camera
		self.imageinfo[dataid]['shape'] = image.shape

	def getTileState(self, dataid):
		try:
			tilestatedata = {}
			tilestatedata['position'] = self.getTilePosition(dataid)
			tilestatedata['scope'] = self.imageinfo[dataid]['scope']
			tilestatedata['camera'] = self.imageinfo[dataid]['camera']
			tilestatedata['shape'] = self.imageinfo[dataid]['shape']
			limits = self.getMosaicLimits()
			tilestatedata['offset'] = (-limits['min'][0], -limits['min'][1])
		except KeyError:
			raise ValueError
		return tilestatedata

	def getTileStates(self):
		tilestatesdata = {}
		for tiledataid in self.getTileDataIDs():
			tilestatesdata[tiledataid] = self.getTileState(tiledataid)
		return tilestatesdata

class ImageMosaic(watcher.Watcher):
	def __init__(self, id, nodelocations, watchfor = event.TileImagePublishEvent, **kwargs):
		# needs own event?
		lockblocking = 1
		watcher.Watcher.__init__(self, id, nodelocations, watchfor,
																					lockblocking, **kwargs)

		self.correlator = correlator.Correlator(fftengine.fftNumeric())
		self.peakfinder = peakfinder.PeakFinder()

		self.imagemosaics = []

		self.positionmethods = {}
		self.positionmethods['correlation'] = self.positionByCorrelation
		self.positionmethods['automatic'] = self.automaticPosition
		self.automaticpriority = ['correlation']
		#self.positionmethod = self.positionmethods.keys()[0]
		self.positionmethod = 'automatic'

		### some things for the pop-up viewer
		self.iv = None
		self.viewer_ready = threading.Event()

		self.defineUserInterface()
		#self.start()

	def die(self, ievent=None):
		self.close_viewer()
		watcher.Watcher.die(self)

	def processData(self, idata):
		tileimage = idata.content['image']
		neighbors = idata.content['neighbor tiles']
		mosaics = []
		for imagemosaic in self.imagemosaics:
			for neighbor in neighbors:
				if imagemosaic.hasTile(neighbor):
					mosaics.append(imagemosaic)
					break
		if len(mosaics) == 0:
			imagemosaic = ImageMosaicInfo()
			position = self.positionmethods[self.positionmethod](idata, None)
			imagemosaic.addTile(idata.id, tileimage, position)
			self.imagemosaics.append(imagemosaic)
			print idata.id, "position =", imagemosaic.getTilePosition(idata.id)
		else:
			for imagemosaic in mosaics:
				position = self.positionmethods[self.positionmethod](idata, imagemosaic)
				imagemosaic.addTile(idata.id, tileimage, position)
				print idata.id, "position =", imagemosaic.getTilePosition(idata.id)

	def automaticPosition(self, idata, imagemosaic):
		for positionmethod in self.automaticpriority:
			try:
				return self.positionmethods[positionmethod](idata, imagemosaic)
			# needs exception?
			except:
				pass
		raise Exception

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

	def positionByCorrelation(self, idata, imagemosaic):
		if imagemosaic is None:
			return (0, 0)
		tileimage = idata.content['image']
		neighbors = idata.content['neighbor tiles']
		positionvotes = ({}, {})
		for neighbor in neighbors:
			if imagemosaic.hasTile(neighbor):
				neighborimage = imagemosaic.getTileImage(neighbor)
				neighborposition = imagemosaic.getTilePosition(neighbor)

				# phase correlate the tile image with the neighbors
				self.correlator.setImage(0, tileimage)
				self.correlator.setImage(1, neighborimage)
				pcimage = self.correlator.phaseCorrelate()
				self.peakfinder.setImage(pcimage)
				self.peakfinder.pixelPeak()
				peak = self.peakfinder.getResults()

				# determine which of the shifts is valid
				unwrappedshift = peak['pixel peak']
				wrappedshift = correlator.wrap_coord(peak['pixel peak'],
																										pcimage.shape)
				shift = self.compareShifts(unwrappedshift, wrappedshift,
																				tileimage, neighborimage)

				# use the shift and the neighbor position to get tile position
				tileposition = (neighborposition[0] + shift[0],
												neighborposition[1] + shift[1])
				peakvalue = peak['pixel peak value']

				# add a vote for this position
				positionvotes = self.votePosition(positionvotes,
													tileposition, peakvalue)

		return self.bestPosition(positionvotes)

	def uiShow(self):
		# show most recent for now
		if len(self.imagemosaics) == 0:
			return
		self.displayNumericArray(self.imagemosaics[-1].getMosaicImage())
		return ''

	def start_viewer_thread(self):
		if self.iv is not None:
			return
		self.viewerthread = threading.Thread(name=`self.id`,
																					target=self.open_viewer)
		self.viewerthread.setDaemon(1)
		self.viewerthread.start()

	def open_viewer(self):
		root = self.root = Toplevel()
		root._root().withdraw()
		root.wm_geometry('=450x400')

		self.iv = ImageViewer.ImageViewer(root, bg='#488')
		self.iv.pack()

		self.viewer_ready.set()
		root.mainloop()

		##clean up if window destroyed
		self.viewer_ready.clear()
		self.iv = None

	def close_viewer(self):
		try:
			self.root.destroy()
		except:
			### root may not exist or already destroyed
			pass

	def displayNumericArray(self, numarray):
		self.start_viewer_thread()
		self.viewer_ready.wait()
		if numarray is not None:
			self.iv.import_numeric(numarray)
			self.iv.update()

	def uiPublishMosaicImage(self):
		# publish most recent for now
		if len(self.imagemosaics) == 0:
			return ''
		odata = data.MosaicImageData(self.ID(),
							self.imagemosaics[-1].getMosaicImage(), scope=None, camera=None)
		self.publish(odata, event.MosaicImagePublishEvent)
		return ''

	def uiClearMosaics(self):
		self.imagemosaics = []
		return ''

	def defineUserInterface(self):
		watcherspec = watcher.Watcher.defineUserInterface(self)
		showspec = self.registerUIMethod(self.uiShow, 'Show Image', ())
		publishspec = self.registerUIMethod(self.uiPublishMosaicImage,
										'Publish Image', ())
		clearspec = self.registerUIMethod(self.uiClearMosaics, 'Clear', ())

		getimagespec = self.registerUIData('Mosaic Image', 'binary',
														permissions='r', callback=self.uiGetImageCallback)

		imagespec = self.registerUIContainer('Image',
																					(showspec, publishspec, clearspec))
		return self.registerUISpec('Image Mosaic',
																(watcherspec, imagespec, getimagespec))

	def uiGetImageCallback(self):
		# most recent for now
		if len(self.imagemosaics) == 0:
			return ''
		mrcstr = Mrc.numeric_to_mrcstr(self.imagemosaics[-1].getMosaicImage())
		return xmlbinlib.Binary(mrcstr)

class StateImageMosaic(ImageMosaic):
	def __init__(self, id, nodelocations, watchfor = event.TileImagePublishEvent, **kwargs):

		ImageMosaic.__init__(self, id, nodelocations, watchfor, **kwargs)

		self.calibrationclients = {}
		calibrationclasses = [calibrationclient.StageCalibrationClient,
													calibrationclient.ImageShiftCalibrationClient]
		for calibrationclass in calibrationclasses:
			instance = calibrationclass(self)
			self.calibrationclients[instance.parameter()] = instance

#		self.positionmethods['pixel size'] = self.positionByPixelSize
#		self.automaticpriority = ['pixel size', 'calibration', 'correlation']
#		self.positionmethod = 'pixel size'

		self.positionmethods['calibration'] = self.positionByCalibration
		self.automaticpriority = ['calibration', 'correlation']
#		self.positionmethod = self.positionmethods.keys()[0]
		self.positionmethod = 'calibration'

		self.start()

	def setProcessingMethod(self, positionmethod):
		if positionmethod in self.positionmethods.keys():
			self.positionmethod = positionmethod
		else:
			raise ValueError

	def processData(self, idata):
		tileimage = idata.content['image']
		neighbors = idata.content['neighbor tiles']
		tilescope = idata.content['scope']
		tilecamera = idata.content['camera']
		mosaics = []
		for imagemosaic in self.imagemosaics:
			for neighbor in neighbors:
				if imagemosaic.hasTile(neighbor):
					mosaics.append(imagemosaic)
					break
		if len(mosaics) == 0:
			imagemosaic = StateImageMosaicInfo()
			position = self.positionmethods[self.positionmethod](idata, None)
			imagemosaic.addTile(idata.id, tileimage, position, tilescope, tilecamera)
			self.imagemosaics.append(imagemosaic)
			print idata.id, "position =", imagemosaic.getTilePosition(idata.id)
		else:
			for imagemosaic in mosaics:
				position = self.positionmethods[self.positionmethod](idata, imagemosaic)
				imagemosaic.addTile(idata.id, tileimage, position,
																									tilescope, tilecamera)
				print idata.id, "position =", imagemosaic.getTilePosition(idata.id)

	def positionByCalibration(self, idata, imagemosaic,
																					parameter='stage position'):
		position = self.calibrationclients[parameter].itransform(
																		idata.content['scope'][parameter],
																		idata.content['scope'],
																		idata.content['camera'])
		# this makes it work with calibration
		position['row'] *= -1
		position['col'] *= -1
		return (position['row'], position['col'])

	def uiPublishMosaicImage(self):
		#ImageMosaic.uiPublishMosaicImage(self)

		if len(self.imagemosaics) == 0:
			return ''
		odata = data.MosaicImageData(self.ID(),
							self.imagemosaics[-1].getMosaicImage(), scope=None, camera=None)
		self.publish(odata, event.MosaicImagePublishEvent)

		statedata = {'image data ID': self.imagemosaics[-1].getTileStates()}
		self.publish(data.StateMosaicData(self.ID(), statedata),
																			event.StateMosaicPublishEvent)

		return ''

#	def defineUserInterface(self):
#		imagemosaicspec = ImageMosaic.defineUserInterface(self)
#		percentspec = self.registerUIData('Percent', 'float',
#																			permissions='rw', default=self.percent)
#		statespec = self.registerUIContainer('State', (percentspec,))
#		self.registerUISpec('State Image Mosaic', imagemosaicspec + statespec)

#	def setPixelSizeAndRotation(self, ievent):
#		idata = self.researchByDataID(ievent.content)
#		self.rotationmatrix = self.calculateRotationMatrix(
#																						idata.content['image angle'])
#		self.pixelsize = Numeric.array([idata.content['pixel size']['y'],
#																		idata.content['pixel size']['x']],
#																												Numeric.Float32)
		# testing
#		theta = 2.310 + 1.0 * math.pi / 2.0
#		pixelsize = (3.56127239707e-07, 3.56127239707e-07)
#		self.rotationmatrix = self.calculateRotationMatrix(theta)
#		self.pixelsize = Numeric.array([pixelsize[0], pixelsize[1]],
#																												Numeric.Float32)

#	def calculateRotationMatrix(self, xtheta, ytheta):
#		xsintheta = math.sin(theta)
#		xcostheta = math.cos(theta)      
#		ysintheta = math.sin(theta)
#		ycostheta = math.cos(theta)      
#		return Numeric.array([[xcostheta, -ysintheta],
#													[xsintheta, ycostheta]], Numeric.Float32)

#	def positionByPixelSize(self, idata, imagemosaic):
#		tilescopestate = idata.content['scope']
#		if self.rotationmatrix is None or self.pixelsize is None:
#			self.printerror('cannot process by pixel size, no calibration available')
#			raise ValueError
#		x = tilescopestate['stage position']['x']
#		y = tilescopestate['stage position']['y']
#		stateposition = Numeric.array([y, x], Numeric.Float32)
#		position = Numeric.matrixmultiply(self.rotationmatrix,
#																		stateposition / self.pixelsize)
#		return (int(round(position[0])), int(round(position[1])))

