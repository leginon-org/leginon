#!/usr/bin/env python3

import grpc
from google.protobuf import json_format as json_format

# requests builders
from utapi_types.v1 import device_id_pb2 as dip
from optics.v1 import aperture_mechanism_control_pb2 as apmc_p
from column.v1 import column_mode_pb2 as cm_p
from column.v1 import normalization_pb2 as norm_p

# used to create stub for access
from optics.v1 import beam_stopper_control_pb2_grpc as bstop_pg
from optics.v1 import aperture_mechanism_control_pb2_grpc as apmc_pg
from optics.v1 import deflectors_pb2_grpc as defl_pg
from optics.v1 import focus_pb2_grpc as foc_pg
from optics.v1 import illumination_pb2_grpc as illu_pg
from optics.v1 import magnification_pb2_grpc as mag_pg
from optics.v1 import optics_pb2_grpc as optics_pg
from optics.v1 import stigmator_pb2_grpc as stig_pg
from optics.v1 import x_lens_alignments_pb2_grpc as xlens_pg
from column.v1 import column_mode_pb2_grpc as cm_pg
from column.v1 import normalization_pb2_grpc as norm_pg

# Can we connect remotely ?
channel = grpc.insecure_channel('localhost:46699', options=[('grpc.max_receive_message_length', 200 * 1024 * 1024)])

bstop_stub = bstop_pg.BeamStopperControlServiceStub(channel)
apmc_stub = apmc_pg.ApertureMechanismControlServiceStub(channel)
defl_stub = defl_pg.DeflectorsServiceStub(channel)
foc_stub = foc_pg.FocusServiceStub(channel)
illu_stub = illu_pg.IlluminationServiceStub(channel)
mag_stub = mag_pg.MagnificationServiceStub(channel)
optics_stub =  optics_pg.OpticsServiceStub(channel)
stig_stub = stig_pg.StigmatorServiceStub(channel)
xlens_stub = xlens_pg.XLensAlignmentsServiceStub(channel)
cm_stub = cm_pg.ColumnModeServiceStub(channel)
norm_stub = norm_pg.NormalizationServiceStub(channel)

cm_probe_mode_map = [('micro','PROBE_MODE_MICRO_PROBE'),('nano', 'PROBE_MODE_NANO_PROBE')]

def handleRpcError(e):
	if e.code() == grpc.StatusCode.ABORTED:
		utapi_response = urp.UtapiResponse()
		utapi_response.ParseFromString(e.trailing_metadata()[0][1])
		print(f"Error with UtapiResponse>\n{utapi_response}<")
	else:
		# Not an UtapiResponse. rethrow exception
		raise

def _response_to_dict(response):
	return json_format.MessageToDict(response)

def _get_by_request(stub,attr_name,request):
	my_attr = getattr(stub,attr_name)
	try:
		# perform my_attr action on the request and convert to list and dict
		return _response_to_dict(my_attr(request))
	except grpc.RpcError as rpc_error:
		handleRpcError(rpc_error)

def _set_by_request(stub, attr_name, request):
	my_attr = getattr(stub,attr_name)
	try:
		# perform my_attr action on the request
		my_attr(request)
	except grpc.RpcError as rpc_error:
		handleRpcError(rpc_error)


import time
from pyscope import fei

class Utapi(fei.Krios):
	name = 'Utapi'
	def __init__(self):
		super(Utapi, self).__init__()
		self.beamstop_device_id = dip.DeviceIdRequest(id='BeamStopper')

	def getDebugAll(self):
		return True

	def getBeamstopPosition(self):
		try:
			state_dict = _get_by_request(bstop_stub,'GetState',self.beamstop_device_id)
			state_short = state_dict['state']
			print(state_short)
		except Exception as e:
			print(e)
			return 'unknown'
		state_map = [('inserted','in'),('retracted','out'),('moving','moving'),('inserted_halfway','halfway'),('undefined','unknown')]
		try:
			result = state_map[list(map((lambda x: x[0].lower()),state_map)).index(state_short.lower())][1]
			return result
		except Exception as e:
			print(e)
			return 'unknown'

	def setBeamstopPosition(self, value):
		"""
		Possible values: ('in','out','halfway')
		"""
		if value == self.getBeamstopPosition():
			return
		state_map = [('Insert','in'),('Retract','out'),('InsertedHalfway','halfway')]
		attr_name = state_map[list(map((lambda x: x[1].lower()),state_map)).index(value.lower())][0]
		max_trials = 5
		trial = 1
		while value != self.getBeamstopPosition():
			_set_by_request(bstop_stub, attr_name, self.beamstop_device_id)
			time.sleep(0.5)
			if self.getDebugAll() and trial > 1:
				print('beamstop positioning trial %d' % trial)
			if trial > max_trials:
				raise RuntimeError('Beamstop setting to %s failed %d times' % (value, trial))
			trial += 1

	def _getApertureMechanismId(self, mechanism_name):
		if mechanism_name == 'condenser':
			# always look up condenser 2 value
			mechanism_name = 'condenser_2'
		mechanism_id = mechanism_name[0].upper()+mechanism_name[1:].replace('_',' ')
		return mechanism_id

	def getApertureSelections(self, mechanism_name):
		'''
		get valid selection for an aperture mechanism to be used in gui,including "open" if available.
		'''
		mechanism_id = self._getApertureMechanismId(mechanism_name)
		# use the name-specified request
		my_request = apmc_p.GetApertureCollectionRequest(
			device_id=dip.DeviceId(id=mechanism_id),
			)
		results = _get_by_request(apmc_stub,'GetApertureCollection',my_request)
		names = list(map((lambda x: str(x['apertureName'])),results['apertures']))
		return names

	def getApertureSelection(self, mechanism_name):
		mechanism_id = self._getApertureMechanismId(mechanism_name)
		my_request = dip.DeviceId(id=mechanism_id)
		#TODO check if the mechanism is retracted.
		# Retracted mechanism will get error in the next statement
		# return "open"
		result = _get_by_request(apmc_stub,'GetSelectedAperture',my_request)
		print(result)
		return result['apertureName']

	def setApertureSelection(self, mechanism_name, name):
		#TODO handle open position
		all_names = self.getApertureSelections(mechanism_name)
		if name not in all_names:
			raise RuntimeError('Invalid aperture %s' % (name))
		mechanism_id = self._getApertureMechanismId(mechanism_name)
		my_request = apmc_p.SelectApertureRequest(device_id=dip.DeviceId(id=mechanism_id),aperture_name=name)
		_set_by_request(apmc_stub, 'SelectAperture', my_request)

	# column modes
	def _get_column_modes(self):
		results = _get_by_request(cm_stub,'GetColumnModes',cm_p.ColumnModeRequest())
		return results

	def getProbeModes(self):
		mode_names = list(map((lambda x: x[0]),cm_probe_mode_map))
		return mode_names

	def getProbeMode(self):
		all_modes = self._get_column_modes()
		try:
			value = cm_probe_mode_map[list(map((lambda x:x[1]),cm_probe_mode_map)).index(all_modes['probeMode'])][0]
		except:
			raise
		return value

	def setProbeMode(self, value):
		try:
			my_index = self.getProbeModes().index(value)
		except ValueError:
			raise RuntimeError('Invalid probe mode %s' % (value))
		my_mode = getattr(cm_p,cm_probe_mode_map[my_index][1])
		my_request =cm_p.ProbeModeRequest(probe_mode=my_mode)
		_set_by_request(cm_stub, 'SetProbeMode', my_request)
