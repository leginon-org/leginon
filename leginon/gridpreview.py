#!/usr/bin/env python

import time
import threading
import node, event, data
import camerafuncs
reload(camerafuncs)


class GridPreview(node.Node):
	def __init__(self, id, nodelocations, **kwargs):
		self.cam = camerafuncs.CameraFuncs(self)
		self.done = []
		self.todo = []
		self.temptodo = []
		self.stoprunning = threading.Event()
		self.running = threading.Event()
		print 'init1 GridPreview is instance of node.Node?', isinstance(self, node.Node)
		node.Node.__init__(self, id, nodelocations, **kwargs)
		print 'init2 GridPreview is instance of node.Node?', isinstance(self, node.Node)

		## default camera config
		currentconfig = self.cam.config()
		currentconfig['state']['dimension']['x'] = 1024
		currentconfig['state']['binning']['x'] = 4
		currentconfig['state']['exposure time'] = 100
		self.cam.config(currentconfig)

		self.defineUserInterface()
		self.start()

	def main(self):
		pass

	def defineUserInterface(self):
		#nodespec = node.Node.defineUserInterface(self)
		cam = self.cam.configUIData()
		defprefs = {'center': {'x':0,'y':0}, 'overlap': 75, 'maxtargets': 9}
		spiralprefs = self.registerUIData('Spiral', 'struct', callback=self.uiSpiralPrefs, default=defprefs, permissions='rw')
		self.sim = self.registerUIData('Simulate TEM/camera', 'boolean', permissions='rw', default=0)
		prefs = self.registerUIContainer('Preferences', (cam, spiralprefs, self.sim))

		start = self.registerUIMethod(self.runLoop, 'Run', ())
		stop = self.registerUIMethod(self.stopLoop, 'Stop', ())
		reset = self.registerUIMethod(self.resetLoop, 'Reset', ())
		controls = self.registerUIContainer('Controls', (start,stop,reset))

		self.registerUISpec('Grid Preview', (prefs, controls))

	def uiSpiralPrefs(self, value=None):
		if value is not None:
			camconfig = self.cam.config()
			camstate = camconfig['state']
			size = camstate['dimension']['x']
			self.prefs = value
			overlap = value['overlap']
			maxtargets = value['maxtargets']
			spacing = size - (overlap / 100.0) * size
			sp = self.spiral2(maxtargets)
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
			print 'TODO', self.todo
			self.resetLoop()
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

				camconfig = self.cam.config()
				camstate = camconfig['state']
				binx = camstate['binning']['x']
				biny = camstate['binning']['y']
				targetrow = target[0] * biny
				targetcol = target[1] * binx

				deltarowcol = {'row':targetrow, 'column':targetcol}

				e = event.StagePixelShiftEvent(self.ID(), deltarowcol)
				print 'moving to next position'
				self.outputEvent(e)

			## this should be calibrated
			time.sleep(2)

			stagepos = self.researchByDataID('stage position')
			stagepos = stagepos.content
			print 'gridpreview stagepos', stagepos

			imarray = self.cam.acquireArray(camstate=None, correction=1)
			thisid = self.ID()
			if self.lastid is None:
				neighbortiles = []
			else:
				neighbortiles = [self.lastid,]
			#imdata = data.ImageTileData(thisid, imarray, neighbortiles)
			imdata = data.StateImageTileData(thisid, imarray, stagepos, neighbortiles)
			print 'publishing tile'
			self.publish(imdata, event.StateImageTilePublishEvent)

			self.lastid = thisid

	def next_target(self):
		target = self.temptodo[0]
		self.acquireTarget(target)

		### update target lists
		self.done.append(target)
		self.temptodo = self.temptodo[1:]
		print 'done', self.done
		print 'temptodo', self.temptodo

	def stopLoop(self):
		self.stoprunning.set()
		return ''

	def runLoop(self):
		if self.running.isSet():
			print 'ALREADY RUNNING'
			return ''
		t = threading.Thread(target=self._loop)
		t.setDaemon(1)
		t.start()
		return ''

	def resetLoop(self):
		if self.running.isSet():
			print 'cannot reset while loop is running'
		else:
			self.temptodo = list(self.todo)
			self.lastid = None
		return ''

	def _loop(self):
		self.stoprunning.clear()
		self.running.set()
		try:
			while self.temptodo and not self.stoprunning.isSet():
				self.next_target()
		except Exception, detail:
			print detail
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




