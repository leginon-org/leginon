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

import ctypes
from ctypes import pythonapi, util, py_object
from numpy import ctypeslib, typeDict
from platform import system as psystem
from os.path import splitext, join, isfile, dirname, abspath, basename
from os.path import join as joinpath
from os import name as osname
from os import environ
from warnings import warn

try:
    fftw_path = environ['FFTW_PATH']
    libfullpath = joinpath(abspath(fftw_path),r'libfftw3.so')
    if not isfile(libfullpath):
        raise IOError
except KeyError:
    libfullpath = r'libfftw3.so.3'
except IOError:
    warn('could not find %s in FFTW_PATH using installtime path'
             %'libfftw3.so')
    libfullpath = r'libfftw3.so.3'

if not isfile(libfullpath) and (osname=='nt' or psystem=='Windows'):
    if isfile(joinpath(dirname(__file__), libfullpath)):
        libfullpath = joinpath(dirname(__file__), libfullpath)

# must use ctypes.RTLD_GLOBAL for threading support
ctypes._dlopen(libfullpath, ctypes.RTLD_GLOBAL)
lib = ctypes.cdll.LoadLibrary(libfullpath)
#check if library is actually loaded there doesn't seem to be a better way to
#do this in ctypes
if not hasattr(lib, 'fftw_plan_dft_1d'):
    raise OSError('Could not load libfftw3.so')

if osname == 'nt' or psystem() == 'Windows':
    lib_threads = lib
else:
    libbase,ext = libfullpath.split('.', 1)
    libdir = dirname(libfullpath)
    lib_threads = joinpath(libdir, libbase + '_threads.'+ ext)
    try:
        lib_threads = ctypes.cdll.LoadLibrary(lib_threads)
    except OSError, e:
        warn("Could not load threading library %s, threading support is disabled"
            %lib_threads)
        lib_threads = None


_typelist =    [('fftw_plan_dft_1d', (typeDict['complex'], typeDict['complex'], 1)),
                       ('fftw_plan_dft_2d', (typeDict['complex'], typeDict['complex'], 2)),
                       ('fftw_plan_dft_3d', (typeDict['complex'], typeDict['complex'], 3)),
                       ('fftw_plan_dft', (typeDict['complex'], typeDict['complex'])),
                       ('fftw_plan_dft_c2r_1d', (typeDict['complex'], typeDict['double'], 1)),
                       ('fftw_plan_dft_c2r_2d', (typeDict['complex'], typeDict['double'], 2)),
                       ('fftw_plan_dft_c2r_3d', (typeDict['complex'], typeDict['double'], 3)),
                       ('fftw_plan_dft_c2r', (typeDict['complex'], typeDict['double'])),
                       ('fftw_plan_dft_r2c_1d', (typeDict['double'], typeDict['complex'], 1)),
                       ('fftw_plan_dft_r2c_2d', (typeDict['double'], typeDict['complex'], 2)),
                       ('fftw_plan_dft_r2c_3d', (typeDict['double'], typeDict['complex'], 3)),
                       ('fftw_plan_dft_r2c', (typeDict['double'], typeDict['complex'])),
                       ('fftw_plan_r2r_1d', (typeDict['double'], typeDict['double'], 1)),
                       ('fftw_plan_r2r_2d', (typeDict['double'], typeDict['double'], 2)),
                       ('fftw_plan_r2r_3d', (typeDict['double'], typeDict['double'], 3)),
                       ('fftw_plan_r2r', (typeDict['double'], typeDict['double']))]

_adv_typelist = [('fftw_plan_many_dft', (typeDict['complex'],
                                              typeDict['complex'])),
                  ('fftw_plan_many_dft_c2r', (typeDict['complex'],
                                                   typeDict['double'])),
                  ('fftw_plan_many_dft_r2c', (typeDict['double'],
                                                   typeDict['complex'])),
                  ('fftw_plan_many_r2r', (typeDict['double'],
                                                   typeDict['double']))]


def set_argtypes(val, types):
    if types[0] == typeDict['complex'] and types[1] == typeDict['complex']:
        set_argtypes_c2c(val,types)
    elif types[0] == typeDict['complex'] or types[1] == typeDict['complex']:
        set_argtypes_c2r(val,types)
    else:
        set_argtypes_r2r(val,types)

def set_argtypes_c2c(val,types):
    if len(types) >2:
        val.argtypes = [ctypes.c_int for i in range(types[2])] +\
                       [ctypeslib.ndpointer(dtype=types[0],ndim=types[2], \
                                            flags='contiguous, writeable, '\
                                                  'aligned'),
                        ctypeslib.ndpointer(dtype=types[1], ndim=types[2],\
                                            flags='contiguous, writeable, '\
                                                  'aligned'),
                        ctypes.c_int, ctypes.c_uint]
    else:
        val.argtypes = [ctypes.c_int, ctypeslib.ndpointer(dtype=ctypes.c_int,
                                                          ndim=1,\
                                                          flags='contiguous, '\
                                                                'aligned'),
                        ctypeslib.ndpointer(dtype=types[0], flags='contiguous,'\
                                                                 ' writeable, '\
                                                                  'aligned'),
                        ctypeslib.ndpointer(dtype=types[1],flags='contiguous, '\
                                                                 'writeable,'\
                                                                 'aligned'),
                        ctypes.c_int, ctypes.c_uint]

def set_argtypes_c2r(val,types):
    if len(types) >2:
        val.argtypes = [ctypes.c_int for i in range(types[2])] +\
                       [ctypeslib.ndpointer(dtype=types[0],ndim=types[2], \
                                            flags='contiguous, writeable, '\
                                                  'aligned'),
                        ctypeslib.ndpointer(dtype=types[1], ndim=types[2],\
                                            flags='contiguous, writeable, '\
                                                  'aligned'),
                        ctypes.c_uint]
    else:
        val.argtypes = [ctypes.c_int, ctypeslib.ndpointer(dtype=ctypes.c_int, 
                                                          ndim=1,\
                                                          flags='contiguous, '\
                                                                'aligned'),
                        ctypeslib.ndpointer(dtype=types[0], flags='contiguous,'\
                                                                 ' writeable, '\
                                                                  'aligned'),
                        ctypeslib.ndpointer(dtype=types[1],flags='contiguous, '\
                                                                 'writeable,'\
                                                                 'aligned'),
                        ctypes.c_uint]

def set_argtypes_r2r(val, types):
    if len(types) > 2:
        val.argtypes = [ctypes.c_int for i in range(types[2])] +\
                       [ctypeslib.ndpointer(dtype=types[0], ndim=types[2],
                                            flags='contiguous, writeable, '\
                                                  'aligned'),
                        ctypeslib.ndpointer(dtype=types[1], ndim=types[2],
                                            flags='contiguous, writeable, '\
                                                  'aligned')] +\
                        [ctypes.c_int for i in range(types[2])] +\
                        [ctypes.c_uint]
    else:
        val.argtypes = [ctypes.c_int, ctypeslib.ndpointer(dtype=ctypes.c_int, 
                                                            ndim=1,
                                                          flags='contiguous, '\
                                                                'aligned'),
                        ctypeslib.ndpointer(dtype=types[0], flags='contiguous,'\
                                                                  'writeable, '\
                                                                  'aligned'),
                        ctypeslib.ndpointer(dtype=types[1], flags='contiguous,'\
                                                                  'writeable, '\
                                                                  'aligned'),
                        ctypeslib.ndpointer(dtype=ctypes.c_int, ndim=1,
                                            flags='contiguous, aligned'),
                        ctypes.c_uint]

def set_argtypes_adv(val, types):
    if types[0] == typeDict['complex'] and types[1] == typeDict['complex']:
        val.argtypes = [ctypes.c_int, ctypeslib.ndpointer(dtype=ctypes.c_int, 
                                                          ndim=1,
                                                          flags='contiguous, '\
                                                                'aligned'),
                        ctypes.c_int,
                        ctypeslib.ndpointer(dtype=types[0], flags='contiguous,'\
                                                                  'aligned,'\
                                                                  'writeable'),
                        ctypeslib.ndpointer(dtype=ctypes.c_int, ndim=1,
                                            flags='contiguous,aligned'),
                        ctypes.c_int, ctypes.c_int,
                        ctypeslib.ndpointer(dtype=types[1], flags='contiguous,'\
                                                                  'aligned,'\
                                                                  'writeable'),
                        ctypeslib.ndpointer(dtype=ctypes.c_int, ndim=1,
                                            flags='contiguous,aligned'),
                        ctypes.c_int, ctypes.c_int,
                        ctypes.c_int, ctypes.c_uint]
    elif types[0] == typeDict['complex'] or types[1]==typeDict['complex']:
        val.argtypes = [ctypes.c_int, ctypeslib.ndpointer(dtype=ctypes.c_int, 
                                                            ndim=1,
                                                          flags='contiguous, '\
                                                                'aligned'),
                        ctypes.c_int,
                        ctypeslib.ndpointer(dtype=types[0], flags='contiguous,'\
                                                                  'aligned,'\
                                                                  'writeable'),
                        ctypeslib.ndpointer(dtype=ctypes.c_int, ndim=1,
                                            flags='contiguous,aligned'),
                        ctypes.c_int, ctypes.c_int,
                        ctypeslib.ndpointer(dtype=types[1], flags='contiguous,'\
                                                                  'aligned,'\
                                                                  'writeable'),
                        ctypeslib.ndpointer(dtype=ctypes.c_int, ndim=1,
                                            flags='contiguous,aligned'),
                        ctypes.c_int, ctypes.c_int,
                        ctypes.c_uint]
    elif types[0] == typeDict['double'] and types[1]==typeDict['double']:
        val.argtypes = [ctypes.c_int, ctypeslib.ndpointer(dtype=ctypes.c_int, 
                                                          ndim=1,
                                                          flags='contiguous, '\
                                                                'aligned'),
                        ctypes.c_int,
                        ctypeslib.ndpointer(dtype=types[0], flags='contiguous,'\
                                                                  'aligned,'\
                                                                  'writeable'),
                        ctypeslib.ndpointer(dtype=ctypes.c_int, ndim=1,
                                            flags='contiguous,aligned'),
                        ctypes.c_int, ctypes.c_int,
                        ctypeslib.ndpointer(dtype=types[1], flags='contiguous,'\
                                                                  'aligned,'\
                                                                  'writeable'),
                        ctypeslib.ndpointer(dtype=ctypes.c_int, ndim=1,
                                            flags='contiguous, aligned'),
                        ctypes.c_int, ctypes.c_int,
                        ctypeslib.ndpointer(dtype=ctypes.c_int, ndim=1,
                                            flags='contiguous, aligned'),
                        ctypes.c_uint]



# set the return and argument types on the plan functions
for name, types in _typelist:
    val = getattr(lib, name)
    val.restype = ctypes.c_void_p
    set_argtypes(val,types)

##do the same for advanced plans
for name, types in _adv_typelist:
    val = getattr(lib, name)
    val.restype = ctypes.c_void_p
    set_argtypes_adv(val,types)

#malloc and free
lib.fftw_malloc.restype = ctypes.c_void_p
lib.fftw_malloc.argtypes = [ctypes.c_int]
lib.fftw_free.restype = None
lib.fftw_free.argtypes = [ctypes.c_void_p]

#create a buffer from memory (necessary for array allocation)
PyBuffer_FromReadWriteMemory = pythonapi.PyBuffer_FromReadWriteMemory
PyBuffer_FromReadWriteMemory.restype = py_object
PyBuffer_FromReadWriteMemory.argtypes = [ctypes.c_void_p, ctypes.c_int]

#executing arrays
lib.fftw_execute.restype = None
lib.fftw_execute.argtypes = [ctypes.c_void_p]

#guru execution
lib.fftw_execute_dft.restype = None
lib.fftw_execute_dft.argtypes = [ctypes.c_void_p,
                        ctypeslib.ndpointer(flags='aligned, contiguous, '\
                                                        'writeable'),\
                        ctypeslib.ndpointer(flags='aligned, contiguous, '\
                                                        'writeable')]

#destroy plans
lib.fftw_destroy_plan.restype = None
lib.fftw_destroy_plan.argtypes = [ctypes.c_void_p]

#enable threading for plans
if lib_threads is not None:
    lib_threads.fftw_init_threads.restype = ctypes.c_int
    lib_threads.fftw_init_threads.argtypes = []
    lib_threads.fftw_plan_with_nthreads.restype = None
    lib_threads.fftw_plan_with_nthreads.argtypes = [ctypes.c_int]
    lib_threads.fftw_cleanup_threads.restype = None
    lib_threads.fftw_cleanup_threads.argtypes = []

    s = lib_threads.fftw_init_threads()
    if not s:
        sys.stderr.write('fftw_init_threads call failed, disabling threads support\n')
        lib_threads = None

#wisdom

# create c-file object from python
PyFile_AsFile = pythonapi.PyFile_AsFile
PyFile_AsFile.argtypes = [ctypes.py_object]
PyFile_AsFile.restype = ctypes.c_void_p

#export to file
lib.fftw_export_wisdom_to_file.argtypes = [ctypes.c_void_p]
lib.fftw_export_wisdom_to_file.restype = None

#export to string
lib.fftw_export_wisdom_to_string.argtypes = None
lib.fftw_export_wisdom_to_string.restype = ctypes.c_char_p

#import from file
lib.fftw_import_wisdom_from_file.argtypes = [ctypes.c_void_p]
lib.fftw_import_wisdom_from_file.restype = ctypes.c_int

#import from string
lib.fftw_import_wisdom_from_string.argtypes = [ctypes.c_char_p]
lib.fftw_import_wisdom_from_string.restype = ctypes.c_int

#import system wisdom
lib.fftw_import_system_wisdom.restype = ctypes.c_int
lib.fftw_import_system_wisdom.argtypes = None

#forget wisdom
lib.fftw_forget_wisdom.restype = None
lib.fftw_forget_wisdom.argtype = None
