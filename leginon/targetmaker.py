import threading
import node, event, data
import uidata
import presets
import calibrationclient
import camerafuncs
import math

class TargetMaker(node.Node):
	eventoutputs = node.Node.eventoutputs + [event.ImageTargetListPublishEvent]
	def __init__(self, id, session, nodelocations, **kwargs):
		self.targetlist = []
		node.Node.__init__(self, id, session, nodelocations, **kwargs)

	def publishTargetList(self):
		if self.targetlist:
			targetlistdata = data.ImageTargetListData(id=self.ID(),
																								targets=self.targetlist)
#			print 'publishing ', targetlistdata['id']
			self.publish(targetlistdata, pubevent=True)

	def defineUserInterface(self):
		node.Node.defineUserInterface(self)
		publishtargetsmethod = uidata.Method('Publish Targets',
																						self.publishTargetList)
		container = uidata.MediumContainer('Target Maker')
		container.addObjects((publishtargetsmethod,))
		self.uiserver.addObject(container)

class SpiralTargetMaker(TargetMaker):
	eventinputs = TargetMaker.eventinputs + [event.PublishSpiralEvent]
	def __init__(self, id, session, nodelocations, **kwargs):
		TargetMaker.__init__(self, id, session, nodelocations, **kwargs)
		self.cam = camerafuncs.CameraFuncs(self)
		self.pixelsizecalclient = calibrationclient.PixelSizeCalibrationClient(self)
		self.addEventInput(event.PublishSpiralEvent, self.publishTargetList)
		self.presetsclient = presets.PresetsClient(self)
		self.defineUserInterface()
		self.start()

	def defineUserInterface(self):
		TargetMaker.defineUserInterface(self)

#		self.maxtargets = uidata.Integer('Maximum Targets', 2, 'rw', persist=True)
#		self.overlap = uidata.Integer('Percent Overlap', 50, 'rw', persist=True)
#		self.center = uidata.Struct('Spiral Center', {'x': 0.0, 'y': 0.0}, 'rw')
#		settingscontainer.addObjects((pselect, self.radius, self.maxtargets, self.overlap, self.center))

		pselect = self.presetsclient.uiPresetSelector()
		self.radius = uidata.Float('Radius (meters)', 1.0e-3, 'rw', persist=True)

		settingscontainer = uidata.Container('Settings')
		settingscontainer.addObjects((pselect, self.radius))

		publishspiralmethod = uidata.Method('Publish Spiral',
																				self.publishTargetList)
		controlcontainer = uidata.Container('Control')
		controlcontainer.addObjects((publishspiralmethod,))

		self.statusmessage = uidata.String('Current status', '', 'r')
		statuscontainer = uidata.Container('Status')
		statuscontainer.addObjects((self.statusmessage,))

		container = uidata.MediumContainer('Spiral Target Maker')
		container.addObjects((settingscontainer, controlcontainer, statuscontainer))
		self.uiserver.addObject(container)

	def setStatusMessage(self, message):
		self.statusmessage.set(message)

	def publishTargetList(self, ievent=None):
		### do targets referenced from current state and prefered preset
		self.setStatusMessage('Publishing target list')
		try:
			scope = self.researchByDataID(('scope',))
			camera = self.researchByDataID(('camera no image data',))
		except node.ResearchError:
			self.setStatusMessage('Error publishing targets, cannot find EM')
			return
		
		pname = self.presetsclient.uiGetSelectedName()

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
			# stage position for now
			scope['stage position'][key] = center[key]

#		maxtargets = self.maxtargets.get()
#		overlap = self.overlap.get()
		#for delta in self.makeSpiral(maxtargets, overlap, size):

		radius = self.radius.get()
		magnification = scope['magnification']
		pixelsize = self.pixelsizecalclient.retrievePixelSize(magnification, False)
		binning = camera['binning']['x']
		imagesize = camera['dimension']['x']

		for delta in self.makeCircle(radius, pixelsize, binning, imagesize):
			initializer = {'id': self.ID(),
											'session': self.session,
											'delta row': delta[0],
											'delta column': delta[1],
											'scope': scope,
											'camera': camera,
											'preset': preset}
			targetdata = data.AcquisitionImageTargetData(initializer=initializer, type='acquisition')
			self.targetlist.append(targetdata)
		TargetMaker.publishTargetList(self)
		self.targetlist = []
		self.setStatusMessage('Target list published')

	def makeCircle(self, radius, pixelsize, binning, imagesize):
		pixelradius = radius/(pixelsize*binning)
		lines = [imagesize/2]
		while lines[-1] < pixelradius - imagesize:
			lines.append(lines[-1] + imagesize)
		pixels = [pixelradius*2]
		for i in lines:
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

