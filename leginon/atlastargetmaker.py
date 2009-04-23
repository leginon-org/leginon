#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import math
import calibrationclient
import leginondata
import event
import instrument
import node
import presets
import targethandler
import gui.wx.AtlasTargetMaker

class AtlasError(Exception):
	pass

class AtlasSizeError(AtlasError):
	pass

def cover(center, size, theta, imagesize):
	m, n = size
	theta %= math.pi
	if theta > math.pi/2.0:
		s = imagesize[0]
	else:
		s = imagesize[1]
	theta %= math.pi/2.0
	if math.atan2(m, n) + theta > math.pi/2.0:
		rm = math.hypot(m, n)*math.sin(math.pi/2.0 + math.atan2(m, n) - theta)
	else:
		rm = math.hypot(m, n)*math.sin(math.pi/2.0 - math.atan2(m, n) + theta)
	nh = int(math.ceil(rm/s)) + 1
	try:
		d = rm/(nh - 1.0)
	except ZeroDivisionError:
		d = 0.0

	targets = []
	for i in range(nh):
		dx = (i*d)/math.sin(theta)
		if dx <= size[0]:
			l1 = (dx, 0.0)
		else:
			l1 = (size[0], (dx - size[0])*math.tan(theta))
		dy = dx*math.tan(theta)
		if dy <= size[1]:
			l2 = (0.0, dy)
		else:
			l2 = (dx - (size[1]/math.tan(theta)), size[1])
		m = math.hypot(l2[0] - l1[0], l2[1] - l1[1])
		m = round(m, 16)
		dm = int(math.ceil(m/s)) + 1
		try:
			dd = m/(dm - 1.0)
		except ZeroDivisionError:
			dd = 0.0
		for i in range(dm):
			x = i*dd*math.cos(theta) + l1[0]
			y = i*dd*math.sin(theta) + l1[1]
			targets.append({'x': x, 'y': y})
	return targets

def optimizeTargets(start, targets):
	targetindicies = []
	while len(targetindicies) < len(targets):
		minmagnitude = None
		for i, target in enumerate(targets):
			if i in targetindicies:
				continue
			magnitude = math.hypot(start[0] - target[0], start[1] - target[1])
			if magnitude < minmagnitude or minmagnitude is None:
				minindex = i
				mintarget = target
				minmagnitude = magnitude
		targetindicies.append(minindex)
		start = mintarget
	ntargets = []
	for i in targetindicies:
		ntargets.append(targets[i])
	return ntargets

class AtlasTargetMaker(node.Node, targethandler.TargetHandler):
	panelclass = gui.wx.AtlasTargetMaker.Panel

	settingsclass = leginondata.AtlasTargetMakerSettingsData
	defaultsettings = {
		'preset': None,
		'label': None,
		'center': {'x': 0.0, 'y': 0.0},
		'size': {'x': 1.99e-3, 'y': 1.99e-3},
	}

	eventinputs = (
		node.Node.eventinputs +
		targethandler.TargetHandler.eventinputs +
		[
			event.MakeTargetListEvent,
		]
	)
	eventoutputs = (
		node.Node.eventoutputs +
		targethandler.TargetHandler.eventoutputs
	)

	def __init__(self, *args, **kwargs):
		self.publishargs = None

		node.Node.__init__(self, *args, **kwargs)

		self.instrument = instrument.Proxy(self.objectservice, self.session)
		self.calibrationclients = {
			'stage position': calibrationclient.StageCalibrationClient(self),
		}
		self.presetsclient = presets.PresetsClient(self)

		self.addEventInput(event.MakeTargetListEvent, self._makeAtlas)

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
			raise
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

	def getState(self):
		# tem/camera from preset?
		self.logger.debug('Getting current instrument state...')
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

	def getPreset(self):
		presetname = self.settings['preset']
		if not presetname:
			raise AtlasError('no preset selected')

		preset = self.presetsclient.getPresetByName(presetname)
		if preset is None:
			raise AtlasError('cannot find preset \'%s\'' % presetname)

		return preset

	def getTargetList(self, evt):
		self.logger.debug('Creating target list...')
		if evt is None: 
			# generated from user invoked method
			targetlist = self.newTargetList(mosaic=True, label='')
			grid = None
		else:
			# generated from external event
			grid = evt['grid']
			gridid = grid['grid ID']
			label = '%06d' % (gridid,)
			targetlist = self.newTargetList(mosaic=True, label=label)
		self.logger.debug('Target list created')
		return targetlist, grid

	def _makeAtlas(self, evt):
		args = self._calculateAtlas()
		kwargs = {'evt': evt}
		self._publishAtlas(*args, **kwargs)

	def _calculateAtlas(self):
		self.logger.info('Creating atlas targets...')
		movetype = 'stage position'
		preset = self.getPreset()
		try:
			self.instrument.setTEM(preset['tem']['name'])
			self.instrument.setCCDCamera(preset['ccdcamera']['name'])
		except ValueError, e:
			raise AtlasError(e)
		scope, camera = self.getState()
		center = dict(self.settings['center'])
		size = self.settings['size']
		targets = self.cover(movetype, center, size, scope['high tension'], preset)
		self.logger.info('Atlas created using %d target(s).' % len(targets))
		return movetype, targets, scope, camera, preset

	def _publishAtlas(self, movetype, targets, scope, camera, preset, evt=None):
		targetlist, grid = self.getTargetList(evt)

		# publish to DB so new targets get right reference
		try:
			self.publish(targetlist, database=True)
		except node.PublishError:
			raise AtlasError('unable to publish atlas targets')

		for target in targets:
			scope[movetype] = dict(scope[movetype])
			scope[movetype].update(target)
			targetdata = self.newTargetForGrid(grid, 0, 0,
																					scope=scope, camera=camera,
																					preset=preset,
																					list=targetlist,
																					type='acquisition')
			self.publish(targetdata, database=True)

		# publish the completed target list with event
		self.publish(targetlist, pubevent=True)
		self.logger.info('Atlas targets published')

	def cover(self, movetype, center, size, hightension, preset):
		center = (center['x'], center['y'])
		size = (size['x'], size['y'])
		shape = (preset['dimension']['y']*preset['binning']['y'],
							preset['dimension']['x']*preset['binning']['x'])
		calibrationclient = self.calibrationclients[movetype]
		magnification = preset['magnification']
		r = calibrationclient.getRotationAndPixelSize(magnification, hightension)
		print r
		xangle, xpixsize, yangle, ypixsize = r
		targets = cover(center, size, theta, imagesize)
		targets = optimizeTargets(center, targets)
		return targets

if __name__ == '__main__':
	pass
