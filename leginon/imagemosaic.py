import watcher
import data
import event
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

	def processData(self, idata):
		#print idata.content['neighbor tiles']
		if len(idata.content['neighbor tiles']) == 0:
			self.imagemosaic[idata.id] = {'image': idata.content['image'],
																'position': {'x': 0.0, 'y': 0.0}}
		else:
			newtileposition = {}
			#print idata.id
			self.correlator.setImage(0, idata.content['image'])
			for neighbor in idata.content['neighbor tiles']:
				# correlate
				self.correlator.setImage(1, self.imagemosaic[neighbor]['image'])
				pcimage = self.correlator.phaseCorrelate()
				# find peak
				self.peakfinder.setImage(pcimage)
				self.peakfinder.subpixelPeak()
				peak = self.peakfinder.getResults()
				#shift = peak['pixel peak']
				shift = correlator.wrap_coord(peak['pixel peak'], pcimage.shape)
				newtileposition[neighbor] = {
					'x': self.imagemosaic[neighbor]['position']['x'] + shift[1],
					'y': self.imagemosaic[neighbor]['position']['y'] + shift[0],
					'peak': peak['pixel peak value']
				}

			self.imagemosaic[idata.id] = {'position': {'x': 0, 'y': 0}, 'peak': 0.0}

			for neighbor in newtileposition:
				for c in ['x', 'y']:
					if newtileposition[neighbor][c] > 0:
						if abs(newtileposition[neighbor][c]
									- self.imagemosaic[idata.id]['position'][c]) > 1:
							if self.imagemosaic[idata.id]['peak'] \
									< newtileposition[neighbor]['peak']:
								self.imagemosaic[idata.id]['position'][c] \
									= newtileposition[neighbor][c]

			self.imagemosaic[idata.id]['image'] = idata.content['image']

	def uiShow(self):
		import Image
		import Numeric
		for dataid in self.imagemosaic:
			print 'self.imagemosaic[%s][\'position\'] = %s' \
				% (dataid, self.imagemosaic[dataid]['position'])
		im = Numeric.zeros((512, 512), Numeric.UnsignedInt8)
		for imagetile in self.imagemosaic:
			row = int(round(self.imagemosaic[imagetile]['position']['y']))
			column = int(round(self.imagemosaic[imagetile]['position']['x']))
			iti = self.imagemosaic[imagetile]['image']
			im[row:row + iti.shape[0], column:column + iti.shape[1]] = iti
		Image.fromstring('L', (im.shape[1], im.shape[0]), im.tostring()).show()
		return ''

	def defineUserInterface(self):
		watcherspec = watcher.Watcher.defineUserInterface(self)
		showspec = self.registerUIMethod(self.uiShow, 'Show', ())

		self.registerUISpec('Image Mosaic', (watcherspec, showspec))

