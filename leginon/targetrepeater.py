#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import leginondata
import event
import threading
import node
import targethandler
import gui.wx.TargetRepeater
import instrument
import acquisition
import rctacquisition
import player

class TargetRepeater(node.Node, targethandler.TargetWaitHandler):
	panelclass = gui.wx.TargetRepeater.Panel
	settingsclass = leginondata.TargetRepeaterSettingsData
	defaultsettings = {
		'bypass':True,
		'reset a': False,
		'reset z': False,
		'reset xy': False,
	}
	eventinputs = node.Node.eventinputs + targethandler.TargetWaitHandler.eventinputs + [event.ImageTargetListPublishEvent]
	eventoutputs = node.Node.eventoutputs + targethandler.TargetWaitHandler.eventoutputs + [event.TargetListDoneEvent]

	def __init__(self, id, session, managerlocation, **kwargs):
		node.Node.__init__(self, id, session, managerlocation, **kwargs)
		self.userpause = threading.Event()
		targethandler.TargetWaitHandler.__init__(self)
		self.instrument = instrument.Proxy(self.objectservice, self.session)

		self.addEventInput(event.ImageTargetListPublishEvent, self.handleTargetListPublish)
		self.player = player.Player(callback=self.onPlayer)
		self.panel.playerEvent(self.player.state())
		# not yet...
		#self.addEventInput(event.QueuePublishEvent, self.handleQueuePublish)

		self.test = False
		self.abort = False
		if self.__class__ == TargetRepeater:
			self.start()

	def handleTargetListPublish(self, pubevent):
		targetlistdata = pubevent['data']

		if self.settings['bypass']:
			tid = self.makeTargetListEvent(targetlistdata)
			self.publish(targetlistdata, pubevent=True)
			self.setStatus('idle')
			status = self.waitForTargetListDone(tid)
		else:
			self.player.pause()
			self.repeatTargetList(targetlistdata)
			status = 'ok'

		self.markAllTargetsDone(targetlistdata)

		e = event.TargetListDoneEvent(targetlistid=targetlistdata.dbid, status=status)
		self.outputEvent(e)
		self.logger.info('All targets and states done')

	def makeStates(self):
		pass

	def onContinue(self):
		self.player.play()
		self.userpause.set()

	def repeatTargetList(self, targetlistdata):
		states = self.makeStates()
		self.logger.info('repeating target at %d states' % (len(states),))
		for scopedata in states:
			self.setStatus('idle')
			self.setStatus('user input')
			self.logger.info('Continue to next state? waiting for user...')
			self.userpause.clear()
			self.player.pause()
			self.userpause.wait()
			self.player.play()
			self.setStatus('processing')

			self.instrument.setData(scopedata)
			newtargetlistdata = self.copyTargetList(targetlistdata)
			if newtargetlistdata is None:
				break

			# declare transform:
			self.declareTransform(self.transformtype)

			tid = self.makeTargetListEvent(newtargetlistdata)
			self.setStatus('waiting')
			self.publish(newtargetlistdata, pubevent=True)
			status = self.waitForTargetListDone(tid)
			state = self.player.wait()
			if state in ('stop'):
				self.logger.info('Aborting')
				break
		self.resetStage()
		self.setStatus('idle')

	def resetStage(self):
		axes = {'a': {'a': 0}, 'z': {'z':0}, 'xy': {'x': 0, 'y': 0}}
		for axis, position in axes.items():
			setting = 'reset ' + axis
			if self.settings[setting]:
				self.logger.info('resetting stage %s' % (axis,))
				try:
					self.instrument.tem.StagePosition = position
				except:
					self.logger.error('reset stage %s failed' % (axis,))

	def markAllTargetsDone(self, targetlistdata):
			alltargets = self.researchTargets(list=targetlistdata)
			donetargets = []
			for target in alltargets:
				if target['status'] not in ('done', 'aborted'):
					donetargets.append(target)
			self.markTargetsDone(donetargets)

	def copyTargetList(self, targetlistdata):
			#make and publish new targetlist
			alltargets = self.researchTargets(list=targetlistdata)
			newtargetlistdata = self.newTargetList()
			newtargetlistdata.update(targetlistdata)
			self.publish(newtargetlistdata, database=True, dbforce=True)
			#fill the list with targets
			newtargets = []
			newimages = {}
			for target in alltargets:
				if target['status'] not in ('done', 'aborted'):
					parentimage = target.special_getitem('image',readimages=False,dereference=True)
					parentid = parentimage.dbid
					if parentid not in newimages.keys():
						newimagedata = self.copyImage(parentimage)
						newimages[parentid] = newimagedata
					else:
						newimagedata = newimages[parentid]
					newtarget = leginondata.AcquisitionImageTargetData(initializer=target)
					newtarget['fromtarget'] = target
					newtarget['list'] = newtargetlistdata
					newtarget['image'] = newimagedata
					newtarget.insert(force=True)
					newtargets.append(newtarget)
			if newtargets:
				return newtargetlistdata
			else:
				return None

	def copyImage(self, oldimage):
		imagedata = leginondata.AcquisitionImageData()
		imagedata.update(oldimage)
		version = self.recentImageVersion(oldimage)
		imagedata['version'] = version + 1
		imagedata['filename'] = None
		imagedata['image'] = oldimage['image']
		## set the 'filename' value
		if imagedata['label'] == 'RCT':
			rctacquisition.setImageFilename(imagedata)
		else:
			acquisition.setImageFilename(imagedata)
		self.logger.info('Publishing new copied image...')
		self.publish(imagedata, database=True)
		return imagedata

	def recentImageVersion(self, imagedata):
		# find most recent version of this image
		p = leginondata.PresetData(name=imagedata['preset']['name'])
		q = leginondata.AcquisitionImageData()
		q['session'] = imagedata['session']
		q['target'] = imagedata['target']
		q['list'] = imagedata['list']
		q['preset'] = p
		allimages = q.query()
		version = 0
		for im in allimages:
			if im['version'] > version:
				version = im['version']
		return version

	def onPlayer(self, state):
		infostr = ''
		if state == 'play':
			infostr += ''
		elif state == 'stop':
			infostr += 'Aborting...'
		if infostr:
			self.logger.info(infostr)
		self.panel.playerEvent(state)
