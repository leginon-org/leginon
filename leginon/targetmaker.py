import threading
import node, event, data
import uidata

class TargetMaker(node.Node):
	def __init__(self, id, session, nodelocations, **kwargs):
		self.targetlist = []
		node.Node.__init__(self, id, session, nodelocations, **kwargs)

	def publishTargetList(self):
		if self.targetlist:
			targetlistdata = data.ImageTargetListData(id=self.ID(),
																								targets=self.targetlist)
			self.publish(targetlistdata, pubevent=True)

	def defineUserInterface(self):
		node.Node.defineUserInterface(self)
		publishtargetsmethod = uidata.UIMethod('Publish Targets',
																						self.publishTargetList)
		container = uidata.UIMediumContainer('Target Maker')
		container.addUIObjects((publishtargetsmethod,))
		self.uiserver.addUIObject(container)

class SpiralTargetMaker(TargetMaker):
	def __init__(self, id, session, nodelocations, **kwargs):
		TargetMaker.__init__(self, id, session, nodelocations, **kwargs)
		self.defineUserInterface()

	def defineUserInterface(self):
		TargetMaker.defineUserInterface(self)
		self.maxtargets = uidata.UIInteger('Maximum Targets', 9, 'rw')
		self.overlap = uidata.UIInteger('Percent Overlap', 25, 'rw')
		self.center = uidata.UIStruct('Spiral Center', {'x': 0.0, 'y': 0.0}, 'rw')
		container = uidata.UIMediumContainer('Spiral Target Maker')
		container.addUIObjects((self.maxtargets, self.overlap, self.center))
		self.uiserver.addUIObject(container)

	def publishTargetList(self):
		scope = self.researchByDataID(('scope,'))
		camera = self.researchByDataID(('camera,'))
		# waiting to revise with presets
		size = camera['dimension']['x']
		center = self.center.get()
		for key in center
			# stage position for now
			scope['stage position'][key] = center[key]
		for delta in self.makeSpiral(size):
			initializer = {'id': self.ID(), 'session': self.session,
											'delta row': delta[0], 'delta column': delta[1],
											'scope': None, 'camera': None, 'preset': None}
			self.targetlist.append(data.ImageTargetData(initializer=initializer))
		TargetMaker.publishTargetList(self)
		print self.targetlist
		self.targetlist = []

	def makeSpiral(self, size):
		maxtargets = self.maxtargets.get()
		overlap = self.overlap.get()
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

