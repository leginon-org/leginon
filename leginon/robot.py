import win32com.client
import time
import pywintypes
import sys
import node
import data
import uidata
import event
import threading

#class Test(object):
#	def __init__(self):
#		self.Signal0 = 1
#		self.Signal1 = 1
#		self.Signal2 = 1
#		self.Signal3 = 1
#		self.Signal4 = 1
#		self.Signal5 = 1
#		self.Signal6 = 1
#		self.Signal7 = 1

class RobotControl(node.Node):
	def __init__(self, id, session, nodelocations, **kwargs):
		node.Node.__init__(self, id, session, nodelocations, **kwargs)

		self.extractok = False
		self.extractlock = threading.Lock()

		#self.scope = scopedict.factory(tecnai.tecnai)()
		#self.communication = Test()

		try:
			self.communication = win32com.client.Dispatch('RobotCommunications.Signal')


		except pywintypes.com_error:
			raise RuntimeError('Cannot initialized robot communications')
		self.statushistory = []
		self.statusindex = -1
		self.statuslength = 50

		self.addEventInput(event.ExtractGridEvent, self.handleExtract)

		self.defineUserInterface()
		self.start()

	def __del__(self):
#		self.scope = None
		self.communication = None

	def condition(self, parameter, value, signal=None, poll=False,
								interval=0.5, timeout=0.0):
		parametervalue = self.getScope(parameter)
		print parameter, parametervalue, value
		elapsed = 0.0
		if poll:
			while parametervalue != value:
				time.sleep(interval)
				if timeout > 0.0:
					elapsed += interval
					if elapsed > timeout:
						raise RuntimeError('parameter is not set to value')
				parametervalue = self.getScope(parameter)
				print parameter, parametervalue, value
		else:
			if parametervalue != value:
				raise RuntimeError('parameter is not set to value')
		if signal is not None:
			signal = 1

	def getScope(self, key):
		parameterdata = self.researchByDataID((key,))
		if parameterdata is None:
			raise RuntimeError('cannot get parameter value')
		return parameterdata[key]

	def setScope(self, key, value):
		scopedata = data.ScopeEMData()
		scopedata['id'] = ('scope',)
		scopedata[key] = value
		try:
			self.publishRemote(scopedata)
		except node.PublishError:
			raise RuntimeError('cannot set parameter to value')

	def setStatus(self, message):
		self.statushistory.append(message)
		if len(self.statushistory) > self.statuslength:
			try:
				self.statushistory = self.statushistory[-self.statuslength:]
			except IndexError:
				pass
		self.statuslabel.set(message)

	def insertStage(self):
		self.insertmethod.disable()
		self.extractmethod.disable()
		self.setStatus('Verifying robot is ready for insertion')
		while not self.communication.Signal0:
			time.sleep(0.5)
		self.communication.Signal0 = 0
		self.setStatus('Robot is ready for insertion')

#		self.setStatus('Zeroing stage position')
#		self.setScope('stage position', {'x': 0.0, 'y': 0.0, 'z': 0.0, 'a': 0.0})
#		self.setStatus('Verifying stage position is zeroed')
#		self.condition('stage position', {'x': 0.0, 'y': 0.0, 'z': 0.0, 'a': 0.0},
#										None, True, 0.5, 15)
#		self.setStatus('Stage position is zeroed')

		self.setStatus('Verifying there is no holder inserted')
		self.condition('holder status', 'not inserted')
		self.setStatus('No holder currently inserted')

		self.setStatus('Verifying vacuum is ready')
		self.condition('vacuum status', 'ready', None, True, 0.5, 600)
		self.setStatus('Vacuum is ready')

		self.setStatus('Closing column valves')
		self.setScope('column valves', 'closed')
		self.setStatus('Verifying column valves are closed')
		self.condition('column valves', 'closed', None, True, 0.5, 15)
		self.setStatus('Column valves are closed')

		self.setStatus('Turning on turbo pump')
		self.setScope('turbo pump', 'on')
		self.setStatus('Verifying turbo pump is on')
		self.condition('turbo pump', 'on', None, True, 0.5, 15)
		self.setStatus('Turbo pump is on')

		self.setStatus('Waiting for stage to be ready')
		self.condition('stage status', 'ready', self.communication.Signal1,
										True, 0.5, 600)
		self.setStatus('Stage is ready, signaled robot to begin insertion step 1')

		self.communication.Signal1 = 1

		self.setStatus('Waiting for robot to complete insertion step 1')
		while not self.communication.Signal2:
			time.sleep(0.5)
		self.communication.Signal2 = 0
		self.setStatus('Robot has completed insertion step 1')

		self.setStatus('Setting holder type to single tilt')
		self.setScope('holder type', 'single tilt')
		self.setStatus('Verifying holder type is set to single tilt')
		self.condition('holder type', 'single tilt', None, True, 0.5, 60)
		self.setStatus('Holder type is set to single tilt')

		self.setStatus('Waiting for stage to be ready')
		self.condition('stage status', 'ready', self.communication.Signal3,
										True, 0.5, 600)
		self.setStatus('Stage is ready, signaled robot to begin insertion step 2')

		self.communication.Signal3 = 1

		self.setStatus('Waiting for robot to complete insertion step 2')
		while not self.communication.Signal4:
			time.sleep(0.5)
		self.communication.Signal4 = 0
		self.setStatus('Robot has completed insertion step 2')
		self.setStatus('Robot has completed insertion')
		self.insertmethod.enable()
		self.extractmethod.enable()
		evt = event.GridInsertedEvent()
		evt['grid number'] = -1
		self.outputEvent(evt)

	def handleExtract(self, ievent):
		self.extract()

	def extractStage(self):
		self.insertmethod.disable()
		self.extractmethod.disable()
		self.setStatus('Verifying robot is ready for extraction')
		while not self.communication.Signal5:
			time.sleep(0.5)
		self.communication.Signal5 = 0
		self.setStatus('Robot is ready for extraction')

#		self.setStatus('Zeroing stage position')
#		self.setScope('stage position', {'x': 0.0, 'y': 0.0, 'z': 0.0, 'a': 0.0})
#		self.setStatus('Verifying stage position is zeroed')
#		self.condition('stage position', {'x': 0.0, 'y': 0.0, 'z': 0.0, 'a': 0.0},
#										None, True, 0.5, 15)
#		self.setStatus('Stage position is zeroed')

		self.setStatus('Verifying holder is inserted')
		self.condition('holder status', 'inserted')
		self.setStatus('Holder is currently inserted')

		self.setStatus('Verifying vacuum is ready')
		self.condition('vacuum status', 'ready', None, True, 0.5, 600)
		self.setStatus('Vacuum is ready')

		self.setStatus('Closing column valves')
		self.setScope('column valves', 'closed')
		self.setStatus('Verifying column valves are closed')
		self.condition('column valves', 'closed', None, True, 0.5, 15)
		self.setStatus('Column valves are closed')

		self.setStatus('Waiting for stage to be ready')
		self.condition('stage status', 'ready', self.communication.Signal6,
										True, 0.5, 600)
		self.setStatus('Stage is ready, signaled robot to begin extraction')

		self.communication.Signal6 = 1

		self.setStatus('Waiting for robot to complete extraction')
		while not self.communication.Signal7:
			time.sleep(0.5)
		self.communication.Signal7 = 0
		self.setStatus('Robot has completed extraction')

		self.extractlock.acquire()
		self.extractok = True
		self.extractlock.release()

		self.insertmethod.enable()
		self.extractmethod.enable()

	def insert(self):
		self.setStatus('Inserting stage')
		try:
			self.insertStage()
		except RuntimeError:
			self.setStatus('Error inserting stage')

	def extract(self):
		self.extractlock.acquire()
		if self.extractok:
			self.extractok = False
			self.extractlock.release()

			self.setStatus('Extracting stage')
			try:
				self.extractStage()
			except RuntimeError:
				self.setStatus('Error extracting stage')
		else:
			self.extractlock.release()

	def defineUserInterface(self):
		node.Node.defineUserInterface(self)

		self.statuslabel = uidata.String('Current Operation', '', 'r')
		statuscontainer = uidata.Container('Status')
		statuscontainer.addObjects((self.statuslabel,))

		self.insertmethod = uidata.Method('Insert', self.insert)
		self.extractmethod = uidata.Method('Extract', self.extract)
		controlcontainer = uidata.Container('Control')
		controlcontainer.addObjects((self.insertmethod, self.extractmethod))

		rccontainer = uidata.MediumContainer('Robot Control')
		rccontainer.addObjects((statuscontainer, controlcontainer))
		self.uiserver.addObject(rccontainer)

'''
	def insert(self):
		# verify robot ready for insertion
		print 'Verifying robot ready for insertion...',
		while not self.communication.Signal0:
			time.sleep(0.5)
			sys.stdout.softspace = 0
			print '.',
		self.communication.Signal0 = 0
		sys.stdout.softspace = 0
		print 'Done.'

		# verify no holder in scope
		print 'Verifying no holder in scope...',
		if self.scope['holder status'] != 'not inserted':
			raise RuntimeError('holder in already in scope')
		sys.stdout.softspace = 0
		print 'Done.'

		# check if vacuum ready
		print 'Waiting for vacuum to be ready...',
		while self.scope['vacuum status'] != 'ready':
			time.sleep(0.5)
			sys.stdout.softspace = 0
			print '.',
		sys.stdout.softspace = 0
		print 'Done.'

		# close column valves
		print 'Closing column valves...',
		self.scope['column valves'] = 'closed'
		while self.scope['column valves'] != 'closed':
			time.sleep(0.5)
			sys.stdout.softspace = 0
			print '.',
		sys.stdout.softspace = 0
		print 'Done.'

		# turn on turbo pump
		print 'Turning on turbo pump...',
		self.scope['turbo pump'] = 'on'
		while self.scope['turbo pump'] != 'on':
			time.sleep(0.5)
			sys.stdout.softspace = 0
			print '.',
		sys.stdout.softspace = 0
		print 'Done.'
	
		# wait for led to turn off
		print 'Waiting for stage...',
		time.sleep(1.0)
		while self.scope['stage status'] == 'busy':
			time.sleep(0.5)
			sys.stdout.softspace = 0
			print '.',
		sys.stdout.softspace = 0
		print 'Done.'

		# robot: load probe first stage, wait to finish
		print 'Robot, first stage...',
		self.communication.Signal1 = 1
		while not self.communication.Signal2:
			time.sleep(0.5)
			sys.stdout.softspace = 0
			print '.',
		self.communication.Signal2 = 0
		sys.stdout.softspace = 0
		print 'Done.'
	
		# set holder type
		print 'Setting holder type to single tilt...',
		self.scope['holder type'] = 'single tilt'
		while self.scope['holder type'] != 'single tilt':
			time.sleep(0.5)
			sys.stdout.softspace = 0
			print '.',
		sys.stdout.softspace = 0
		print 'Done.'

		# wait for led to turn off
		print 'Waiting for stage...',
		time.sleep(1.0)
		while self.scope['stage status'] == 'busy':
			time.sleep(0.5)
			sys.stdout.softspace = 0
			print '.',
		sys.stdout.softspace = 0
		print 'Done.'

		# robot: load probe second stage, retract
		print 'Robot, second stage',
		self.communication.Signal3 = 1
		while not self.communication.Signal4:
			time.sleep(0.5)
			sys.stdout.softspace = 0
			print '.',
		self.communication.Signal4 = 0
		sys.stdout.softspace = 0
		print 'Done.'

		# when done turbo off?

	def extract(self):
		# verify robot ready for extraction
		print 'Verifying robot ready for extraction...',
		while not self.communication.Signal5:
			time.sleep(0.5)
			sys.stdout.softspace = 0
			print '.',
		self.communication.Signal5 = 0
		sys.stdout.softspace = 0
		print 'Done.'

		# verify holder in scope
		print 'Verifying holder in scope...',
		if self.scope['holder status'] == 'inserted':
			raise RuntimeError('no holder in scope')
		print 'Done.'

		# check if vacuum ready
		print 'Checking if vacuum is ready...',
		while self.scope['vacuum status'] != 'ready':
			time.sleep(0.5)
			sys.stdout.softspace = 0
			print '.',
		sys.stdout.softspace = 0
		print 'Done.'

		# close column valves
		print 'Closing column valves...',
		self.scope['column valves'] = 'closed'
		if self.scope['column valves'] != 'closed':
			raise RuntimeError('cannot close column valves')
		print 'Done.'

		# wait for led to turn off
		print 'Waiting for stage...',
		time.sleep(1.0)
		while self.scope['stage status'] == 'busy':
			time.sleep(0.5)
			sys.stdout.softspace = 0
			print '.',
		sys.stdout.softspace = 0
		print 'Done.'

		# robot: unload probe
		print 'Robot, unload probe...',
		self.communication.Signal6 = 1
		while not self.communication.Signal7:
			time.sleep(0.5)
			sys.stdout.softspace = 0
			print '.',
		self.communication.Signal7 = 0
		sys.stdout.softspace = 0
		print 'Done.'

if __name__ == '__main__':
	rc = RobotControl()
	rc.insertStage()
	rc.extractStage()
	del rc

'''

