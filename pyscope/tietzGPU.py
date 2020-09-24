#####################################################################################
# Copyright 2020 by Marco Oster/TVIPS GmbH
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation and/or
#    other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its contributors
#    may be used to endorse or promote products derived from this software without
#    specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
######################################################################################

from __future__ import print_function

import sys
sys.coinit_flags = 0

if sys.maxsize < 2**32 + 1:
    print("It's strongly recommended to use a 64 bit enabled python distribution, especially if you are interested in burst mode. \nOtherwise consider reducing the data using real-time drift correction on the GPU")


import comtypes, comtypes.client
import comtypes.server, comtypes.server.localserver
import mmap
import os

CAMC_PATH = r"c:\tvips\emmenu\bin\camc4.exe"

if not os.path.exists(CAMC_PATH):
    raise RuntimeError("CAMC4 not found")

camclib = comtypes.client.GetModule(CAMC_PATH)

import threading
import time
import logging
import numpy as np

import ccdcamera

log = logging.getLogger(__name__)
#logging.basicConfig(level=logging.DEBUG, format='%(asctime)s -%(levelname)s - %(message)s')

class CAMCBusyException(Exception):
    pass

class CamcGPU(object):

    #static properties
    camera = None

    def __init__(self):
        try:
            comtypes.CoInitializeEx()
        except:
            comtypes.CoInitialize()

        #get ICameraGpu interface
        self.camera = comtypes.client.CreateObject(camclib.Camera).QueryInterface(camclib.ICameraGpu)

        class CAMCCallBack(comtypes.COMObject):
            _com_interfaces_ = [camclib.ICAMCCallBack, camclib.ICAMCImageCallBack]
            _reg_clsid_ = "{B06DDC47-93F5-4236-890F-CE8E3FAB2DD5}"
            _reg_threading_ = "Both"
            _reg_progid_ = "Leginon.TVIPSCAMCCallBack.1"
            _reg_novers_progid_ = "Leginon.TVIPSCAMCCallBack"
            _reg_desc_ = "Leginon CAMC callback"
            _reg_clsctx_ = comtypes.CLSCTX_INPROC_SERVER | comtypes.CLSCTX_LOCAL_SERVER
            _regcls_ = comtypes.server.localserver.REGCLS_MULTIPLEUSE

            #callbacks
            _singleImageCallback = None
            _burstImageCallback = None

            #variable to communicate to any instance requesting the lock
            yieldLock = 1

            def __init__(self):
                super(CAMCCallBack, self).__init__()

            #methods for ICAMCCallBack
            def LivePing(self):
                #print("Ping")
                pass

            def RequestLock(self):
                log.debug("LockRequest from external") 
                return self.yieldLock


            #methods for ICAMCImageCallBack
            def BurstImageAvailable(self):
                log.debug("Burst image available")
                if self._burstImageCallback is not None:
                    self._burstImageCallback()


            def SingleImageAvailable(self):
                log.debug("Single Image Available")
                if self._singleImageCallback is not None:
                    self._singleImageCallback()
                    #reset callback
                    self._singleImageCallback = None

            #additional methods

            def SetSingleImageCallback(self, func):
                if self._singleImageCallback is not None:
                    log.debug("Callback already installed, overwriting")
                self._singleImageCallback = func

            def SetBurstImageCallback(self, func):
                #install callback
                if self._burstImageCallback is not None:
                    log.debug("Callback already installed, overwriting")
                self._burstImageCallback = func


        #callbacks
        self.camccallback = CAMCCallBack()
        self.camera.RegisterCAMCCallBack(self.camccallback.QueryInterface(camclib.ICAMCCallBack), 'Leginon')
        self.camera.RegisterCAMCImageCallBack(self.camccallback.QueryInterface(camclib.ICAMCImageCallBack))



class CamcSharedMemReader(object):
    dt_camc_shared_params = np.dtype([
       ('buf_index', np.uint32),
       ('total_buf_size', np.uint32),
       ('num_buf', np.uint32),
       ('offset_hist', np.uint32),
       ('offset_image16', np.uint32),
       ('offset_image8', np.uint32),
       ('offset_min', np.uint32),
       ('offset_max', np.uint32),
       ('offset_mean', np.uint32),
       ('offset_std', np.uint32),
       ('offset_power', np.uint32),
       ('offset_linescan', np.uint32),
       ('offset_plugin_data', np.uint32),
       ('plugin0_GUID', np.byte, 16),
       ('plugin0_offset', np.uint32), #relative to offset_plugin_data
       ('plugin0_data_size', np.uint32),
       ('reserved', np.byte, 52) #more plugin data here
       ])

    def _ReadSharedParams(self):
        
        params_mmap = mmap.mmap(-1, 128, "CAMC_SHARED_PARAMS_BUFFER")
        params_mmap.seek(0)
        params = np.frombuffer(params_mmap.read(128), self.dt_camc_shared_params)
        params_mmap.close()

        log.debug(params.__repr__())

        return params
        
    def GetLastImage(self, sizeX, sizeY):
        params = self._ReadSharedParams()
        idx = params['buf_index'][0]
        bufsize = params['total_buf_size'][0]
        numbuf = params['num_buf'][0]
        log.debug("Reading out last image: Index {}".format(idx))
        
        #use that information for opening camc livebuffer
        log.debug("opening file with {:d} bytes, that's {:d} Mb".format(bufsize*numbuf, bufsize*numbuf/1024/1024))
        livebuffer = mmap.mmap(-1, bufsize*numbuf, "CAMC_SHARED_LIVEBUFFER") #Note: if that call fails, you probably run a 32 bit python.
        livebuffer.seek(idx*bufsize + params['offset_image16'][0])
        image = np.frombuffer(livebuffer.read(2*sizeX*sizeY), dtype=np.uint16) #todo: check whether this is a copy or just a view of the memory
        log.debug("livebuffer read")
        image.shape = (sizeX, sizeY)
        livebuffer.close()
        
        log.debug("returning image")
        return image


class GPUCameraBase(ccdcamera.CCDCamera):
    cameratype = None
    _lock = threading.RLock()

    def __init__(self):
        self.unsupported = []
        super(GPUCameraBase, self).__init__()
        self.camc = CamcGPU()
        self.memreader = CamcSharedMemReader()

        self.HadCAMCOnce = False #keep track of having had camc once, since the Islocked routine might return "Leginon" also from a former session and bypass initialization

        #ccdcamera.CCDCamera specific initialization copied from tietz2.py
        self.save_frames = False #TODO: Burst mode can get multiple frames. How is the mechanism? Set save_frames to True and expect nframes to be > 1?
        self.nframes = 1 #TODO: is that the number of frames requested?

        # set binning first so we can use it
        self.initSettings()
        self.movie_aborted = False #TODO: is that set externally? A reasonable reaction would be to abort the running burst acquisition

    #function decorator
    def RequestCamera(func):

        def wrap_func(self, *args, **kwargs):
            self._lock.acquire()
            log.debug("Threadlock acquired")
            self.camc.camccallback.yieldLock = 0

            try:
                culprit, state = self.camc.camera.IsLocked
                log.debug("CAMC lock state: {} by {}".format("unlocked" if state == 0 else "locked", culprit))

                if not (state == 1 and culprit == "Leginon" and self.HadCAMCOnce): #as long as I have the lock, I'm also initialized
                    tries = 100
                    success = -1
                    while (success != camclib.crSucceed and tries > 0):
                        success = self.camc.camera.RequestLock()
                        log.debug("Tried to acquire lock ({} tries left): {}".format(tries,success) )
                        if (success == camclib.crSucceed):
                            break #don't lose time then
                        tries -= 1
                        time.sleep(0.1)

                    if success != camclib.crSucceed:
                        culprit, state = self.camc.camera.IsLocked
                        raise CAMCBusyException("Could not get camera lock within 10s. Blame " + culprit)

                    self.HadCAMCOnce = True

                    self.camc.camera.Initialize(self.cameratype, 0)
                    log.debug("CAMC initialized after having lost the lock (or first time init)")

                log.debug("CAMC lock state after trying to get the lock: {} by {}".format("unlocked" if state == 0 else "locked", culprit))

                #make sure correct camera is selected
                self.camc.ActiveCamera = self.cameratype

                log.debug("SetActive cameraid {:d}".format(self.cameratype))

                return func(self, *args, **kwargs)

            finally:
                self.camc.camccallback.yieldLock = 1
                self._lock.release()
                log.debug("Thread lock released, allowed CAMC to yield camc cameralock")

        return wrap_func

    '''
    @RequestCamera
    def acquireImage(self):
        self.camc.camera.Format(0,0,4096,4096,1,1)
        print("format set")
        self.camc.camera.AcquireImageAsync(40)
        print("Acquiring image")
    '''

    #to be called within a requested camera context
    def _getMinExpOffset(self):
        #this assumes the camera is already configured (Format has been called, mode, geometry and LC_rows selected)
        return self.camc.camera.RTPROPERTY(camclib.rtpMinExpTime, 
            self.cameratype, 
            self.dimension['y'], 
            self.camc.camera.LParam[camclib.cpReadoutMode], 
            self.camc.camera.LParam[camclib.cpImageGeometry], 
            self.dimension['x'], 
            self.camc.camera.LParam[camclib.cpLCRows], 
            0,0,0)

    #ccdcamera.CCDCamera specific initialization copied from tietz2.py
    def initSettings(self):
        self.dimension = self.getCameraSize()
        self.binning = {'x':1, 'y':1}
        self.offset = {'x':0, 'y':0}
        self.exposure = 100.0
        self.exposuretype = 'normal'
        self.start_frame_number = 1 #TODO: ??
        self.end_frame_number = None #TODO: ??

    def getCameraModelName(self):
        return self.camera_name

    def getIntensityAveraged(self):
        '''
        Returns True if camera array value is normalized internally
        and thus does not increase value for longer exposure time.
        '''
        return False

    def getBinnedMultiplier(self):
        '''
        Binned array values and not sum of the pixels but an average.
        '''
        binning = self.getBinning()
        return binning['x']*binning['y']

    def getCalculateNormOnDark(self):
        '''
        Reduce the norm image calculation since dark is taken frequently.
        '''
        return False

    def requireRecentDarkOnBright(self):
        return True

    def setDimension(self, value):
        self.dimension = value

    def getDimension(self):
        return self.dimension

    def getCameraBinnings(self):
        return self.binning_limits

    def setBinning(self, value):
        self.binning = value

    def getBinning(self):
        return self.binning

    def setOffset(self, value):
        self.offset = value

    def getOffset(self):
        return self.offset

    def setExposureTime(self, ms):
        self.exposure = float(ms)

    def getExposureTime(self):
        # milliseconds
        return float(self.exposure)

    def _setFormat(self):
        """
        Call Format to set format for next exposure. Camc needs to be locked and correct camera selected, use within @RequestCamera protected methods

        """
        # final bin
        binning = self.binning
        dimension = self.dimension

        # final range
        unbinoff = {'x':self.offset['x']*binning['x'], 'y':self.offset['y']*binning['y']}

        # send it to camera
        self.camc.camera.Format(unbinoff['x'], unbinoff['y'], dimension['x'], dimension['y'], binning['x'], binning['y'])

    @RequestCamera
    def _getImage(self):
        """Get a single image."""


        self._setFormat()

        self.camc.camera.LParam[camclib.cpBurstNumImages] = 1
        self.camc.camera.LParam[camclib.cpReadoutMode] = 1 #Beam blanking mode for single images

        #TODO: Revisit this if Leginon is ever ported to python3 and use async await
        im = None
        ImageReceivedEvent = threading.Event()

        self.camc.camccallback.SetSingleImageCallback(ImageReceivedEvent.set)

        self.camc.camera.AcquireImageAsync(int(self.exposure)) 

        ImageReceivedEvent.wait(0.001 * self.exposure + 10) #timeout

        if not ImageReceivedEvent.isSet():
            raise Exception("Could not acquire image in reasonable time")

        im = self.memreader.GetLastImage(self.dimension['x'], self.dimension['y'])

        return im

    @RequestCamera
    def _getBurstImage(self, n=10):

        self._setFormat()

        self.camc.camera.LParam[camclib.cpBurstNumImages] = n 
        self.camc.camera.LParam[camclib.cpReadoutMode] = 3 #RS mode for burst
        self.camc.camera.LParam[camclib.cpBurstUseProcessing] = 0

        expOffset = self._getMinExpOffset()

        camcExpTime = max(expOffset, int(self.exposure) - expOffset)

        #allocate
        import gc; gc.collect()
        im = np.empty((n, self.dimension['x'], self.dimension['y']), dtype=np.uint16)

        evt = threading.Event()
        self.camc.camccallback.SetBurstImageCallback(evt.set)

        self.camc.camera.AcquireImageAsync(camcExpTime)
        seen = np.zeros(n, dtype=np.bool)
        for j in range(n):
            evt.wait(3)
            seen[j] = not evt.isSet() #keep track of missing events
            im[j] = self.memreader.GetLastImage(self.dimension['x'], self.dimension['y'])
            evt.clear()

        missed = np.count_nonzero(seen)
        if missed > 0:
            print("TVIPS XF416: missed {:d} burst images at {:d}({:d})ms exposure time".format(missed, int(self.exposure), camcExpTime))


        return im 

    @RequestCamera
    def _getDriftCorrectedImage(self, n=10):

        self._setFormat()

        self.camc.camera.LParam[camclib.cpBurstNumImages] = n 
        self.camc.camera.LParam[camclib.cpReadoutMode] = 3 #RS mode for burst

        expOffset = self._getMinExpOffset()

        camcExpTime = max(expOffset, int(self.exposure) - expOffset)

        #set up drift correction parameters
        """
        8001 cpXcfCutAcp Long DriftDoCutACP 
        8002 cpXcfAcpPixels Long DriftCutACPPixels 
        8003 cpXcfWidth Long DriftXcfWidth 
        8004 cpXcfHeight Long DriftXcfHeight 
        8005 cpXcfOffsetX Long DriftXcfOffsetX 
        8006 cpXcfOffsetY Long DriftXcfOffsetY 
        8007 cpXcfApplyBandPass Long DriftXcfApplyBandpass 
        8008 cpXcfBandLow Long DriftXcfBandLow 
        8009 cpXcfBandHigh Long DriftXcfBandHigh 
        8010 cpXcfDoPhaseCorrelation Long Do Phase Correlation 
        8011 cpXcfDoFitPeak Long Fit XCF Peak 
        8012 cpXcfBinning Long Calculate XCF on binned image
        """

        self.camc.camera.LParam[camclib.cpXcfCutAcp] = 0
        self.camc.camera.LParam[camclib.cpXcfWidth] = self.dimension['x']
        self.camc.camera.LParam[camclib.cpXcfHeight] = self.dimension['y']
        self.camc.camera.LParam[camclib.cpXcfOffsetX] = self.offset['x']
        self.camc.camera.LParam[camclib.cpXcfOffsetY] = self.offset['y']

        self.camc.camera.LParam[camclib.cpXcfApplyBandPass] = 1
        self.camc.camera.LParam[camclib.cpXcfBandLow] = 0
        self.camc.camera.LParam[camclib.cpXcfBandHigh] = 3

        self.camc.camera.LParam[camclib.cpXcfDoFitPeak] = 1

        self.camc.camera.LParam[camclib.cpBurstUseProcessing] = 1
        self.camc.camera.LParam[camclib.cpBurstWhatProcessing] = 2 #(0=sum, 1=avr, 2=align, 3=counting )

        ImageReceivedEvent = threading.Event()

        self.camc.camccallback.SetBurstImageCallback(ImageReceivedEvent.set)
        self.camc.camera.AcquireImageAsync(camcExpTime) 

        ImageReceivedEvent.wait(0.001 * self.exposure * n + 10) #timeout

        if not ImageReceivedEvent.isSet():
            raise Exception("Could not acquire image in reasonable time")

        im = self.memreader.GetLastImage(self.dimension['x'], self.dimension['y'])

        return im



class XF416(GPUCameraBase):
    name = 'TVIPS-XF416'  #Used for database record and gui display. Short and without space.
    camera_name = 'TVIPS XF416' # full name for camera internal interface. No limit on the name.
    binning_limits = [1, 2, 4, 8]

    cameratype = camclib.ctXF416e_GPU

class XF416R(GPUCameraBase):
    name = 'TVIPS-XF416r'
    camera_name = 'TVIPS XF416 retractable'
    binning_limits = [1, 2, 4, 8]

    cameratype = camclib.ctXF416e_GPUr

    #todo: insert code for retracting/inserting




