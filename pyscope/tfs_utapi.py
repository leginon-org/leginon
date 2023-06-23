#!/usr/bin/env python3

import grpc

# used to find device id name
from utapi_types.v1 import device_id_pb2 as dip

from optics.v1 import beam_stopper_control_pb2_grpc as bscpg
from optics.v1 import aperture_mechanism_control_pb2 as amcp
from optics.v1 import aperture_mechanism_control_pb2_grpc as amcpg


channel = grpc.insecure_channel('localhost:46699', options=[('grpc.max_receive_message_length', 200 * 1024 * 1024)])
beam_stopper = bscpg.BeamStopperControlServiceStub(channel)
aperture_mechanism = amcpg.ApertureMechanismControlServiceStub(channel)

def handleRpcError(e):
	if e.code() == grpc.StatusCode.ABORTED:
		utapi_response = urp.UtapiResponse()
		utapi_response.ParseFromString(e.trailing_metadata()[0][1])
		print(f"Error with UtapiResponse>\n{utapi_response}<")
	else:
		# Not an UtapiResponse. rethrow exception
		raise

import time
from pyscope import fei

class Utapi(fei.Krios):
	name = 'Utapi'
	def __init__(self):
		super(Utapi, self).__init__()
		self.beamstop = bscpg.BeamStopperControlServiceStub(channel)
		self.beamstop_device_id = dip.DeviceIdRequest(id='BeamStopper')

	def getDebugAll(self):
		return True

	def getBeamstopPosition(self):
		state = self.beamstop.GetState(self.beamstop_device_id).__str__()
		state_short = state[:state.index('\n')]
		state_map = [('state: inserted','in'),('state: retracted','out')]
		if state:
			result = state_map[list(map((lambda x: x[0].lower()),state_map)).index(state_short.lower())][1]
			return result
		else:
			print('no state returned')
			return 'unknown'
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
			my_attr = getattr(beam_stopper,attr_name)
			try:
				my_attr(self.beamstop_device_id)
			except grpc.RpcError as rpc_error:
				handleRpcError(rpc_error)
			time.sleep(0.5)
			if self.getDebugAll() and trial > 1:
				print('beamstop positioning trial %d' % trial)
			if trial > max_trials:
				raise RuntimeError('Beamstop setting to %s failed %d times' % (value, trial))
			trial += 1

	def getApertureSelections(self, mechanism_name):
		'''
		get valid selection for an aperture mechanism to be used in gui,including "open" if available.
		'''
		if mechanism_name == 'condenser':
			# always look up condenser 2 value
			mechanism_name = 'condenser_2'
		mechanism_id = mechanism_name[0].upper()+mechanism_name[1:].replace('_',' ')
		aperture_collection_request = amcp.GetApertureCollectionRequest(
			device_id=dip.DeviceId(id=mechanism_id),
			#aperture_type=amcp.ApertureType.APERTURE_TYPE_CIRCULAR)
			)
		try:
			aperture_collection = aperture_mechanism.GetApertureCollection(aperture_collection_request)
		except Exception as e:
			if e.code() == grpc.StatusCode.ABORTED:
				print("aperture mechnism '%s' not available to control" % mechanism_name)
				return []
		print("aperture_collection: ", aperture_collection)
		aperture_collection_str = str(aperture_collection)

		# This may be string or integer.
		aperture_list = aperture_collection_str.split('aperture_name: ')[1:]

		names = list(map((lambda x: str(x.split('"')[1])),aperture_list))

		#TODO check if the mechanism can be retracted.
		return names
