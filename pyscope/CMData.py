#
# CM data structure
# Author: Min Su    su5@purdue.edu    min.su0@gmail.com
#         Wen Jiang
#
# Change Log:
# 12-29-2006 Min Su Implementation


from ctypes import *

class TCMInfo(Structure):
    _fields_ = [("CmType", c_int),           # integer; { 0..7: CM10/12/20/300/100/120/200/300 }
                ("ObjLens", c_int),          # integer; { 0..3: High Contrast/Twin/Supertwin/Ultratwin
                                             # for CM10/CM100 1 = BioTWIN; for CM120 0 = BioTWIN }
                ("DiffLens", c_int),         # integer; { 0..1: normal diffractionlens/special diffraction lens }
                ("Gun", c_int),              # integer; { 0..2: Tungsten/LAB6/FEG }
                ("Magn", c_float),           # single;  { the magnification as displayed on data monitor }
                ("HolderInserted", c_int),   # integer;
                ("GonioMeter", c_int),       # integer; { 0..2: manual/CompuStage/manual with SRS }
                ("CompuEnabled", c_int),     # integer;
                ("Joysticks", c_int),        # integer; { bitwise: ...bazyx; 1 if enabled }
                ("AxesAvail", c_int)]        # integer; { bitwise: ...bazyx; 1 if available }

class TCMVar(Structure):
    _fields_ = [("Page", c_int),             # integer; { MICROCONTROLLER page number }
                ("ButtonState", c_int),      # integer; { status of press,on,off pushbuttons, bitwise }
                ("Magn", c_float),           # single;  { the magnification as displayed on data monitor }
                ("HT", c_float),             # single;  { high tension }
                ("D1", c_float),             # single;  { measuring data }
                ("D2", c_float),             # single;  { " }
                ("Angle", c_float),          # single;  { " }
                ("Spotsize", c_float),       # single;  { in nm's as displayed }
                ("Intensity", c_float),      # single;  { lens software setting 1000..100 000 }
                ("BeamShiftX", c_float),     # single;  { low dose settings }
                ("BeamShiftY", c_float),     # single;
                ("ImageShiftX", c_float),    # single;
                ("ImageShiftY", c_float),    # single;
                ("MainScrn", c_int),         # integer; { status of mainscreen up <> 0 /down = 0 }
                ("DFmode", c_int),           # integer; { df mode }
                ("TVdetPos", c_int),         # integer; { TV position 0 = none, 1 = central, 3 = off-axis }
                ("measx", c_float),          # single;  { measuring shifts x }
                ("measy", c_float),          # single;  { measuring shifts y}
                ("beamx", c_float),          # single;  { beam deflection values x }
                ("beamy", c_float),          # single;  { beam deflection values y }
                ("defocus", c_float),        # single;  { defocus display value in nanometres }
                ("focusstep", c_int),        # integer; { current focus step size }
                ("objcurrent", c_float),     # single;  { objective lens setting, value between 0 and 100 000 }
                ("dftx", c_float),           # single;  { dark field tilts x }
                ("dfty", c_float)]           # single;  { dark field tilts y }



class ALIGNMENTSTYPE(Structure):
    _fields_ = [("a", c_int * 5000)]



class CSREGTYPE(Structure):
    _fields_ = [ ("filled", c_int),
                 ("xpos",   c_float),
                 ("ypos",   c_float),
                 ("zpos",   c_float),
                 ("apos",   c_float),
                 ("bpos",   c_float)]

class CSREGISTERSTYPE(Structure):
    _fields_ = [("r", CSREGTYPE * 25)]


class STIGTYPE(Structure):
    _fields_ = [("s", c_int * 1500)]

class MODETYPE(Structure):
    _fields_ = [("m", c_int * 256)]

class CURRENTS(Structure):
    _fields_ = [("c", c_float * 26)]
    
class ROTALGNTYPE(Structure):
    _fields_ = [ ("x", c_float),
                 ("y", c_float)]
    

class ROTATIONALIGNMENTTYPE(Structure):
    _fields_ = [("RotAlgn", ROTALGNTYPE * 7)]


class FEGDATATYPE(Structure):
    _fields_ = [("state", c_int),          
                ("time", c_int),          
                ("filament", c_float),    
                ("extrvolt", c_float),   
                ("gunlens", c_float),    
                ("emission", c_float),   
                ("igp3", c_float),       
                ("extrlimit", c_float)]


class PRESSURETYPE(Structure):
    _fields_ = [("P1", c_float),   
                ("P2", c_float),    
                ("P3", c_float),   
                ("IGP", c_float)]


class FCAMVALUESTYPE(Structure):
    _fields_ = [("exposure_nr", c_char*4),      # char array;     
                ("stock", c_int),               # integer; { exposure stock }
                ("seriessize", c_int),          # integer; { size of exposure series }
                ("temexposureLE", c_int),       # integer; { status of TEM Exposure button LED }
                ("double", c_int),              # integer; { Double exposure active / inactive }
                ("expmodeseries", c_int),       # integer; { Series exposure active / inactive  }
                ("seriesthrfocus", c_int),      # integer; { Through focus series exposure active / inactive }
##                ("exptimeauto", c_int)          # integer: { Auto exposure time active / inactive }
                ("exptimemanual", c_int),       # integer; { Manual exposure time active / inactive }
                ("exptimetimer", c_int),        # integer; { Timer exposure time active / inactive }
                ("pvprunning", c_int),          # integer; { PVP running: can't make exposure then }
                ("measuredexptime", c_float),   # single; { measured exposure time value }
                ("manualsetexptime", c_float),  # single; { manual exposure time value  }
                ("emulsionnumb", c_float),      # single; { emulsion setting }
                ("dataintfactor", c_float)]     # single; { data intensity factor }


class POS(Structure):
            _fields_ = [("x", c_float*1),
                        ("y", c_float*1),
                        ("z", c_float*1),
                        ("a", c_float*1),
                        ("b", c_float*1)]
