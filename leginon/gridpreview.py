#!/usr/bin/env python

import time
import threading
import node, event, data
import camerafuncs
import cPickle
import Mrc
import calibrationclient
import presets
import copy
import uidata

class GridPreview(node.Node):
	def __init__(self, id, session, nodelocations, **kwargs):
		self.cam = camerafuncs.CameraFuncs(self)
		self.done = []
		self.todo = []
		self.temptodo = []
		self.stoprunning = threading.Event()
		self.running = threading.Event()
		node.Node.__init__(self, id, session, nodelocations, **kwargs)
		self.calclient = calibrationclient.StageCalibrationClient(self)
		self.presetsclient = presets.PresetsClient(self)

		self.defineUserInterface()
		self.start()

	def defineUserInterface(self):
		node.Node.defineUserInterface(self)
		self.presetname = uidata.UIString('Preset Name', 'vlm170', 'rw')
		self.simulateflag = uidata.UIBoolean('Simulation', False, 'rw')
		spiral = {'center': {'x':0.0,'y':0.0}, 'overlap': 20, 'maxtargets': 4}
		self.spiral = uidata.UIStruct('Spiral', spiral, 'rw', self.uiSpiralPrefs)
		settingscontainer = uidata.UIContainer('Settings')
		settingscontainer.addUIObjects((self.presetname, self.simulateflag,
																		self.spiral))

		startmethod = uidata.UIMethod('Start', self.runLoop)
		stopmethod = uidata.UIMethod('Stop', self.stopLoop)
		resetmethod = uidata.UIMethod('Reset', self.resetLoop)
		controlcontainer = uidata.UIContainer('Control')
		controlcontainer.addUIObjects((startmethod, stopmethod, resetmethod))

		container = uidata.UIMediumContainer('Grid Preview')
		container.addUIObjects((settingscontainer, controlcontainer))
		self.uiserver.addUIObject(container)

	def setMyPresetData(self):
		presetname = self.presetname.get()
		presetlist = self.presetsclient.retrievePresets(presetname)
		self.presetdata = presetlist[0]

	def uiSpiralPrefs(self, value):
		self.setMyPresetData()
		size = self.presetdata['dimension']['x']
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
		return value

	def uiCalibrate(self):
		pass

	def uiEstimate(self):
		pass

	def getScope(self):
		return self.researchByDataID(('scope',))

	def acquireTarget(self, target):
		print 'TARGET', target
		if self.simulateflag.get():
#			print 'SIMULATED'
			time.sleep(1)
		else:

			if target is None:
				# move to center
				center = self.spiral.get()['center']
				gonpos = {'stage position': {'x':center['x'], 'y':center['y']}}
				emdata = data.ScopeEMData(('scope',), initializer=gonpos)
				print 'moving to center', center
				self.publishRemote(emdata)
			else:
				# move to next postion
				scopestate = self.getScope()

				targetrow, targetcol = target
				print 'targetrow', targetrow
				pixelshift = {'row':targetrow, 'col':targetcol}
				print 'transforming'
				newstate = self.calclient.transform(pixelshift, scopestate, self.presetdata)
				print 'done transforming'
				emdat = data.ScopeEMData(('scope',), initializer=newstate)
				print 'moving to next position'
				self.publishRemote(emdat)

			## this should be calibrated
			time.sleep(2)

			imagedata = self.cam.acquireCameraImageData(camstate=None, correction=True)
			imarray = imagedata['image']
			thisid = self.ID()
			if self.lastid is None:
				neighbortiles = []
			else:
				neighbortiles = [self.lastid,]

			print 'AAAAAAAAAAAAAAAAAAAAAAAAAAAA'

#			filename = self.tilefilename(thisid)
#			Mrc.numeric_to_mrc(imarray, filename)
#			storedata = {'id':thisid,'image':filename, 'state': stagepos, 'neighbors': neighbortiles, 'target':target}
#			self.logAppend(storedata)

			scope = imagedata['scope']
			print 'SCOPE', scope
			camera = imagedata['camera']
			print 'CAMERA', camera
			pdata = copy.deepcopy(self.presetdata)
			print 'PDATA', pdata
			imdata = data.TileImageData(thisid, initializer=imagedata, preset=pdata, neighbor_tiles=neighbortiles)
#			print 'publishing tile'
			print 'PUBLISHING'
			self.publish(imdata, pubevent=True)

			print 'BBBBBBBBBBBBBBBBBBBBB'
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

	def runLoop(self):
		if self.running.isSet():
			self.printerror('loop is already running')
			return
		t = threading.Thread(target=self._loop)
		t.setDaemon(1)
		t.start()

	def resetLoop(self):
		if self.running.isSet():
			self.printerror('cannot reset while loop is running')
		else:
			self.temptodo = list(self.todo)
			self.lastid = None
#			self.logClear()

	def _loop(self):
		self.stoprunning.clear()
		self.running.set()

		presetname = self.presetname.get()
		presetlist = self.presetsclient.retrievePresets(presetname)
		presetdata = presetlist[0]
		self.presetsclient.toScope(presetdata)
		self.outputEvent(event.LockEvent(self.ID()))
		try:
			while self.temptodo and not self.stoprunning.isSet():
				self.next_target()
#			self.logPrint()
		except Exception, detail:
			self.printerror('error while executing loop: ' + str(detail))
		self.outputEvent(event.UnlockEvent(self.ID()))
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
