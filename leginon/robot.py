import scopedict
import tecnai
import win32com.client
import time

class RobotControl(object):
	def __init__(self):
		self.scope = scopedict.factory(tecnai.tecnai)()
		self.communication = win32com.client.Dispatch('RobotCommunications.Signal')

	def __del__(self):
		del self.communication

	def insert(self):
		# verify robot ready for insertion
		print 'Verifying robot ready for insertion',
		while not self.communication.Signal0:
			time.sleep(0.5)
			print '.',
		self.communication.Signal0 = 0
		print 'Done.'

		# verify no holder in scope
		print 'Verifying no holder in scope...',
		if self.scope['holder status'] != 'not inserted':
			raise RuntimeError('holder in already in scope')
		print 'Done.'

		# check if vacuum ready
		print 'Waiting for vacuum to be ready...',
		while self.scope['vacuum status'] != 'ready':
			time.sleep(0.5)
		print 'Done.'

		# close column valves
		print 'Closing column valves...',
		self.scope['column valves'] = 'closed'
		while self.scope['column valves'] != 'closed':
			time.sleep(0.5)
		print 'Done.'

		# turn on turbo pump
		print 'Turning on turbo pump...',
		self.scope['turbo pump'] = 'on'
		while self.scope['turbo pump'] != 'on':
			time.sleep(0.5)
		print 'Done.'
	
		# wait for led to turn off
		print 'Waiting for stage...',
		time.sleep(1.0)
		while self.scope['stage status'] == 'busy':
			time.sleep(0.5)
		print 'Done.'

		# robot: load probe first stage, wait to finish
		print 'Robot, first stage',
		self.communication.Signal1 = 1
		while not self.communication.Signal2:
			time.sleep(0.5)
			print '.',
		self.communication.Signal2 = 0
		print 'Done.'
	
		# set holder type
		print 'Setting holder type to single tilt...',
		self.scope['holder type'] = 'single tilt'
		while self.scope['holder type'] != 'single tilt':
			time.sleep(0.5)
		print 'Done.'

		# wait for led to turn off
		print 'Waiting for stage...',
		time.sleep(1.0)
		while self.scope['stage status'] == 'busy':
			time.sleep(0.5)
		print 'Done.'

		# robot: load probe second stage, retract
		print 'Robot, second stage',
		self.communication.Signal3 = 1
		while not self.communication.Signal4:
			time.sleep(0.5)
			print '.',
		self.communication.Signal4 = 0
		print 'Done.'

		# when done turbo off?

	def extract(self):
		# verify robot ready for extraction
		print 'Verifying robot ready for extraction',
		while not self.communication.Signal5:
			time.sleep(0.5)
			print '.',
		self.communication.Signal5 = 0
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
		print 'Done.'

		# robot: unload probe
		print 'Robot, unload probe',
		self.communication.Signal6 = 1
		while not self.communication.Signal7:
			time.sleep(0.5)
			print '.',
		self.communication.Signal7 = 0
		print 'Done.'

if __name__ == '__main__':
	rc = RobotControl()
	rc.insert()
	rc.extract()
	del rc

