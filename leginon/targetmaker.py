import threading
import node, event, data
import uidata
import presets

class TargetMaker(node.Node):
	eventoutputs = node.Node.eventoutputs + [event.ImageTargetListPublishEvent]
	def __init__(self, id, session, nodelocations, **kwargs):
		self.targetlist = []
		node.Node.__init__(self, id, session, nodelocations, **kwargs)

	def publishTargetList(self):
		if self.targetlist:
			targetlistdata = data.ImageTargetListData(id=self.ID(),
																								targets=self.targetlist)
			print 'publishing ', targetlistdata['id']
			self.publish(targetlistdata, pubevent=True)

	def defineUserInterface(self):
		node.Node.defineUserInterface(self)
		publishtargetsmethod = uidata.Method('Publish Targets',
																						self.publishTargetList)
		container = uidata.MediumContainer('Target Maker')
		container.addObjects((publishtargetsmethod,))
		self.uiserver.addObject(container)

class SpiralTargetMaker(TargetMaker):
	def __init__(self, id, session, nodelocations, **kwargs):
		TargetMaker.__init__(self, id, session, nodelocations, **kwargs)
		self.presetsclient = presets.PresetsClient(self)
		self.defineUserInterface()
		self.start()

	def defineUserInterface(self):
		TargetMaker.defineUserInterface(self)

		pselect = self.presetsclient.uiPresetSelector()
		self.maxtargets = uidata.Integer('Maximum Targets', 2, 'rw')
		self.overlap = uidata.Integer('Percent Overlap', 50, 'rw')
		self.center = uidata.Struct('Spiral Center', {'x': 0.0, 'y': 0.0}, 'rw')
		settingscontainer = uidata.Container('Settings')
		settingscontainer.addObjects((pselect, self.maxtargets, self.overlap, self.center))

		publishspiralmethod = uidata.Method('Publish Spiral', self.publishTargetList)
		self.progress = uidata.Progress('', 0)
		controlcontainer = uidata.Container('Control')
		controlcontainer.addObjects((self.progress, publishspiralmethod))

		container = uidata.MediumContainer('Spiral Target Maker')
		container.addObjects((settingscontainer, controlcontainer))
		self.uiserver.addObject(container)

	def publishTargetList(self):
		self.progress.set(0)

		### do targets referenced from current state
		scope = self.researchByDataID(('scope',))
		camera = self.researchByDataID(('camera',))
		pname = self.presetsclient.uiGetSelectedName()
		preset = self.presetsclient.getPresetByName(pname)
		camera.friendly_update(preset)
		size = camera['dimension']['x']

		center = self.center.get()
		for key in center:
			# stage position for now
			scope['stage position'][key] = center[key]

		maxtargets = self.maxtargets.get()
		overlap = self.overlap.get()
		for delta in self.makeSpiral(maxtargets, overlap, size):
			initializer = {'id': self.ID(), 'session': self.session, 'delta row': delta[0], 'delta column': delta[1], 'scope': scope, 'camera': camera, 'preset': preset}
			self.targetlist.append(data.ImageTargetData(initializer=initializer))
			self.progress.set(self.progress.get() + 100/maxtargets)
		self.progress.set(100)
		TargetMaker.publishTargetList(self)
		self.targetlist = []

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

