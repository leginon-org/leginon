#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import convolver
import data
import imagefun
import Mrc
import Numeric
import random
import targetfinder
import threading
import uidata

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
		return []

class Image(object):
	def __init__(self, image):
		self.image = image

class MaskedImage(Image):
	def __init__(self, image, mask):
		Image.__init__(self, image)
		self.mask = mask

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
		self.plugins = []
		for pluginclass in pluginclasses:
			plugin = pluginclass()
			self.plugins.append(plugin)
		self.userinterfaceitems = self.defineUserInterface()

	def _process(self, input):
		return input

	def process(self, input):
		if not isinstance(input, self.inputclass):
			raise TypeError('Wrong input class for pipeline process')
		output = self._process(input)
		for plugin in self.plugins:
			output = plugin.process(output)
			if isinstance(output, Image):
				if isinstance(output, MaskedImage):
					self.imageviewer.setImage(output.mask)
				else:
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

	def onProcess(self):
		print 'process'

	def onProceed(self):
		self.verifyevent.set()

	def defineUserInterface(self):
		userinterfaceitems = []

		self.verify = {}
		self.containers = {}
		for plugin in self.plugins:
			self.containers[plugin] = uidata.Container(plugin.name)
			self.verify[plugin] = uidata.Boolean('Wait for verification', False, 'rw',
																						persist=True)
			objects = []
			objects.append(self.verify[plugin])
			objects += plugin.userinterfaceitems
			self.containers[plugin].addObjects(objects)
			userinterfaceitems.append(self.containers[plugin])

		self.processmethod = uidata.Method('Process', self.onProcess)
		userinterfaceitems.append(self.processmethod)
		self.proceedmethod = uidata.Method('Proceed', self.onProceed)
		userinterfaceitems.append(self.proceedmethod)

		return userinterfaceitems

class LowPassFilterPlugin(Plugin):
	name = 'Low Pass Filter'
	inputclass = Image
	outputclass = Image
	def __init__(self):
		Plugin.__init__(self)
		self.convolver = convolver.Convolver()

	def _process(self, input):
		size = self.size.get()
		sigma = self.sigma.get()
		kernel = convolver.gaussian_kernel(size, sigma)
		self.convolver.setKernel(kernel)
		return self.outputclass(self.convolver.convolve(image=input.image))

	def onSetSize(self, value):
		if not value % 2:
			value += 1
		return value

	def defineUserInterface(self):
		self.size = uidata.Number('Size', 5, 'rw', callback=self.onSetSize,
															persist=True)
		self.sigma = uidata.Number('Sigma', 1.4, 'rw', persist=True)
		return [self.size, self.sigma]

class ThresholdPlugin(Plugin):
	name = 'Threshold'
	inputclass = Image
	outputclass = MaskedImage

	def _process(self, input):
		min = imagefun.min(input.image)
		max = imagefun.max(input.image)
		cutoff = (max - min) / 10.0
		return self.outputclass(input.image,
														imagefun.threshold(input.image, cutoff))

class BlobFinderPlugin(Plugin):
	name = 'Blob Finder'
	inputclass = MaskedImage
	outputclass = ImageTargets

	def _process(self, input):
		border = self.border.get()
		maxblobs = self.maxblobs.get()
		minblobsize = self.minblobsize.get()
		maxblobsize = self.maxblobsize.get()
		scale = int(1.0/self.scale.get())
		try:
			blobs = imagefun.find_blobs(input.image[::scale, ::scale],
																	input.mask[::scale, ::scale],
																	border/scale, maxblobs,
																	maxblobsize/scale, minblobsize/scale)
		except (ValueError, imagefun.TooManyBlobs):
			blobs = []
		targets = map(lambda b: (scale*b.stats['center'][1],
															scale*b.stats['center'][0]),
									blobs)
		return self.outputclass(input.image, targets)

	def defineUserInterface(self):
		self.border = uidata.Number('Border', 0, 'rw', persist=True)
		self.maxblobs = uidata.Number('Maximum Blobs', 100, 'rw', persist=True)
		self.minblobsize = uidata.Number('Minimum Blob Size', 0, 'rw', persist=True)
		self.maxblobsize = uidata.Number('Maximum Blob Size', 1000, 'rw',
																			persist=True)
		self.scale = uidata.Number('Scale', 1.0, 'rw', persist=True)
		return [self.border, self.maxblobs,
						self.minblobsize, self.maxblobsize,
						self.scale]

class SquareBlobFinderPlugin(BlobFinderPlugin):
	name = 'Square Blob Finder'

	def _process(self, input):
		squaredimension = self.squaredimension.get()
		minblobsizetolerance = self.minblobsizetolerance.get()
		maxblobsizetolerance = self.maxblobsizetolerance.get()
		shape = input.image.shape
		self.maxblobs.set(shape[0]*shape[1]/squaredimension**2)
		self.minblobsize.set((squaredimension * (minblobsizetolerance))**2)
		self.maxblobsize.set((squaredimension * (maxblobsizetolerance))**2)
		self.border.set(squaredimension/10)
		return BlobFinderPlugin._process(self, input)

	def defineUserInterface(self):
		self.squaredimension = uidata.Number('Square Dimension', 200, 'rw',
																					persist=True)
		self.minblobsizetolerance = uidata.Number('Minimum Blob Size Tolerance',
																							0.6, 'rw', persist=True)
		self.maxblobsizetolerance = uidata.Number('Maximum Blob Size Tolerance',
																							1.25, 'rw', persist=True)
		userinterfaceitems = []
		userinterfaceitems.append(self.squaredimension)
		userinterfaceitems.append(self.minblobsizetolerance)
		userinterfaceitems.append(self.maxblobsizetolerance)
		userinterfaceitems += BlobFinderPlugin.defineUserInterface(self)
		return userinterfaceitems

class TargetBorderPlugin(Plugin):
	name = 'Target Border'
	inputclass = ImageTargets
	outputclass = ImageTargets

	def _process(self, input):
		targets = []
		border = self.border.get()
		shape = input.image.shape
		for target in input.targets:
			if target[0] < border:
				continue
			if target[1] < border:
				continue
			if target[0] > shape[0] - border:
				continue
			if target[1] > shape[1] - border:
				continue
			targets.append(target)
		return self.outputclass(input.image, targets)

	def defineUserInterface(self):
		self.border = uidata.Number('Border', 0, 'rw', persist=True)
		return [self.border]

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
		self.ntargets = uidata.Number('Number of targets', 1, 'rw', persist=True)
		return [self.ntargets]

class CenterOffsetTargetsPlugin(Plugin):
	name = 'Center Offset Targets'
	inputclass = ImageTargets
	outputclass = OffsetCenterTargets

	def _process(self, input):
		rows, columns = input.image.shape
		targets = []
		for target in input.targets:
			column, row = target
			deltarow = row - rows/2
			deltacolumn = column - columns/2
			targets.append((deltarow, deltacolumn))
		return self.outputclass(targets)

class SquareFinder(targetfinder.TargetFinder):
	def __init__(self, id, session, nodelocations, **kwargs):
		targetfinder.TargetFinder.__init__(self, id, session, nodelocations,
																				**kwargs)
		self.image = None
		self.verifyevent = threading.Event()

		pluginclasses = [LowPassFilterPlugin, ThresholdPlugin,
											SquareBlobFinderPlugin, TargetBorderPlugin,
											RandomTargetPlugin, CenterOffsetTargetsPlugin]
		self.pluginpipeline = PluginPipeline(Image, Targets, pluginclasses)

		self.defineUserInterface()

		self.pluginpipeline.setImageViewer(self.ui_image)
		self.pluginpipeline.setTargetViewer(self.ui_image)

		self.start()

	def load(self, filename=None):
		if filename is None:
			filename = self.filename.get()
		try:
			self.pluginpipeline.process(Image(Mrc.mrc_to_numeric(filename)))
		except IOError:
			self.messagelog.error('Load file "%s" failed' % filename)

	def findTargets(self, imagedata):
		output = self.pluginpipeline.process(Image(imagedata['image']))
		targets = map(lambda t: self.newTargetData(imagedata, 'acquisition',
																								t[0], t[1]), output.targets)
		self.targetlist += targets

	def defineUserInterface(self):
		targetfinder.TargetFinder.defineUserInterface(self)
		self.uidataqueueflag.set(False)

		self.messagelog = uidata.MessageLog('Message Log')
		self.ui_image = uidata.TargetImage('Image', None, 'r')
		self.ui_image.addTargetType('acquisition')

		self.filename = uidata.String('Test filename', None, 'rw',
																				persist=True)
		self.loadmethod = uidata.Method('Load', self.load)
		filecontainer = uidata.Container('File')
		filecontainer.addObjects((self.filename, self.loadmethod))

		pipelinecontainer = uidata.Container('Pipeline')
		pipelinecontainer.addObjects(self.pluginpipeline.userinterfaceitems)

		container = uidata.LargeContainer('Square Finder')
		container.addObjects((self.messagelog, filecontainer,
													pipelinecontainer, self.ui_image))
		self.uiserver.addObjects((container,))

