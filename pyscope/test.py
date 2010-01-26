import win32com.client
import pythoncom

def testTecnai():
	try:
		tecnai = win32com.client.Dispatch('Tecnai.Instrument')
	except pythoncom.com_error, (hr, msg, exc, arg):
		print 'Failed to initialize Tecnai interface: %s' % msg
		return
	else:
		print 'Initialized Tecnai interface'

	try:
		lowdose = win32com.client.Dispatch('LDServer.LdSrv')
	except pythoncom.com_error, (hr, msg, exc, arg):
		print 'Failed to initialize Low Dose interface: %s' % msg
		return
	else:
		print 'Initialized Low Dose interface'

	try:
		exposure = win32com.client.Dispatch('adaExp.TAdaExp',
																				clsctx=pythoncom.CLSCTX_LOCAL_SERVER)
	except pythoncom.com_error, (hr, msg, exc, arg):
		print 'Failed to initialize Exposure Adapter: %s' % msg
		return
	else:
		print 'Initialized Exposure Adapter interface'

	print 'Tecnai test successful'

def testTietz():
	try:
		camera = win32com.client.Dispatch('CAMC4.Camera')		
	except pythoncom.com_error, (hr, msg, exc, arg):
		print 'Failed to initialize interface CAMC4.Camera: %s' % msg
		return

	try:
		ping = win32com.client.Dispatch('pyscope.CAMCCallBack')
	except pythoncom.com_error, (hr, msg, exc, arg):
		print 'Failed to initialize interface pyscope.Ping: %s' % msg
		return

	try:
		hr = camera.RegisterCAMCCallBack(ping, 'EM')
	except pythoncom.com_error, (hr, msg, exc, arg):
		print 'Error registering callback COM object: %s' % msg
		return

	hr = camera.RequestLock()
	if hr == win32com.client.constants.crDeny:
		print 'Error locking camera, denied lock'
		return
	elif hr == win32com.client.constants.crBusy:
		print 'Error locking camera, camera busy'
		return
	elif hr == win32com.client.constants.crSucceed:
		pass

	cameratypes = [('Tietz Simulation', 'ctSimulation'),
									('Tietz SCX', 'ctSCX'),
									('Tietz PXL', 'ctPXL'),
									('Tietz PVCam', 'ctPVCam'),
									('Tietz FastScan', 'ctFastScan'),
									('Tietz FastScan Firewire', 'ctF114_FW')]

	for name, cameratype in cameratypes:
		cameratype = getattr(win32com.client.constants, cameratype)
		print name + ':',
		try:
			hr = camera.Initialize(cameratype, 0)
		except pythoncom.com_error, (hr, msg, exc, arg):
			print 'error initializing camera, %s' % msg
		else:
			print 'camera initialization succeeded'

	camera.UnlockCAMC()

def testGatan():
	pythoncom.CoInitializeEx(pythoncom.COINIT_MULTITHREADED)
	camera = None
	try:
		camera = win32com.client.dynamic.Dispatch('TecnaiCCD.GatanCamera')
	except pythoncom.com_error, e:
		pass
	else:
		print 'Initialized Gatan interface (.1)'

	try:
		camera = win32com.client.dynamic.Dispatch('TecnaiCCD.GatanCamera.2')
	except pythoncom.com_error, e:
		pass
	else:
		print 'Initialized Gatan interface (.2)'

	if camera is None:
		print 'Gatan test failed (unable to initialize interfaces)'
		return

	print 'Gatan test successful'

if __name__ == '__main__':
	print 'Testing Tecnai...'
	testTecnai()
	print 
	#print 'Testing Tietz...'
	#testTietz()
	#print 'Tietz test completed.'

	print 'Testing Gatan...'
	testGatan()
