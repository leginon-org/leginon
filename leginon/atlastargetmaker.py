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

	targets.append(minrow)

	for i in range(1, nrows - 1):
		row = i*rowstep + minrow[0]
		if row < mincolumn[0]:
			angle = math.atan2(minrow[1] - mincolumn[1], mincolumn[0] - minrow[0])
			column1 = minrow[1] - (row - minrow[0])*math.cos(angle)
		else:
			angle = math.atan2(mincolumn[1] - maxrow[1], maxrow[0] - mincolumn[0])
			column1 = mincolumn[1] + (row - mincolumn[0])*math.cos(angle)

		if row < maxcolumn[0]:
			angle = math.atan2(maxcolumn[1] - minrow[1], maxcolumn[0] - minrow[0])
			column2 = minrow[1] + (row - minrow[0])*math.cos(angle)
		else:
			angle = math.atan2(maxrow[1] - maxcolumn[1], maxrow[0] - maxcolumn[0])
			column2 = maxcolumn[1] - (row - maxcolumn[0])*math.cos(angle)

		ncolumns = int(math.ceil(float(column2 - column1)/shape[1]))
		columnstep = float(column2 - column1)/ncolumns
		ncolumns += 1

		for j in range(ncolumns):
			targets.append((row, column1 + j*columnstep))

	targets.append(maxrow)

	return targets

class AtlasTargetMaker(node.Node, targethandler.TargetHandler):
	panelclass = gui.wx.AtlasTargetMaker.Panel

	settingsclass = data.AtlasTargetMakerSettingsData
	defaultsettings = {
		'preset': None,
		'overlap': 10.0,
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

	def validateSettings(self):
		radius = self.settings['radius']
		if radius <= 0.0:
			raise AtlasError('invalid radius specified')
		overlap = self.settings['overlap']/100.0
		if overlap < 0.0 or overlap >= 100.0:
			raise AtlasError('invalid overlap specified')
		return radius, overlap

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
		#radius, overlap = self.validateSettings()
		movetype = 'stage position'
		preset = self.getPreset()
		try:
			self.instrument.setTEM(preset['tem']['name'])
			self.instrument.setCCDCamera(preset['ccdcamera']['name'])
		except ValueError, e:
			raise AtlasError(e)
		scope, camera = self.getState()
		center = {'x': 0.0, 'y': 0.0}
		size = {'x': 2.0, 'y': 2.0}
		scope[movetype].update(center)
		targets = self.cover(movetype, center, size, preset)
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

	def cover(self, movetype, center, size, preset):
		return self._cover(movetype,
												(center['x'], center['y']),
												(size['x'], size['y']),
												(preset['dimension']['x'], preset['dimension']['y']),
												(preset['binning']['x'], preset['binning']['y']),
												preset['magnification'],
												preset['hightension'])

	def _cover(self, movetype, center, size, dimension, binning, magnification, hightension):
		magnificaion, hightension = parameters
		calibrationclient = self.calibrationclients[movetype]
		rectangle = (
			(center[0] - size[0]/2, center[1] - size[1]/2),
			(center[0] + size[0]/2, center[1] - size[1]/2),
			(center[0] - size[0]/2, center[1] + size[1]/2),
			(center[0] + size[0]/2, center[1] + size[1]/2),
		)
		pixelheight, pixelwidth = dimension[1]*binning[1], dimension[0]*binning[0]
		matrix, imatrix = calibrationclient.getMatrices(magnification, hightension)
		pixelrectangle = [numarray.matrixmultiply(imatrix, c) for c in rectangle]
		targets = cover(pixelrectangle, (pixelheight, pixelwidth))
		return targets

if __name__ == '__main__':
	rectangle = [(-1.0, 0.0), (0.0, 1.0), (1.0, 0.0), (0.0, -1.0)]
	shape = (0.25, 0.25)
	print cover(rectangle, shape)

