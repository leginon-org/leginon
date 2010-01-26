#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import leginondata
import instrument
import node
import socket
import threading
import gui.wx.Instrument
from pyscope import tem, ccdcamera, registry
import sys
if sys.platform == 'win32':
	import pythoncom

class EM(node.Node):
	panelclass = gui.wx.Instrument.Panel
	def __init__(self, name, session, managerlocation, tcpport=None, **kwargs):

		self.instruments = {}

		self.pauses = {
			'magnification':  1.5,
			'spot size': 0.4,
			'image shift': 0.2,
			'beam shift': 0.1,
			'defocus': 0.4,
			'focus': 0.4,
			'intensity': 0.1,
			'main screen position': 1.0,
		}

		node.Node.__init__(self, name, session, managerlocation, **kwargs)

		# the handler thread waits for queue requests and processes them
		# scope and camera are typically COM objects and need to be initialized
		# in this thread
		self.exitevent = threading.Event()
		self.handlerthread = threading.Thread(name='EM handler thread',
																					target=self.handler)
		self.handlerthread.start()
		#self.handler()

	def exit(self):
		node.Node.exit(self)
		''' 
		for i in self.instruments:
			try:
				i.exit()
			except:
				pass
		''' 
		self.instruments = {}
		self.exitevent.set()

	def handler(self):
		classes = registry.getClasses()
		tems = []
		ccdcameras = []
		fastccdcameras = []
		for i in classes:
			name, c = i
			if issubclass(c, tem.TEM):
				tems.append(i)
			elif issubclass(c, ccdcamera.FastCCDCamera):
				fastccdcameras.append(i)
			elif issubclass(c, ccdcamera.CCDCamera):
				ccdcameras.append(i)
		for name, c in tems + ccdcameras + fastccdcameras:
			if issubclass(c, tem.TEM):
				instrumentclass = instrument.TEM
				wxaddmethod = self.panel.addTEM
			elif issubclass(c, ccdcamera.FastCCDCamera):
				instrumentclass = instrument.FastCCDCamera
				wxaddmethod = self.panel.addCCDCamera
			elif issubclass(c, ccdcamera.CCDCamera):
				instrumentclass = instrument.CCDCamera
				wxaddmethod = self.panel.addCCDCamera

			class ObjectClass(c, instrumentclass):
				def __init__(self):
					self._hostname = socket.gethostname().lower()
					c.__init__(self)
					instrumentclass.__init__(self)

				def getHostname(self):
					return self._hostname

			tries = 3
			instance = None
			for i in range(1,tries+1):
				try:
					instance = ObjectClass()
					self.instruments[name] = instance
					self.objectservice._addObject(name, instance)
					self.logger.info('Added interface for %s' % name)
					break
				except Exception, e:
					self.logger.debug('Initialization of %s failed: %s' % (name, e))
					continue
			if instance is None:
				continue

			if self.hasMagnifications(name):
				self.initializeMagnifications(name)

			wxaddmethod(name)
		if not self.instruments:
			self.logger.warning('No interfaces could be initiailized')

		self.start()

		# exiting this thread seems to disconnect the COM servers
		self.exitevent.wait()

	def hasMagnifications(self, name):
		try:
			instance = self.instruments[name]
		except KeyError:
			raise ValueError('no instrument %s' % name)
		if not hasattr(instance, 'getMagnificationsInitialized'):
			return False
		if not hasattr(instance, 'setMagnifications'):
			return False
		return True

	def initializeMagnifications(self, name):
		try:
			instance = self.instruments[name]
		except KeyError:
			raise ValueError('no instrument %s' % name)
		if instance.getMagnificationsInitialized():
			return
		instrumentdata = leginondata.InstrumentData()
		instrumentdata['name'] = name
		instrumentdata['hostname'] = instance.getHostname()
		queryinstance = leginondata.MagnificationsData()
		queryinstance['instrument'] = instrumentdata
		try:
			result = self.research(queryinstance, results=1)[0]
		except IndexError:
			self.logger.warning('No magnifications saved for %s' % name)
			return
		instance.setMagnifications(result['magnifications'])

	def getMagnifications(self, name):
		try:
			instance = self.instruments[name]
		except KeyError:
			raise ValueError('no instrument %s' % name)
		self.logger.info('Getting magnifications from the instrument...')
		instance.findMagnifications()
		self.logger.info('Saving...')
		instrumentdata = leginondata.InstrumentData()
		instrumentdata['name'] = name
		instrumentdata['hostname'] = instance.getHostname()
		magnificationsdata = leginondata.MagnificationsData()
		magnificationsdata['instrument'] = instrumentdata
		magnificationsdata['magnifications'] = instance.getMagnifications()
		self.publish(magnificationsdata, database=True, dbforce=True)
		self.logger.info('Magnifications saved.')
		self.panel.onGetMagnificationsDone()

	def resetDefocus(self, name):
		self.instruments[name]._execute(self.name, 'resetDefocus', 'method')

	def refresh(self, name, attributes):
		# hack
		self.logger.info('Refreshing parameters for %s...' % name)
		try:
			instrument = self.instruments[name]
		except KeyError:
			self.logger.info('Refreshing failed.' % name)
			return
		values = {}
		instrument.lock(self.name)
		try:
			if isinstance(attributes, list):
				for attribute in attributes:
					try:
						value = instrument._execute(self.name, attribute, 'r')
						if isinstance(value, Exception):
							raise
						else:
							values[attribute] = value
					except TypeError:
						# in theory this is an invalid execution name
						pass
					except:
						self.logger.warning('Failed to refresh attribute \'%s\''
																% attribute)
			elif isinstance(attributes, dict):
				for attribute, value in attributes.items():
					try:
						value = instrument._execute(self.name, attribute, 'w', (value,))
						if isinstance(value, Exception):
							raise
						else:
							values[attribute] = value
						value = instrument._execute(self.name, attribute, 'r')
						if isinstance(value, Exception):
							raise
						else:
							values[attribute] = value
					except TypeError:
						# in theory this is an invalid execution name
						pass
					except AttributeError:
						self.logger.warning('Failed to refresh attribute \'%s\''
																% attribute)
			else:
				pass
		finally:
			instrument.unlock(self.name)
		self.panel.setParameters(name, values)
		self.logger.info('Refresh completed.')

