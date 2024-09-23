#!/usr/bin/env python3
SIMULATION = False

if not SIMULATION:
	from pyscope import fei
	import grpc
	from google.protobuf import json_format as json_format

	# requests builders
	from utapi_types.v1 import device_id_pb2 as dip
	from utapi_types.v1 import utapi_response_pb2 as urp
	from utapi_types.v1 import vector_pb2 as vctr_p
	from optics.v1 import aperture_mechanism_control_pb2 as apmc_p
	from optics.v1 import deflectors_pb2 as defl_p
	from optics.v1 import focus_pb2 as foc_p
	from optics.v1 import illumination_pb2 as illu_p
	from optics.v1 import magnification_pb2 as mag_p
	from optics.v1 import stigmator_pb2 as stig_p
	from optics.v1 import x_lens_alignments_pb2 as xaln_p
	from column.v1 import column_mode_pb2 as cm_p
	from column.v1 import normalization_pb2 as norm_p
	from column.v1 import beam_blanker_pb2 as bb_p
	from source.v1 import high_tension_pb2 as ht_p
	from source.v1 import feg_pb2 as feg_p
	from source.v1 import feg_flashing_pb2 as flash_p
	from vacuum.v1 import column_valves_pb2 as colv_p
	from vacuum.v1 import vacuum_pb2 as vac_p
	from vacuum.v1 import vacuum_chambers_pb2 as vchm_p
	from sample.v0 import loader_pb2 as ldr_p
	from system_integral.v0 import column_temperature_pb2 as ctemp_p
	from stage.v1 import stage_pb2 as stage_p
	from acquisition.v1 import fluscreen_pb2 as scrn_p

	# used to create stub for access
	from optics.v1 import beam_stopper_control_pb2_grpc as bstop_pg
	from optics.v1 import aperture_mechanism_control_pb2_grpc as apmc_pg
	from optics.v1 import deflectors_pb2_grpc as defl_pg
	from optics.v1 import focus_pb2_grpc as foc_pg
	from optics.v1 import illumination_pb2_grpc as illu_pg
	from optics.v1 import magnification_pb2_grpc as mag_pg
	from optics.v1 import optics_pb2_grpc as optics_pg
	from optics.v1 import stigmator_pb2_grpc as stig_pg
	from optics.v1 import x_lens_alignments_pb2_grpc as xaln_pg
	from column.v1 import column_mode_pb2_grpc as cm_pg
	from column.v1 import normalization_pb2_grpc as norm_pg
	from column.v1 import beam_blanker_pb2_grpc as bb_pg
	from source.v1 import high_tension_pb2_grpc as ht_pg
	from source.v1 import feg_pb2_grpc as feg_pg
	from source.v1 import feg_flashing_pb2_grpc as flash_pg
	from vacuum.v1 import column_valves_pb2_grpc as colv_pg
	from vacuum.v1 import vacuum_pb2_grpc as vac_pg
	from vacuum.v1 import vacuum_chambers_pb2_grpc as vchm_pg
	from sample.v0 import loader_pb2_grpc as ldr_pg
	from system_integral.v0 import column_temperature_pb2_grpc as ctemp_pg
	from stage.v1 import stage_pb2_grpc as stage_pg
	from acquisition.v1 import fluscreen_pb2_grpc as scrn_pg

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
	xaln_stub = xaln_pg.XLensAlignmentsServiceStub(channel)
	cm_stub = cm_pg.ColumnModeServiceStub(channel)
	norm_stub = norm_pg.NormalizationServiceStub(channel)
	bb_stub = bb_pg.BeamBlankerServiceStub(channel)
	ht_stub = ht_pg.HighTensionServiceStub(channel)
	feg_stub = feg_pg.FegServiceStub(channel)
	flash_stub = flash_pg.FegFlashingServiceStub(channel)
	colv_stub = colv_pg.ColumnValvesServiceStub(channel)
	vac_stub = vac_pg.VacuumServiceStub(channel)
	vchm_stub = vchm_pg.VacuumChambersServiceStub(channel)
	ldr_stub = ldr_pg.LoaderServiceStub(channel)
	ctemp_stub = ctemp_pg.ColumnTemperatureServiceStub(channel)
	stage_stub = stage_pg.StageServiceStub(channel)
	scrn_stub = scrn_pg.FluscreenServiceStub(channel)

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
	print('_get_by_request',stub, attr_name, request)
	my_attr = getattr(stub,attr_name)
	try:
		# perform my_attr action on the request and convert to list and dict
		return _response_to_dict(my_attr(request))
	except grpc.RpcError as rpc_error:
		handleRpcError(rpc_error)

def _set_by_request(stub, attr_name, request):
	print('_set_by_request',stub, attr_name, request)
	my_attr = getattr(stub,attr_name)
	try:
		# perform my_attr action on the request
		return my_attr(request)
	except grpc.RpcError as rpc_error:
		handleRpcError(rpc_error)

def _get_vector_xy(msg_dict, key):
	if not msg_dict or key not in msg_dict.keys():
		# error state
		return {'x':None,'y':None}
	r = {'x':0.0, 'y':0.0}
	for k in r.keys():
		if k in msg_dict[key].keys():
			r[k] = msg_dict[key][k]
	return r

def _make_vector(vector, original_vector, relative = 'absolute'):
	"""
	Return vector xy dict either relative to original or absolute values.
	"""
	if relative == 'relative':
		try:
			vector['x'] += original_vector['x']
		except KeyError:
			pass
		try:
			vector['y'] += original_vector['y']
		except KeyError:
			pass
	elif relative == 'absolute':
		pass
	else:
		raise ValueError
	# handle missing key that means no change.
	if 'x' not in vector.keys():
		vector['x'] = original_vector['x']
	if 'y' not in vector.keys():
		vector['y'] = original_vector['y']
	if 'x' not in original_vector.keys():
		vector['x'] = vector['x']
	if 'y' not in original_vector.keys():
		vector['y'] = vector['y']
	return vector

def underscore_to_spacecap(value):
	bits = value.split("_")
	new_bits = map((lambda x: x.replace(x[0],x[0].upper(),1)), bits)
	return ' '.join(new_bits)

def underscore_to_camelcase(value,capitalize_first=False):
	"""
	Copied from https://stackoverflow.com/questions/4303492/how-can-i-simplify-this-conversion-from-underscore-to-camelcase-in-python	
	"""
	def camelcase():
		yield str.lower
		while True:
			yield str.capitalize
	c = camelcase()
	r = "".join(c.__next__()(x) if x else '_' for x in value.split("_"))
	if capitalize_first:
		r = r.replace(r[0],r[0].upper(),1)
	return r

def camelcase_to_underscore(value):
	def underscore():
		yield '_'+str.lower
	indices = [i for i,l in enumerate(value) if l.isupper()]
	if indices[0] == 0:
		indices.pop(0)
	for i, x in enumerate(indices):
		offset = i+x
		value = value.replace(value[offset], '_'+value[offset].lower()) 
	return value.lower()

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
	cold_feg_flash_types = {'low':1,'high':2}

	def __init__(self):
		super(Utapi, self).__init__()
		self.cold_feg_flash_types = {'low':1,'high':2}
		self.beamstop_device_id = dip.DeviceIdRequest(id='BeamStopper')
		# default to let the scope control auto normalization.
		self.noramlize_all_after_setting = False
		self.need_normalize_all = False
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
			# always look up condenser 2 value for Krios
			mechanism_name = 'condenser_2'
		mechanism_id = underscore_to_spacecap(mechanism_name)
		return mechanism_id

	def _isApertureMechanismRetractable(self, device_obj):
		is_retractable = _get_by_request(apmc_stub,'GetIsRetractable',device_obj)
		return bool(is_retractable)

	def getApertureSelections(self, mechanism_name):
		'''
		get valid selection for an aperture mechanism to be used in gui,including "open" if available.
		'''
		mechanism_id = self._getApertureMechanismId(mechanism_name)
		# use the name-specified request
		device_obj=dip.DeviceId(id=mechanism_id)
		my_request = apmc_p.GetApertureCollectionRequest(
			device_id=device_obj,
			)
		results = _get_by_request(apmc_stub,'GetApertureCollection',my_request)
		is_retractable = self._isApertureMechanismRetractable(device_obj)
		names = list(map((lambda x: str(x['apertureName'])),results['apertures']))
		if is_retractable:
			names.append('open')
		return names

	def getApertureSelection(self, mechanism_name):
		mechanism_id = self._getApertureMechanismId(mechanism_name)
		device_obj = dip.DeviceId(id=mechanism_id)
		# check if the mechanism is retracted.
		# Retracted mechanism will get error in the next statement
		is_retractable = self._isApertureMechanismRetractable(device_obj)
		if is_retractable:
			state = _get_by_request(apmc_stub,'GetState', device_obj)['state']
			if state == 'RETRACTED':
				return "open"
			if state != 'INSERTED':
				# invalid state, return no selection
				return None
		result = _get_by_request(apmc_stub,'GetSelectedAperture',device_obj)
		return result['apertureName']
		
	def retractApertureMechanism(self, mechanism_name):
		'''
		Retract aperture mechanism.
		'''
		return self.setApertureSelection(mechanism_name, 'open')

	def setApertureSelection(self, mechanism_name, name):
		#TODO handle open position
		all_names = self.getApertureSelections(mechanism_name)
		if name not in all_names:
			raise RuntimeError('Invalid aperture %s' % (name))
		mechanism_id = self._getApertureMechanismId(mechanism_name)
		device_obj = dip.DeviceId(id=mechanism_id)
		is_retractable = self._isApertureMechanismRetractable(device_obj)
		if is_retractable and name == 'open':
			_set_by_request(apmc_stub,'Retract', device_obj)
			return
		my_request = apmc_p.SelectApertureRequest(device_id=device_obj,aperture_name=name)
		_set_by_request(apmc_stub, 'SelectAperture', my_request)

	#source
	def _getHighTensionSettings(self):
		my_request = getattr(ht_p,'HighTensionSettingsRequest')()
		return _get_by_request(ht_stub, 'GetHighTensionSettings', my_request)
	
	def getHighTension(self):
		r = self._getHighTensionSettings()
		# ht_offset returns 0.0 if not available and therefore not transfered
		return r['htValue']
	
	def _getFegValue(self, my_device):
		result_key = my_device.replace(my_device[0],my_device[0].lower())
		my_request = getattr(feg_p,'%sRequest' % my_device)()
		r = _get_by_request(feg_stub, 'Get%s' % my_device, my_request)
		try:
			return r[result_key]
		except:
			return -1.0

	def getGunLens(self):
		my_device = 'FocusIndex'
		my_request = getattr(feg_p,'%sRequest' % my_device)()
		r = _get_by_request(feg_stub, 'Get%s' % my_device, my_request)
		return r['coarse'] + r['fine']*0.1 if 'fine' in r.keys() else float(r['coarse'])

	def getColdFegBeamCurrent(self):
		my_device = 'BeamCurrent'
		return set._getFegValue(my_device)

	def getExtractorVoltage(self):
		my_device = 'ExtractorVoltage'
		return set._getFegValue(my_device)
	
	def hasColdFeg(self):
		try:
			flash_type_constant = self.cold_feg_flash_types['low']
			r = self._getFlashingAdvised(flash_type_constant)
			return True
		except Exception as e:
			print(e)
			return False

	def _getFlashingAdvised(self,flash_type_constant):
		my_device = 'FegFlashing'
		my_request = getattr(flash_p,'%sRequest' % my_device)(flashing_type=flash_type_constant)
		r = _get_by_request(flash_stub, 'GetFlashingAdvised', my_request)

	def getFlashingAdvised(self, flash_type):
		advised_only = self.getFeiConfig('source','flash_cold_feg_only_if_advised')
		try:
			flash_type_constant = self.cold_feg_flash_types[flash_type]
			r = self._getFlashingAdvised(flash_type_constant)
			# r can either be {} or {'flashing_advised': True}
			should_flash = bool(r)
		except AttributeError as e:
			return False
		except KeyError:
			self.logger.debug('flash type can only be %s' % list(self.cold_feg_flash_types.keys()))
			return False
		except Exception as e:
			self.logger.debug('other getFlashAdvised exception %s' % e)
			return False
		if advised_only:
			return should_flash
		else:
			if flash_type == 'low':
				# only low temp can flash without advised.
				return True
		return should_flash

	def _performColdFegFlashing(self, flash_type_constant):
		my_device = 'FegFlashing'
		my_request = getattr(flash_p,'%sRequest' % my_device)(flashing_type=flash_type_constant)
		r = _set_by_request(flash_stub, 'PerformFlashing', my_request)

	def setColdFegFlashing(self,state):
		# 'on' starts flashing, 'off' stops flashing
		# tfs flashing can not be stopped.
		if not self.hasColdFeg():
			return
		# low temperature (lowT) flashing can be done any time even if not advised.
		# highT flashing can only be done if advised.
		if state != 'on':
			# tfs flashing can not be stopped.
			return
		for flash_type in ('high','low'):
			if self.getFlashingAdvised(flash_type):
				flash_type_constant = self.cold_feg_flash_types[flash_type]
				try:
					self._performColdFegFlashing(flash_type_constant)
					# no need to do lowT flashing if highT is done
					break
				except Exception as e:
					raise RuntimeError(e)

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
		if not self.projection_submode_map:
			raise ValueError('objective mode and submode mapping not set')
		if int_value in self.projection_submode_map.keys():
			mode_name, mode_id, obj_mode_name = self.projection_submode_map[int_value]
			obj_mode_name = obj_mode_name.lower()
			self.setObjectiveMode(obj_mode_name)
			if obj_mode_name not in self.sup_mag_data.keys():
				self._addSupportedMagData(obj_mode_name)
			
			index = self.sup_mag_data[obj_mode_name]['displayedMagnifications'].index(int_value)
			mag_float = self._getSupportedMagnifications()['supportedMagnifications'][index]
			my_request = getattr(mag_p,'SetMagnificationRequest')(magnification=mag_float)
			_set_by_request(mag_stub, 'SetMagnification', my_request)
		else:
			raise ValueError('Magnification %d not in mapping. Can not determine how to set the value ' % (int_value))

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
		self.setMagnifications(magnifications)
		# once we have self.magnifications, we can set by int values
		self.setObjectiveMode(saved_mode)
		self.setMagnification(saved_mag)

	def _getIlluminationSettings(self):
		my_request = getattr(illu_p,'IlluminationSettingsRequest')()
		return _get_by_request(illu_stub, 'GetIlluminationSettings', my_request)
	
	def getSpotSize(self):
		return self._getIlluminationSettings()['spotSizeIndex']

	def getIntensity(self):
		return self._getIlluminationSettings()['illuminatedAreaDiameter']

	def _setIllumination(self, req_key_name, value):
		req_key_name = 'illuminated_area_diameter'
		my_device = underscore_to_camelcase(req_key_name,True)
		kwargs = {}
		kwargs[req_key_name] = value
		my_request = getattr(illu_p,'%sRequest' % my_device)
		my_request = my_request(**kwargs)
		return _get_by_request(illu_stub, 'Set%s' % my_device, my_request)

	def setSpotSize(self, value):
		req_key_name = 'spot_size_index'
		return self._setIllumination(req_key_name, value)

	def setIntensity(self, value):
		req_key_name = 'illuminated_area_diamter'
		return self._setIllumination(req_key_name, value)

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
		# See porto file for enum values (norm_p.Normalization.Normalize)
		norm_map = [
					('spotsize',1),  # takes 4 s on simulator to complete.
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
				# protobuf message parsing drops the item if the value is default of the type.
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

	def _getAllDeflectors(self):
		try:
			my_request = getattr(defl_p,'DeflectorsSettingsRequest')()
			return _get_by_request(defl_stub, 'GetDeflectorsSettings', my_request)
		except Exception as e:
			self.logger.error('Error getting deflector values: %s' %e)
			return {}

	def _setDeflector(self, req_key_name, vector, original_vector, min_move, relative = 'absolute'):
		my_device = underscore_to_camelcase(req_key_name,True)
		#
		vector = _make_vector(vector, original_vector, relative)
		vec = original_vector
		if abs(vec['x']-vector['x'])+abs(vec['x']-vector['y']) < min_move:
			# small move is ignored.
			return
		v_req = vctr_p.Vector(x=vector['x'],y=vector['y'])
		if req_key_name.startswith('x_'):
			req_attr_name = 'Set%sRequest' % my_device
		else:
			req_attr_name = '%sRequest' % my_device
		my_request = getattr(defl_p,req_attr_name)
		kwargs = {}
		kwargs[req_key_name]=v_req
		my_request = my_request(**kwargs)
		_set_by_request(defl_stub,'Set%s' % my_device, my_request)

	def getBeamTilt(self):
		"""
		Beam Tilt in radians for vector axes x,y.
		"""
		#TODO: this might need to be mapped to ImageBeamTilt, not BeamTilt
		r = self._getAllDeflectors()
		return _get_vector_xy(r,'beamTilt')

	def setBeamTilt(self, vector, relative = 'absolute'):
		my_device = 'BeamTilt'
		original_vector = getattr(self,'get%s' % my_device)()
		min_move = 1e-6

		req_key_name = camelcase_to_underscore(my_device)
		self._setDeflector(req_key_name, vector, original_vector, min_move, relative)

	def getBeamShift(self):
		"""
		Beam Tilt in meters for vector axes x,y.
		"""
		r = self._getAllDeflectors()
		return _get_vector_xy(r,'beamShift')

	def setBeamShift(self, vector, relative = 'absolute'):
		my_device = 'BeamShift'
		original_vector = getattr(self,'get%s' % my_device)()
		min_move = 1e-9

		req_key_name = camelcase_to_underscore(my_device)
		self._setDeflector(req_key_name, vector, original_vector, min_move, relative)

	def getImageShift(self):
		"""
		ImageBeamShift in meters for vector axes x,y.
		"""
		r = self._getAllDeflectors()
		return _get_vector_xy(r,'imageBeamShift')

	def setImageShift(self, vector, relative = 'absolute'):
		my_device = 'ImageBeamShift'
		original_vector = getattr(self,'get%s' % 'ImageShift')()
		min_move = 1e-9

		req_key_name = camelcase_to_underscore(my_device)
		self._setDeflector(req_key_name, vector, original_vector, min_move, relative)

	def getDiffractionShift(self):
		"""
		Diffraction shift in meters for vector axes x,y.
		"""
		r = self._getAllDeflectors()
		result = _get_vector_xy(r,'difffractionShift')
		if result['x'] is None:
			return None

	def setDiffractionShift(self, vector, relative = 'absolute'):
		my_device = 'DiffractionShift'
		original_vector = getattr(self,'get%s' % my_device)()
		min_move = 1e-9

		req_key_name = camelcase_to_underscore(my_device)
		self._setDeflector(req_key_name, vector, original_vector, min_move, relative)

	def getXDeflectorTilt(self):
		"""
		X lens Tilt in radians for vector axes x,y.
		"""
		r = self._getAllDeflectors()
		return _get_vector_xy(r,'xDeflectorTilt')

	def setXDeflectorTilt(self, vector, relative = 'absolute'):
		my_device = 'XDeflectorTilt'
		original_vector = getattr(self,'get%s' % my_device)()
		min_move = 1e-6

		req_key_name = camelcase_to_underscore(my_device)
		self._setDeflector(req_key_name, vector, original_vector, min_move, relative)

	def getXDeflectorShift(self):
		"""
		X lens Shift in meters for vector axes x,y.
		"""
		r = self._getAllDeflectors()
		return _get_vector_xy(r,'xDeflectorShift')

	def setXDeflectorShift(self, vector, relative = 'absolute'):
		my_device = 'XDeflectorShift'
		original_vector = getattr(self,'get%s' % my_device)()
		min_move = 1e-9
		#
		req_key_name = camelcase_to_underscore(my_device)
		self._setDeflector(req_key_name, vector, original_vector, min_move, relative)

	def _getAllStigmators(self):
		try:
			my_request = getattr(stig_p,'StigmatorSettingsRequest')()
			return _get_by_request(stig_stub, 'GetStigmatorSettings', my_request)
		except Exception as e:
			self.logger.error('Error getting stigmator values: %s' %e)
			return {}

	def getStigmator(self):
		stigmator_invalid = False
		r = self._getAllStigmators()
		if r is None:
			stigmator_invalid = True
		# new_r uses pyscope keys
		new_r = {}
		keys = ['condenserStigmator','diffractionStigmator','objectiveStigmator','xStigmator']
		for k in keys:
			new_k = camelcase_to_underscore(k).split('_')[0]
			new_r[new_k] = {}
			if stigmator_invalid: #LM has no stigmator value passed
				new_r[new_k] = {'x':None,'y':None}
			elif k not in r.keys(): # axis not registered if its value is 0.0
				new_r[new_k] = {'x':0.0,'y':0.0}
			else:
				for axis in ('x','y'):
					if axis not in r[k]:
						r[k][axis] = 0.0
				new_r[new_k] = r[k]
		return new_r

	def setStigmator(self, stigs, relative = 'absolute'):
		original_stigs = getattr(self,'getStigmator')()
		for device_type in stigs.keys():
			req_key_name = device_type+'_stigmator'
			original_vector = original_stigs[device_type]
			if original_vector['x'] is None and original_vector['y'] is None:
				self.logger.debug('%s is deactivated for setting' % device_type)
				return
			min_move = 1e-9 # TODO: what is the good value ?
			self._setStigmator(req_key_name, stigs[device_type], original_vector, min_move, relative)

	def _setStigmator(self, req_key_name, vector, original_vector, min_move, relative = 'absolute'):
		my_device = underscore_to_camelcase(req_key_name,True)
		#
		vector = _make_vector(vector, original_vector, relative)
		vec = original_vector
		if abs(vec['x']-vector['x'])+abs(vec['x']-vector['y']) < min_move:
			# small move is ignored.
			return
		v_req = vctr_p.Vector(x=vector['x'],y=vector['y'])
		my_request = getattr(stig_p,'%sRequest' % my_device)
		kwargs = {}
		kwargs[req_key_name]=v_req
		my_request = my_request(**kwargs)
		_set_by_request(stig_stub,'Set%s' % my_device, my_request)

	def _getFocusSettings(self):
		my_request = getattr(foc_p,'FocusSettingsRequest')()
		return _get_by_request(foc_stub, 'GetFocusSettings', my_request)
	
	def getFocus(self):
		try:
			return self._getFocusSettings()['focus']
		except KeyError:
			return 0.0

	def setFocus(self, value):
		my_request = getattr(foc_p,'FocusRequest')(focus=value)
		return _get_by_request(foc_stub, 'SetFocus', my_request)

	def getDefocus(self):
		try:
			return self._getFocusSettings()['defocus']
		except KeyError:
			return 0.0

	def setDefocus(self, defocus, relative = 'absolute'):
		old_defocus = self.getDefocus
		if relative == 'relative':
			defocus += old_defocus
		elif relative == 'absolute':
			pass
		else:
			raise ValueError
		# normalize by always sending 0 focus first
		self.setFocus(0.0)
		my_request = getattr(foc_p,'DefocusRequest')(defocus=defocus)
		return _get_by_request(foc_stub, 'SetDefocus', my_request)
	
	def resetDefocus(self):
		my_request = getattr(foc_p,'ResetDefocusRequest')()
		return _get_by_request(foc_stub, 'ResetDefocus', my_request)

	def getXLensAlignmentRange(self, lens_id):
		my_request = getattr(xaln_p,'GetXLensPresetRangeRequest')(x_lens_id=lens_id)
		r = _get_by_request(xaln_stub, 'GetXLensPresetRange', my_request)
		return (r['minXLensPreset'],r['maxXLensPreset'])

	def getXLensAlignment(self, lens_id=1):
		my_request = getattr(xaln_p,'GetXLensPresetRequest')(x_lens_id=lens_id)
		return _get_by_request(xaln_stub, 'GetXLensPreset', my_request)['xLensPreset']
		
	def setXLensAlignment(self, lens_id, value, relative = 'absolute'):
		#TODO: Check on real scope. Simulator only has valid results with lens_id=1
		old_value = self.getXLensAlignment(lens_id)
		if relative == 'relative':
			value += old_value
		elif relative == 'absolute':
			pass
		else:
			raise ValueError('XLensAlignment option %s not assigned' % relative)
		my_min, my_max = self.getXLensAlignmentRange(lens_id)
		if value > my_max or value < my_min:
			raise ValueError('preset %d set value %.3f out of range' % (lens_id, value))
		my_request = getattr(xaln_p,'SetXLensPresetRequest')(x_lens_id=lens_id, x_lens_preset=value)
		return _get_by_request(xaln_stub, 'SetXLensPreset', my_request)

	#vacuum
	def getColumnValvePositions(self):
		return ['open','closed']

	def getColumnValvePosition(self):
		my_request = getattr(colv_p,'ColumnValvesStateRequest')()
		r = _get_by_request(colv_stub, 'GetColumnValvesState', my_request)
		try:
			state = r['state'].lower()
			return state
		except KeyError:
			return 'undefined'

	def setColumnValvePosition(self, state):
		if state not in self.getColumnValvePositions():
			return self.logger.debug('Invalid column valve state: %s' % state)
		if not self.getColumnValvePosition():
			return self.logger.debug('Not allowed to set colunm valve to %s' % state)
		my_request = getattr(colv_p,'ColumnValvesSetterRequest')()
		action = state.replace(state[0],state[0].upper(),1)
		if action == 'Closed':
			action = 'Close'
		attr_name = '%sColumnValves' % (action)
		return _get_by_request(colv_stub, attr_name, my_request)

		return r['state']

	def getVacuumStatus(self):
		my_request = getattr(vac_p,'VacuumStateRequest')()
		status = _get_by_request(vac_stub, 'GetVacuumState', my_request)['state']
		return status.replace('VACUUM_STATE_','').lower()

	def runBufferCycle(self):
		my_request = getattr(vac_p,'RunBufferCycleRequest')()
		_get_by_request(vac_stub, 'RunBufferCycle', my_request)

	def isBufferCycleRunning(self):
		my_request = getattr(vac_p,'IsPrevacuumPumpRunningRequest')()
		return bool(_get_by_request(vac_stub, 'GetIsPrevacuumPumpRunning', my_request)) # False gives no key in the result

	def _getPressureChambers(self):
		request_key = 'chambers'
		my_device = 'VacuumChambers'
		my_request = getattr(vchm_p,'Get%sRequest' % my_device)()
		return _get_by_request(vchm_stub, 'Get%s' % my_device, my_request)[request_key]

	def _getChamberPressure(self,chamber):
		if chamber not in self._getPressureChambers():
			raise KeyError
		my_device = 'VacuumChamberPressure'
		request_key = 'chamber'
		result_key = 'pressureCollection'
		my_request = getattr(vchm_p,'Get%sRequest' % my_device)(chamber=chamber)
		return _get_by_request(vchm_stub, 'Get%s' % my_device, my_request)[result_key]

	def getColumnPressure(self):
		return self._getChamberPressure('Column')['pressure']

	def getProjectionChamberPressure(self):
		return self._getChamberPressure('Projection')['pressure']

	def getLinerPressure(self):
		return self._getChamberPressure('SourceBuffer')['pressure']

	def hasGridLoader(self):
		return super(Utapi, self).hasGridLoader()
		#TODO broken service not functional
		my_device = 'SampleloaderType'
		my_request = getattr(ldr_p,'Get%sRequest' % my_device)()
		return _get_by_request(ldr_stub, 'Get%s' % my_device, my_request)

	def hasAutoFiller(self):
		my_device = 'HolderTemperatureSupported'
		my_device = 'DewarLevelSupported'
		my_request = getattr(ctemp_p,'Is%sRequest' % my_device)()
		my_device = 'DewarLevelSupported'
		return _get_by_request(ctemp_stub, 'Is%s' % my_device, my_request)

	def _getStageState(self):
		my_device = 'StageState'
		my_request = getattr(stage_p,'Get%sRequest' % my_device)()
		return _get_by_request(stage_stub, 'Get%s' % my_device, my_request)['state']

	def getStageStatus(self):
		result_state_name = self._getStageState()
		state = (result_state_name.split('STAGE_STATE_')[1]).lower()
		if state == 'not_ready':
			return 'busy'
		if state == 'unspecified':
			return 'unknown'
		return state

	def getStagePosition(self):
		my_device = 'StagePosition'
		my_request = getattr(stage_p,'Get%sRequest' % my_device)()
		r = _get_by_request(stage_stub, 'Get%s' % my_device, my_request)['position']
		r['a'] = r['rx']
		r['b'] = 0.0
		del r['rx']
		return r

	def resetStageSpeed(self):
		self.stage_speed_fraction = self.default_stage_speed_fraction

	def setStageSpeed(self, value):
		self.speed_deg_per_second = float(value)
		self.stage_speed_fraction = min(value/self.stage_top_speed,1.0)

	def waitForStageReady(self,position_log,timeout=10):
		state = self._getStageState()
		my_msg = 'for %s' % position_log if position_log else ''
		if 'READY' not in state:
			raise ValueError('Stage at invalid state: %s %s' % (state, my_msg))
		t0 = time.time()
		dt = 0.0 # delta time
		trials = 0
		while state != 'STAGE_STATE_READY':
			self.logger.debug('wait 0.2 s for stage to be ready %s' % my_msg)
			trials += 1
			time.sleep(0.2)
			state = self._getStageState()
			if dt >= timeout:
				raise RuntimeError('stage is not going to ready status in %d seconds. Last state: %s' % (int(timeout), state))
			dt = time.time() - t0 
		if self.getDebugStage() and trials > 0:
			print(datetime.datetime.now())
			donetime = time.time() - t0
			print('took extra %.1f seconds to get to ready status' % (donetime))

	def _getStageLimits(self):
		"""
		Return limits for stage movement.  The returned value puts limit
		"""
		stage_axis_map = [('x', stage_p.AXIS_X),('y', stage_p.AXIS_Y),('z', stage_p.AXIS_Z),('a',stage_p.AXIS_RX),('b',stage_p.AXIS_RZ)]
		my_device = 'StagePositionLimits'
		my_request = getattr(stage_p,'Get%sRequest' % my_device)()
		r = _get_by_request(stage_stub, 'Get%s' % my_device, my_request)['axesLimits']
		mapped_limits = {}
		axis_constants = list(map((lambda x:x[1]), stage_axis_map))
		axis_names = list(map((lambda x:x[0]), stage_axis_map))
		for k in r.keys():
			axis = axis_names[axis_constants.index(int(k))]
			mapped_limits[axis] = [r[k]['minimum'],r[k]['maximum']]
		return mapped_limits

	def getStageLimits(self):
		limits = self.getFeiConfig('stage','stage_limits')
		if limits is None:
			return self._getStageLimits()
		else:
			return limits

	def _validateStageLimit(self, p, axes=[]):
		limits = self.getStageLimits()
		for axis in axes:
			if axis not in p.keys():
				continue
			if not (limits[axis][0] < p[axis] and limits[axis][1] > p[axis]):
				if axis in ('x','y','z'):
					um_p = p[axis]*1e6
					raise ValueError('Requested %s axis position %.1f um out of range.' % (axis,um_p))
				else:
					deg_p = math.degrees(p[axis])
					raise ValueError('Requested %s axis position %.1f degrees out of range.' % (axis,deg_p))

	def setDirectStagePosition(self,value):
		self.checkStageLimits(value)
		self._setStagePosition(value)

	def checkStageLimits(self, position):
		self._validateStageLimit(position,['x','y','z','a','b'])

	def checkStagePosition(self, position):
		self.checkStageLimits(position)
		current = self.getStagePosition()
		bigenough = {}
		minimum_stage = self.getMinimumStageMovement()
		for axis in ('x', 'y', 'z', 'a', 'b'):
			if axis in position:
				delta = abs(position[axis] - current[axis])
				if delta > minimum_stage[axis]:
					bigenough[axis] = position[axis]
		return bigenough

	def _setStagePosition(self, position, relative = 'absolute'):
		self.waitForStageReady('before setting %s' % (position,))
		current_position = self.getStagePosition()
		if relative == 'relative':
			for key in position:
				position[key] += current_position[key]
		elif relative != 'absolute':
			raise ValueError
		short_pos_str = ''
		self._validateStageLimit(position, ['x','y','z','a','b'])
		position_options = {}
		stage_axis_name_map = [('x', 'x'),('y', 'y'),('z', 'z'),('a','rx'),('b',stage_p,'rz')]
		pyscope_names = list(map((lambda x: x[0]), stage_axis_name_map))
		position_message = stage_p.Position()
		valid_api_axes = []
		for key, value in position.items():
			axis_api_name = stage_axis_name_map[pyscope_names.index(key)][1]
			valid_api_axes.append(axis_api_name)
			short_pos_str +='%s %d' % (key,int(value*1e6))
			setattr(position_message, axis_api_name, value)
		if len(valid_api_axes) == 0:
			return
		#TODO check low speed move limit on the real scope
		try:
			if self.stage_speed_fraction == self.default_stage_speed_fraction:
				my_request = stage_p.MoveStageRequest(move_type=1,position=position_message)
				_set_by_request(stage_stub,'MoveStage', my_request)
			else:
				api_position_dict = _response_to_dict(position_message)
				valid_api_axes.sort()
				valid_api_axes.reverse()
				# Low speed move needs to be done on individual axis
				for k in valid_api_axes:
					self.waitForStageReady('before setting %s' % (k,))
					p_msg = stage_p.Position()
					setattr(p_msg,k,api_position_dict[k])
					my_request = stage_p.MoveStageRequest(move_type=1,position=p_msg,speed_factor=self.stage_speed_fraction)
					_set_by_request(stage_stub,'MoveStage', my_request)
		except Exception as e:
			if self.getDebugStage():
				print(datetime.datetime.now())
				print('Error in going to %s' % (position,))
			raise RuntimeError('set %s with error: %s' % (short_pos_str, e))
		self.waitForStageReady('after setting %s' % (short_pos_str,))

	def setStagePosition(self, value):
		# pre-position x and y (maybe others later)
		value = self.checkStagePosition(value)
		if not value:
			# no big enough movement
			return
		# calculate pre-position
		prevalue = {}
		prevalue2 = {}
		# correct xyz
		if self.correctedstage:
			delta = self.getXYZStageBacklashDelta()
			for axis in ('x','y','z'):
				if axis in value:
					prevalue[axis] = value[axis] - delta
			self._validateStageLimit(prevalue,['x','y','z'])
		# relax xy
		relax = self.getXYStageRelaxDistance()
		if abs(relax) > 1e-9:
			for axis in ('x','y'):
				if axis in value:
					prevalue2[axis] = value[axis] + relax
			self._validateStageLimit(prevalue2,['x','y'])
		# preposition a
		if self.corrected_alpha_stage:
			# alpha tilt backlash only in one direction
			alpha_delta_degrees = self.alpha_backlash_delta
			if 'a' in list(value.keys()):
					axis = 'a'
					prevalue[axis] = value[axis] - alpha_delta_degrees*3.14159/180.0
		self._validateStageLimit(prevalue,['a',])
		if prevalue:
			# set all axes in value
			for axis in list(value.keys()):
				if axis not in list(prevalue.keys()):
					prevalue[axis] = value[axis]
					# skip those requiring no further change
					del value[axis]
			self._setStagePosition(prevalue)
			time.sleep(0.2)
		# set all remaining axes in the remaining value
		if abs(relax) > 1e-9 and prevalue2:
			for axis in list(value.keys()):
				if axis not in list(prevalue2.keys()):
					prevalue2[axis] = value[axis]
					# skip those requiring no further change
					del value[axis]
			self._setStagePosition(prevalue2)
			time.sleep(0.2)
		# final position
		return self._setStagePosition(value)

	def getLowDose(self):
		return 'disabled'

	def setLowDose(self, ld):
		self.logger.debug('Low Dose disabled')
		return
	def getHolderStatus(self):
		return 'unknown'

	def getHolderType(self):
		# TODO depends on hasAutoLoader
		return 'cryo'
