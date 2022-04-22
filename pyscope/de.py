## de.py
## Leginon interface for Direct Electron cameras
## 
## CHANGE LOG
##   2021-12-17 : Initial version using DE API v2, based on the previous de.py
##                from the Leginon repository. (bbammes@directelectron.com)
##   2022-01-04 : Fixed bugs. (bbammes@directelectron.com)

import DEAPI

import numpy
import os
import time
import pyami.imagefun
import ccdcamera
import threading
from pyami import moduleconfig


## Print debugging output to the terminal
## DEBUG_ALL shows every function call.
## DEBUG_SPECIFIC is a flag that can be used in the code to output only specific
##   function calls. To use this flag, change "if DEBUG_ALL:" to
##   "if DEBUG_ALL or DEBUG_SPECIFIC:" in the particular places you want to
##   output. Note: DEBUG_SPECIFIC is only helpful if DEBUG_ALL = False.
DEBUG_ALL = False
DEBUG_SPECIFIC = False


## Global variables for DE-Server and storing the current active camera
__deserver = None
__active_camera = None
__deserver_lock = threading.RLock()


## Decorator for thread safe DE-Server calls
def locked(fun):
    def newfun(*args, **kwargs):
        __deserver_lock.acquire()
        try:
            return fun(*args, **kwargs)
        finally:
            __deserver_lock.release()
    return newfun


################################################################################
## Thread-safe DE-Server functions. DE-Server API functions should occur only
## within this section. Interactions with DE-Server API in the remainder of this
## file should only occur through these thread-safe wrapped functions.


## Connect to DE-Server
@locked
def de_connect():
    global __deserver
    if __deserver:
        return
    if DEBUG_ALL:
        print 'de_connect()'
    __deserver = DEAPI.Client()
    __deserver.Connect()
    print 'DE-Server connected'


## Disconnect from DE-Server
@locked
def de_disconnect():
    global __deserver
    if DEBUG_ALL:
        print 'de_disconnect()'
    __deserver.Disconnect()
    __deserver = None
    print 'DE-Server disconnected'


## Set the active camera in DE-Server
@locked
def de_setActiveCamera(camera_name):
    global __deserver
    global __active_camera
    if __active_camera != camera_name:
        if DEBUG_ALL:
            print 'de_setActiveCamera(%s)' % camera_name
        camera_names_list = __deserver.ListCameras()
        if camera_name in camera_names_list:
            __deserver.SetCurrentCamera(camera_name)
            __active_camera = camera_name
        else:
            print '%s is not a valid camera name in DE-Server' % camera_name


## List all camera properties
@locked
def de_listProperties(camera_name):
    if DEBUG_ALL:
        print 'de_listProperties()'
    global __deserver
    de_setActiveCamera(camera_name)
    return __deserver.ListProperties()


## Get a camera property value
@locked
def de_getProperty(camera_name, property_name):
    global __deserver
    de_setActiveCamera(camera_name)
    property_value = __deserver.GetProperty(property_name)
    if DEBUG_ALL:
        print 'de_getProperty(%s) = [%s]' % (property_name, property_value)
    return property_value


## Set a camera property value
@locked
def de_setProperty(camera_name, property_name, property_value):
    global __deserver
    de_setActiveCamera(camera_name)
    __deserver.SetProperty(property_name, property_value)
    if DEBUG_ALL:
        print 'de_setProperty(%s, %s)' % (property_name, property_value)


## Get an image
@locked
def de_getImage(camera_name):
    global __deserver
    de_setActiveCamera(camera_name)
    if DEBUG_ALL:
        print 'de_getImage()'
    t0 = time.time()
    timeout_count = 600
    while (__deserver.GetProperty('Autosave Status') == 'In Progress') and (timeout_count > 0):
        time.sleep(0.1)
        timeout_count -= 1
    image = __deserver.GetImage('uint16')
    t1 = time.time()
    print 'Image acquired in %0.3f s' % (t1 - t0)
    return image


## End thread-safe DE-Server functions.
################################################################################


################################################################################
## DECameraBase class. This class contains parameters and functions that are
## common to all Direct Electron cameras. Note: BEFORE calling the parent
## "__init__" in each derived class, you MUST set self.model_name and
## self.hardware_binning.


class DECameraBase(ccdcamera.CCDCamera):
    
    
    ## Parameters
    log_methods = False
    properties_list = []
    camera_size = {'x': -1, 'y': -1}
    retractable = True
    hardware_binning = {'x': -1, 'y': -1}
    software_binning_acts_like_summing = True
    pixel_size_in_meters = -1.0
    frames_per_second = -1.0
    exposure_time_seconds = -1.0
    exposure_mode = 'normal'
    frames_per_movie_frame = -1
    current_binning = {'x': -1, 'y': -1}
    current_offset = {'x': -1, 'y': -1}
    current_dimension = {'x': -1, 'y': -1}
    
    
    ## Constructor
    def __init__(self):
        ccdcamera.CCDCamera.__init__(self)
        self.connectDEAPI()
    
    
    ## Destructor
    def __del__(self):
        self.disconnectDEAPI()
    
    
    ## Get the sensor size for the current camera
    def _getCameraSize(self):
        if DEBUG_ALL:
            print '_getCameraSize()'
        sensor_size_x = int(self.getProperty('Sensor Size X (pixels)'))
        sensor_size_y = int(self.getProperty('Sensor Size Y (pixels)'))
        return {'x': sensor_size_x, 'y': sensor_size_y}
    
    
    ## Get an image from the camera
    def _getImage(self):
        if DEBUG_ALL:
            print '_getImage()'
        self.preAcquisitionSetup()
        t0 = time.time()
        image = de_getImage(self.model_name)
        t1 = time.time()
        self.exposure_timestamp = (t1 + t0) / 2.0
        if not isinstance(image, numpy.ndarray):
            raise ValueError('GetImage did not return array')
        return image
    
    
    ## Connect to DE-Server and set the camera properties to default initial values
    def connectDEAPI(self):
        if DEBUG_ALL:
            print 'connectDEAPI()'
        
        # Connect to DE-Server and set the active camera
        de_connect()
        de_setActiveCamera(self.model_name)
        
        # Save the list of all property names for the current camera
        self.getPropertiesList()
        
        # Get the full size of the camera
        self.camera_size = self._getCameraSize();
        
        # Check whether the camera is retractable
        self.retractable = self.hasProperty('Camera Position Control')
        
        # Get camera properties that will not be changed by Leginon
        self.hardware_binning = {'x': 1, 'y': 1}
        if self.hasProperty('Hardware Binning X'):
            if self.hardware_binning['x'] > 0:
                self.setProperty('Hardware Binning X', self.hardware_binning['x'])
            self.hardware_binning['x'] = int(self.getProperty('Hardware Binning X'))
        if self.hasProperty('Hardware Binning Y'):
            if self.hardware_binning['y'] > 0:
                self.setProperty('Hardware Binning Y', self.hardware_binning['y'])
            self.hardware_binning['y'] = int(self.getProperty('Hardware Binning Y'))
        self.software_binning_acts_like_summing = True
        binning_method = self.getProperty('Binning Method')
        if (binning_method == 'Average') or (binning_method == 'Sample'):
            self.software_binning_acts_like_summing = False
        self.pixel_size_in_meters = float(self.getProperty('Sensor Pixel Pitch (um)')) / 1000000.0
        
        # Set default initial property values for the camera
        self.setProperty('Exposure Mode', 'Normal')
        self.setProperty('Image Processing - Flatfield Correction', 'Dark and Gain')
        self.setProperty('Image Processing - Apply Gain on Final', 'On')
        self.setProperty('Image Processing - Apply Gain on Movie', 'Off')
        self.setProperty('Binning Mode', 'Software Only')
        self.setProperty('Autosave Movie Sum Count', 1)
        
        # Set default initial geometry (binning and ROI) for the camera
        self.setProperty('Binning X', 1)
        self.setProperty('Binning Y', 1)
        self.setProperty('ROI Offset X', 0)
        self.setProperty('ROI Offset Y', 0)
        self.setProperty('ROI Size X', self.camera_size['x'])
        self.setProperty('ROI Size Y', self.camera_size['y'])
        
        # Get the initial geometry (binning and ROI) back from DE-Server to ensure nothing was adjusted
        binning_x = int(self.getProperty('Binning X'))
        binning_y = int(self.getProperty('Binning Y'))
        roi_offset_x = int(self.getProperty('ROI Offset X'))
        roi_offset_y = int(self.getProperty('ROI Offset Y'))
        roi_size_x = int(self.getProperty('ROI Size X'))
        roi_size_y = int(self.getProperty('ROI Size Y'))
        
        # Save the current values of properties that will be set during preAcquisitionSetup
        self.binning = {'x': binning_x, 'y': binning_y}
        self.offset = {'x': roi_offset_x, 'y': roi_offset_y}
        self.dimension = {'x': roi_size_x, 'y': roi_size_y}
        self.current_binning = {'x': self.binning['x'], 'y': self.binning['y']}
        self.current_offset = {'x': self.offset['x'], 'y': self.offset['y']}
        self.current_dimension = {'x': self.dimension['x'], 'y': self.dimension['y']}
        
        # Save other properties that are updated on-demand
        self.frames_per_second = float(self.getProperty('Frames Per Second'))
        self.exposure_time_seconds = float(self.getProperty('Exposure Time (seconds)'))
        exposure_type = self.getProperty('Exposure Mode')
        self.exposure_mode = exposure_type.lower()
        self.frames_per_movie_frame = int(self.getProperty('Autosave Movie Sum Count'))
    
    
    ## Disconnect from DE-Server
    def disconnectDEAPI(self):
        if DEBUG_ALL:
            print 'disconnectDEAPI()'
        de_disconnect()
    
    
    ## Get a list of all DE-Server property names
    def getPropertiesList(self):
        if DEBUG_ALL:
            print 'getPropertiesList()'
        self.properties_list = de_listProperties(self.model_name)
    
    
    ## Check whether a property name exists for the current camera
    def hasProperty(self, property_name):
        if DEBUG_ALL:
            print 'hasProperty(%s)' % property_name
        return property_name in self.properties_list
    
    
    ## Get the value of a camera property
    def getProperty(self, property_name):
        if DEBUG_ALL:
            print 'getProperty(%s)' % property_name
        property_value = de_getProperty(self.model_name, property_name)
        return property_value
    
    
    ## Set the value of a camera property
    def setProperty(self, property_name, property_value):
        if DEBUG_ALL:
            print 'setProperty(%s, %s)' % (property_name, property_value)
        de_setProperty(self.model_name, property_name, property_value)
    
    
    ## Get the exposure time in milliseconds
    def getExposureTime(self):
        if DEBUG_ALL:
            print 'getExposureTime()'
        return round(self.exposure_time_seconds * 1000.0, 2)
    
    
    ## Set the exposure time in milliseconds
    def setExposureTime(self, milliseconds):
        if DEBUG_ALL:
            print 'setExposureTime(%s)' % milliseconds
        seconds = round(milliseconds / 1000.0, 5)
        if seconds != self.exposure_time_seconds:
            self.setProperty('Exposure Time (seconds)', seconds)
            self.exposure_time_seconds = round(float(self.getProperty('Exposure Time (seconds)')), 5)
    
    
    ## Get the frame time in milliseconds
    def getFrameTime(self):
        if DEBUG_ALL:
            print 'getFrameTime()'
        return round(1000.0 / self.frames_per_second, 2)
    
    
    ## Set the frame time in milliseconds
    def setFrameTime(self, milliseconds):
        if DEBUG_ALL:
            print 'setFrameTime(%s)' % milliseconds
        fps = round(1000.0 / milliseconds, 1)
        if fps != self.frames_per_second:
            self.setProperty('Frames Per Second', fps)
            self.frames_per_second = round(float(self.getProperty('Frames Per Second')), 1)
    
    
    ## Get the frame rate in Hz
    def getFramesPerSecond(self):
        if DEBUG_ALL:
            print 'getFramesPerSecond()'
        return round(self.frames_per_second, 1)
    
    
    ## Set the frame rate in Hz
    def setFramesPerSecond(self, frames_per_second):
        if DEBUG_ALL:
            print 'setFramesPerSecond(%s)' % frames_per_second
        fps = round(frames_per_second, 1)
        if fps != self.frames_per_second:
            self.setProperty('Frames Per Second', fps)
            self.frames_per_second = round(float(self.getProperty('Frames Per Second')), 1)
    
    
    # Get the maximum frames per second of the camera
    def getFramesPerSecondMax(self):
        if DEBUG_ALL:
            print 'getFramesPerSecondMax()'
        return round(float(self.getProperty('Frames Per Second (Max)')), 1)
    
    
    ## Set the frame rate to the maximum speed of the camera
    def setFramesPerSecondToMax(self):
        if DEBUG_ALL:
            print 'setFramesPerSecondToMax()'
        fps = self.getFramesPerSecondMax()
        if fps != self.frames_per_second:
            self.setProperty('Frames Per Second', fps)
            self.frames_per_second = round(float(self.getProperty('Frames Per Second')), 1)
    
    
    ## Get the readout delay in milliseconds (obsolete)
    def getReadoutDelay(self):
        if DEBUG_ALL:
            print 'getReadoutDelay()'
        return 0.0
    
    
    ## Set the readout delay in milliseconds (obsolete)
    def setReadoutDelay(self, milliseconds):
        if DEBUG_ALL:
            print 'setReadoutDelay(%s)' % milliseconds
        return
    
    
    ## Get the current binning value
    def getBinning(self):
        if DEBUG_ALL:
            print 'getBinning()'
        return self.binning
    
    
    ## Set the current binning value
    def setBinning(self, binning_dict):
        if DEBUG_ALL:
            print 'setBinning(%s, %s)' % (binning_dict['x'], binning_dict['y'])
        self.binning = {'x': binning_dict['x'], 'y': binning_dict['y']}
    
    
    ## Get the multiplier for scaling binned images so that binning performs like summing binned pixels
    def getBinnedMultiplier(self):
        if DEBUG_ALL:
            print 'getBinnedMultiplier()'
        multiplier = float(self.hardware_binning['x'] * self.hardware_binning['y'])
        if not self.software_binning_acts_like_summing:
            multiplier *= float(self.binning['x'] * self.binning['y'])
        return multiplier
    
    
    ## Get the current output image dimensions
    def getDimension(self):
        if DEBUG_ALL:
            print 'getDimension()'
        return self.dimension
    
    
    ## Set the current output image dimensions
    def setDimension(self, dimension_dict):
        if DEBUG_ALL:
            print 'setDimension(%s, %s)' % (dimension_dict['x'], dimension_dict['y'])
        self.dimension = {'x': dimension_dict['x'], 'y': dimension_dict['y']}
    
    
    ## Get the current ROI offset values
    def getOffset(self):
        if DEBUG_ALL:
            print 'getOffset()'
        return self.offset
    
    
    ## Set the current ROI offset values
    def setOffset(self, offset_dict):
        if DEBUG_ALL:
            print 'setOffset(%s, %s)' % (offset_dict['x'], offset_dict['y'])
        self.offset = {'x': offset_dict['x'], 'y': offset_dict['y']}
    
    
    ## Get the camera pixel size in meters
    def getPixelSize(self):
        if DEBUG_ALL:
            print 'getPixelSize()'
        return {'x': self.pixel_size_in_meters, 'y': self.pixel_size_in_meters}
    
    
    ## Get whether the camera is retractable
    def getRetractable(self):
        if DEBUG_ALL:
            print 'getRetractable()'
        return self.retractable
    
    
    ## Insert (value = True) or retract (value = False) the camera
    def setInserted(self, value):
        if DEBUG_ALL:
            print 'setInserted(%s)' % value
        if self.retractable:
            camera_position = self.getProperty('Camera Position Status')
            if value:
                if (camera_position != 'Extended'):
                    self.setProperty('Camera Position Control', 'Extend')
                    timeout_count = 30
                    while (self.getProperty('Camera Position Status') != 'Extended') and (timeout_count > 0):
                        time.sleep(1.0)
                        timeout_count -= 1
            else: 
                if (camera_position != 'Retracted'):
                    self.setProperty('Camera Position Control', 'Retract')
                    timeout_count = 30
                    while (self.getProperty('Camera Position Status') != 'Retracted') and (timeout_count > 0):
                        time.sleep(1.0)
                        timeout_count -= 1
    
    
    ## Get the camera position (True indicates inserted, False indicates retracted)
    def getInserted(self):
        if DEBUG_ALL:
            print 'getInserted()'
        if self.retractable:
            camera_position = self.getProperty('Camera Position Status')
            return camera_position == 'Extended'
        return True
    
    
    ## Get a list of the valid exposure types
    def getExposureTypes(self):
        if DEBUG_ALL:
            print 'getExposureTypes()'
        return ['normal','dark','trial','gain']
    
    
    ## Get the current exposure type
    def getExposureType(self):
        if DEBUG_ALL:
            print 'getExposureType()'
        exposure_type = self.getProperty('Exposure Mode')
        return exposure_type.lower()
    
    
    ## Set the exposure type
    def setExposureType(self, value):
        if DEBUG_ALL:
            print 'setExposureType(%s)' % value
        if value != self.exposure_mode:
            self.setProperty('Exposure Mode', value.capitalize())
            exposure_type = self.getProperty('Exposure Mode')
            self.exposure_mode = exposure_type.lower()
    
    
    ## Set the state of electron counting ('On' or 'Off')
    def setElectronCounting(self, state):
        if DEBUG_ALL:
            print 'setElectronCounting(%s)' % state
        if (state == 'On') and self.hasProperty('Event Counting - Method'):
            self.setProperty('Image Processing - Mode', 'Counting')
        else:
            self.setProperty('Image Processing - Mode', 'Integrating')
    
    
    ## Get the state of electron counting ('On' or 'Off')
    def getElectronCounting(self):
        if DEBUG_ALL:
            print 'getElectronCounting()'
        state = self.getProperty('Image Processing - Mode')
        if state == 'Counting':
            return 'On'
        return 'Off'
    
    
    ## Get the total number of frames to be acquired at the current exposure time and frame rate
    def getNumberOfFrames(self):
        if DEBUG_ALL:
            print 'getNumberOfFrames()'
        return int(self.getProperty('Frame Count'))
    
    
    ## Get the number of frames to sum for each output movie frame
    def getMovieSumCount(self):
        if DEBUG_ALL or DEBUG_SPECIFIC:
            print 'getMovieSumCount()'
        return self.frames_per_movie_frame
    
    
    ## Get the number of frames to sum for each output movie frame
    def setMovieSumCount(self, value):
        if DEBUG_ALL or DEBUG_SPECIFIC:
            print 'setMovieSumCount(%s)' % value
        if value != self.frames_per_movie_frame:
            self.setProperty('Autosave Movie Sum Count', value)
            self.frames_per_movie_frame = int(self.getProperty('Autosave Movie Sum Count'))
    
    
    ## Get whether the frame stack will be saved during the next acquisition
    def getSaveRawFrames(self):
        if DEBUG_ALL or DEBUG_SPECIFIC:
            print 'getSaveRawFrames()'
        return self.getProperty('Autosave Movie') == 'On'
    
    
    ## Set whether the frame stack will be saved during the next acquisition
    def setSaveRawFrames(self, value):
        if DEBUG_ALL or DEBUG_SPECIFIC:
            print 'setSaveRawFrames(%s)' % value
        if value:
            self.setProperty('Autosave Movie', 'On')
        else:
            self.setProperty('Autosave Movie', 'Off')
    
    
    ## Get the filename of the frame stack saved during the last acquisition
    def getPreviousRawFramesName(self):
        if DEBUG_ALL:
            print 'getPreviousRawFramesName()'
        output_fullpath = self.getProperty('Autosave Integrated Movie Frames File Path')
        if self.hasProperty('Event Counting - Method'):
            if self.getProperty('Image Processing - Mode') == 'Counting':
                output_fullpath = self.getProperty('Autosave Counted Movie Frames File Path')
        if len(output_fullpath) > 0 :
            return os.path.basename(output_fullpath)
        return ''
    
    
    ## Get the number of frames saved during the last acquisition
    def getNumberOfFramesSaved(self):
        if DEBUG_ALL:
            print 'getNumberOfFramesSaved()'
        if self.hasProperty('Event Counting - Method'):
            if self.getProperty('Image Processing - Mode') == 'Counting':
                return int(self.getProperty('Autosave Counted Movie Frames Written'))
        return int(self.getProperty('Autosave Integrated Movie Frames Written'))
    
    
    ## Get the camera temperature status
    def getTemperatureStatus(self):
        if DEBUG_ALL:
            print 'getTemperatureStatus()'
        return self.getProperty('Temperature - Detector Status')
    
    
    ## Get the camera sensor temperature in Celsius
    def getTemperature(self):
        if DEBUG_ALL:
            print 'getTemperature()'
        return float(self.getProperty('Temperature - Detector (Celsius)'))
    
    
    ## Perform dark and gain correction in DE-Server instead of in Leginon
    def getSystemGainDarkCorrected(self):
        if DEBUG_ALL:
            print 'getSystemGainDarkCorrected()'
        return True
    
    
    ## Get the frame time in milliseconds for counting mode where the camera frame rate is always set to its maximum value
    def getFrameTimeForCounting(self):
        if DEBUG_ALL:
            print 'getFrameTimeForCounting()'
        raw_frame_time = 1000.0 / self.frames_per_second
        return round(raw_frame_time * self.frames_per_movie_frame, 2)
    
    
    ## Set the frame time in milliseconds for counting mode where the camera frame rate is always set to its maximum value
    def setFrameTimeForCounting(self, milliseconds):
        if DEBUG_ALL:
            print 'setFrameTimeForCounting(%s)' % milliseconds
        raw_frame_time = 1000.0 / self.frames_per_second
        dose_fractionation = round(milliseconds / raw_frame_time, 0)
        if dose_fractionation < 0:
            dose_fractionation = 1
        self.setMovieSumCount(dose_fractionation)
    
    
    ## Perform camera setup before acquiring an image
    def preAcquisitionSetup(self):
        if DEBUG_ALL:
            print 'preAcquisitionSetup()'
        if (self.binning['x'] != self.current_binning['x']) or (self.binning['y'] != self.current_binning['y']):
            self.setProperty('Binning X', self.binning['x'])
            self.setProperty('Binning Y', self.binning['y'])
            self.binning['x'] = int(self.getProperty('Binning X'))
            self.binning['y'] = int(self.getProperty('Binning Y'))
            self.current_binning = {'x': self.binning['x'], 'y': self.binning['y']}
        offset_x = self.offset['x'] * self.binning['x']
        offset_y = self.offset['y'] * self.binning['y']
        dimension_x = self.dimension['x'] * self.binning['x']
        dimension_y = self.dimension['y'] * self.binning['y']
        if (offset_x != self.current_offset['x']) or (offset_y != self.current_offset['y']) or (dimension_x != self.current_dimension['x']) or (dimension_y != self.current_dimension['y']):
            self.setProperty('ROI Offset X', 0)
            self.setProperty('ROI Offset Y', 0)
            self.setProperty('ROI Size X', dimension_x)
            self.setProperty('ROI Size Y', dimension_y)
            self.setProperty('ROI Offset X', offset_x)
            self.setProperty('ROI Offset Y', offset_y)
            self.offset['x'] = int(self.getProperty('ROI Offset X')) / self.binning['x']
            self.offset['y'] = int(self.getProperty('ROI Offset Y')) / self.binning['y']
            self.dimension['x'] = int(self.getProperty('Image Size X (pixels)'))
            self.dimension['y'] = int(self.getProperty('Image Size Y (pixels)'))
            self.current_offset = {'x': self.offset['x'], 'y': self.offset['y']}
            self.current_dimension = {'x': self.dimension['x'], 'y': self.dimension['y']}


## End DECameraBase class.
################################################################################


################################################################################
## DE12 class.


class DE12(DECameraBase):
    
    
    ## Parameters
    name = 'DE12'
    model_name = 'DE12'
    
    
    ## Constructor
    def __init__(self):
        self.hardware_binning = {'x': 1, 'y': 1}
        DECameraBase.__init__(self)
        self.setFramesPerSecond(20)
        self.setElectronCounting('Off')
        self.setMovieSumCount(1)


## End DE12 class.
################################################################################


################################################################################
## DEDirectView class.


class DEDirectView(DECameraBase):
    
    
    ## Parameters
    name = 'DEDirectView'
    model_name = 'DirectView'
    
    
    ## Constructor
    def __init__(self):
        self.hardware_binning = {'x': 1, 'y': 1}
        DECameraBase.__init__(self)
        self.setFramesPerSecond(20)
        self.setElectronCounting('Off')
        self.setMovieSumCount(1)


## End DEDirectView class.
################################################################################


################################################################################
## DE20 class.


class DE20(DECameraBase):
    
    
    ## Parameters
    name = 'DE20'
    model_name = 'DE20'
    
    
    ## Constructor
    def __init__(self):
        self.hardware_binning = {'x': 1, 'y': 1}
        DECameraBase.__init__(self)
        self.setFramesPerSecond(20)
        self.setElectronCounting('Off')
        self.setMovieSumCount(1)


## End DE20 class.
################################################################################


################################################################################
## DE16Integrating class.


class DE16Integrating(DECameraBase):
    
    
    ## Parameters
    name = 'DE16Integrating'
    model_name = 'DE16'
    
    
    ## Constructor
    def __init__(self):
        self.hardware_binning = {'x': 1, 'y': 1}
        DECameraBase.__init__(self)
        self.setFramesPerSecond(20)
        self.setElectronCounting('Off')
        self.setMovieSumCount(1)


## End DE16Integrating class.
################################################################################


################################################################################
## DE16Counting class.


class DE16Counting(DECameraBase):
    
    
    ## Parameters
    name = 'DE16Counting'
    model_name = 'DE16'
    
    
    ## Constructor
    def __init__(self):
        self.hardware_binning = {'x': 1, 'y': 1}
        DECameraBase.__init__(self)
        self.setFramesPerSecondToMax()
        self.setElectronCounting('On')
        self.setMovieSumCount(self.getFramesPerSecond / 4)
    
    
    ## Override the original getFrameTime function to calculate the dose fractionated frame time
    def getFrameTime(self):
        if DEBUG_ALL:
            print 'getFrameTime()'
        return self.getFrameTimeForCounting()
    
    
    ## Override the original setFrameTime function to set the dose fractionated frame time without changing the camera frame rate
    def setFrameTime(self, milliseconds):
        if DEBUG_ALL:
            print 'setFrameTime(%s)' % milliseconds
        self.setFrameTimeForCounting(milliseconds)


## End DE16Counting class.
################################################################################


################################################################################
## DE64Integrating class.


class DE64Integrating(DECameraBase):
    
    
    ## Parameters
    name = 'DE64Integrating'
    model_name = 'DE64'
    
    
    ## Constructor
    def __init__(self):
        self.hardware_binning = {'x': 1, 'y': 1}
        DECameraBase.__init__(self)
        self.setFramesPerSecond(20)
        self.setElectronCounting('Off')
        self.setMovieSumCount(1)


## End DE64Integrating class.
################################################################################


################################################################################
## DE64Counting class.


class DE64Counting(DECameraBase):
    
    
    ## Parameters
    name = 'DE64Counting'
    model_name = 'DE64'
    
    
    ## Constructor
    def __init__(self):
        self.hardware_binning = {'x': 2, 'y': 2}
        DECameraBase.__init__(self)
        self.setFramesPerSecondToMax()
        self.setElectronCounting('On')
        self.setMovieSumCount(self.getFramesPerSecond / 4)
    
    
    ## Override the original getFrameTime function to calculate the dose fractionated frame time
    def getFrameTime(self):
        if DEBUG_ALL:
            print 'getFrameTime()'
        return self.getFrameTimeForCounting()
    
    
    ## Override the original setFrameTime function to set the dose fractionated frame time without changing the camera frame rate
    def setFrameTime(self, milliseconds):
        if DEBUG_ALL:
            print 'setFrameTime(%s)' % milliseconds
        self.setFrameTimeForCounting(milliseconds)


## End DE64Counting class.
################################################################################


################################################################################
## Centuri class.


class DECenturiIntegrating(DECameraBase):
    
    
    ## Parameters
    name = 'DECenturiIntegrating'
    model_name = 'Centuri'
    
    
    ## Constructor
    def __init__(self):
        self.hardware_binning = {'x': 1, 'y': 1}
        DECameraBase.__init__(self)
        self.setFramesPerSecond(20)
        self.setElectronCounting('Off')
        self.setMovieSumCount(1)


## End DECenturiIntegrating class.
################################################################################


################################################################################
## DECenturiCounting class.


class DECenturiCounting(DECameraBase):
    
    
    ## Parameters
    name = 'DECenturiCounting'
    model_name = 'Centuri'
    
    
    ## Constructor
    def __init__(self):
        self.hardware_binning = {'x': 1, 'y': 1}
        DECameraBase.__init__(self)
        self.setFramesPerSecondToMax()
        self.setElectronCounting('On')
        self.setMovieSumCount(self.getFramesPerSecond / 4)
    
    
    ## Override the original getFrameTime function to calculate the dose fractionated frame time
    def getFrameTime(self):
        if DEBUG_ALL:
            print 'getFrameTime()'
        return self.getFrameTimeForCounting()
    
    
    ## Override the original setFrameTime function to set the dose fractionated frame time without changing the camera frame rate
    def setFrameTime(self, milliseconds):
        if DEBUG_ALL:
            print 'setFrameTime(%s)' % milliseconds
        self.setFrameTimeForCounting(milliseconds)


## End DECenturiCounting class.
################################################################################


################################################################################
## DEApollo class.


class DEApollo(DECameraBase):
    
    
    ## Parameters
    name = 'DEApollo'
    model_name = 'Apollo'
    
    
    ## Constructor
    def __init__(self):
        self.hardware_binning = {'x': 1, 'y': 1}
        DECameraBase.__init__(self)
        self.setFramesPerSecondToMax()
        self.setMovieSumCount(1)
    
    
    ## Override the original getFrameTime function to calculate the dose fractionated frame time
    def getFrameTime(self):
        if DEBUG_ALL:
            print 'getFrameTime()'
        return self.getFrameTimeForCounting()
    
    
    ## Override the original setFrameTime function to set the dose fractionated frame time without changing the camera frame rate
    def setFrameTime(self, milliseconds):
        if DEBUG_ALL:
            print 'setFrameTime(%s)' % milliseconds
        self.setFrameTimeForCounting(milliseconds)
    
    
    ## Override the original setFramesPerSecond since Apollo has a fixed frame rate
    def setFramesPerSecond(self, frames_per_second):
        if DEBUG_ALL:
            print 'setFramesPerSecond(%s)' % frames_per_second
        self.frames_per_second = round(float(self.getProperty('Frames Per Second')), 1)

    ## remove warning in Leginon which asks for gain by Leginon (Apil 15 2022 by XF)
    def getSystemDarkSubtracted(self):
    return True

    def getFrameGainCorrected(self):
    return True

    def getSumGainCorrected(self):
    return True


## End DEApollo class.
################################################################################
