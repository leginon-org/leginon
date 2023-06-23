#!/usr/bin/env python3

import grpc

from optics.v1 import beam_stopper_control_pb2_grpc as bscpg
from utapi_types.v1 import device_id_pb2 as dip

channel = grpc.insecure_channel('localhost:46699', options=[('grpc.max_receive_message_length', 200 * 1024 * 1024)])
beam_stopper = bscpg.BeamStopperControlServiceStub(channel)

import time
from pyscope import simtem

class Utapi(simtem.SimTEM300):
	name = 'Tecnai'
	def __init__(self):
		super(Utapi, self).__init__()
		self.beamstop = bscpg.BeamStopperControlServiceStub(channel)
		self.beamstop_device_id = dip.DeviceIdRequest(id='BeamStopper')

	def getDebugAll(self):
		return True

	def getBeamstopPosition(self):
		state = self.beamstop.GetState(self.beamstop_device_id).__str__()
		print("state: ", state)
		state_map = [('state: inserted\n','in'),('state: retracted\n','out')]
		if state:
			result = state_map[list(map((lambda x: x[0].lower()),state_map)).index(state.lower())][1]
			print(result)
			return result
		# all counted as invalid state
		return 'unknown'

	def setBeamstopPosition(self, value):
		"""
		Possible values: ('in','out','halfway')
		Tecnically tecnai has no software control on this.
		"""
		if value == self.getBeamstopPosition():
			return
		state_map = [('Insert','in'),('Retract','out')]
		attr_name = state_map[list(map((lambda x: x[1].lower()),state_map)).index(value.lower())][0]
		max_trials = 5
		trial = 1
		while value != self.getBeamstopPosition():
			response = getattr(beam_stopper,attr_name)(self.beamstop_device_id)
			print("Insert response: ", response.code, response.message)
			time.sleep(2.0)
			if self.getDebugAll() and trial > 1:
				print('beamstop positioning trial %d' % trial)
			if trial > max_trials:
				raise RuntimeError('Beamstop setting to %s failed %d times' % (value, trial))
			trial += 1

