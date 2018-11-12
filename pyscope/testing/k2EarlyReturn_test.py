from pyscope import dmsem
import time
import threading

"""
This is a test of K2 early return function timing.
"""

sumnum = 1
clear_time = 50

d = dmsem.GatanK2Super()
#d.setExposureTime(8000)
#d.setEarlyReturnFrameCount(sumnum)
# grabnum is maximized as default.
grabnum = d.getEarlyReturnRamGrabs()

dc = dmsem.GatanK2Counting()
#dc.setEarlyReturnFrameCount(100)
t_saved = []
t_not_saved1 = []
t_not_saved2 = []

def fastAcquire(dc):
    t1 =time.time()
    dc.setExposureTime(1000)
    dc.setSaveRawFrames(False)
    image = dc.getImage()  #This calls GS_getAcquiredImage
    print image.mean()
    t2 = time.time()
    return t2 - t1

def frameSavingAcquire(d):
    print 'ExposureTime set'
    d.setSaveRawFrames(True)
    print 'set to save frames'
    t0 =time.time()
    image = d.getImage()  #This calls GS_getAcquiredImage
    print image.mean()
    print d.getEarlyReturnFrameCount()
    print d.camera.getNumGrabSum()
    t1 =time.time()
    print '________________________'
    return t1 - t0

for i in range(2):
    t0 =time.time()
    d.setExposureTime(4000*(i+1))
    t_saved.append(frameSavingAcquire(d))
    #t_not_saved1.append(fastAcquire(dc))
    t_not_saved2.append(fastAcquire(dc))
    t3 = time.time()
    if clear_time > (t3-t0):
        # sleep to make sure all frames are saved to disk
        time.sleep(clear_time-(t3-t0))

print '____grab %d____sum %d________________' % (grabnum,sumnum)
print 'numGrabSum', d.camera.getNumGrabSum()
print '       frame saved return', map((lambda x: '%7.3f' % x),t_saved)
print 'frame 1st not save return', map((lambda x: '%7.3f' % x),t_not_saved1)
print 'frame 2nd not save return', map((lambda x: '%7.3f' % x),t_not_saved2)
print '________________________'
