#!/usr/bin/env python

import time
import threading
import node, event, data
import camerafuncs

class GridPreview(node.Node, camerafuncs.CameraFuncs):
	def __init__(self, id, nodelocations):
		self.done = []
		self.todo = []
		self.stoprunning = threading.Event()
		self.running = threading.Event()
		node.Node.__init__(self, id, nodelocations)
		self.start()

	def main(self):
		pass

	def defineUserInterface(self):
		nodespec = node.Node.defineUserInterface(self)
		cam = self.cameraConfigUIData()
		defprefs = {'center': {'x':0,'y':0}, 'overlap': 20, 'maxtargets': 9}
		spiralprefs = self.registerUIData('Spiral', 'struct', callback=self.uiSpiralPrefs, default=defprefs, permissions='rw')
		self.sim = self.registerUIData('Simulate TEM/camera', 'boolean', permissions='rw', default=0)
		prefs = self.registerUIContainer('Preferences', (cam, spiralprefs, self.sim))

		start = self.registerUIMethod(self.runLoop, 'Run', ())
		stop = self.registerUIMethod(self.stopLoop, 'Stop', ())
		controls = self.registerUIContainer('Controls', (start,stop))

		self.registerUISpec('Grid Preview', (prefs, controls, nodespec))

	def uiSpiralPrefs(self, value=None):
		if value is not None:
			camconfig = self.cameraConfig()
			camstate = camconfig['state']
			size = camstate['dimension']['x']
			self.prefs = value
			overlap = value['overlap']
			maxtargets = value['maxtargets']
			spacing = size - (overlap / 100.0) * size
			sp = self.spiral2(maxtargets)
			self.lastid = None
			self.todo = []
			for point in sp:
				if point[0] == 0 and point[1] == 0:
					self.todo.append(None)
				else:
					x = spacing * point[0]
					y = spacing * point[1]
					self.todo.append( (x,y) )
				#gonx = center['x'] + point[0] * spacing
				#gony = center['y'] + point[1] * spacing
				#self.todo.append( (gonx,gony) )
		return self.prefs

	def uiCalibrate(self):
		return ''

	def uiEstimate(self):
		return ''

	def acquireTarget(self, target):
		print 'TARGET', target
		if self.sim.get():
			print 'SIMULATED'
			time.sleep(1)
		else:

			if target is None:
				# move to center
				center = self.prefs['center']
				gonpos = {'stage position': {'x':center['x'], 'y':center['y']}}
				emdata = data.EMData('scope', gonpos)
				print 'moving to center', center
				self.publishRemote(emdata)
			else:
				# move to next postion
				deltarowcol = {'row':target[0], 'column':target[1]}
				e = event.StagePixelShiftEvent(self.ID(), deltarowcol)
				print 'moving to next position'
				self.outputEvent(e)

			## this should be calibrated
			time.sleep(2)

			stagepos = self.researchByDataID('stage position')

			imarray = self.cameraAcquireArray(camstate=None, correction=1)
			thisid = self.ID()
			if self.lastid is None:
				neighbortiles = []
			else:
				neighbortiles = [self.lastid,]
			imdata = data.EMImageTileData(thisid, imarray, stagepos, neighbortiles)
			print 'publishing tile'
			self.publish(imdata, event.EMImageTilePublishEvent)

			self.lastid = thisid


	def next_target(self):
		target = self.todo[0]
		self.acquireTarget(target)

		### update target lists
		self.done.append(target)
		self.todo = self.todo[1:]
		print 'done', self.done
		print 'todo', self.todo

	def stopLoop(self):
		self.stoprunning.set()
		return ''

	def runLoop(self):
		if self.running.isSet():
			return ''
		t = threading.Thread(target=self._loop)
		t.setDaemon(1)
		t.start()
		return ''

	def _loop(self):
		self.stoprunning.clear()
		self.running.set()
		while self.todo and not self.stoprunning.isSet():
			self.next_target()
		self.running.clear()
		self.stoprunning.clear()

	def spiral(self, length):
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

	def spiral2(self, length):
		spiral = [(0,0)]
		dir = (1,0)
		xmax = xmin = ymax = ymin = 0
		while len(spiral) < length:
			cur_pos = spiral[-1]
			next_pos = (cur_pos[0] + dir[0], cur_pos[1] + dir[1])
			spiral.append(dir)
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




