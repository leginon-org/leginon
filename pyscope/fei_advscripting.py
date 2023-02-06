import sys
from pyami import moduleconfig
configs = moduleconfig.getConfigured('fei.cfg')


class FEIAdvScriptingConnection(object):
	instr = None
	acq = None
	csa = None
	cameras = []

import comtypes
import comtypes.client
# a clean class instance at import
connection = FEIAdvScriptingConnection()

def chooseTEMAdvancedScriptingName():
	if 'version' not in configs.keys() or 'tfs_software_version' not in configs['version'].keys():
		print('Need version section in fei.cfg. Please update it')
		raw_input('Hit return to exit')
		sys.exit(0)
	version_text = configs['version']['tfs_software_version']
	bits = version_text.split('.')
	if len(bits) != 3 or not bits[1].isdigit():
		print ('Unrecognized Version number, not in the format of %d.%d.%d')
		raw_input('Hit return to exit')
	major_version = int(bits[0])
	minor_version = int(bits[1])
	if 'software_type' not in  configs['version'].keys():
		print('Need software_type in version section in fei.cfg. Please update it')
		raw_input('Hit return to exit')
		sys.exit(0)
	software_type = configs['version']['software_type'].lower()
	adv_script_version = configs['version']['tem_advanced_scripting_version']
	if adv_script_version:
		return '%d' % adv_script_version
	if software_type == 'titan':
		# titan major version is one higher than talos
		major_version += 1
	if major_version > 2 or minor_version >= 15:
		return '2'
	else:
		return '1'

def get_feiadv():
	'''
	Returns adv_scripting connection. Connect if not not done.
	'''
	global connection
	# a simple test for server connection.
	if connection.cameras:
		try:
			camera_name_list = list(map(lambda x: x.Name,connection.cameras))
		except comtypes.COMError as e:
			# This gives back comtypes.COMError if there is no connection to server.
			# forcing instr attribute to None to force reconnection.
			connection.instr = None
	# make a coonection
	if connection.instr is None:
		try:
			comtypes.CoInitializeEx(comtypes.COINIT_MULTITHREADED)
		except:
			comtypes.CoInitialize()
		type_name = 'TEMAdvancedScripting.AdvancedInstrument.' + chooseTEMAdvancedScriptingName()
		connection.instr = comtypes.client.CreateObject(type_name)
		connection.acq = connection.instr.Acquisitions
		connection.csa = connection.acq.CameraSingleAcquisition
		connection.cameras = connection.csa.SupportedCameras
	return connection

def connectToFEIAdvScripting():
	'''
	Connects to the COM server
	'''
	global connection
	connection = get_feiadv()
	return connection
