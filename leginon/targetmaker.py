#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#
import threading
import node, event, data
import uidata
import presets
import calibrationclient
import math
import EM
import targethandler

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
	eventinputs = node.Node.eventinputs + targethandler.TargetHandler.eventinputs + EM.EMClient.eventinputs
	eventoutputs = node.Node.eventoutputs + targethandler.TargetHandler.eventoutputs + EM.EMClient.eventoutputs
	def __init__(self, id, session, managerlocation, **kwargs):
		self.targetlist = []
		node.Node.__init__(self, id, session, managerlocation, **kwargs)
		self.emclient = EM.EMClient(self)

#	def defineUserInterface(self):
#		node.Node.defineUserInterface(self)
#		publishtargetsmethod = uidata.Method('Publish Targets',
#																						self.publishTargetList)
#		container = uidata.LargeContainer('Target Maker')
#		container.addObjects((publishtargetsmethod,))
#		self.uicontainer.addObject(container)

class MosaicTargetMaker(TargetMaker):
	eventinputs = TargetMaker.eventinputs + [event.MakeTargetListEvent]
	def __init__(self, id, session, managerlocation, **kwargs):
		TargetMaker.__init__(self, id, session, managerlocation, **kwargs)
		self.pixelsizecalclient = calibrationclient.PixelSizeCalibrationClient(self)
		self.addEventInput(event.MakeTargetListEvent, self.makeMosaicTargetList)
		self.presetsclient = presets.PresetsClient(self)
		self.defineUserInterface()
		self.start()

	def defineUserInterface(self):
		TargetMaker.defineUserInterface(self)

		self.statusmessage = uidata.String('Current status', '', 'r')
		statuscontainer = uidata.Container('Status')
		statuscontainer.addObjects((self.statusmessage,))

		self.presetname = self.presetsclient.uiSinglePresetSelector('Preset', '', 'rw', persist=True)
		self.radius = uidata.Float('Radius (meters)', 1.0e-3, 'rw', persist=True)
		self.overlap = uidata.Integer('Overlap (percent)', 0, 'rw', persist=True)
		self.listlabel = uidata.String('Label', '', 'rw', persist=True)
		settingscontainer = uidata.Container('Settings')
		settingscontainer.addObjects((self.presetname, self.radius, self.overlap, self.listlabel))

		publishtargetlistmethod = uidata.Method('Publish Target List', self.makeMosaicTargetList)
		controlcontainer = uidata.Container('Control')
		controlcontainer.addObjects((publishtargetlistmethod,))

		container = uidata.LargeContainer('Mosaic Target Maker')
		container.addObjects((statuscontainer, settingscontainer, controlcontainer))
		self.uicontainer.addObject(container)

	def setStatusMessage(self, message):
		self.statusmessage.set(message)

	def makeMosaicTargetList(self, ievent=None):
		# make targets using current instrument state and selected preset
		self.setStatusMessage('getting current EM state')
		try:
			scope = self.emclient.getScope()
			camera = self.emclient.getCamera()
		except node.ResearchError:
			self.setStatusMessage('Error publishing targets, cannot find EM')
			return
		
		pname = self.presetname.get()

		if pname is None:
			self.setStatusMessage('Error publishing targets, no preset selected')
			return

		self.setStatusMessage('Finding preset "%s"' % pname)
		preset = self.presetsclient.getPresetByName(pname)

		if preset is None:
			message = 'Error publishing tagets, cannot find preset "%s"' % pname
			self.setStatusMessage(message)
			return

		self.setStatusMessage('Updating target settings')
		scope.friendly_update(preset)
		camera.friendly_update(preset)
		size = camera['dimension']['x']

		center = {'x': 0.0, 'y': 0.0}
		for key in center:
			# stage position
			scope['stage position'][key] = center[key]

		radius = self.radius.get()
		overlap = self.overlap.get()/100.0
		if overlap < 0.0 or overlap >= 100.0:
			self.setStatusMessage('Invalid overlap specified')
			return
		magnification = scope['magnification']
		try:
			pixelsize = self.pixelsizecalclient.retrievePixelSize(magnification)
		except calibrationclient.NoPixelSizeError:
			print 'No available pixel size'
			return
		binning = camera['binning']['x']
		imagesize = camera['dimension']['x']

		self.setStatusMessage('Creating target list')
		if ievent is None: 
			### generated from user invoked method
			label = self.listlabel.get()
			targetlist = self.newTargetList(mosaic=True, label=label)
			grid = None
		else:
			### generated from external event
			grid = ievent['grid']
			gridid = grid['grid ID']
			label = '%06d' % (gridid,)
			targetlist = self.newTargetList(mosaic=True, label=label)
		self.setStatusMessage('Publishing target list')
		### publish to DB so new targets get right reference
		self.publish(targetlist, database=True)
		for delta in self.makeCircle(radius, pixelsize, binning, imagesize, overlap):
			targetdata = self.newTargetForGrid(grid, delta[0], delta[1], scope=scope, camera=camera, preset=preset, list=targetlist, type='acquisition')
			self.publish(targetdata, database=True)
		### publish with event
		self.publish(targetlist, pubevent=True)
		self.setStatusMessage('Target list published')

	def makeCircle(self, radius, pixelsize, binning, imagesize, overlap=0.0):
		imagesize = int(round(imagesize*(1.0 - overlap)))
		if imagesize <= 0:
			raise ValueError('Invalid overlap value')
		pixelradius = radius/(pixelsize*binning)
		lines = [imagesize/2]
		while lines[-1] < pixelradius - imagesize:
			lines.append(lines[-1] + imagesize)
		pixels = [pixelradius*2]
		for i in lines:
			if i > pixelradius:
				pixels.append(0.0)
			else:
				pixels.append(pixelradius*math.cos(math.asin(i/pixelradius))*2)
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

