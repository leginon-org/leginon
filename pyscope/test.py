import win32com.client
import pythoncom

def testTecnai():
	try:
		tecnai = win32com.client.Dispatch('Tecnai.Instrument')
	except pythoncom.com_error, (hr, msg, exc, arg):
		print 'Failed to initialize Tecnai interface: %s' % msg
		return

	try:
		lowdose = win32com.client.Dispatch('LDServer.LdSrv')
	except pythoncom.com_error, (hr, msg, exc, arg):
		print 'Failed to initialize low dose interface: %s' % msg
		return

	try:
		exposure = win32com.client.Dispatch('adaExp.TAdaExp',
																				clsctx=pythoncom.CLSCTX_LOCAL_SERVER)
	except pythoncom.com_error, (hr, msg, exc, arg):
		print 'Failed to initialize exposure adapter: %s' % msg
		return

	print 'Tecnai test successful'

def testTietz():
	try:
		camera = win32com.client.Dispatch('CAMC4.Camera')		
	except pythoncom.com_error, (hr, msg, exc, arg):
		print 'Failed to initialize interface CAMC4.Camera: %s' % msg
		return

	try:
		ping = win32com.client.Dispatch('pyScope.CAMCCallBack')
	except pythoncom.com_error, (hr, msg, exc, arg):
		print 'Failed to initialize interface pyScope.Ping: %s' % msg
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

	cameratype = win32com.client.constants.ctSCX
	#cameratype = win32com.client.constants.ctSimulation

	try:
		hr = camera.Initialize(cameratype, 0)
	except pythoncom.com_error, (hr, msg, exc, arg):
		print 'Error initializing camera: %s' % msg
		return

	camera.UnlockCAMC()

	print 'Tietz test successful'

if __name__ == '__main__':
	print 'Testing Tecnai...'
	testTecnai()
	print
	print 'Testing Tietz...'
	testTietz()

