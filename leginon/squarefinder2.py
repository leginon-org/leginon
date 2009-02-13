#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

try:
	import numarray as Numeric
	import fft as FFT
	import numarray.linear_algebra.mlab as MLab
except:
	import Numeric
	import FFT
	import MLab
from pyami import convolver, arraystats, mrc
import numextension
import random
import targetfinder
import threading
import uidata

def sobel(image):
	c = convolver.Convolver()
	c.setImage(image)
	r = c.convolve(kernel=convolver.sobel_row_kernel)
	c = c.convolve(kernel=convolver.sobel_col_kernel)
	return Numeric.hypot(r, c), Numeric.arctan2(r, c)

def canny(image, sigma=1.8, nonmaximawindow=7, hysteresis=True):
	gaussiankernel = convolver.gaussian_kernel(sigma)
	c = convolver.Convolver()
	c.setImage(image)
	gaussianimage = c.convolve(kernel=gaussiankernel)
	edgeimage, gradientimage = sobel(gaussianimage)

	numextension.nonmaximasuppress(edgeimage, gradientimage, nonmaximawindow)

	if hysteresis:
		mean = arraystats.mean(edgeimage)
		stdev = arraystats.std(edgeimage)
		lowthreshold = mean + stdev
		highthreshold = 2*lowthreshold
		edgeimage = numextension.hysteresisthreshold(edgeimage,
																			lowthreshold, highthreshold) * edgeimage

	return edgeimage, gradientimage

def findpeak(b):
	return -b[0]/b[1] + b[2]/b[1]

def findPeakAngle(houghimage):
	sumimage = Numeric.sum(houghimage[houghimage.shape[0]/8:,:,:], 2)
	angleindex = Numeric.argmax(Numeric.sum(sumimage))
	#angle = math.radians(angleindex*(90.0/houghimage.shape[1]))
	angle = (angleindex*Numeric.pi)/(houghimage.shape[1]*2.0)
	return angleindex, angle

def findFFTPeak(array):
	n = 2**16
	fft = FFT.real_fft(array, n=n)
	autocorrelation = Numeric.absolute(fft)**2
	# weak
	for i in xrange(autocorrelation.shape[0]):
		if autocorrelation[i] < autocorrelation[0]/10.0:
			break
	for j in xrange(i, autocorrelation.shape[0]):
		if autocorrelation[j] > autocorrelation[0]/10.0:
			break
	for k in xrange(j, autocorrelation.shape[0]):
		if autocorrelation[k] < autocorrelation[0]/10.0:
			break
	frequency = Numeric.argmax(autocorrelation[j:k]) + j

	period = 2.0*autocorrelation.shape[0]/frequency
	phaseangle = Numeric.arctan2(fft[frequency].imag, fft[frequency].real)
	phase = (-phaseangle/(2.0*Numeric.pi) % 1.0)*period

	return period, phase

def translate(position, angles, offsets, periods):
	points = Numeric.zeros((2, 2), Numeric.Float)
	for i, value in enumerate(offsets + periods*position):
		points[i] =  value*Numeric.array([Numeric.sin(angles[i]),
																			Numeric.cos(angles[i])])

	slopes = Numeric.tan(angles + Numeric.pi/2)

	intercepts = points[:, 0] - slopes*points[:, 1]

	column = (intercepts[1] - intercepts[0])/(slopes[0] - slopes[1])
	row = slopes[0]*column + intercepts[0]
	return row, column

class Plugin(object):
	name = 'Unamed'
	def __init__(self, outputplugin=None):
		self.outputplugin = outputplugin
		self.userinterfaceitems = self.defineUserInterface()

	def setOutputPlugin(self, outputplugin):
		self.outputplugin = outputplugin

	def _process(self):
		raise NotImplementedError

	def process(self, input):
		return self._process(input)

	def defineUserInterface(self):
		self.uicontainer = uidata.Container(self.name)

class Image(object):
	def __init__(self, image):
		self.image = image

class GradientImage(Image):
	def __init__(self, image, edge, gradient):
		Image.__init__(self, image)
		self.edge = edge
		self.gradient = gradient

class HoughImage(Image):
	def __init__(self, image, houghimage, houghimage90):
		Image.__init__(self, image)
		self.houghimage = houghimage
		self.houghimage90 = houghimage90

class HoughImageData(Image):
	def __init__(self, image, angles, phases, periods):
		Image.__init__(self, image)
		self.angles = angles
		self.phases = phases
		self.periods = periods

class HoughSquareData(object):
	def __init__(self, coordinates, center, values):
		self.coordinates = coordinates
		self.center = center
		self.values = values

class HoughSquaresData(Image):
	def __init__(self, image, squares):
		Image.__init__(self, image)
		self.squares = squares

class Targets(object):
	def __init__(self, targets):
		self.targets = targets

class OffsetCenterTargets(Targets):
	pass

class ImageTargets(Image, Targets):
	def __init__(self, image, targets):
		Image.__init__(self, image)
		Targets.__init__(self, targets)

class PluginPipeline(object):
	def __init__(self, inputclass, outputclass, pluginclasses=[],
											imageviewer=None, targetviewer=None):
		self.inputclass = inputclass
		self.outputclass = outputclass
		self.imageviewer = imageviewer
		self.targetviewer = targetviewer
		self.verifyevent = threading.Event()
		self.processevent = threading.Event()
		self.plugins = []
		for pluginclass in pluginclasses:
			plugin = pluginclass()
			self.plugins.append(plugin)
		self.userinterfaceitems = self.defineUserInterface()

	def _process(self, input):
		return input

	def process(self, input):
		if not isinstance(input, self.inputclass):
			raise TypeError('wrong input class for pipeline process')
		output = self._process(input)
		for plugin in self.plugins:
			output = plugin.process(output)
			if self.display.get():
				if isinstance(output, Image):
					#if isinstance(output, MaskedImage):
					#	self.imageviewer.setImage(output.mask)
					#else:
					#	self.imageviewer.setImage(output.image)
					self.imageviewer.setImage(output.image)
				if isinstance(output, Targets):
					if not isinstance(output, OffsetCenterTargets):
						self.targetviewer.setTargetType('acquisition', output.targets)
			if self.verify[plugin].get():
				try:
					self.containers[plugin].addObject(uidata.Message('Verify', 'info',
																							'Waiting for user verification'))
				except ValueError:
					pass
				self.verifyevent.clear()
				self.verifyevent.wait()
				if self.processevent.isSet():
					self.processevent.clear()
					self.verifyevent.clear()
					return self.process(input)
				try:
					self.containers[plugin].deleteObject('Verify')
				except ValueError:
					pass
		if not isinstance(output, self.outputclass):
			output = None
		return output

	def setImageViewer(self, imageviewer):
		self.imageviewer = imageviewer

	def setTargetViewer(self, targetviewer):
		self.targetviewer = targetviewer

	def onReprocess(self):
		self.processevent.set()
		self.verifyevent.set()

	def onProceed(self):
		self.verifyevent.set()

	def defineUserInterface(self):
		userinterfaceitems = []

		self.display = uidata.Boolean('Display image', True, 'rw', persist=True)
		userinterfaceitems.append(self.display)

		self.verify = {}
		self.containers = {}
		for plugin in self.plugins:
			self.containers[plugin] = plugin.uicontainer
			self.verify[plugin] = uidata.Boolean('Wait for verification', False, 'rw',
																						persist=True)
			self.containers[plugin].addObject(self.verify[plugin])
			userinterfaceitems.append(self.containers[plugin])

		self.reprocessmethod = uidata.Method('Reprocess', self.onReprocess)
		userinterfaceitems.append(self.reprocessmethod)
		self.proceedmethod = uidata.Method('Proceed', self.onProceed)
		userinterfaceitems.append(self.proceedmethod)

		return userinterfaceitems

class CannyEdgeDetectorPlugin(Plugin):
	name = 'Canny Edge Detector'
	inputclass = Image
	outputclass = GradientImage
	def __init__(self):
		Plugin.__init__(self)
		self.convolver = convolver.Convolver()

	def _process(self, input):
		edgeimage, gradientimage = canny(input.image, hysteresis=False)
		return self.outputclass(input.image, edgeimage, gradientimage)

class HoughLineTransformPlugin(Plugin):
	name = 'Hough Line Transform'
	inputclass = GradientImage
	outputclass = HoughImage

	def _process(self, input):
		gradientangletolerance = 0.05
		houghimage = numextension.houghline(input.edge, input.gradient,
																				gradientangletolerance)
		houghimage90 = numextension.houghline(MLab.rot90(input.image),
																					MLab.rot90(input.gradient),
																					gradientangletolerance)
		return self.outputclass(input.image, houghimage, houghimage90)

class HoughDataPlugin(Plugin):
	name = 'Hough Data'
	inputclass = HoughImage
	outputclass = HoughImageData

	def _process(self, input):
		output = self.outputclass(input.image, [], [[], []], [[], []])
		for i, image in enumerate([input.houghimage, input.houghimage90]):
			angleindex, angle = findPeakAngle(image)
			output.angles.append(angle)

			for j in range(image.shape[2]):
				peaks = []
				rhos = image[:, angleindex, j]
				period, phase = findFFTPeak(rhos)
				output.phases[i].append(phase)
				output.periods[i].append(period)
		return output

class HoughSquareFinderPlugin(Plugin):
	name = 'Hough Square Finder'
	inputclass = HoughImageData
	outputclass = HoughSquaresData

	def _process(self, input):
		for i, phases in enumerate(input.phases):
			if phases[0] > phases[1]:
				input.phases[i][1] += input.periods[i][1]
	
		for i, phase in enumerate(input.phases[1]):
			input.phases[1][i] = \
									(input.image.shape[1]*Numeric.sin(input.angles[1]) - phase) \
																									% input.periods[1][i]
		input.phases[1].reverse()
		input.angles[1] -= Numeric.pi/2.0
	
		angles = Numeric.array([input.angles[0], input.angles[1]])
		offsets = Numeric.array([[input.phases[0][0],
																input.phases[1][0]],
															[input.phases[0][1],
																input.phases[1][1]]])
		periods = Numeric.array([[input.periods[0][0],
																input.periods[1][0]],
															[input.periods[0][1],
																input.periods[1][1]]])
		indices = [(0, 0), (1, 0), (1, 1), (0, 1)]
		o = map(lambda (i, j): Numeric.array([offsets[i, 0], offsets[j, 1]]),
																																	indices)
		p = map(lambda (i, j): Numeric.array([periods[i, 0], periods[j, 1]]),
																																	indices)
	
		ih = Numeric.hypot(input.image.shape[0], input.image.shape[1])
		ms = int(ih/min(periods[:, 0])) + 1
		ns = int(ih/min(periods[:, 1])) + 1

		output = self.outputclass(input.image, [])
		for m in range(-ms, ms + 1):
			for n in range(-ns, ns + 1):
				square = []
				for i, j in [(0, 0), (1, 0), (1, 1), (0, 1)]:
					square.append(translate(Numeric.array([m, n]), angles,
												Numeric.array([offsets[i, 0], offsets[j, 1]]),
												Numeric.array([periods[i, 0], periods[j, 1]])))
	
				add = True
				for row, column in square:
					if (row < 0 or round(row) >= input.image.shape[0]
							or column < 0 or round(column) >= input.image.shape[1]):
						add = False
				if add:
					center = ((square[2][0] - square[0][0])/2.0 + square[0][0],
										(square[2][1] - square[0][1])/2.0 + square[0][1])
	
					rowrange = (int(round(square[3][0])), int(round(square[1][0])))
					lowscalars = [Numeric.tan(Numeric.arctan2(square[3][1] - square[0][1],
																									square[0][0] - square[3][0])),
												Numeric.tan(Numeric.arctan2(square[1][1] - square[0][1],
																									square[1][0] - square[0][0]))]
					highscalars = [Numeric.tan(Numeric.arctan2(
																									square[2][1] - square[3][1],
																									square[2][0] - square[3][0])),
													Numeric.tan(Numeric.arctan2(
																									square[1][1] - square[2][1],
																									square[2][0] - square[1][0]))]
					values = []
					for r in range(*rowrange):
						if r < square[0][0]:
							low = lowscalars[0]*(square[0][0] - r) + square[0][1]
						else:
							low = lowscalars[1]*(r - square[0][0]) + square[0][1]
						if r < square[2][0]:
							high = square[2][1] - highscalars[0]*(square[2][0] - r)
						else:
							high = square[2][1] - highscalars[1]*(r - square[2][0])
						
						for c in range(int(round(low)), int(round(high))):
							values.append(input.image[r, c])
	
					output.squares.append(HoughSquareData(square, center, values))
		return output
	
class SquareTargetPlugin(Plugin):
	name = 'Square Target'
	inputclass = HoughSquaresData
	outputclass = ImageTargets

	def _process(self, input):
		rows, columns = input.image.shape
		targets = []
		for square in input.squares:
			y, x = map(int, map(round, square.center))
			targets.append((x, y))
		return self.outputclass(input.image, targets)

class RandomTargetPlugin(Plugin):
	name = 'Random Target Selection'
	inputclass = ImageTargets
	outputclass = ImageTargets

	def _process(self, input):
		ntargets = self.ntargets.get()
		try:
			targets = random.sample(input.targets, ntargets)
		except ValueError:
			targets = input.targets
		return self.outputclass(input.image, targets)

	def defineUserInterface(self):
		Plugin.defineUserInterface(self)
		self.ntargets = uidata.Number('Number of targets', 1, 'rw', persist=True,
																	size=(4, 1))
		self.uicontainer.addObject(self.ntargets)

class SquareFinder2(targetfinder.TargetFinder):
	def __init__(self, id, session, managerlocation, **kwargs):
		targetfinder.TargetFinder.__init__(self, id, session, managerlocation,
																				**kwargs)
		self.image = None

		pluginclasses = [CannyEdgeDetectorPlugin,
											HoughLineTransformPlugin,
											HoughDataPlugin,
											HoughSquareFinderPlugin,
											SquareTargetPlugin,
											RandomTargetPlugin]
		self.pluginpipeline = PluginPipeline(Image, Targets, pluginclasses)

		self.defineUserInterface()

		self.pluginpipeline.setImageViewer(self.ui_image)
		self.pluginpipeline.setTargetViewer(self.ui_image)

		self.start()

	def load(self, filename=None):
		if filename is None:
			filename = self.filename.get()
		try:
			self.pluginpipeline.process(Image(mrc.read(filename)))
		except IOError:
			self.messagelog.error('Load file "%s" failed' % filename)

	def findTargets(self, imagedata):
		output = self.pluginpipeline.process(Image(imagedata['image']))
		print 'output =', output
		targets = map(lambda t: self.newTargetData(imagedata, 'acquisition',
																								t[0], t[1]), output.targets)
		self.targetlist += targets

	def defineUserInterface(self):
		targetfinder.TargetFinder.defineUserInterface(self)

		self.messagelog = uidata.MessageLog('Message Log')
		self.ui_image = uidata.TargetImage('Image', None, 'r')
		self.ui_image.addTargetType('acquisition')

		self.filename = uidata.String('Test filename', None, 'rw',
																				persist=True)
		self.loadmethod = uidata.Method('Load', self.load)
		filecontainer = uidata.Container('File')
		filecontainer.addObjects((self.filename, self.loadmethod))

		pipelinecontainer = uidata.Container('Pipeline')
		for uiobject in self.pluginpipeline.userinterfaceitems:
			if isinstance(uiobject, uidata.Method):
				pipelinecontainer.addObject(uiobject)
			else:
				pipelinecontainer.addObject(uiobject, position={'expand': 'all'})

		container = uidata.LargeContainer('Square Finder')
		container.addObject(self.messagelog, position={'position': (0, 0),
																										'span': (1, 2),
																										'expand': 'all',
																										'justify': ['center']})
		container.addObject(pipelinecontainer, position={'position': (1, 0),
																									'justify': ['center']})
		container.addObject(filecontainer, position={'position': (2, 0),
																									'justify': ['center']})
		container.addObject(self.ui_image, position={'position': (1, 1),
																									'span': (2, 1)})
		self.uicontainer.addObject(container)

