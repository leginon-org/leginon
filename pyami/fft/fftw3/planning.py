#   This file is part of PyFFTW.
#
#    Copyright (C) 2009 Jochen Schroeder
#    Email: jschrod@berlios.de
#
#    PyFFTW is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    PyFFTW is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with PyFFTW.  If not, see <http://www.gnu.org/licenses/>.

import numpy as np
from numpy import typeDict
from lib import lib, _typelist, PyFile_AsFile, PyBuffer_FromReadWriteMemory, lib_threads
from ctypes import byref, c_double, c_int

fftw_flags = {'measure':0,
              'destroy input': 1,
              'unaligned': 2,
              'conserve memory':4,
              'exhaustive':8,
              'preserve input': 16,
              'patient': 32,
              'estimate': 64}

realfft_type = {'halfcomplex r2c':0,
                'halfcomplex c2r':1,
                'discrete hartley':2,
                'realeven 00':3,
                'realeven 01':4,
                'realeven 10':5,
                'realeven 11':6,
                'realodd 00':7,
                'realodd 01':8,
                'realodd 10':9,
                'realodd 11':10}


fft_direction = {'forward' : -1, 'backward': 1}

def create_aligned_array(shape, dtype=typeDict['complex'], boundary=16):
    """Create an array which is aligned in memory

    Parameters:
        shape       --  the shape of the array 
        dtype       --  the dtype of the array (default=typeDict['complex'])
        boundary    --  the byte boundary to align to (default=16)
    """
    N = np.prod(shape)*np.array(1,dtype).nbytes
    tmp = np.zeros(N+boundary, dtype=np.uint8)
    address = tmp.__array_interface__['data'][0]
    offset = (boundary - address % boundary)
    return tmp [offset:offset + N].view(dtype=dtype).reshape(shape)


def execute(plan):
    """Execute fftw-plan, i.e. perform Fourier transform on the arrays given
    when the plan was created"""
    lib.fftw_execute(plan)

def guru_execute_dft(plan, inarray, outarray):
        """Guru interface: perform Fourier transform on two arrays,
        outarray=fft(inarray) using the given plan. Important: This function
        does not perform any checks on the array shape and alignment for
        performance reasons. It is therefore crucial to only provide arrays
        with the same shape, dtype and alignment as the arrays used for planning,
        failure to do so can lead to unexpected behaviour and even python
        segfaulting.
        """
        lib.fftw_execute_dft(plan, inarray, outarray)

def destroy_plan(plan):
    """Delete the given plan"""
    if isinstance(plan,Plan):
        del plan
    else:
        lib.fftw_destroy_plan(plan)

def select(inarray,outarray):
    """From a given input and output np array select the appropriate
    fftw3 plan to create.""" 
    if inarray.shape != outarray.shape:
        if inarray.dtype == outarray.dtype:
            raise TypeError, "Input array and output array must have the same "\
                             "shape if they have the same dtype"
        elif inarray.dtype == typeDict['complex'] and outarray.dtype == typeDict['double']:
            inshape = list(outarray.shape)
            inshape[-1] = inshape[-1]/2 + 1
            if inarray.shape != tuple(inshape):
                raise TypeError, "For complex to real transforms the complex "\
                                 "array must be of shape (n1 x n2 x...x "\
                                 "(n-1)/2 +1"
        elif inarray.dtype == typeDict['double'] and outarray.dtype == typeDict['complex']:
            outshape = list(inarray.shape)
            outshape[-1] = outshape[-1]/2 + 1
            if outarray.shape != tuple(outshape):
                raise TypeError, "For real to complex transforms the complex "\
                                 "array must be of shape (n1 x n2 x...x "\
                                 "(n-1)/2 +1"
    if inarray.dtype != typeDict['double'] and inarray.dtype != typeDict['complex']:
        raise TypeError, "Input array has to be either floating point or"\
                         " complex"
    elif outarray.dtype != typeDict['double'] and outarray.dtype != typeDict['complex']:
        raise TypeError, "Output array has to be either floating point "\
                         "or complex"
    i = 0
    while(i < len(_typelist)):
        name, types = _typelist[i]
        if inarray.dtype != types[0]:
            i += 8
            continue
        elif outarray.dtype != types[1]:
            i += 4
            continue
        elif i in [3,7,11,15]:
            return getattr(lib, name), name, types
        elif len(inarray.shape) != types[2]:
            i += 1
            continue
        else:
            return getattr(lib, name), name, types

def _create_complex2real_plan(inarray, outarray, flags):
    """Internal function to create complex fft plan given an input and output
    np array and the direction and flags integers"""
    func, name, types = select(inarray,outarray)
    #this is necessary because the r2c and c2r transforms always use the
    #shape of the larger array (the real one)
    if np.prod(inarray.shape) < np.prod(outarray.shape):
        shape = outarray.shape
    else:
        shape = inarray.shape
    
    if len(types) < 3:
        plan = func(len(shape), np.asarray(shape, dtype=c_int),
                    inarray, outarray,  flags)
        if plan is None:
            raise Exception, "Error creating fftw plan %s for the given "\
                             "parameters" %name
        else:
            return plan, name
    elif types[2] == 1:
        plan = func(shape[0], inarray, outarray,  flags)
        if plan is None:
            raise Exception, "Error creating fftw plan %s for the given "\
                             "parameters" %name
        else:
            return plan, name
    elif types[2] == 2:
        plan = func(shape[0], shape[1], inarray, outarray, flags)
        if plan is None:
            raise Exception, "Error creating fftw plan %s for the given "\
                             "parameters" %name
        else:
            return plan, name
    elif types[2] == 3:
        plan = func(shape[0], shape[1], shape[2],inarray, outarray, flags)
        if plan is None:
            raise Exception, "Error creating fftw plan %s for the given "\
                             "parameters" %name
        else:
            return plan, name
    else:
        raise ValueError, 'the dimensions are not correct'


def _create_complex_plan(inarray, outarray, direction, flags):
    """Internal function to create complex fft plan given an input and output
    np array and the direction and flags integers"""
    func, name, types = select(inarray,outarray)
    #this is necessary because the r2c and c2r transforms always use the
    #shape of the larger array (the real one)
    if np.prod(inarray.shape) < np.prod(outarray.shape):
        shape = outarray.shape
    else:
        shape = inarray.shape

    if len(types) < 3:
        plan = func(len(shape),
                    np.asarray(shape, dtype=c_int),
                    inarray, outarray, direction, flags)
        if plan is None:
            raise Exception, "Error creating fftw plan %s for the given "\
                             "parameters" %name
        else:
            return plan, name
    elif types[2] == 1:
        plan = func(shape[0], inarray, outarray, direction, flags)
        if plan is None:
            raise Exception, "Error creating fftw plan %s for the given "\
                             "parameters" %name
        else:
            return plan, name
    elif types[2] == 2:
        plan = func(shape[0], shape[1], inarray, outarray,\
                    direction, flags)
        if plan is None:
            raise Exception, "Error creating fftw plan %s for the given "\
                             "parameters" %name
        else:
            return plan, name
    elif types[2] == 3:
        plan = func(shape[0], shape[1], shape[2],\
                    inarray, outarray, direction, flags)
        if plan is None:
            raise Exception, "Error creating fftw plan %s for the given "\
                             "parameters" %name
        else:
            return plan, name
    else:
        raise ValueError, 'the dimensions are not correct'

def _create_real_plan(inarray, outarray, realtype, flags):
    """Internal function to create real fft plan given an input and output 
    np array and the realtype and flags integers"""
    if realtype == None:
        raise ValueError, "Two real input arrays but no realtype list given"
    func, name, types = select(inarray,outarray)
    if len(types) < 3:
        plan = func(len(inarray.shape), np.asarray(inarray.shape,dtype=c_int),\
             inarray, outarray, np.asarray(realtype), flags)
        if plan is None:
            raise Exception, "Error creating fftw plan %s for the given "\
                             "parameters" %name
        else:
            return plan, name
    elif types[2] == 1:
        plan = func(inarray.shape[0], inarray, outarray, realtype[0], flags)
        if plan is None:
            raise Exception, "Error creating fftw plan %s for the given "\
                             "parameters" %name
        else:
            return plan, name
    elif types[2] == 2:
        plan = func(inarray.shape[0], inarray.shape[1], inarray, outarray,\
                    realtype[0], realtype[1], flags)
        if plan is None:
            raise Exception, "Error creating fftw plan %s for the given "\
                             "parameters" %name
        else:
            return plan, name
    elif types[2] == 3:
        plan = func(inarray.shape[0], inarray.shape[1],inarray.shape[2], \
                    inarray, outarray, realtype[0], realtype[1], \
                    realtype[2], flags)
        if plan is None:
            raise Exception, "Error creating fftw plan %s for the given "\
                             "parameters" %name
        else:
            return plan, name
    else:
        raise ValueError, 'the dimensions are not correct'

def _create_plan(inarray, outarray, direction='forward', flags=['estimate'],
                realtypes=None, nthreads=1):
    """Internal function to create a complex fft plan given an input and output
    np array and the direction and flags integers"""
    if lib_threads is not None:
        lib_threads.fftw_plan_with_nthreads(nthreads)
    elif nthreads > 1:
        raise ValueError, "Cannot use more than 1 thread for non-threaded fftw: %s" % (nthreads)
    if inarray.dtype == np.typeDict['complex'] and \
                        outarray.dtype == np.typeDict['complex']:
        return _create_complex_plan(inarray,outarray, fft_direction[direction],
                                     _cal_flag_value(flags))
    elif inarray.dtype == np.typeDict['complex'] or \
                          outarray.dtype == np.typeDict['complex']:
        return _create_complex2real_plan(inarray,outarray, 
                                         _cal_flag_value(flags))
    elif inarray.dtype == np.typeDict['double'] and \
                          outarray.dtype == np.typeDict['double']:
        return _create_real_plan(inarray,outarray, \
                                 [realfft_type[r] for r in realtypes],\
                                 _cal_flag_value(flags))
    else:
        raise TypeError, "The input or output array has a dtype which is not supported by fftw: %r, %r"\
            % (inarray.dtype, outarray.dtype)

def _cal_flag_value(flags):
    """Calculate the integer flag value from a list of string flags"""
    ret = 0
    for f in flags:
        ret += fftw_flags[f]
    return ret

def print_plan(plan):
    """Print a nerd-readable version of the plan to stdout"""
    lib.fftw_print_plan(plan)

def fprint_plan(plan, filename):
    """Print a nerd-readable version of the plan to the given filename"""
    fp = open(filename, 'w')
    c_fp = PyFile_AsFile(fp)
    lib.fftw_fprint_plan(plan, c_fp)
    fp.close()

class Plan(object):
    """Object representing a fftw plan used to execute Fourier transforms in
    fftw
    
    Attributes:
        shape       --  the shape of the input and output arrays, i.e. the FFT
        flags       --  a list of the fft flags used in the planning
        direction   --  the direction of the FFT
        ndim        --  the dimensionality of the FFT
        inarray     --  the input array
        outarray    --  the output array
        """
    def __init__(self, inarray=None, outarray=None, direction='forward',
                 flags=['estimate'], realtypes=None, create_plan=True,
                 nthreads = 1):
        """Initialize the fftw plan. 
        Parameters:
            inarray     --  array to be transformed (default=None)
            outarray    --  array to contain the Fourier transform
                            (default=None)
            If one of the arrays is None, the fft is considered to be
            an inplace transform.

            direction   --  direction of the Fourier transform, forward
                            or backward (default='forward')
            flags       --  list of fftw-flags to be used in planning
                            (default=['estimate'])
            realtypes   --  list of fft-types for real-to-real ffts, this
                            needs to be given if both input and output
                            arrays are real (default=None)
            create_plan --  weather to actually create the plan (default=True)
            nthreads    --  number of threads to be used by the plan,
                            available only for threaded libraries (default=1)
            """

        self.flags = flags
        self.direction = direction
        self.realtypes = realtypes
        self.nthreads = nthreads
        if create_plan:
            if inarray is None and outarray is None:
                raise 'Need at least one array to create the plan'
            elif outarray is None:
                self.create_plan(inarray,inarray)
            elif inarray is None:
                self.create_plan(outarray,outarray)
            else:
                self.create_plan(inarray,outarray)

    def __set_shape(self,shape):
        if len(shape)==1:
            self.ndim = 1
            self.N = tuple(shape)

        elif len(shape) > 1:
            self.ndim = len(shape)
            self.N = tuple(shape)
        else:
            raise ValueError, 'shape must be at least one dimensional'

    def __get_shape(self):
        return self.N
    shape = property(__get_shape, __set_shape)

    def create_plan(self, inarray, outarray):
        """Create the actual fftw-plan from inarray and outarray"""
        self.plan, self.type_plan = _create_plan(inarray,outarray,
                                                 direction=self.direction,
                                                 flags=self.flags,
                                                 realtypes=self.realtypes,
                                                 nthreads=self.nthreads)
        self.shape = inarray.shape
        self.inarray = inarray
        self.outarray = outarray

    def _get_parameter(self):
        return self.plan
    _as_parameter_ = property(_get_parameter)

    def __call__(self):
        """Perform the Fourier transform outarray = fft(inarray) for
        the arrays given at plan creation"""
        self.execute()

    def execute(self):
        """Execute the fftw plan, i.e. perform the FFT outarray = fft(inarray)
        for the arrays given at plan creation"""
        execute(self)

    def __del__(self):
        lib.fftw_destroy_plan(self.plan)

    def guru_execute_dft(self,inarray,outarray):
        """Guru interface: perform Fourier transform on two given arrays,
        outarray=fft(inarray). Important: This method does not perform any
        checks on the array shape and alignment for performance reasons. It is
        therefore crucial to only provide arrays with the same shape, dtype and
        alignment as the arrays used for planning, failure to do so can lead to
        unexpected behaviour and possibly python segfaulting
        """
        guru_execute_dft(self,inarray,outarray)

    def get_flops(self):
        """Return an exact count of the number of floating-point additions,
        multiplications, and fused multiply-add operations involved in
        the plan's execution. The total number of floating-point
        operations (flops) is add + mul + 2*fma, or add + mul + fma if
        the hardware supports fused multiply-add instructions
        (although the number of FMA operations is only approximate
        because of compiler voodoo).
        """
        add = c_double(0)
        mul = c_double(0)
        fma = c_double(0)
        lib.fftw_flops(self, byref (add), byref (mul), byref (fma))
        return add.value, mul.value, fma.value
