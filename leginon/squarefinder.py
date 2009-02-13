#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

from pyami import imagefun, convolver, mrc, arraystats
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
		self.uicontainer = uidata.Container(self.name)

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

class LowPassFilterPlugin(Plugin):
	name = 'Low Pass Filter'
	inputclass = Image
	outputclass = Image
	def __init__(self):
		Plugin.__init__(self)
		self.convolver = convolver.Convolver()

	def _process(self, input):
		sigma = self.sigma.get()
		kernel = convolver.gaussian_kernel(sigma)
		self.convolver.setKernel(kernel)
		return self.outputclass(self.convolver.convolve(image=input.image))

	def onSetSize(self, value):
		if not value % 2:
			value += 1
		return value

	def defineUserInterface(self):
		Plugin.defineUserInterface(self)
		self.sigma = uidata.Number('Sigma', 1.4, 'rw', persist=True, size=(6, 1))
		self.uicontainer.addObject(self.sigma, position={'position': (0, 0)})

class ThresholdPlugin(Plugin):
	name = 'Threshold'
	inputclass = Image
	outputclass = MaskedImage

	def _process(self, input):
		min = arraystats.min(input.image)
		max = arraystats.max(input.image)
		cutoff = (max - min) / self.cutoff.get()
		return self.outputclass(input.image,
														imagefun.threshold(input.image, cutoff))

	def defineUserInterface(self):
		Plugin.defineUserInterface(self)
		self.cutoff = uidata.Float('Cutoff', 10.0, 'rw', persist=True, size=(4, 1))
		self.uicontainer.addObject(self.cutoff)

class BlobFinderPlugin(Plugin):
	name = 'Blob Finder'
	inputclass = MaskedImage
	outputclass = ImageTargets

	def _process(self, input):
		border = self.border.get()
		maxblobs = self.maxblobs.get()
		minblobsize = self.minblobsize.get()
		maxblobsize = self.maxblobsize.get()
		scale = self.scale.getSelectedValue()
		threshold = self.threshold.get()
		thresholdpoint = self.thresholdpoint.get()
		if scale is None:
			scale = 1
		else:
			scale = int(scale.split('/')[-1])
		try:
			blobs = imagefun.find_blobs(input.image[::scale, ::scale],
																	input.mask[::scale, ::scale],
																	border/scale, maxblobs,
																	maxblobsize/scale, minblobsize/scale)
		except ValueError:
			blobs = []

		thresholdedblobs = []
		for blob in blobs:
			blobvalues = list(blob.value_list)
			blobvalues.sort()
			thresholdvalue = blobvalues[int(len(blobvalues) * thresholdpoint)]
			if thresholdvalue < threshold:
				thresholdedblobs.append(blob)

		blobs = thresholdedblobs

		targets = map(lambda b: (scale*b.stats['center'][1],
															scale*b.stats['center'][0]),
									blobs)
		return self.outputclass(input.image, targets)

	def defineUserInterface(self):
		Plugin.defineUserInterface(self)
		self.border = uidata.Number('Border', 0, 'rw', persist=True, size=(4, 1))
		self.maxblobs = uidata.Number('Maximum number of blobs', 100, 'rw',
																	persist=True, size=(4, 1))
		self.minblobsize = uidata.Number('Minimum', 0, 'rw', persist=True,
																			size=(6, 1))
		self.maxblobsize = uidata.Number('Maximum', 1000, 'rw', persist=True,
																			size=(6, 1))
		self.blobsizecontainer = uidata.Container('Blob Size')
		self.blobsizecontainer.addObject(self.minblobsize,
																			position={'position': (0, 0)})
		self.blobsizecontainer.addObject(self.maxblobsize,
																			position={'position': (0, 1)})

		scales = ['1', '1/2', '1/4', '1/8', '1/16']
		self.scale = uidata.SingleSelectFromList('Scale', scales, 0, persist=True)

		self.threshold = uidata.Number('Blob', 25000, 'rw', persist=True,
																		size=(5,1))
		self.thresholdpoint = uidata.Number('Point', 0.5, 'rw', persist=True,
																				size=(5,1))
		thresholdcontainer = uidata.Container('Threshold')
		thresholdcontainer.addObject(self.threshold)
		thresholdcontainer.addObject(self.thresholdpoint)

		self.uicontainer.addObjects((self.blobsizecontainer, self.border,
																	self.maxblobs, self.scale,
																	thresholdcontainer))

class SquareBlobFinderPlugin(BlobFinderPlugin):
	name = 'Square Blob Finder'

	def _process(self, input):
		squaredimension = self.squaredimension.get()
		minblobsizetolerance = self.minblobsizetolerance.get()/100.0
		maxblobsizetolerance = self.maxblobsizetolerance.get()/100.0
		shape = input.image.shape
		self.maxblobs.set(shape[0]*shape[1]/squaredimension**2)
		self.minblobsize.set((squaredimension * (minblobsizetolerance))**2)
		self.maxblobsize.set((squaredimension * (maxblobsizetolerance))**2)
		#self.centersize.set(squaredimension/4)
		self.border.set(squaredimension/10)
		return BlobFinderPlugin._process(self, input)

	def defineUserInterface(self):
		BlobFinderPlugin.defineUserInterface(self)
		self.squaredimension = uidata.Number('Dimension of square', 200, 'rw',
																					persist=True, size=(4, 1))
		self.minblobsizetolerance = uidata.Number('Minimum', 60, 'rw',
																							persist=True, size=(3, 1))
		self.maxblobsizetolerance = uidata.Number('Maximum', 125, 'rw',
																							persist=True, size=(3, 1))
		tolerancecontainer = uidata.Container('Tolerance (Percent)')
		tolerancecontainer.addObject(self.minblobsizetolerance,
																	position={'position': (0, 0)})
		tolerancecontainer.addObject(self.maxblobsizetolerance,
																	position={'position': (0, 1)})

		self.uicontainer.deleteObject(self.blobsizecontainer)
		blobsizecontainer = uidata.Container('Square Blob Size')
		blobsizecontainer.addObject(self.squaredimension)
		blobsizecontainer.addObject(tolerancecontainer, position={'expand': 'all'})
		blobsizecontainer.addObject(self.blobsizecontainer,
																position={'expand': 'all'})
		self.uicontainer.addObject(blobsizecontainer)

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
		Plugin.defineUserInterface(self)
		self.border = uidata.Number('Border', 0, 'rw', persist=True, size=(4, 1))
		self.uicontainer.addObject(self.border)

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
	def __init__(self, id, session, managerlocation, **kwargs):
		targetfinder.TargetFinder.__init__(self, id, session, managerlocation,
																				**kwargs)
		self.image = None

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
			self.pluginpipeline.process(Image(mrc.read(filename)))
		except IOError:
			self.logger.error('Load file "%s" failed' % filename)

	def findTargets(self, imagedata):
		output = self.pluginpipeline.process(Image(imagedata['image']))
		targets = map(lambda t: self.newTargetData(imagedata, 'acquisition',
																								t[0], t[1]), output.targets)
		self.targetlist += targets

	def defineUserInterface(self):
		targetfinder.TargetFinder.defineUserInterface(self)

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
		container.addObject(pipelinecontainer, position={'position': (1, 0),
																									'justify': ['center']})
		container.addObject(filecontainer, position={'position': (2, 0),
																									'justify': ['center']})
		container.addObject(self.ui_image, position={'position': (1, 1),
																									'span': (2, 1)})
		self.uicontainer.addObject(container)

