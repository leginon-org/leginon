import tecnai
import time

class RobotControl(object):
	def __init__(self):
		self.scope = tecnai.tecnai()

	def insert(self):
		# verify robot ready for insertion
		print 'Verifying robot ready for insertion...',
		print 'Done.'

		# verify no holder in scope
		print 'Verifying no holder in scope...',
		if self.scope.getHolderStatus() != 'not inserted':
			raise RuntimeError('holder in already in scope')
		print 'Done.'

		# check if vacuum ready
		print 'Checking if vacuum is ready...',
		print 'Done.'

		# close column valves
		print 'Closing column valves...',
		print 'Done.'

		# turn on turbo pump
		print 'Turning on turbo pump...',
		self.scope.setTurboPump('on')
		while self.scope.getTurboPump() != 'on':
			time.sleep(0.5)
		print 'Done.'
	
		# robot: load probe first stage, wait to finish
		print 'Robot, first stage...',
		print 'Done.'
	
		# set holder type
		print 'Setting holder type to single tilt...',
		self.scope.setHolderType('single tilt')
		while self.scope.getHolderType() != 'single tilt':
			time.sleep(0.5)
		print 'Done.'

		# wait for led to turn off
		print 'Waiting for stage...',
		while self.scope.getStageStatus() != 'busy':
			time.sleep(0.5)
		print 'Done.'

		# robot: load probe second stage, retract
		print 'Robot, second stage...',
		print 'Done.'

		# when done turbo off?

	def extract(self):
		# verify robot ready for extraction
		print 'Verifying robot ready for extraction...',
		print 'Done.'

		# verify holder in scope
		print 'Verifying holder in scope...',
		if self.scope.getHolderStatus() != 'inserted':
			raise RuntimeError('no holder in scope')
		print 'Done.'

		# check if vacuum ready
		print 'Checking if vacuum is ready...',
		print 'Done.'

		# close column valves
		print 'Closing column valves...',
		print 'Done.'

		# robot: unload probe
		print 'Robot, unload probe...',
		print 'Done.'

