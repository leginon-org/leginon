#!/usr/bin/env python

import time
import threading
import node, event, data
import camerafuncs
import cPickle
import Mrc
import calibrationclient


class GridPreview(node.Node):
	def __init__(self, id, nodelocations, **kwargs):
		self.cam = camerafuncs.CameraFuncs(self)
		self.done = []
		self.todo = []
		self.temptodo = []
		self.stoprunning = threading.Event()
		self.running = threading.Event()
		node.Node.__init__(self, id, nodelocations, **kwargs)
		self.calclient = calibrationclient.StageCalibrationClient(self)

		# will be in presets or something
		self.magnification = 56.0

		## default camera config
		currentconfig = self.cam.config()
		currentconfig['state']['dimension']['x'] = 1024
		currentconfig['state']['binning']['x'] = 2
		currentconfig['state']['exposure time'] = 400

		currentconfig['state']['binning']['x'] = 1
		currentconfig['state']['offset']['x'] = 0
		currentconfig['state']['offset']['y'] = 0
		currentconfig['auto offset'] = 0

		self.cam.config(currentconfig)

		self.defineUserInterface()
		self.start()

	def defineUserInterface(self):
		#nodespec = node.Node.defineUserInterface(self)
		# will be in presets or something
		mag = self.registerUIData('Magnification', 'float', callback=self.uiMagnification, default=self.magnification, permissions='rw')
		self.sim = self.registerUIData('Simulate TEM/camera', 'boolean', permissions='rw', default=0)
		cam = self.cam.configUIData()
		defprefs = {'center': {'x':0,'y':0}, 'overlap': 50, 'maxtargets': 4}
		spiralprefs = self.registerUIData('Spiral', 'struct', callback=self.uiSpiralPrefs, default=defprefs, permissions='rw')
		self.sim = self.registerUIData('Simulate TEM/camera', 'boolean', permissions='rw', default=0)
		prefs = self.registerUIContainer('Preferences', (mag, cam, spiralprefs, self.sim))

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
			sp = self.relative_spiral(maxtargets)
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
#			print 'TODO', self.todo
			self.resetLoop()
		return self.prefs

	def uiCalibrate(self):
		return ''

	def uiEstimate(self):
		return ''

	# will be in presets or something
	def uiMagnification(self, value=None):
		if value is not None:
			self.magnification = value
		return self.magnification

	def getScope(self):
		return self.researchByDataID('scope').content

	def acquireTarget(self, target):
#		print 'TARGET', target
		if self.sim.get():
#			print 'SIMULATED'
			time.sleep(1)
		else:

			if target is None:
				# move to center
				center = self.prefs['center']
				gonpos = {'stage position': {'x':center['x'], 'y':center['y']}}
				emdata = data.EMData('scope', gonpos)
#				print 'moving to center', center
				self.publishRemote(emdata)
			else:
				# move to next postion
				camconfig = self.cam.config()
				camstate = camconfig['state']
#				print 'camstate', camstate
				scopestate = self.getScope()

				targetrow, targetcol = target
#				print 'targetrow', targetrow
				pixelshift = {'row':targetrow, 'col':targetcol}
				newstate = self.calclient.transform(pixelshift, scopestate, camstate)
				emdat = data.EMData('scope', newstate)
#				print 'moving to next position'
				self.publishRemote(emdat)

			## this should be calibrated
			time.sleep(2)

			stagepos = self.researchByDataID('stage position')
			stagepos = stagepos.content
#			print 'gridpreview stagepos', stagepos

			imagedata = self.cam.acquireCameraImageData(camstate=None, correction=1)
			imarray = imagedata.content['image']
			thisid = self.ID()
			if self.lastid is None:
				neighbortiles = []
			else:
				neighbortiles = [self.lastid,]

			filename = self.tilefilename(thisid)
			Mrc.numeric_to_mrc(imarray, filename)
			storedata = {'id':thisid,'image':filename, 'state': stagepos, 'neighbors': neighbortiles, 'target':target}
			self.logAppend(storedata)

			scope = imagedata.content['scope']
			camera = imagedata.content['camera']
			imdata = data.TileImageData(thisid, imarray, scope, camera, neighbortiles)
#			print 'publishing tile'
			self.publish(imdata, event.TileImagePublishEvent)

			self.lastid = thisid

	def logAppend(self, data):
		self.loglist.append(data)
		self.logSave()

	def logClear(self):
		self.loglist = []
		self.logSave()

	def logSave(self):
		f = open('gp.log', 'w')
		cPickle.dump(self.loglist, f, 1)
		f.close()

	def logLoad(self):
		f = open('gp.log', 'r')
		self.loglist = cPickle.load(f)
		f.close()

	def logPrint(self):
		for im in self.loglist:
			print im['id'], im['target'], im['state']

	def tilefilename(self, id):
		indexstr = '%04d' % (id[-1],)
		filename = 'gp' + indexstr + '.mrc'
		return filename

	def next_target(self):
		target = self.temptodo[0]
		self.acquireTarget(target)

		### update target lists
		self.done.append(target)
		self.temptodo = self.temptodo[1:]
#		print 'done', self.done
#		print 'temptodo', self.temptodo

	def stopLoop(self):
		self.stoprunning.set()
		return ''

	def runLoop(self):
		if self.running.isSet():
			self.printerror('loop is already running')
			return ''
		t = threading.Thread(target=self._loop)
		t.setDaemon(1)
		t.start()
		return ''

	def resetLoop(self):
		if self.running.isSet():
			self.printerror('cannot reset while loop is running')
		else:
			self.temptodo = list(self.todo)
			self.lastid = None
			self.logClear()
		return ''

	def _loop(self):
		self.stoprunning.clear()
		self.running.set()

		# will be in presets or something
		emdata = data.EMData('scope', {'magnification': self.magnification})
		self.publishRemote(emdata)

		self.cam.state(self.cam.config()['state'])
		try:
			while self.temptodo and not self.stoprunning.isSet():
				self.next_target()
			self.logPrint()
		except Exception, detail:
			print detail
		self.running.clear()
		self.stoprunning.clear()

	def absolute_spiral(self, length):
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

	def relative_spiral(self, length):
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
