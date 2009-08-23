#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#
import threading
import node, event, leginondata
import presets
import calibrationclient
import math
import instrument
import targethandler
import gui.wx.MosaicTargetMaker
import gui.wx.Node
import gridlabeler

class AtlasError(Exception):
	pass

class AtlasSizeError(AtlasError):
	pass

def magnitude(coordinate, coordinates):
	return map(lambda c: math.sqrt(sum(map(lambda m, n: (n - m)**2,
																					coordinate, c))), coordinates)

def closestTarget(start, targets):
	values = magnitude(start, targets)
	return values.index(min(values))

def sortTargets(targets, start=None):
	if start is not None:
		targets.insert(0, start)
	for i in range(1, len(targets) - 1):
		index = closestTarget(targets[i], targets[i+1:])
		targets.insert(i, targets.pop(index))
	if start is not None:
		del targets[0]
	return targets

class TargetMaker(node.Node, targethandler.TargetHandler):
	eventinputs = node.Node.eventinputs + targethandler.TargetHandler.eventinputs
	eventoutputs = node.Node.eventoutputs + targethandler.TargetHandler.eventoutputs
	def __init__(self, id, session, managerlocation, **kwargs):
		self.targetlist = []
		node.Node.__init__(self, id, session, managerlocation, **kwargs)
		self.instrument = instrument.Proxy(self.objectservice, self.session)

class MosaicTargetMaker(TargetMaker):
	panelclass = gui.wx.MosaicTargetMaker.Panel
	settingsclass = leginondata.MosaicTargetMakerSettingsData
	defaultsettings = {
		'preset': None,
		'label': '',
		'radius': 0.0005,
		'overlap': 1.0,
		'max targets': 128,
		'max size': 16384,
		'mosaic center': 'stage center',
	}
	eventinputs = TargetMaker.eventinputs + [event.MakeTargetListEvent]
	def __init__(self, id, session, managerlocation, **kwargs):
		TargetMaker.__init__(self, id, session, managerlocation, **kwargs)
		self.pixelsizecalclient = calibrationclient.PixelSizeCalibrationClient(self)
		self.addEventInput(event.MakeTargetListEvent, self._makeAtlas)
		self.presetsclient = presets.PresetsClient(self)

		self.publishargs = None
		self.start()

	def calculateAtlas(self):
		self.publishargs = None
		try:
			self.publishargs = self._calculateAtlas()
			if self.publishargs:
				self.logger.info('Press \'Publish Atlas\' to continue')
		except AtlasError, e:
			self.logger.exception('Atlas creation failed: %s' % e)
		except Exception, e:
			self.logger.exception('Atlas creation failed: %s' % e)
		self.panel.atlasCalculated()

	def publishAtlas(self):
		try:
			if not self.publishargs:
				raise AtlasError('no targets calculated')
			self._publishAtlas(*self.publishargs)
		except AtlasError, e:
			self.logger.exception('Atlas creation failed: %s' % e)
		except Exception, e:
			self.logger.exception('Atlas creation failed: %s' % e)
		self.panel.atlasPublished()

	def checkLabel(self, label):
		targetlist = self.newTargetList(mosaic=True, label=label)
		targets = self.researchTargets(session=self.session, list=targetlist)
		if targets:
			raise AtlasError('label "%s" is already used, choose another' % (label,))

	def validateSettings(self, evt=None):
		if evt is None:
			label = self.settings['label']
			self.checkLabel(label)
		radius = self.settings['radius']
		if radius <= 0.0:
			raise AtlasError('invalid radius specified')
		overlap = self.settings['overlap']/100.0
		if overlap >= 100.0:
			raise AtlasError('invalid overlap specified')
		return radius, overlap

	def getState(self):
		# tem/camera from preset?
		self.logger.debug('Getting current instrument state...')
		presetname = self.settings['preset']
		preset = self.presetsclient.getPresetByName(presetname)
		temname = preset['tem']['name']
		self.instrument.setTEM(temname)
		camname = preset['ccdcamera']['name']
		self.instrument.setCCDCamera(camname)
		try:
			scope = self.instrument.getData(leginondata.ScopeEMData)
		except:
			raise AtlasError('unable to access microscope')
		try:
			camera = self.instrument.getData(leginondata.CameraEMData)
		except:
			raise AtlasError('unable to access camera')
		self.logger.debug('Get current instrument state completed')
		return scope, camera

	def getAlpha(self, scope):
		try:
			alpha = scope['stage position']['a']
		except KeyError:
			return None
		degrees = alpha * 180.0 / 3.14159
		if degrees != 0.0:
			infostr = 'Using current alpha tilt in targets: %.2f deg' % degrees
			self.logger.info(infostr)
		return alpha

	def getPreset(self):
		presetname = self.settings['preset']
		if not presetname:
			raise AtlasError('no preset selected')

		preset = self.presetsclient.getPresetByName(presetname)
		if preset is None:
			raise AtlasError('cannot find preset \'%s\'' % presetname)

		return preset

	def updateState(self, preset, scope, camera, center=None):
		self.logger.debug('Updating target settings...')

		scope.friendly_update(preset)
		camera.friendly_update(preset)

		if center is not None:
						for key in center:
							scope['stage position'][key] = center[key]
		self.logger.debug('Target settings updated')

	def getPixelSize(self, scope, ccdcamera):
		try:
			magnification = scope['magnification']
		except KeyError:
			raise AtlasError('unable to get magnification')
		try:
			return self.pixelsizecalclient.retrievePixelSize(scope['tem'], ccdcamera['ccdcamera'], magnification)
		except calibrationclient.NoPixelSizeError:
			raise AtlasError('unable to get pixel size')

	def getCameraParameters(self, camera):
		try:
			return camera['binning']['x'], camera['dimension']['x']
		except KeyError:
			raise AtlasError('unable to get camera geometry')

	def getTargetList(self, evt):
		self.logger.debug('Creating target list...')
		if evt is None:
			# generated from user invoked method
			targetlist = self.newTargetList(mosaic=True, label=self.settings['label'])
			grid = None
		else:
			# generated from external event
			grid = evt['grid']
			label = gridlabeler.getGridLabel(grid)
			targetlist = self.newTargetList(mosaic=True, label=label)
		self.logger.debug('Target list created')
		return targetlist, grid

	def _makeAtlas(self, evt):
		args = self._calculateAtlas(evt)
		kwargs = {'evt': evt}
		self._publishAtlas(*args, **kwargs)

	def _calculateAtlas(self,evt=None):
		self.logger.info('Creating atlas targets...')
		radius, overlap = self.validateSettings(evt)
		scope, camera = self.getState()
		alpha = self.getAlpha(scope)
		preset = self.getPreset()
		if self.settings['mosaic center'] == 'stage center':
			center = {'x':0.0, 'y':0.0}
		else:
			center = None
		self.updateState(preset, scope, camera, center)
		pixelsize = self.getPixelSize(scope, camera)
		binning, imagesize = self.getCameraParameters(camera)
		targets = self.makeCircle(radius, overlap, pixelsize, binning, imagesize)
		return targets, scope, camera, preset

	def _publishAtlas(self, targets, scope, camera, preset, evt=None):
		targetlist, grid = self.getTargetList(evt)

		# publish to DB so new targets get right reference
		try:
			self.publish(targetlist, database=True)
		except node.PublishError:
			raise AtlasError('unable to publish atlas targets')

		for target in targets:
			targetdata = self.newTargetForGrid(grid,
																					target[0], target[1],
																					scope=scope, camera=camera,
																					preset=preset,
																					list=targetlist,
																					type='acquisition')
			self.publish(targetdata, database=True)

		# publish the completed target list with event
		self.publish(targetlist, pubevent=True)
		self.logger.info('Atlas targets published')

	def makeCircle(self, radius, overlap, pixelsize, binning, imagesize):
		maxtargets = self.settings['max targets']
		maxsize = self.settings['max size']

		imagesize = int(round(imagesize*(1.0 - overlap)))
		if imagesize <= 0:
			raise AtlasSizeError('invalid overlap')

		pixelradius = radius/(pixelsize*binning)
		if pixelradius > maxsize/2:
			raise AtlasSizeError('final image will be huge, try using more binning')

		lines = [imagesize/2]
		while lines[-1] < pixelradius - imagesize:
			lines.append(lines[-1] + imagesize)

		pixels = [pixelradius*2]
		for i in lines:
			if i > pixelradius:
				pixels.append(0.0)
			else:
				pixels.append(pixelradius*math.cos(math.asin(i/pixelradius))*2)
		if len(pixels) > maxtargets:
			raise AtlasSizeError('too many targets needed')

		images = []
		for i in pixels:
			images.append(int(math.ceil(i/imagesize)))

		targets = []
		sign = 1
		for n, i in enumerate(images):
			xs = range(-sign*imagesize*(i - 1)/2, sign*imagesize*(i + 1)/2,
									sign*imagesize)
			y = n*imagesize
			for x in xs:
				targets.insert(0, (x, y))
				if y > 0:
					targets.append((x, -y))
			sign = -sign

		txs, tys = zip(*targets)
		xsize = max(txs) - min(txs) + imagesize
		ysize = max(tys) - min(tys) + imagesize

		self.logger.info('Calculated atlas with size %dx%d pixels, from %d target(s)' % (xsize, ysize, len(targets)))

		return targets

	def makeSpiral(self, maxtargets, overlap, size):
		spacing = size - (overlap / 100.0) * size
		spiral = self.relativeSpiral(maxtargets)
		deltalist = []
		for x, y in spiral:
			column, row = (x*spacing, y*spacing)
			try:
				lastdelta = deltalist[-1]
				deltalist.append((row + lastdelta[0], column + lastdelta[1]))
			except IndexError:
				deltalist.append((row, column))
		return deltalist

	def absoluteSpiral(self, length):
		spiral = [(0,0)]
		dir = (1,0)
		xmax = xmin = ymax = ymin = 0
		while len(spiral) < length:
			cur_pos = spiral[-1]
			next_pos = (cur_pos[0] + dir[0], cur_pos[1] + dir[1])
			spiral.append(next_pos)
			cur_pos = next_pos
			if cur_pos[0] > xmax:
				xmax = cur_pos[0]
				dir = (0,1)
			elif cur_pos[0] < xmin:
				xmin = cur_pos[0]
				dir = (0,-1)
			elif cur_pos[1] > ymax:
				ymax = cur_pos[1]
				dir = (-1,0)
			elif cur_pos[1] < ymin:
				ymin = cur_pos[1]
				dir = (1,0)
		return spiral

	def relativeSpiral(self, length):
		spiral = [(0,0)]
		spiraldir = [(0,0)]
		dir = (1,0)
		xmax = xmin = ymax = ymin = 0
		while len(spiral) < length:
			cur_pos = spiral[-1]
			next_pos = (cur_pos[0] + dir[0], cur_pos[1] + dir[1])
			spiral.append(next_pos)
			spiraldir.append(dir)
			cur_pos = next_pos
			if cur_pos[0] > xmax:
				xmax = cur_pos[0]
				dir = (0,1)
			elif cur_pos[0] < xmin:
				xmin = cur_pos[0]
				dir = (0,-1)
			elif cur_pos[1] > ymax:
				ymax = cur_pos[1]
				dir = (-1,0)
			elif cur_pos[1] < ymin:
				ymin = cur_pos[1]
				dir = (1,0)
		return spiraldir

if __name__ == '__main__':
	import random

	def randomTargets(nc, nt, scale):
		random.seed()
		return map(lambda t: tuple(map(lambda c: (random.random() - 0.5)*2*scale,
																		range(nc))), range(nt))

	start = (0.0, 0.0)
	targets = randomTargets(2, 16, 2.0e-3)
	print sortTargets(targets, start)

