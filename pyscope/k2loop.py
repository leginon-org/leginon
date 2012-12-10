
import time
import gatansocket

gs = gatansocket.GatanSocket()

# readmodes = {'linear': 0, 'counting': 1, 'super resolution': 2}
# hardwareProc = {'none': 0, 'dark': 2, 'gain': 4, 'dark+gain': 6}

readMode = 1
scaling = 1.0
hardwareProc = 1
doseFrac = False
frameTime = 0.25
alignFrames = False
saveFrames = False
filt = 'None'

processing = 'unprocessed'
binning = 1
top = 0
left = 0
#bottom = 3712
#right = 3840
right = 3712
bottom = 3840

exposure = 0.5
shutterDelay = 0.0

def log(s):
	t = time.time()
	f = open('c:\\loop.log', 'a')
	f.write(str(t) + ': ' + s + '\n')
	f.close()

def loop(n):
	for i in range(n):
		log('I: %s' % (i,))
		if not gs.IsCameraInserted(0):
			log('   *** INSERTING')
			gs.InsertCamera(0, True)
		log('   SetK2Parameters')
		gs.SetK2Parameters(readMode, scaling, hardwareProc, doseFrac, frameTime, alignFrames, saveFrames, filt='')
		log('   GetImage')
		gs.GetImage(processing, binning, top, left, bottom, right, exposure, shutterDelay)
