
import time
import gatansocket

gs = gatansocket.GatanSocket()

# readmodes = {'linear': 0, 'counting': 1, 'super resolution': 2}
# hardwareProc = {'none': 0, 'dark': 2, 'gain': 4, 'dark+gain': 6}

readMode = 1
scaling = 1.0
hardwareProc = 0
doseFrac = False
frameTime = 0.25
alignFrames = False
saveFrames = False
filt = 'None'

processing = 'unprocessed'
binning = 1
top = 0
left = 0
bottom = 3968
right = 4096
exposure = 0.5
shutterDelay = 0.0

def loop(n):
	for i in range(n):
		print 'I', i
		if not gs.IsCameraInserted(0):
			print '   *** INSERTING'
			gs.InsertCamera(0, True)
		print '   ACQ'
		gs.SetK2Parameters(readMode, scaling, hardwareProc, doseFrac, frameTime, alignFrames, saveFrames, filt='')
		gs.GetImage(processing, binning, top, left, bottom, right, exposure, shutterDelay)
