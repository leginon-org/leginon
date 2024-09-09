#!/usr/bin/env python3
SIMULATION = False

if not SIMULATION:
	from pyscope import fei
	import grpc
	from google.protobuf import json_format as json_format

	# requests builders
	from utapi_types.v1 import device_id_pb2 as dip
	from utapi_types.v1 import utapi_response_pb2 as urp
	from optics.v1 import aperture_mechanism_control_pb2 as apmc_p
	from optics.v1 import deflectors_pb2_grpc as defl_pg
	from optics.v1 import focus_pb2 as foc_p
	from optics.v1 import illumination_pb2 as illu_p
	from optics.v1 import magnification_pb2 as mag_p
	from column.v1 import column_mode_pb2 as cm_p
	from column.v1 import normalization_pb2 as norm_p
	from column.v1 import beam_blanker_pb2 as bb_p

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
	from column.v1 import beam_blanker_pb2_grpc as bb_pg

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
	bb_stub = bb_pg.BeamBlankerServiceStub(channel)

else:
	from pyscope import simtem
	import sim_utapi
	channel = False
	dip = sim_utapi
	bstop_p = sim_utapi
	cm_p = sim_utapi
	mag_p = sim_utapi
	bstop_stub = sim_utapi.BeamStopperControlStub(channel)
	cm_stub = sim_utapi.ColumnModeStub(channel)
	mag_stub = sim_utapi.MagnificationStub(channel)

def handleRpcError(e):
	if e.code() == grpc.StatusCode.ABORTED:
		utapi_response = urp.UtapiResponse()
		utapi_response.ParseFromString(e.trailing_metadata()[0][1])
		print(f"Error with UtapiResponse>\n{utapi_response}<")
	else:
		# Not an UtapiResponse. rethrow exception
		raise

def _response_to_dict(response):
	if SIMULATION:
		return response
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
		return my_attr(request)
	except grpc.RpcError as rpc_error:
		handleRpcError(rpc_error)


import time

class Logger(object):
	def __init__(self,logtype=''):
		self.level = 0
		self.logtype = ''
		if logtype:
			self.logtype = logtype.upper()+' '

	def setLevel(self,value):
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
	cm_objective_sub_mode_map = [
							('lm','OBJECTIVE_MODE_LM'),
							('m','OBJECTIVE_SUB_MODE_ML'),
							('sa', 'OBJECTIVE_SUB_MODE_SA'),
							('mh', 'OBJECTIVE_SUB_MODE_MH')
	]
	cm_probe_mode_map = [	('micro','PROBE_MODE_MICRO_PROBE'),
							('nano', 'PROBE_MODE_NANO_PROBE')
	]
	bb_map = [
							('on','Blank'),
							('off','UnBlank')
	]
	# (pyscope value, utapi Method)
	bstop_attr_map = [	('in','Insert'),
						('out','Retract'),
						('halfway','InsertedHalfway')
	]
	def __init__(self):
		super(Utapi, self).__init__()
		self.beamstop_device_id = dip.DeviceIdRequest(id='BeamStopper')
		# default to let the scope control auto normalization.
		self.noramlize_all_after_setting = False
		self.need_noramlize_all = False
		self.sup_mag_data = {}
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
		# response state is 'INSERTED' instead of 'INSERT'
		state_map = list(map((lambda x: (x[0],x[1].upper()+'ED')),self.bstop_attr_map))
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
	def _getColumnModes(self):
		results = _get_by_request(cm_stub,'GetColumnModes',cm_p.ColumnModeRequest())
		return results

	def _getColumnModeByMap(self, cm_name, my_map):
		all_modes = self._getColumnModes()
		try:
			key = cm_name
			# dictionary response keys starts are camelCasing, not CamelCasing.
			mode_key = key.replace(key[0],key[0].lower(),1)
			value = my_map[list(map((lambda x:x[1]),my_map)).index(all_modes[mode_key])][0]
		except:
			raise
		return value

	def _mapColumnModeConstant(self,cm_name, my_map, value):
		"""
		Return column mode constant without setting
		"""
		try:
			# find index all the values
			my_index = getattr(self,'get%ss' % cm_name)().index(value)
		except ValueError:
			raise RuntimeError('Invalid %s %s' % (cm_name,value))
		my_mode_constant = getattr(cm_p,my_map[my_index][1])
		self.logger.debug('columnModeConstant %s, %s ' % (cm_p, my_mode_constant))
		return my_mode_constant

	def _getRequestConstant(self, cm_name, my_map, value):
		my_constant = self._mapColumnModeConstant(cm_name, my_map, value)
		request_name = cm_name+'Request'
		return request_name, my_constant

	def getProbeModes(self):
		mode_names = list(map((lambda x: x[0]),self.cm_probe_mode_map))
		return mode_names

	def getProbeMode(self):
		return self._getColumnModeByMap('ProbeMode', self.cm_probe_mode_map)

	def setProbeMode(self, value):
		cm_name = 'ProbeMode'
		req_name, my_const = self._getRequestConstant(cm_name, self.cm_probe_mode_map,value)
		my_request =getattr(cm_p,req_name)(probe_mode=my_const)
		_set_by_request(cm_stub, 'Set%s' % cm_name, my_request)

	def getObjectiveModes(self):
		mode_names = list(map((lambda x: x[0]),self.cm_objective_mode_map))
		return mode_names

	def getObjectiveMode(self):
		return self._getColumnModeByMap('ObjectiveMode', self.cm_objective_mode_map)

	def setObjectiveMode(self, value):
		# Objective mode setting recalls the last magnification the mode used.
		cm_name = 'ObjectiveMode'
		req_name, my_const = self._getRequestConstant(cm_name, self.cm_objective_mode_map,value)
		my_request =getattr(cm_p,req_name)(objective_mode=my_const)
		_set_by_request(cm_stub, 'Set%s' % cm_name, my_request)

	def getObjectiveSubModes(self):
		mode_names = list(map((lambda x: x[0]),self.cm_objective_sub_mode_map))
		return mode_names

	def getObjectiveSubMode(self):
		return self._getColumnModeByMap('ObjectiveSubMode', self.cm_objective_sub_mode_map)

	def getProjectionModes(self):
		mode_names = list(map((lambda x: x[0]),self.cm_projection_mode_map))
		return mode_names

	def getProjectionMode(self):
		return self._getColumnModeByMap('ProjectionMode', self.cm_projection_mode_map)
	def _setProjectionMode(self, value):
		"""
		# This is an internal method for testing.  Leginon instrument
		includes projection mode definition.
		"""
		cm_name = 'ProjectionMode'
		req_name, my_const = self._getRequestConstant(cm_name, self.cm_projection_mode_map,value)
		my_request =getattr(cm_p,req_name)(projection_mode=my_const)
		_set_by_request(cm_stub, 'Set%s' % cm_name, my_request)

	def setProjectionMode(self, value):
		# Not setable in Leginon instrument
		pass

	def getProjectionSubModes(self):
		# Return objective_mode in lm or objective_sub_mode in hm
		mode_names = list(map((lambda x: x[0]),self.cm_objective_mode_map))
		sub_mode_names = list(map((lambda x: x[0]),self.cm_objective_sub_mode_map))
		return sub_mode_names

	def getProjectionSubMode(self):
		obj_mode = self._getColumnModeByMap('ObjectiveMode', self.cm_objective_mode_map)
		if obj_mode == 'lm':
			# no sub_mode. Return obj_mode
			return obj_mode
		obj_sub_mode=self._getColumnModeByMap('ObjectiveSubMode', self.cm_objective_sub_mode_map)
		return obj_sub_mode

	def getProjectionSubModeName(self):
		return self.getProjectionSubMode().upper()

	def getProjectionSubModeIndex(self, mode, sub_mode):
		# use fei.py definition wihout setting mag
		cm_name = 'ObjectiveMode'
		my_map = self.cm_objective_mode_map
		my_const = self._mapColumnModeConstant(cm_name, my_map, mode)
		if mode in ('lm','lad'):
			return my_const
		else:
			my_map = self.getObjectiveSubModes()
			sub_mode_index = my_map.index(sub_mode)
			return sub_mode_index

	def setProjectionSubMode(self, value):
		raise ValuError('can not set projection submode')

	def getMagnification(self):
		attr_name = 'GetMagnification'
		my_request = getattr(mag_p, attr_name+'Request')()
		mag_data = _get_by_request(mag_stub,attr_name, my_request)
		return self._mag_float_to_int(mag_data['magnification'])

	def _getSupportedMagnifications(self):
		attr_name = 'GetSupportedMagnifications'
		my_request = getattr(mag_p, attr_name+'Request')()
		sup_mag_data = _get_by_request(mag_stub,attr_name, my_request)
		return sup_mag_data

	def _mag_float_to_int(self, mag_float):
		precision = 1

		if mag_float <= 100.0:
			precision = 1
		elif mag_float < 400.0: #496.7=> 500
			precision = 5
		elif mag_float < 1000.0:
			precision = 10
		elif mag_float < 4000.0:
			precision = 50
		elif mag_float < 10000.0:
			precision = 100
		elif mag_float < 14000.0:
			precision = 500
		elif mag_float < 100000.0:
			precision = 1000
		else:
			precision = 5000
		return precision*int(round(mag_float/precision))

	def setMagnification(self, int_value):
		obj_mode = self.getObjectiveMode()
		if int_value in self.projection_submode_map.keys():
			mode_name, mode_id, obj_mode_name = self.projection_submode_map[int_value]
			obj_mode_name = obj_mode_name.lower()
			self.setObjectiveMode(obj_mode_name)
			index = self.sup_mag_data[obj_mode_name]['displayedMagnifications'].index(int_value)
			mag_float = self._getSupportedMagnifications()['supportedMagnifications'][index]
			my_request = getattr(mag_p,'SetMagnificationRequest')(magnification=mag_float)
			_set_by_request(mag_stub, 'SetMagnification', my_request)

	def _addSupportedMagData(self,obj_mode_name):
		om = obj_mode_name.lower()
		if self.getObjectiveMode() != om:
			self.setObjectiveMode(om)
		self.sup_mag_data[om] = self._getSupportedMagnifications()
		mags_in_om = list(map((lambda x: self._mag_float_to_int(x)),self.sup_mag_data[om]['supportedMagnifications']))
		self.sup_mag_data[om]['displayedMagnifications'] = mags_in_om

	def findMagnifications(self):
		obj_modes = self.getObjectiveModes()
		saved_mode = self.getObjectiveMode()
		saved_mag = self.getMagnification()
		magnifications = []
		for om in obj_modes:
			self.setObjectiveMode(om)
			self._addSupportedMagData(om)
			mags_in_om = self.sup_mag_data[om]['displayedMagnifications']
			magnifications.extend(mags_in_om)
			for i, m in enumerate(mags_in_om):
				sub_mode = self.getProjectionSubMode()
				sub_mode_index = self.getProjectionSubModeIndex(om, self.sup_mag_data[om]['objectiveSubModes'][i].lower())
				self.addProjectionSubModeMap(m, sub_mode, sub_mode_index, om, overwrite=True)
				magnifications.append(m)
		self.setMagnifications(magnifications)
		# once we have self.magnifications, we can set by int values
		self.setObjectiveMode(saved_mode)
		self.setMagnification(saved_mag)

	def getBeamBlank(self):
		attr_name = 'GetBeamBlankerState'
		my_map = self.bb_map
		my_request = getattr(bb_p,'BeamBlankerStateRequest')()
		state_short = _get_by_request(bb_stub, attr_name, my_request)['state']

		try:
			result = my_map[list(map((lambda x: x[1].upper()+'ED'),my_map)).index(state_short)][0]
			return result
		except Exception as e:
			self.logger.debug(e)
			return 'unknown'

	def setBeamBlank(self, value):
		my_map = self.bb_map
		attr_name = my_map[list(map((lambda x: x[0]),my_map)).index(value)][1]
		my_request =getattr(bb_p,'BeamBlankerSetterRequest')()
		r=_set_by_request(bb_stub, '%sBeam' % attr_name, my_request)
		# TODO: This is asynchronous so should watch with future method
		# until done. see example. The completion is very fast, though.

	def normalizeLens(self, value='all'):
		# constant values not exposed as attribute anywhere. see proto file
		norm_map = [
					('spotsize',1),  # 4 s on simulator
					('intensity',2), # 4 s
					('objective',3), # 4 s
					('projector',4), # 4 s
					('imagecor',6),
					('probecor',7),
		]
		if value == 'all':
			# This takes 16 s on simulator
			# TODO: consider making them asynchronous
			my_request = getattr(norm_p,'NormalizeAllRequest')()
			_set_by_request(norm_stub,'NormalizeAll', my_request)
		else:
			my_map = norm_map
			try:
				const_value = my_map[list(map((lambda x: x[0]),my_map)).index(value)][1]
			except ValueError as e:
				self.logger.debug('%s is not a valid lens to normalize' % value)
			my_request = getattr(norm_p, 'NormalizeRequest')(normalization=const_value)
			_set_by_request(norm_stub, 'Normalize', my_request)

	def getAutoNormalizeEnabled(self, value):
		try:
			my_request = norm_p.GetAtutoNormalizeEnabledRequest()
			result = _get_by_request(norm_stub,'GetAutoNormalizeEnabled', my_request)
			if 'enabled' not in result.keys():
				return False
			else:
				return result['enabled']
		except:
			# does not have valid function
			return False

	def setAutoNormalizeEnabled(self, value):
		if self.normalize_all_after_setting:
			my_request = norm_p.SetAutoNormalizeEnabledRequest(enable=bool(value))
			_set_by_request(norm_stub, 'SetAutoNormalizeEnabled', my_request)
			self.need_normalize_all = not bool(value)
		else:
			# not affected by the value
			self.need_normalize_all = False
