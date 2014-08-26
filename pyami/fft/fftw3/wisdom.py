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

from lib import lib, PyFile_AsFile
import ctypes

def export_wisdom_to_file(filename):
    """Export accumulated wisdom to file given by the filename"""
    fp = open(filename, 'a')
    c_fp = PyFile_AsFile(fp)
    lib.fftw_export_wisdom_to_file(c_fp)
    fp.close()

def export_wisdom_to_string():
    """Returns a string with the accumulated wisdom"""
    return lib.fftw_export_wisdom_to_string()

def import_wisdom_from_file(filename):
    """Imports wisdom from the file given by the filename"""
    fp = open(filename,'r')
    c_fp = PyFile_AsFile(fp)
    if lib.fftw_import_wisdom_from_file(c_fp):
        pass
    else:
        raise IOError, "Could not read wisdom from file %s" % filename

def import_wisdom_from_string(wisdom):
    """Import wisdom from the given string"""
    if lib.fftw_import_wisdom_from_string(wisdom):
        pass
    else:
        raise Exception, "Could not read wisdom from string: %s" % wisdom

def import_system_wisdom():
    """Import the system wisdom, this lives under /etc/fftw/wisdom on
    Unix/Linux systems"""
    if lib.fftw_import_system_wisdom():
        pass
    else:
        raise IOError, "Could not read system wisdom. On GNU/Linux and Unix "\
                "system wisdom is located in /etc/fftw/wisdom"

def forget_wisdom():
    """Clear all wisdom"""
    lib.fftw_forget_wisdom()


