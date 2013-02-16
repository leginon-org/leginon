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

"""
Python bindings to the FFTW library. 

Usage:

    In order to use PyFFTW you should have a basic understanding of the
    FFTW3 interface. For documentation about FFTW3 go to http://www.fftw.org
    In order to achieve maximum performance FFTW3 requires a planning stage
    where the actual FFT is created from an input and output array.
    To perform the FFT between the input and output array the plan is then
    executed. This interface is therefore significantly different from the
    traditional A = fft(B) interface.
    In contrast to the C-library PyFFTW utilizes the Plan class for planning.
    To create a fftw plan one creates a Plan object using an input and output
    array, and possible parameters. PyFFTW determines from the input and output
    arrays the correct plan to create. To perform the FFT one can either 
    call the Plan directly or call the method execute() or pass the plan
    to the execute function.
    

    Example:
    --------
    
    #create arrays
    >>>inputa = numpy.zeros((1024,3), dtype=complex)
    >>>outputa = numpy.zeros((1024,3), dtype=complex)
    
    # create a forward and backward fft plan
    >>>fft = fftw3.Plan(inputa,outputa, direction='forward', flags=['measure'])
    >>>ifft = fftw3.Plan(outputa, inputa, direction='backward', flags=['measure'])
    
    #initialize the input array
    >>>inputa[:] = 0
    >>>inputa += exp(-x**2/2)
    
    #perform a forward transformation
    >>>fft() # alternatively fft.execute() or fftw.execute(fft)
    
    # do some calculations with the output array
    >>>outputa *= D
    
    #perform a backward transformation
    >>>ifft() 
    
    The planning functions expect aligned, contiguous input arrays of 
    any shape. 
    Currently strides are not implemented. The dtype has to either be complex
    or double. If you want to perform ffts on single or longdouble precision
    arrays use the appropriate fftw3f or fftw3l module. FFTW overwrites the 
    arrays in the planning process, thus, if you use planning strategies 
    other than 'estimate' the arrays are going to be overwritten and have to 
    be reinitialized. 
    
    *IMPORTANT*
    -----------

    Because the plan uses pointers to the data of the arrays you cannot 
    perform operations on the arrays that change the data pointer. Therefore
    
    >>>a = zeros(1024, dtype=complex)
    >>>p = plan(a,b)
    >>>a = a+10
    >>>p()
    
    does not work, i.e. the a object references different memory, however 
    the Fourier transform will be performed on the original memory (the 
    plan actually contains a reference to the orgininal data (p.inarray), 
    otherwise this operation could even result in a python segfault).
    
    Aligned memory:
    ---------------
    
    On many platforms using the SIMD units for part of the floating point
    arithmetic significantly improves performance. FFTW can make use of the 
    SIMD operations, however the arrays have to be specifically aligned 
    in memory. PyFFTW provides a function which creates an numpy array 
    which is aligned to 
    a specified boundary. In most circumstances the default alignment to 16 
    byte boundary is what you want. Note that the same precautions as above     
    apply, i.e. creating an aligned array and then doing something like 
    a=a+1 will result in new memory allocated by python which might not 
    be aligned.
    
    PyFFTW interface naming conventions:
    ------------------------------------

    All exposed fftw-functions do have the same names as the C-functions with the
    leading fftw_ striped from the name.
    Direct access to the C-functions is available by importing lib.lib, the usual
    precautions for using C-functions from Python apply. 
    
    Advanced and Guru interface:
    ----------------------------

    Currently only the execute_dft function from the fftw guru and advanced 
    interface is exposed.
    It is explicitly name guru_execute_dft. You should only use
    these if you know what you're doing, as no checking is done on these functions.
    


Constants:

    fftw_flags      -- dictionary of possible flags for creating plans
    fft_direction   -- the direction of the fft (see the fftw documentation
                       for the mathematical meaning).
    realfft_type    -- a dictionary of possible types for real-to-real
                       transforms (see the fftw documentation for a 
                       more detailed description).
"""
__all__ = ["export_wisdom_to_file", "export_wisdom_to_string",
           "import_wisdom_from_string", "import_wisdom_from_file",
           "import_system_wisdom", "forget_wisdom", "AlignedArray",
           "create_aligned_array", "execute", "guru_execute_dft",
           "destroy_plan", "Plan", "fftw_flags", "fft_direction",
           "realfft_type"]
from wisdom import export_wisdom_to_file, export_wisdom_to_string,\
        import_wisdom_from_string, import_wisdom_from_file, \
        import_system_wisdom, forget_wisdom

from planning import create_aligned_array,\
        execute, guru_execute_dft, destroy_plan,\
        Plan, fftw_flags, fft_direction, realfft_type, \
        print_plan, fprint_plan
