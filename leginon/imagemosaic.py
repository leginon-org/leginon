import watcher
import data
import event
import Numeric
import fftengine
import correlator
import peakfinder
reload(fftengine)
reload(correlator)
reload(peakfinder)

class ImageMosaic(watcher.Watcher):
	def __init__(self, id, nodelocations):
		# needs own event?
		watchfor = event.PublishEvent
		lockblocking = 1
		watcher.Watcher.__init__(self, id, nodelocations, watchfor, lockblocking)

		self.imagemosaic = {}

		self.correlator = correlator.Correlator(fftengine.fftNumeric())
		self.peakfinder = peakfinder.PeakFinder()

		self.start()

	def main(self):
		pass

	def getPeakValue(self, image1, image2):
		#print image1.shape
		#print image2.shape
		self.correlator.setImage(0, image1)
		self.correlator.setImage(1, image2)
		pcimage = self.correlator.phaseCorrelate()
		self.peakfinder.setImage(pcimage)
		self.peakfinder.pixelPeak()
		peak = self.peakfinder.getResults()
		#print peak
		return peak['pixel peak value']

	def testimages(self, t1, t2):
		import Image
		import time
		Image.fromstring('L', (t1.shape[1], t1.shape[0]), t1.tostring()).show()
		time.sleep(2.0)
		Image.fromstring('L', (t2.shape[1], t2.shape[0]), t2.tostring()).show()

	def processData(self, idata):
		print idata.id
		if len(idata.content['neighbor tiles']) == 0:
			if len(self.imagemosaic) == 0:
				self.imagemosaic[idata.id] = {'image': idata.content['image'],
																'position': (0, 0)}
		else:
			newposition = {}
			position = (0, 0)
			peakvalue = 0.0
			#self.correlator.setImage(0, idata.content['image'])
			for neighbor in idata.content['neighbor tiles']:
				if neighbor not in self.imagemosaic:
					break
				# correlate
				self.correlator.setImage(0, idata.content['image'])
				self.correlator.setImage(1, self.imagemosaic[neighbor]['image'])
				pcimage = self.correlator.phaseCorrelate()
				# find peak
				self.peakfinder.setImage(pcimage)
				self.peakfinder.pixelPeak()
				peak = self.peakfinder.getResults()
				shift = peak['pixel peak']
				wrapshift = correlator.wrap_coord(peak['pixel peak'], pcimage.shape)

				if shift[0] != wrapshift[0] and shift[1] != wrapshift[1]:
					baseimage = idata.content['image']
					nimage = self.imagemosaic[neighbor]['image']

					peakmatrix = Numeric.zeros((2,2), Numeric.Float32)

					# both shifts valid (works)
					peakmatrix[0, 0] = self.getPeakValue(
						nimage[shift[0]:,
											shift[1]:],
						baseimage[:nimage.shape[0]-shift[0],
										:nimage.shape[1]-shift[1]])

					# 0 shift valid, 1 wrap valid
					peakmatrix[0, 1] = self.getPeakValue(
						nimage[shift[0]:,
											:baseimage.shape[1]+wrapshift[1]],
						baseimage[:baseimage.shape[0]-shift[0],
										-wrapshift[1]:])

					# 0 wrap valid, 1 shift valid
					peakmatrix[1, 0] = self.getPeakValue(
						nimage[:baseimage.shape[0]+wrapshift[0],
											shift[1]:],
						baseimage[-wrapshift[0]:,
										:baseimage.shape[1]-shift[1]])

					# both wraps valid (works)
					peakmatrix[1, 1] = self.getPeakValue(
						nimage[:baseimage.shape[0]+wrapshift[0],
											:baseimage.shape[1]+wrapshift[1]],
						baseimage[-wrapshift[0]:,
										-wrapshift[1]:])

					maxvalue = 0.0
					maxpeak = (-1, -1)
					#print peakmatrix
					for i in range(len(peakmatrix)):
						for j in range(len(peakmatrix[i])):
							if peakmatrix[i, j] > maxvalue:
								maxvalue = peakmatrix[i, j]
								maxpeak = (i, j)

					if maxpeak[0] == 1:
						shift = (wrapshift[0], shift[1])

					if maxpeak[1] == 1:
						shift = (shift[0], wrapshift[1])

				elif shift[0] != wrapshift[0]:
					baseimage = idata.content['image']
					nimage = self.imagemosaic[neighbor]['image']

					shiftpeak = self.getPeakValue(nimage[shift[0]:, shift[1]:],
						baseimage[:nimage.shape[0]-shift[0],
								:nimage.shape[1]-shift[1]])

					wrapshiftpeak = self.getPeakValue(
						nimage[:nimage.shape[0]+wrapshift[0], wrapshift[1]:],
						baseimage[-wrapshift[0]:, :baseimage.shape[1]-wrapshift[1]])

					if shiftpeak < wrapshiftpeak:
						shift = wrapshift
				elif shift[1] != wrapshift[1]:
					baseimage = idata.content['image']
					nimage = self.imagemosaic[neighbor]['image']
					shiftpeak = self.getPeakValue(nimage[shift[0]:, shift[1]:],
						baseimage[:nimage.shape[0]-shift[0],
								:nimage.shape[1]-shift[1]])
					wrapshiftpeak = self.getPeakValue(
						nimage[wrapshift[0]:, :baseimage.shape[1]+wrapshift[1]],
						baseimage[:baseimage.shape[0]-wrapshift[0], -wrapshift[1]:])
					if shiftpeak < wrapshiftpeak:
						shift = wrapshift

				newposition[neighbor] = {}
				newposition[neighbor]['position'] = \
					(self.imagemosaic[neighbor]['position'][0] + shift[0],
						self.imagemosaic[neighbor]['position'][1] + shift[1])
				newposition[neighbor]['peak'] = peak['pixel peak value']

				print newposition[neighbor]['position']
				if newposition[neighbor]['position'][0] >= 0 \
						and newposition[neighbor]['position'][1] >= 0:
					if newposition[neighbor]['position'][0] != position[0] \
							or newposition[neighbor]['position'][1] != position[1]:
						if peakvalue < newposition[neighbor]['peak']:
							position  = newposition[neighbor]['position']
							peakvalue = newposition[neighbor]['peak'] 

			self.imagemosaic[idata.id] = {}
			self.imagemosaic[idata.id]['image'] = idata.content['image']
			self.imagemosaic[idata.id]['position'] = position
		print 'using', self.imagemosaic[idata.id]['position']
		#self.uiShow()

	def uiShow(self):
		import Image
		i = self.makeImage(self.imagemosaic)
		Image.fromstring('L', (i.shape[1], i.shape[0]), i.tostring()).show()
		return ''

	def makeImage(self, mosaic):
		imageshape = [0, 0]
		for imagetileid in mosaic:
			for i in range(len(imageshape)):
				size = mosaic[imagetileid]['position'][i] \
					+ mosaic[imagetileid]['image'].shape[i]
				if size > imageshape[i]:
					imageshape[i] = size
		image = Numeric.zeros(tuple(imageshape), Numeric.UnsignedInt8)
		for imagetileid in mosaic:
			row = mosaic[imagetileid]['position'][0]
			column = mosaic[imagetileid]['position'][1]
			iti = mosaic[imagetileid]['image']
			image[row:row+iti.shape[0], column:column+iti.shape[1]] = iti
		return image

	def defineUserInterface(self):
		watcherspec = watcher.Watcher.defineUserInterface(self)
		showspec = self.registerUIMethod(self.uiShow, 'Show', ())

		self.registerUISpec('Image Mosaic', (watcherspec, showspec))

