#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import math
import numarray
import calibrationclient
import data
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

def cover(rectangle, shape):
	rows = [row for row, column in rectangle]
	minrow = rectangle[numarray.argmin(rows)]
	maxrow = rectangle[numarray.argmax(rows)]

	columns = [column for row, column in rectangle]
	mincolumn = rectangle[numarray.argmin(columns)]
	maxcolumn = rectangle[numarray.argmax(columns)]

	nrows = int(math.ceil(float(maxrow[0] - minrow[0])/shape[0]))
	rowstep = float(maxrow[0] - minrow[0])/nrows
	nrows += 1

	targets = []

	for i in range(nrows):
		row = i*rowstep + minrow[0]
		if minrow[1] == mincolumn[1]:
			column1 = minrow[1]
		elif row < mincolumn[0]:
			angle = math.atan2(minrow[1] - mincolumn[1], mincolumn[0] - minrow[0])
			column1 = minrow[1] - (row - minrow[0])*math.cos(angle)
		else:
			angle = math.atan2(mincolumn[1] - maxrow[1], maxrow[0] - mincolumn[0])
			column1 = mincolumn[1] + (row - mincolumn[0])*math.cos(angle)

		if minrow[0] == maxcolumn[0]:
			column2 = maxcolumn[1]
		elif row < maxcolumn[0]:
			angle = math.atan2(maxcolumn[1] - minrow[1], maxcolumn[0] - minrow[0])
			column2 = minrow[1] + (row - minrow[0])*math.cos(angle)
		else:
			angle = math.atan2(maxrow[1] - maxcolumn[1], maxrow[0] - maxcolumn[0])
			column2 = maxcolumn[1] - (row - maxcolumn[0])*math.cos(angle)

		deltacolumn = float(column2 - column1)
		ncolumns = int(math.ceil(deltacolumn/shape[1]))
		try:
			columnstep = deltacolumn/ncolumns
		except ZeroDivisionError:
			columnstep = 0.0
		ncolumns += 1

		for j in range(ncolumns):
			targets.append((row, column1 + j*columnstep))

	return targets

def optimizeTargets(start, targets, matrix):
	mtargets = [numarray.matrixmultiply(matrix, target) for target in targets]
	targetindicies = []
	while len(targetindicies) < len(mtargets):
		minmagnitude = None
		for i, target in enumerate(mtargets):
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

	settingsclass = data.AtlasTargetMakerSettingsData
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
			scope = self.instrument.getData(data.ScopeEMData)
		except:
			raise AtlasError('unable to access microscope')
		try:
			camera = self.instrument.getData(data.CameraEMData, image=False)
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
		for a, value in self.settings['center'].items():
			if value is not None:
				scope[movetype][a] = value
		center = dict(scope[movetype])
		size = self.settings['size']
		targets = self.cover(movetype, center, size, scope['high tension'], preset)
		self.logger.info('Atlas created using %d target(s).' % len(targets))
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

	def cover(self, movetype, center, size, hightension, preset):
		center = (center['x'], center['y'])
		size = (size['x'], size['y'])
		shape = (preset['dimension']['y']*preset['binning']['y'],
							preset['dimension']['x']*preset['binning']['x'])
		calibrationclient = self.calibrationclients[movetype]
		magnification = preset['magnification']
		matrix, imatrix = calibrationclient.getMatrices(magnification, hightension)
		if matrix is None or imatrix is None:
			raise AtlasError('no calibration available')
		targets = self._cover(center, size, shape, imatrix)
		targets = optimizeTargets(center, targets, matrix)
		return targets

	def _cover(self, center, size, shape, matrix):
		rectangle = (
			(center[0] - size[0]/2, center[1] - size[1]/2),
			(center[0] + size[0]/2, center[1] - size[1]/2),
			(center[0] - size[0]/2, center[1] + size[1]/2),
			(center[0] + size[0]/2, center[1] + size[1]/2),
		)
		rectangle = [numarray.matrixmultiply(matrix, c) for c in rectangle]
		for c in rectangle:
			c[0], c[1] = c[1], c[0]
		targets = cover(rectangle, shape)
		return targets

if __name__ == '__main__':
	'''
	matrix = numarray.identity(2, numarray.Float)
	start = (0.0, 0.0)
	targets = [(1.0, 1.0), (2.0, 2.0), (5.0, 5.0), (1.4, 1.2)]
	print optimizeTargets(start, targets, matrix)
	'''

	matrix = numarray.identity(2, numarray.Float)
	angle = math.pi/4
	matrix[0, 0] = math.cos(angle)
	matrix[1, 0] = math.sin(angle)
	matrix[0, 1] = -math.sin(angle)
	matrix[1, 1] = math.cos(angle)
	rectangle = [(0.0, 0.0), (0.0, 1.0), (1.0, 0.0), (1.0, 1.0)]
	rectangle = [numarray.matrixmultiply(matrix, c) for c in rectangle]
	shape = (0.5, 0.5)
	print cover(rectangle, shape)

