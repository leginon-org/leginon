#
# cmlib.py is base Library for CM200/CM300 microscope
# Author: Min Su    su5@purdue.edu    min.su0@gmail.com
#         Wen Jiang
# Structure Biology, Purdue University, West Lafayette, IN
#
# Change Log:
# 12-29-2006 Min Su Implementation
# cmremote32.dll is wrapped using ctypes
# Caching machnism is implemented, but not efficiently used 


from ctypes import *
import CMData
import time

Debug = False

CacheDelay = {
    'delay_cmvar'       : 0,
    'delay_cminfo'      : 0,
    'delay_pos'         : 0,
    'delay_camvalues'   : 0,
    'delay_pressures'   : 0,
    'delay_rotalignment': 0,
    'delay_scrncurrent' : 0,
    'delay_emssncurrent': 0,
    'delay_HTcond'      : 0,
    'delay_stigmators'  : 0
}

##CacheDelay = {
##    'delay_cmvar'       : 10,
##    'delay_cminfo'      : 10,
##    'delay_pos'         : 0,
##    'delay_camvalues'   : 10,
##    'delay_pressures'   : 30,
##    'delay_rotalignment': 0,
##    'delay_scrncurrent' : 5,
##    'delay_emssncurrent': 30,
##    'delay_HTcond'      : 30,
##    'delay_stigmators'  : 0
##}

CacheTime = {
    'cmvar_pre'       : time.time(),
    'cmvar_now'       : time.time(),
    'cminfo_pre'      : time.time(),
    'cminfo_now'      : time.time(),
    'pos_pre'         : time.time(),
    'pos_now'         : time.time(),
    'camvalues_pre'   : time.time(),
    'camvalues_now'   : time.time(),
    'pressures_pre'   : time.time(),
    'pressures_now'   : time.time(),
    'rotalignment_pre': time.time(),
    'rotalignment_now': time.time(),
    'scrncurrent_pre' : time.time(),
    'scrncurrent_now' : time.time(),
    'emssncurrent_pre': time.time(),
    'emssncurrent_now': time.time(),
    'HTcond_pre'      : time.time(),
    'HTcond_now'      : time.time(),
    'stigmators_pre'  : time.time(),
    'stigmators_now'  : time.time()
}

CacheInfo = {
    'cmvar'       : CMData.TCMVar(0),
    'cminfo'      : CMData.TCMInfo(0),
    'pos'         : CMData.POS(),
    'camvalues'   : CMData.FCAMVALUESTYPE(),
    'pressures'   : CMData.PRESSURETYPE(0),
    'rotalignment': CMData.ROTATIONALIGNMENTTYPE(),
    'scrncurrent' : c_float(0),
    'emssncurrent': c_float(0),
    'HTcond'      : c_int(0),
    'stigmators'  : CMData.STIGTYPE()
}
   
focus = 0.0            # Because CM doesn't provide focus value, 
                       # thus a global variable is defined here to trace the focus change
                       # in case Z-height need to be adjusted. Mimic the function of Tecnai.

imageshift_LM = {'x': 0.0, 'y': 0.0} # CM cannot retrieve imageshift from LM mode(Mag<1500X),
                                     # thus a global variable is defined here to record imageshift in LM mode.


class CMLIB(object):
    name = 'CM Library'
    def __init__(self):        
        self.cmremote32 = windll.cmremote32    # from ctyps import cmremote32.dll
        self.cmremote32.SetTimeOutTime(0,3000) # Default timeout value in ms for cmremote32.dll
                                               # to wait for an answer from SECS2_32.exe
        self.trials = 3                        # try 3 times
        #self.waitmid = 2                       # wait for 2 sec
        #self.waitend = 1                       # wait for 1 sec
        self.waitmid = 0                       # wait for 2 sec
        self.waitend = 0                       # wait for 1 sec
        
        self.EquipmentAvailable()              # check the communication to microscope
        

    # Print err message from SECS2_32.exe
    def _errmsg(self,err):      
        if err == 1:
            print 'err message: NOTSENT'
        elif err == 2:
            print 'err message: TIMEOUT'
        elif err == 3:
            print 'err message: NOMEM'
        elif err == 4:
            print 'err message: TOOMANYREQUEST'
        elif err == 5:
            print 'err message: SECSCLOSED'
        elif err == 10:
            print 'err message: OTHERFUNCTION'
        elif err == 11:
            print 'err message: ILLEGALPARAM'
        else:
            print 'undocumented err message'


    # Establish communication to microscope
    def EquipmentAvailable(self):
        model   = create_string_buffer('\000' * 32)
        version = create_string_buffer('\000' * 32)
        i = 0
        while i < self.trials:
            print 'model', model
            print 'version', version
            err = self.cmremote32.EquipmentAvailable(0,model,version)
            if err != 0:
                if err == 65535:
                    self._errmsg(err)
                    return                    
                print 'Connet to CM %s time faild' %(i+1)
                self._errmsg(err)
                time.sleep(self.waitmid)
                i += 1
            else:
                print "CM Model: %s  Version: %s" % (repr(model.value), \
                                                  repr(version.value))
                i = self.trials + 1
                time.sleep(self.waitend)


    # Retrieves various system variables
    def GetCMVar(self):
        global CacheDelay
        global CacheTime
        global CacheInfo
        CacheTime['cmvar_now'] = time.time()
        leng  = c_int(0)    # Leng gives the length of cmvar, refer to CM Tutor for detail                                

        if (CacheTime['cmvar_now'] - CacheTime['cmvar_pre'] > CacheDelay['delay_cmvar']):
            i = 0
            while i < self.trials:
                err = self.cmremote32.GetCMvar(0,byref(CacheInfo['cmvar']),byref(leng))
                if err != 0:
                    if err == 65535:
                        self._errmsg(err)
                        return
                    print 'GetCMVar %s time faild' %(i+1)
                    self._errmsg(err)
                    time.sleep(self.waitmid)
                    i += 1
                else:
                    if Debug == True:
                        print 'retrived CMVar from microscope'
                    CacheTime['cmvar_pre'] = CacheTime['cmvar_now']
                    time.sleep(self.waitend)
                    return CacheInfo['cmvar']
                    i = self.trials + 1 
        else:
            if Debug == True:
                print 'retrived CMVar from Cache'
            return CacheInfo['cmvar']


    # Retrieves various system parameters
    def GetCMInfo(self):
        global CacheDelay
        global CacheTime
        global CacheInfo
        CacheTime['cminfo_now'] = time.time()
        leng  = c_int(0)    # refer to GetCMVar for detail
        
        if (CacheTime['cminfo_now'] - CacheTime['cminfo_pre'] > CacheDelay['delay_cminfo']):
            i = 0
            while i < self.trials:
                err = self.cmremote32.GetCMinfo(0,byref(CacheInfo['cminfo']),byref(leng))
                if err != 0:
                    if err == 65535:
                        self._errmsg(err)
                        return                   
                    print 'GetCMInfo %s time faild' %(i+1)
                    self._errmsg(err)
                    time.sleep(self.waitmid)
                    i += 1
                else:
                    if Debug == True:
                        print 'retrived CMInfo from microscope'
                    CacheTime['cminfo_pre'] = CacheTime['cminfo_now']
                    time.sleep(self.waitend)
                    return CacheInfo['cminfo']
                    i = self.trials + 1
        else:
            if Debug == True:
                print 'retrived CMInfo from Cache'
            return CacheInfo['cminfo']


    # Reads the current x,y,z,a,b postion of the compuStage.
    # Note x,y,z valuse are in micrometer,the tilt angles in degree
    def CSAskPos(self):
        global CacheDelay
        global CacheTime
        global CacheInfo
        CacheTime['pos_now'] = time.time()
        
        if (CacheTime['pos_now'] - CacheTime['pos_pre'] > CacheDelay['delay_pos']):
            i = 0
            while i < self.trials:
                err = self.cmremote32.CSAskPos(0,byref(CacheInfo['pos'].x),byref(CacheInfo['pos'].y),\
                                               byref(CacheInfo['pos'].z),byref(CacheInfo['pos'].a),byref(CacheInfo['pos'].b))
                if err != 0:
                    if err == 65535:
                        self._errmsg(err)
                        return                    
                    print 'CSAskPos %s time faild' %(i+1)
                    self._errmsg(err)
                    time.sleep(self.waitmid)
                    i += 1
                else:
                    if Debug == True:
                        print 'retrived CSAskPos from microscope'
                    CacheTime['pos_pre'] = CacheTime['pos_now']
                    time.sleep(self.waitend)
                    return CacheInfo['pos']
                    i = self.trials + 1
        else:
            if Debug == True:
                print 'retrived CSAskPos from Cache'
            return CacheInfo['pos']


    # Retrieves various camera setting
    def GetCmCamValues(self):
        global CacheDelay
        global CacheTime
        global CacheInfo
        CacheTime['camvalues_now'] = time.time()
 
        if (CacheTime['camvalues_now'] - CacheTime['camvalues_pre'] > CacheDelay['delay_camvalues']):
            i = 0
            while i < self.trials:
                err = self.cmremote32.GetCmCamValues(0,byref(CacheInfo['camvalues']))
                if err != 0:
                    if err == 65535:
                        self._errmsg(err)
                        return                    
                    print 'GetCmCamValues %s time faild' %(i+1)
                    self._errmsg(err)
                    time.sleep(self.waitmid)
                    i += 1
                else:
                    if Debug == True:
                        print 'retrived GetCmCamValues from microscope'
                    CacheTime['camvalues_pre'] = CacheTime['camvalues_now']
                    time.sleep(self.waitend)
                    return CacheInfo['camvalues']
                    i = self.trials + 1
        else:
            if Debug == True:
                print 'retrived GetCmCamValues from Cache'
            return CacheInfo['camvalues']


    # Retrieves vacumm information
    def PressureReadout(self):
        global CacheDelay
        global CacheTime
        global CacheInfo
        CacheTime['pressures_now'] = time.time()
        
        if (CacheTime['pressures_now'] - CacheTime['pressures_pre'] > CacheDelay['delay_pressures']):
            i = 0
            while i < self.trials:
                err = self.cmremote32.PressureReadout(0,byref(CacheInfo['pressures']))
                if err != 0:
                    if err == 65535:
                        self._errmsg(err)
                        return                    
                    print 'PressureReadout %s time faild' %(i+1)
                    self._errmsg(err)
                    time.sleep(self.waitmid)
                    i += 1
                else:
                    if Debug == True:
                        print 'retrived PressureReadout from microscope'
                    CacheTime['pressures_pre'] = CacheTime['pressures_now']
                    time.sleep(self.waitend)
                    return CacheInfo['pressures']
                    i = self.trials + 1
        else:
            if Debug == True:
                print 'retrived PressureReadout from Cache'
            return CacheInfo['pressures']


    # Retrieves the rotation alignment
    def GetRotationAlignment(self):
        global CacheDelay
        global CacheTime
        global CacheInfo
        CacheTime['rotalignment_now'] = time.time()
        
        if (CacheTime['rotalignment_now'] - CacheTime['rotalignment_pre'] > CacheDelay['delay_rotalignment']):
            i = 0
            while i < self.trials:
                err = self.cmremote32.GetRotationAlignment(0,byref(CacheInfo['rotalignment']))
                if err != 0:
                    if err == 65535:
                        self._errmsg(err)
                        return                    
                    print 'GetRotationAlignment %s time faild' %(i+1)
                    self._errmsg(err)
                    time.sleep(self.waitmid)
                    i += 1
                else:
                    if Debug == True:
                        print 'retrived RotationAlignment from microscope'
                    CacheTime['rotalignment_pre'] = CacheTime['rotalignment_now']
                    time.sleep(self.waitend)
                    return CacheInfo['rotalignment']
                    i = self.trials + 1
        else:
            if Debug == True:
                print 'retrived RotationAlignment from Cache'
            return CacheInfo['rotalignment']


    # Measure the electron current on the viewing screen in Ampere
    # The retrieved current value is multiplied by 2.5 to correct for
    # lost electrons due to backscatters from the main screen
    # See CM Tutor for detail
    def ScreenCurrent(self):
        global CacheDelay
        global CacheTime
        global CacheInfo
        CacheTime['scrncurrent_now'] = time.time()
        
        if (CacheTime['scrncurrent_now'] - CacheTime['scrncurrent_pre'] > CacheDelay['delay_scrncurrent']):
            i = 0
            while i < self.trials:
                err = self.cmremote32.ScreenCurrent(0,byref(CacheInfo['scrncurrent']))
                if err != 0:
                    if err == 65535:
                        self._errmsg(err)
                        return                    
                    print 'ScreenCurrent %s time faild' %(i+1)
                    self._errmsg(err)
                    time.sleep(self.waitmid)
                    i += 1
                else:
                    if Debug == True:
                        print 'retrived ScreenCurrent from microscope'
                    CacheTime['scrncurrent_pre'] = CacheTime['scrncurrent_now']
                    time.sleep(self.waitend)
                    return CacheInfo['scrncurrent'].value * 2.5
                    i = self.trials + 1
        else:
            if Debug == True:
                print 'retrived ScreenCurrent from Cache'
            return CacheInfo['scrncurrent'].value * 2.5


    # Reads the emission currents of the microscope in Amperes
    def EmissionCurrent(self):
        global CacheDelay
        global CacheTime
        global CacheInfo
        CacheTime['emssncurrent_now'] = time.time()
        
        if (CacheTime['emssncurrent_now'] - CacheTime['emssncurrent_pre'] > CacheDelay['delay_emssncurrent']):
            i = 0
            while i < self.trials:
                err = self.cmremote32.EmissionCurrent(0,byref(CacheInfo['emssncurrent']))
                if err != 0:
                    if err == 65535:
                        self._errmsg(err)
                        return                    
                    print 'EmissionCurrent %s time faild' %(i+1)
                    self._errmsg(err)
                    time.sleep(self.waitmid)
                    i += 1
                else:
                    if Debug == True:
                        print 'retrived EmissionCurrent from microscope'
                    CacheTime['emssncurrent_pre'] = CacheTime['emssncurrent_now']
                    time.sleep(self.waitend)
                    return CacheInfo['emssncurrent'].value
                    i = self.trials + 1              
        else:
            if Debug == True:
                print 'retrived EmissionCurrent from Cache'
            return CacheInfo['emssncurrent'].value


    # Determine whether high tension may be switched on or not.
    # Note that the actual swithcing of the high tension is not
    # possible through the remote control for safty reasons
    def RetrHTCond(self):
        global CacheDelay
        global CacheTime
        global CacheInfo
        CacheTime['HTcond_now'] = time.time()
        
        if (CacheTime['HTcond_now'] - CacheTime['HTcond_pre'] > CacheDelay['delay_HTcond']):
            i = 0
            while i < self.trials:
                err = self.cmremote32.RetrHTCond(0,byref(CacheInfo['HTcond']))
                if err != 0:
                    if err == 65535:
                        self._errmsg(err)
                        return                    
                    print 'RetrHTCond %s time faild' %(i+1)
                    self._errmsg(err)
                    time.sleep(self.waitmid)
                    i += 1
                else:
                    if Debug == True:
                        print 'retrived RetrHTCond from microscope'
                    CacheTime['HTcond_pre'] = CacheTime['HTcond_now']
                    time.sleep(self.waitend)
                    return CacheInfo['HTcond'].value
                    i = self.trials + 1
        else:
            if Debug == True:
                print 'retrived RetrHTCond from Cache'
            return CacheInfo['HTcond'].value


    # Reads the current position of the CompuStage.
    # Note that the x,y values are in micrometers.
    # For the CompuStage, it is equivalent to CSAskPos with only x,y report.
    def SRSReadPos(self):
        global CacheDelay
        global CacheTime
        global CacheInfo
        CacheTime['pos_now'] = time.time()
        
        if (CacheTime['pos_now'] - CacheTime['pos_pre'] > CacheDelay['delay_pos']):
            i = 0
            while i < self.trials:
                err = self.cmremote32.SRSReadPos(0,byref(CacheInfo['pos'].x),byref(CacheInfo['pos'].y))
                if err != 0:
                    if err == 65535:
                        self._errmsg(err)
                        return                    
                    print 'SRSReadPos %s time faild' %(i+1)
                    self._errmsg(err)
                    time.sleep(self.waitmid)
                    i += 1
                else:
                    if Debug == True:
                        print 'retrived SRSReadPos from microscope'
                    CacheTime['pos_pre'] = CacheTime['pos_now']
                    time.sleep(self.waitend)
                    return CacheInfo['pos']
                    i = self.trials + 1
        else:
            if Debug == True:
                print 'retrived SRSReadPos from Cache'
            return CacheInfo['pos']


    # Moves the compuStage to the x,y,z,a,b postion specified. 
    # Note x,y,z valuse are in micrometer,the a and b values in degree.
    # m identifies the method of stage movement.
    def CSGotoPos(self,x,y,z,a,b,m):
##        if (x > 900) or (x < -900) or (y > 900) or (y < -900) or (a > 60) or (a < -60):
##            print "WARINING, Compustage will be out of range, RESET your value"
##            return
        # a pointer needs to be passed to the CSGotoPos function.
        # The orignial explanation is wrong in the cmremote32.h.
        i = 0
        while i < self.trials:
            ## err = self.cmremote32.CSGotoPos(0,byref(x),byref(y),byref(z),byref(a),byref(b),m)
            err = self.cmremote32.CSGotoPos(0,c_float(x),c_float(y),c_float(z),c_float(a),c_float(b),m)
            if err != 0:
                if err == 65535:
                    self._errmsg(err)
                    return                
                print 'CSGotoPos %s time faild' %(i+1)
                self._errmsg(err)
                time.sleep(self.waitmid*2)
                i += 1
            else:
                if Debug == True:
                    print "CSGotoPos -- succeed"
                time.sleep(self.waitend)
                i = self.trials + 1


    # Move the CompuStage to the x,y position specified.
    # Equivalent to CSGotoPos with method identified as 'Xgoto or Ygoto'
    def SRSGotoPos(self,x,y):
        if (x > 900) or (x < -900) or (y > 900) or (y < -900):
            print "WARINING, Compustage will be out of range, RESET your value"
            return
        # a pointer needs to be passed to the CSGotoPos function.
        # The orignial explanation is wrong in the cmremote32.h.
        i = 0
        while i < self.trials:
            err = self.cmremote32.SRSGotoPos(0,byref(x),byref(y))
            if err != 0:
                if err == 65535:
                    self._errmsg(err)
                    return                
                print 'SRSGotoPos %s time faild' %(i+1)
                self._errmsg(err)
                time.sleep(self.waitmid)
                i += 1
            else:
                if Debug == True:
                    print "SRSGotoPos -- succeed"
                time.sleep(self.waitend)
                i = self.trials + 1


    # Changes the high tension by the deltaht value specified.
    # Free HT must be on for this function to work.
    def ChangeFreeHT(self,deltaht):
        i = 0
        while i < self.trials:
            err = self.cmremote32.ChangeFreeHT(0,c_float(deltaht))
            if err != 0:
                if err == 65535:
                    self._errmsg(err)
                    return                
                print 'ChangeFreeHT %s time faild' %(i+1)
                self._errmsg(err)
                time.sleep(self.waitmid)
                i += 1
            else:
                if Debug == True:
                    print "ChangeFreeHT -- succeed"
                time.sleep(self.waitend)
                i = self.trials + 1


    #Direct operation contains the following functionality with the diroperation:
    #1	set D mode, Param is the number of camera lengths from the smallest one (0..15) 
    #2	set Focus step size, Param is the step size (1..9)
    #3	set HM/SA magnification, Param is the magnification step from the smallest (LM !) one (0..38)
    #4	set HT step, Param  is the number of steps from the lowest HT setting (0..5)
    #5	set LAD mode, Param is the number of steps from the smallest LAD camera length (0..20)
    #6	set LM magnification, Param is the magnification step from the smallest one (0..38)
    #8	set Spot size, Param is the spot size (1..11)
    #9	set High Tension to maximum, Param has no function
    #10	switch beam blanker on, Param has no function
    #11	switch beam blanker off, Param has no function
    #12	switch EDX protection on, Param has no function
    #13	switch EDX protection off, Param has no function
    #14	switch External XY deflection on, Param has no function
    #15	switch External XY deflection off, Param has no function
    #16 normalise imaging lenses (= pressing TEM Exposure with main screen down but this operation can be performed with screen up)
    # Note:	Neither setting HM/SA or LM magnifications switches the microscope to
    # image mode and this function only operates correctly when it is in image mode.
    # The difference between these two direct operations is that going through the
    # set LM magnification first goes down to the minimum LM magnification and then
    # up to the requested value, while set HM/SA magnification goes up to the maximum
    # magnification and then down to the requested value.
    def DirectOperation(self,diroperation,param):
        i = 0
        while i < self.trials:
            err = self.cmremote32.DirectOperation(0,diroperation,param)
            if err != 0:
                if err == 65535:
                    self._errmsg(err)
                    return                
                print 'DirectOperation %s time faild' %(i+1)
                self._errmsg(err)
                time.sleep(self.waitmid)
                i += 1
            else:
                if Debug == True:
                    print "DirectOperation -- succeed"
                time.sleep(self.waitend)
                i = self.trials + 1


    # Set the rotation alignment to the microscope
    def SetRotationAlignment(self,RotAl):
        i = 0
        while i < self.trials:
            err = self.cmremote32.SetRotationAlignment(0,byref(RotAl))
            if err != 0:
                if err == 65535:
                    self._errmsg(err)
                    return                
                print 'SetRotationAlignment %s time faild' %(i+1)
                self._errmsg(err)
                time.sleep(self.waitmid)
                i += 1
            else:
                if Debug == True:
                    print "SetRotationAlignment -- succeed"
                time.sleep(self.waitend)
                i = self.trials + 1


    # Softkey presses one of the softkeys alongside the MICROCONTROLLER screen by Presses.
    # Counting convention of the sofkeys is 0 to 15, starting at top left, goingdown,
    # then to the right-hand side (so bottom left = 7; top right = 8, etc.).
    # pressesg = press times (1,2,3...)
    def Softkey(self,softkey,pressesg):
        i = 0
        while i < self.trials:
            err = self.cmremote32.Softkey(0,softkey,pressesg)
            if err != 0:
                if err == 65535:
                    self._errmsg(err)
                    return                
                print 'Softkeyt %s time faild' %(i+1)
                self._errmsg(err)
                time.sleep(self.waitmid)
                i += 1
            else:
                if Debug == True:
                    print "Softkey -- succeed"
                time.sleep(self.waitend)
                i = self.trials + 1


    # Turnknob turns one of the turn knobs on the CM microscope.
    # The numbers of turns is given by Count. Note that the latter is an integer
    # while some turnknobs can be turned more than +/-65536 turns. Trap input
    # causing word overflow and, for larger numbers, repeat Turnknob until the
    # required number of turns has been given.
    # 
    # The turnknob id's are:

    # Ratio	        0	Intensity	     9 
    # Contrast	    1	ShiftX	        12
    # Brightness	2	ShiftY	        13
    # Zoom	        3	MultifunctionX 	14
    # Magnification	6	MultifunctionY	15
    # FocusKnob	    7	SpotSize 	    16
    # FocusStep	    8	Filament	    17
    #
    # Turnknob ranges are:
    #
    # Intensity	Normally 2204 with Intensity Fine on (ranges from 1000 to 100000
    # in CM variables display value). Note that recent CM software versions may
    # have more sensitive Intensity control on FEGs in Nanoprobe.
    # Magnification	dependent on image or diffraction, see Direct Operation 
    # Focus	1048580 with Focus Step size 1
    # Focus Step	9
    # Zoom	750
    # Ratio	1000
    # Contrast	5000
    # Brightness	10000
    def TurnKnob(self,Knob,Count):
        i = 0
        while i < self.trials:
            err = self.cmremote32.TurnKnob(0,Knob,Count)
            if err != 0:
                if err == 65535:
                    self._errmsg(err)
                    return                
                print 'TurnKnob %s time faild' %(i+1)
                self._errmsg(err)
                time.sleep(self.waitmid)
                i += 1
            else:
                if Debug == True:
                    print "TurnKnob -- succeed"
                time.sleep(self.waitend)
                i = self.trials + 1


    # Pushbutton presses one of the push buttons on the CM microscope.
    # Some push buttons can have presstype On, Off or Press other ones just Press.
    # On (0), Off (1) and Press (2).
    # The push button id's are (* identifies as On,Off,Press; others as Press only):
    # Buttons that cannot be pushed are HT, Vacuum Off and the main panel On, Standby, Off.
    #
    # Diffraction	   3	SplitScreen	    43
    # * Autofocus	   4	ExchSignal	    44
    # * Reset	       6	* Exp1	        45
    # * Ready	       7	* Exp2	        46
    # Stigmator	      27	* Exp3	        47
    # DarkField	      28	* Zmode	        48
    # Alignment	      29	* YZmode	    49
    # * VacuumOn      31	Ymode	        50
    # * FullFrame     32	* StemExposure	51
    # * SelectedArea  33	SetButton	    52
    # * Crosshairs	  34	AutoButton	    53
    # * Line	      35	* InvertSignal 	54
    # Scanstop	      36	* ExchControl	55
    # * Slow	      37	* Exposure	    60
    # * Fast	      38	* IntRST	    61
    # * TV	          39	IntFine	        62
    # * DualSignal	  41	Wobbler	        63
    # DualMag	      42
    def PushButton(self,button,presstype):
        i = 0
        while i < self.trials:
            err = self.cmremote32.PushButton(0,button,presstype)
            if err != 0:
                if err == 65535:
                    self._errmsg(err)
                    return                
                print 'PushButton %s time faild' %(i+1)
                self._errmsg(err)
                time.sleep(self.waitmid)
                i += 1
            else:
                if Debug == True:
                    print "PushButton -- succeed"
                time.sleep(self.waitend)
                i = self.trials + 1


    # Switches Free HT CONTROL (1=on;0=off))
    def SwitchFreeHT(self,onoff):
        i = 0
        while i < self.trials:
            err = self.cmremote32.SwitchFreeHT(0,onoff)
            if err != 0:
                if err == 65535:
                    self._errmsg(err)
                    return                
                print 'SwitchFreeHT %s time faild' %(i+1)
                self._errmsg(err)
                time.sleep(self.waitmid)
                i += 1
            else:
                if Debug == True:
                    print "SwitchFreeHT -- succeed"
                time.sleep(self.waitend)
                i = self.trials + 1


    # Resets the display of the CM Microcontroller. It allows one to force an
    # update of the screen after remote control operations have been performed
    # (screen updates have very low priority on the microscope and the microscope
    # can be so busy with remote control that it appears to work incorrectly becasus
    # the screen has not been chaged yet). Also use the function after switching
    # SwitchFreeHt off (the microscope does not do an update then).
    def ResetDisplay(self):
        i = 0
        while i < self.trials:
            err = self.cmremote32.ResetDisplay(0)
            if err != 0:
                if err == 65535:
                    self._errmsg(err)
                    return                
                print 'ResetDisplay %s time faild' %(i+1)
                self._errmsg(err)
                time.sleep(self.waitmid)
                i += 1
            else:
                if Debug == True:
                    print "ResetDisplay -- succeed"
                time.sleep(self.waitend)
                i = self.trials + 1


    # Retrieve all the stigmators setting as a single block
    def GetStigmators(self):
        global CacheDelay
        global CacheTime
        global CacheInfo
        CacheTime['stigmators_now'] = time.time()
        leng  = c_int(0)    # refer to GetCMVar for detail
        
        if (CacheTime['stigmators_now'] - CacheTime['stigmators_pre'] > CacheDelay['delay_stigmators']):
            i = 0
            while i < self.trials:
                err = self.cmremote32.GetStigmators(0,byref(CacheInfo['stigmators']),byref(leng))
                if err != 0:
                    if err == 65535:
                        self._errmsg(err)
                        return
                    print 'GetStigmators %s time faild' %(i+1)
                    self._errmsg(err)
                    time.sleep(self.waitmid)
                    i += 1
                else:
                    if Debug == True:
                        print 'retrived GetStigmators from microscope'
                    CacheTime['stigmators_pre'] = CacheTime['stigmators_now']
                    time.sleep(self.waitend)
                    return CacheInfo['stigmators']
                    i = self.trials + 1
        else:
            if Debug == True:
                print 'retrived GetStigmators from Cache'
            return CacheInfo['stigmators']


    # Set stigmator setting back to microscope
    def SetStigmators(self, stigs = 'None'):
        global CacheInfo
        leng  = c_int(0)    # refer to GetCMVar for detail
        
        if stigs == 'None':
            print 'No stigmator setting sent to the microscope'
            return
        
        i = 0
        while i < self.trials:
            if stigs == 'Obj':
                err = self.cmremote32.SetObjStigmator(0,byref(CacheInfo['stigmators']),1184)  # The length of stigmators structure is 1184
            if stigs == 'C2':
                err = self.cmremote32.SetC2Stigmator(0,byref(CacheInfo['stigmators']),1184)
            if stigs == 'Diff':
                err = self.cmremote32.SetDifStigmator(0,byref(CacheInfo['stigmators']),1184)

            if err != 0:
                if err == 65535:
                    self._errmsg(err)
                    return               
                print 'SetStigmators %s time faild' %(i+1)
                self._errmsg(err)
                time.sleep(self.waitmid)
                i += 1
            else:
                if Debug == True:
                    print "SetStigmators -- succeed"
                time.sleep(self.waitend)
                i = self.trials + 1

    def GetAlignment(self):
        a = CMData.ALIGNMENTSTYPE()
        leng  = c_int(0)    # refer to GetCMVar for detail
        err = self.cmremote32.GetAlignment(0,byref(a), byref(leng))
	myarray = a.a

    def GetCurrents(self):
        c = CMData.CURRENTS()
        leng  = c_int(0)    # refer to GetCMVar for detail
        err = self.cmremote32.CurrentReadout(0,byref(c), byref(leng))
	myarray = c.c
	return myarray

    def __del__(self):
        print 'close connection to SECS2'
        self.cmremote32.CloseConnection()   # close connection between cmremote32.dll to SECS2
        
