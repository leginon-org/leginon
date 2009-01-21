#
# COPYRIGHT:
#      The Leginon software is Copyright 2003
#      The Scripps Research Institute, La Jolla, CA
#      For terms of the license agreement
#      see  http://ami.scripps.edu/software/leginon-license
#
'''
This python module is for controlling Gatan dual axis holder using
National Instrument USB-6008 Data Acquisition module.

set/get Beta angle
'''

import ctypes
import numpy

### load NI DLL:
### C:\WINDOWS\SYSTEM32\nicaiu.dll
nidaq = ctypes.windll.nicaiu

###################################
# Setup some typedefs and constants

### the typedefs
int32 = ctypes.c_long
uInt32 = ctypes.c_ulong
uInt64 = ctypes.c_ulonglong
float64 = ctypes.c_double
TaskHandle = uInt32

### the constants based on NIDAQmxBase.h
DAQmx_Val_Cfg_Default = int32(-1)
DAQmx_Val_Volts = 10348
DAQmx_Val_Rising = 10280
DAQmx_Val_FiniteSamps = 10178
DAQmx_Val_GroupByChannel = 0
DAQmx_Val_ChanForAllLines = 1

### bit 1 & 2 of Port0 are used to 
### connect to the DC Motor driver
ROTATE_CLOCK_WISE = 0x1
ROTATE_COUNTERCLOCK_WISE = 0x2

### actual measured range
MIN_V_MEASURE = -2.95
MAX_V_MEASURE = 2.88

### constant to convert Volt in degree
### for now...
k_av = 100 / 2.6290938190967497


### initialize variables
analoginput = "Dev1/ai0"
timeout = float64(10.0)
amin = float64(-3.0)
amax = float64(3.0)
aval = float64()

digitalchannel = "Dev1/port0"
w_data = numpy.zeros(1,dtype=numpy.uint32)
written = int32()

taskHandle = TaskHandle(0)
samplesPerChan = 10
pointsToRead = int32(1)
read = int32()

def CHK(err):
	'''a simple error checking routine'''
	if err < 0:
		buf_size = 100
		buf = ctypes.create_string_buffer('\000' * buf_size)
		nidaq.DAQmxGetErrorString(err,ctypes.byref(buf),buf_size)
		raise RuntimeError('nidaq call failed with error %d: %s'%(err,repr(buf.value)))

def _get_analog_input():
	'''read and return a voltage from chosen analog input'''
	CHK(nidaq.DAQmxCreateTask("", ctypes.byref(taskHandle)))
	CHK(nidaq.DAQmxCreateAIVoltageChan(taskHandle, analoginput, "",
							DAQmx_Val_Cfg_Default,
							amin, amax,
							DAQmx_Val_Volts, None))

	CHK(nidaq.DAQmxStartTask(taskHandle))
	CHK(nidaq.DAQmxReadAnalogF64(taskHandle, pointsToRead, timeout,
							DAQmx_Val_GroupByChannel, ctypes.byref(aval),
							samplesPerChan, ctypes.byref(read), None))

	if taskHandle.value != 0:
		nidaq.DAQmxStopTask(taskHandle)
		nidaq.DAQmxClearTask(taskHandle)

	return aval.value

def _set_digital_output(val):
	'''set defined digital output port to val'''
	CHK(nidaq.DAQmxCreateTask("", ctypes.byref(taskHandle)))
	CHK(nidaq.DAQmxCreateDOChan(taskHandle,digitalchannel, "", DAQmx_Val_ChanForAllLines))
	w_data[0] = val
	CHK(nidaq.DAQmxWriteDigitalU32(taskHandle, 1, 1,timeout, DAQmx_Val_GroupByChannel, w_data.ctypes.data, written, None))
	if taskHandle.value != 0:
		nidaq.DAQmxStopTask(taskHandle)
		nidaq.DAQmxClearTask(taskHandle)

def _rotate_counterclock_wise(v):
	'''rotates counterclock wise until analog input reads v'''
	cur_v = _get_analog_input()
	try:
		while cur_v > v:
			_set_digital_output(ROTATE_COUNTERCLOCK_WISE)
			cur_v = _get_analog_input()
			if cur_v <= MIN_V_MEASURE:
				break
	finally:
		_set_digital_output(0)
	
	return cur_v

def _rotate_clock_wise(v):
	'''rotates clock wise until analog input reads v'''
	cur_v = _get_analog_input()
	try:
		while cur_v < v:
			_set_digital_output(ROTATE_CLOCK_WISE)
			cur_v = _get_analog_input()
			if cur_v >= MAX_V_MEASURE:
				break
	finally:
		_set_digital_output(0)
	
	return cur_v


def _set_angle(v):
	'''choose which way to rotate, based on current position'''
	cur_v = _get_analog_input()

	if cur_v > v:
		cur_v = _rotate_counterclock_wise(v)
	elif cur_v < v:
		cur_v = _rotate_clock_wise(v)

	return cur_v


def setBeta(angle):
	'''sets Beta angle (deg)'''
	v = angle2volt(angle)
	nv = _set_angle(v)
	return volt2angle(nv)

def getBeta():
	'''get current Beta angle (deg)'''
	v = _get_analog_input()
	angle = volt2angle(v)
	return angle

def volt2angle(v):
	angle = k_av * v
	return angle

def angle2volt(angle):
	v = angle / k_av
	return v

