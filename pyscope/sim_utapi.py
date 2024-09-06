
class DeviceIdRequest(object):
	def __init__(self, id):
		self.id = id
		return

class GetStateRequest(object):
	def __init__(self, device):
		return None

class SetStateRequest(object):
	def __init__(self, device):
		return None

class Insert(object):
	def __init__(self, device):
		return None

class Retract(object):
	def __init__(self, device):
		return None

	
class BeamStopperControlStub(object):
	def __init__(self, channel):
		self.state = 'RETRACTED'

	def GetState(self,request):
		return {'state':self.state}

	def Insert(self,request):
		self.state = 'INSERTED'
		return {'state':self.state}

	def Retract(self,request):
		self.state = 'RETRACTED'
		return {'state':self.state}

PROBE_MODE_MICRO_PROBE='PROBE_MODE_MICRO_PROBE'
PROBE_MODE_NANO_PROBE='PROBE_MODE_NANO_PROBE'
OBJECTIVE_MODE_LM='OBJECTIVE_MODE_LM'
OBJECTIVE_MODE_HM='OBJECTIVE_MODE_HM'

OBJECTIVE_SUB_MODE_LM='OBJECTIVE_SUB_MODE_LM'
OBJECTIVE_SUB_MODE_ML='OBJECTIVE_SUB_MODE_ML'
OBJECTIVE_SUB_MODE_SA='OBJECTIVE_SUB_MODE_SA'
OBJECTIVE_SUB_MODE_MH='OBJECTIVE_SUB_MODE_MH'

class ColumnModeRequest(object):
	def __init__(self):
		pass

class ProbeModeRequest(object):
	def __init__(self, probe_mode=PROBE_MODE_MICRO_PROBE):
		self.probe_mode = probe_mode

class ObjectiveModeRequest(object):
	def __init__(self, objective_mode=OBJECTIVE_MODE_LM):
		self.objective_mode = objective_mode

class ObjectiveSubModeRequest(object):
	def __init__(self, objective_sub_mode=OBJECTIVE_SUB_MODE_LM):
		self.objective_sub_mode = objective_sub_mode

class ColumnModeStub(object):
	def __init__(self, channel):
		self.probe_mode = PROBE_MODE_MICRO_PROBE
		self.objective_mode = OBJECTIVE_MODE_LM
		self.objective_sub_mode = OBJECTIVE_SUB_MODE_LM

	def GetColumnModes(self, request):
		return {
			'probeMode': self.probe_mode,
			'objectiveMode': self.objective_mode,
			'objectiveSubMode': self.objective_sub_mode,
		}

	def SetProbeMode(self, request):
		self.probe_mode = request.probe_mode

	def SetObjectiveMode(self, request):
		self.objective_mode = request.objective_mode
		if self.objective_mode not in (OBJECTIVE_MODE_LM,):
			self.objective_sub_mode = OBJECTIVE_SUB_MODE_SA
		else:
			self.objective_sub_mode = OBJECTIVE_SUB_MODE_LM

	def SetObjectiveSubMode(self, request):
		self.objective_sub_mode = request.objective_sub_mode

SUPPORTED_MAGNIFICATIONS = [
			49.3,
			101.4,
			502.0,
			1009.0,
			5002.0,
			25030.9,
			50040.0,
		]
class MagnificationRequest(object):
	def __init__(self, magnification=5002.0):
		self.magnification = magnification

class GetMagnificationRequest(object):
	def __init__(self):
		pass

class GetSupportedMagnificationsRequest(object):
	def __init__(self):
		pass

class MagnificationStub(object):
	def __init__(self, channel):
		self.magnification = SUPPORTED_MAGNIFICATIONS[0]
		self.supported_magnifications = {
			'supportedMagnifications': SUPPORTED_MAGNIFICATIONS,
			'objectiveSubModes':['LM','LM','SA','SA','SA','SA','SA']
		}

	def GetSupportedMagnifications(self, request):
		return self.supported_magnifications

	def GetMagnification(self, request):
		return {'magnification':self.magnification}

	def SetMagnification(self, request):
		self.magnification = request.magnification
