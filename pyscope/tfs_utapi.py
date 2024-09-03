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

class Logger(object):
	def __init__(self,logtype=''):
		self.level = 0
		if logtype:
			self.logtype = logtype.upper()+' '

	def setLever(self,value):
		self.level = value

	def info(self, msg):
		if self.level >= 1:
			print('%sINFO: %s' % (self.logtype,msg))

	def warning(self, msg):
		if self.level >= 1:
			print('%sWARNING: %s' % (self.logtype,msg))

	def debug(self, msg):
		if self.level >= 3:
			print('%sDEBUG: %s' % (self.logtype,msg))

	def error(self, msg):
		if self.level >= 1:
			print('%sERROR: %s' % (self.logtype,msg))

class Utapi(fei.Krios):
	name = 'Utapi'
	# (pyscope value, utapi CONSTANT)
	cm_projection_mode_map = [	('imaging','PROJECTION_MODE_IMAGING'),
							('diffraction', 'PROJECTION_MODE_DIFFRACTION')
	]
	cm_objective_mode_map = [	('lm','OBJECTIVE_MODE_LM'),
							('hm', 'OBJECTIVE_MODE_HM')
	]
	cm_objective_sub_mode_map = [	('lm','OBJECTIVE_MODE_LM'),
							('hm', 'OBJECTIVE_MODE_HM')
	]
	cm_probe_mode_map = [	('micro','PROBE_MODE_MICRO_PROBE'),
							('nano', 'PROBE_MODE_NANO_PROBE')
	]
	# (pyscope value, utapi Method)
	bstop_attr_map = [	('in','Insert'),
						('out','Retract'),
						('halfway','InsertedHalfway')
	]
	def __init__(self):
		super(Utapi, self).__init__()
		self.beamstop_device_id = dip.DeviceIdRequest(id='BeamStopper')
		self.logger = Logger()
		self.stage_logger = Logger()
		if self.getDebugAll():
			self.logger.setLevel(3)
			self.stage_logger.setLevel(3)

	def getDebugAll(self):
		return True

	def getBeamstopPosition(self):
		self.logger.debug('---getBeamstopPosition---')
		try:
			state_dict = _get_by_request(bstop_stub,'GetState',self.beamstop_device_id)
			self.logger.debug('GetState result: %s' % state_dict)
			state_short = state_dict['state']
		except Exception as e:
			self.logger.debug(e)
			return 'unknown'
		state_map = list(map((lambda x: (x[0],x[1].upper())),self.bstop_attr_map))
		state_map.extend([('moving','MOVING'),('halfway','INSERTED_HALFWAY'),('unknown','UNDEFINED')])
		try:
			result = state_map[list(map((lambda x: x[1]),state_map)).index(state_short)][0]
			return result
		except Exception as e:
			self.logger.debug(e)
			return 'unknown'

	def setBeamstopPosition(self, value):
		"""
		Possible values: ('in','out','halfway')
		"""
		self.logger.debug('---setBeamstopPosition---')
		if value == self.getBeamstopPosition():
			return
		accepted_values = ['in','out']
		if value not in accepted_values:
				raise ValueError('Beamstop setting to %s not possible' % value)
		attr_name = self.bstop_attr_map[list(map((lambda x: x[0].lower()),self.bstop_attr_map)).index(value.lower())][1]
		# try 5 times
		max_trials = 5
		trial = 1
		while value != self.getBeamstopPosition():
			_set_by_request(bstop_stub, attr_name, self.beamstop_device_id)
			time.sleep(0.5)
			if trial > 1:
				self.logger.debug('beamstop positioning trial %d' % trial)
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

	def _getColumnModeByMap(self, cm_name, my_map):
		all_modes = self._get_column_modes()
		try:
			key = cm_name
			key.replace(key[0],key[0].lower(),1)
			value = my_map[list(map((lambda x:x[1]),my_map)).index(all_modes[key])][0]
		except:
			raise
		return value

	def _mapColumnModeConstant(self,cm_name, my_map):
		try:
			# find index all the values
			my_index = getattr(self,'get%ss' % cm_name)().index(value)
		except ValueError:
			raise RuntimeError('Invalid %s %s' % (cm_name,value))
		my_mode = getattr(cm_p,my_map[my_index][1])
		return my_mode

	def getProbeModes(self):
		mode_names = list(map((lambda x: x[0]),self.cm_probe_mode_map))
		return mode_names

	def getProbeMode(self):
		return self._getColumnModeByMap('ProbeMode', self.cm_probe_mode_map)

	def setProbeMode(self, value):
		cm_name = 'ProbeMode'
		my_map = self.cm_probe_mode_map
		my_mode = self._mapColumnMode(cm_name, my_map)
		request_name = cm_name+'Request'
		my_request =cm_p.ProbeModeRequest(probe_mode=my_mode)
		_set_by_request(cm_stub, 'Set%s' % cm_name, my_request)

	def getProjectionModes(self):
		mode_names = list(map((lambda x: x[0]),self.cm_projection_mode_map))
		return mode_names

	def getProjectionMode(self):
		return self._getColumnModeByMap('ProjectionMode', self.cm_projection_mode_map)

	def setProjectionMode(self, value):
		# Not setable in Leginon instrument
		pass

	def getProjectionSubModes(self):
		mode_names = list(map((lambda x: x[0]),self.cm_objective_mode_map))
		sub_mode_names = list(map((lambda x: x[0]),self.cm_objective_sub_mode_map))
		return mode_names

	def getProjectionSubMode(self):
		return self._getColumnModeByMap('ObjectiveSubMode', self.cm_objective_sub_mode_map)

	def setProjectionSubMode(self, value):
		raise ValuError('can not set projection submode')
