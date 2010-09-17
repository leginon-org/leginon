#!/usr/bin/env python
# The line above will attempt to interpret this script in python.
# It uses the current environment, which must define a path to the python
# executable.

# Python
import sys
import os
import ConfigParser
import subprocess
import webbrowser
import datetime
# To supress the DeprecationWarning in Numpy when importing Scipy,
# use "warnings" to filter it.
import warnings
warnings.filterwarnings(action='ignore', module='scipy')

        
         
#==========================================================================
#  Check Packages Class
#  Includes functions to: 
#   1. Check that Python modules have been installed on this system
#   2. Insure the minimum versions of packages are installed
#   3. Insure configuration files are readable
#   4. Run Package tests
#   5. Print troublshooting information about packages
#
#  Default values are provided for the minimum version
#  allowed for Appion/Legigon for each package. These values may be overridden
#  when calling the member functions which accept the min version as a 
#  parameter. 
#
# To add a new troubleshooting function:
# 1. Define the function
# 2. Provide a default min version value if one is needed.
# 3. Add an identifer for your function to the function_map in __init__.
#==========================================================================
class CheckPackages(object):

    #==========================================================================
    # Provide default minimum version values
    #
    # These are intentionally NOT set in the init function so that they can 
    # be used as default function parameter values. 
    #==========================================================================
    
    # min version of Python
    minPyVer = (2, 3, 4)
    
    # min version of the Python Imaging Library (PIL)
    minPILVer = (1, 1, 4)
    
    # min version of MySQL Python client (MySQLdb)
    minMySQLdbVer = (1, 2)
    
    # define the TESTED versions of Numpy
    testedNumpyVers = ('1.0.2','1.0.1') 
    
    # min version of Python XML module
    minPyXMLVer = (0, 8, 2)
    
    # min version of wxPython
    minWxPythonVer = (2, 5, 2, 8)
    
    #==========================================================================
    # The function map defined in the init function basically just gives a 
    # nickname to each of the system validation functions defined in this class.
    # These names can be used to call runValidation().
    #==========================================================================
    def __init__(self, displayResults=True, logFilename='troubleshooter.log'):
        self.displayResults = displayResults  
        self.currentDir = os.getcwd()
        self.logFilename = logFilename
        
        # remove any existing logfile
        if os.path.isfile(self.logFilename):
            os.remove(self.logFilename)
            
        # print the current date and time to the log
        msg = "This file is the Myami Troubleshooting log file. The troubleshooter was last run:\n" 
        msg += str(datetime.datetime.now())
        self.writeToLog(msg)
  
        # every troubleshooting function in this class should have an entry here
        self.function_map = {'PYTHON' : self.checkPythonVersion,
                        'PYTHONPATH' : self.printPythonPath,
                        'PIL' : self.checkPILVersion,
                        'MYSQLDB' : self.checkMySQLdbVersion,
                        'NUMPY' : self.checkNumpyVersion,
                        'NUMPYTEST' : self.runNumpyTest,
                        'SCIPY' : self.checkScipyVersion,
                        'SCIPYTEST' : self.runScipyTest,
                        'PYXML' : self.checkPyXMLVersion,
                        'WXPYTHON' : self.checkWxPythonVersion,
                        'WXPYTHONAPP' : self.testWxPythonApp,
                        'LEGINON' : self.leginonInstalled,
                        'SINEDONCFG' : self.checkSinedonConfig,
                        'SINEDONCFGPATH' : self.printSinedonCfgPath,
                        'LEGINONCFG' : self.checkLeginonConfig,
                        'LEGINONCFGPATH' : self.printLeginonCfgPath,
                        'EMANTEST' : self.runEmanTest,
                        'XMIPPTEST' : self.runXmippTest,
                        'APPION' : self.checkAppion,
                        'WEBSERVER' : self.runWebServerCheck
                        }

        
    #==========================================================================
    # runValidation
    #
    # This function can be used to execute any combination of troubleshooting 
    # functions in this class.
    #
    # packages: input parameter "packages" is an array of values representing 
    # the package tests that are available in the checkPackages class. These
    # values are defined within this class in function_map. 
    # An example of using this function is:
    #
    #  # Create an instance of the CheckPackages class
    #  checkPkgs = checkPackages.CheckPackages()
    #
    #  # Create a list of the packages to check
    #  packages = ['PYTHON',
    #              'PYTHONPATH',
    #              'PIL']
    #
    #  # Use the list as input to runValidation    
    #   checkPkgs.runValidation(packages)
    #
    #==========================================================================
    def runValidation(self, packages) :
        
        for package in packages :
            try :
                self.function_map[package]()
            except Exception, (instance) :
                self.showMessage(' ')
                self.showMessage(instance)
                self.showMessage(' ')
                
        return True
    
    #==========================================================================
    # Instead of using "print" throughout this class, use showMessage. It will
    # allow the caller to suppress visual output. All messages will always 
    # be available in the log file.
    #==========================================================================
    def showMessage(self,msg):
        if (self.displayResults):
            print msg
        self.writeToLog(msg)
    
    def writeToLog(self, message):
        logfile = open(self.currentDir + "/" + self.logFilename, 'a')
        # using print instead of .write so that message is converted to a string if needed 
        print >> logfile, message
        logfile.close()

    def runCommand(self, cmd, input=None):
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # use communicate instead of wait to avoid the possibility of dead lock 
        # if the output pipe fills up.
        output =  proc.communicate(input)
        return output

    #==========================================================================
    # return True if version is at least minimum
    #==========================================================================
    def versionAtLeast(self, version, minimum):
    
        # pad shortest one with zeros to make lengths equal
        version = list(version)
        minimum = list(minimum)
        lenv = len(version)
        lenm = len(minimum)
        diff = lenv-lenm
        if diff < 0:
            version = version + [0 for i in range(diff)]
        else:
            minimum = minimum + [0 for i in range(diff)]
        n = max(lenv,lenm)
        for i in range(n):
            if version[i] > minimum[i]:
                return True
            if version[i] < minimum[i]:
                return False
            # else equal, so check next digit
        return True

    #==========================================================================
    # Run checkwebserver.php to troubleshoot the Web server
    #==========================================================================
    def runWebServerCheck(self):
        self.showMessage("Launching the Web Server Troubleshooter in a web browser...")
        url = 'http://localhost/myamiweb/test/checkwebserver.php'
        webbrowser.open_new(url)

    #==========================================================================
    # Throw exception if Leginon is already installed
    # TODO: Add a function to check which version is installed
    #==========================================================================
    def leginonInstalled(self):        
        try:
            import leginon
        except:
            return False
        else:
            raise Exception("!!!! WARNING !!!! An existing Leginon installation has been found here: %(myver)s . It is best to uninstall your previous Leginon before installing the new one.  The best way to uninstall is to move it to a backup location, just in case you need to revert to the old version." % {'myver' : leginon.__path__[0] }  )
    
        return True
    
    
    
    #==========================================================================
    # Returns: the installed python version
    #==========================================================================
    def getPythonVersion(self):    
        return sys.version_info[:3]

    #==========================================================================
    ## Python
    ## minVersion >= 2.3.4 defined like version = (2,3,4)
    ##
    ## Returns: the running python version
    #==========================================================================
    def checkPythonVersion(self, minVersion = minPyVer):
        # Set minVersion to the default value if none is provided
        if (minVersion is False) :
            minVersion = self.minPyVer 

        ## check for minimum python version
        mypyver = self.getPythonVersion()
        mystr = '.'.join(map(str,mypyver))
        minstr = '.'.join(map(str,minVersion))
        versionOK = self.versionAtLeast(mypyver, minVersion)
                
        if (not versionOK) :
            raise Exception("!!!! WARNING !!!! Python version %(myver)s is too old. Please upgrade to %(minver)s or greater." % {'myver' : mystr, 'minver' : minstr }  )
        
        return mypyver

    
    #==========================================================================
    # Prints information about the Python path
    #==========================================================================
    def printPythonPath(self):    
    
        ## print location of executable, module path and home directory
        msg =  '\n'
        msg += 'Python Path:\n'
        msg += '    Python executable (if wrong, check PATH in your environment):\n'
        msg += '        %s\n' % (sys.executable,)
        msg += '    Python module search path (if wrong, check PYTHONPATH):\n'
        
        for dir in sys.path:
            msg += '        %s\n' % (dir,)
        if not sys.path:
            msg += '        (Empty)\n'
        msg += '    Python says home directory is:  %s\n' % (os.path.expanduser('~'),)
        
        self.showMessage(msg)

    #==========================================================================
    ## Python Imaging Library
    ## minVersion >= 1.1.4
    ## Returns: installed version if version OK, else 0
    #==========================================================================
    def checkPILVersion(self, minVersion = minPILVer):
        version = 0
        minstr = '.'.join(map(str,minVersion))
                    
        try:
            import Image
        except:
            raise Exception("!!!! WARNING !!!! Could not import Python Imaging Library (PIL). You must install Python Imaging Library version %(minver)s or greater." % {'minver' : minstr }  )
        else:
            mystr = Image.VERSION
            mypilver = map(int, mystr.split('.'))
            versionOK = self.versionAtLeast(mypilver, minVersion)
            
            if (versionOK) : 
                version = mystr
            else :
                raise Exception("!!!! WARNING !!!! Python Imaging Library (PIL) version %(myver)s is too old. Please upgrade to %(minver)s or greater." % {'myver' : mystr, 'minver' : minstr }  )
                
        return version
    
    #==========================================================================
    ## Python MySQL client module
    ## minVersion = (1, 2)
    ## Returns: installed version if version OK, else 0
    #==========================================================================
    def checkMySQLdbVersion(self, minVersion = minMySQLdbVer):
        version = 0
        minstr = '.'.join(map(str,minVersion))
                
        try:
            import MySQLdb
        except:
            raise Exception("!!!! WARNING !!!! Could not import MySQL Python client (MySQLdb). You must install MySQLdb module version %(minver)s or greater." % {'minver' : minstr }  )
        else:
            mystr = MySQLdb.__version__
            mymysqlver = MySQLdb.version_info[:3]
            versionOK = self.versionAtLeast(mymysqlver, minVersion)

            if (versionOK) : 
                version = mystr
            else :
                raise Exception("!!!! WARNING !!!! MySQL Python client (MySQLdb) version %(myver)s is too old. Please upgrade to %(minver)s or greater." % {'myver' : mystr, 'minver' : minstr }  )
                                
        return version
    
    #==========================================================================
    ## numpy
    ##  testedVersions = ('1.0.2','1.0.1')
    ## Returns: installed version if version OK, else 0
    #==========================================================================
    def checkNumpyVersion(self, testedVersions = testedNumpyVers):
        version = 0
            
        try:
            import numpy
        except ImportError:
            raise Exception("!!!! WARNING !!!! Could not import Numpy. You must install Numpy. Tested versions: %(minver)s." % {'minver' : testedVersions }  )
        else:
            mystr = numpy.__version__
            version = mystr
            versionOK = False
            if (mystr in testedVersions) : versionOK = True
            
            if (not versionOK) : 
                raise Exception("!!!! WARNING !!!! Numpy version %(myver)s has not been tested. Tested versions: %(minver)s" % {'myver' : mystr, 'minver' : testedVersions }  )
 
        return version
    
    #==========================================================================
    # Run Numpy tests
    #==========================================================================
    def runNumpyTest(self):
        import numpy
        numpy.test()

    
    #==========================================================================
    ## scipy
    ## Returns: 1 version OK, else 0
    #==========================================================================
    def checkScipyVersion(self):
        version = 0
                    
        try:
            import scipy.optimize
        except ImportError:
            raise Exception("!!!! WARNING !!!! Could not import the scipy.optimize module. You must install scipy first.")
        else:
            try:
                scipy.optimize.leastsq
                version = 1
            except:
                raise Exception("!!!! WARNING !!!! The installed version of Scipy does not include the leastsq function. Install a version of scipy.optimize with leastsq."   )
                
        return version
            
    #==========================================================================
    # Run Scipy tests
    #==========================================================================
    def runScipyTest(self):
        import scipy
        scipy.test()

    
    #==========================================================================
    ## Python XML module
    ##    minVersion = (0, 8, 2)
    ## Returns: installed version if version OK, else 0
    #==========================================================================
    def checkPyXMLVersion(self, minVersion = minPyXMLVer):
        version = 0
        minstr = '.'.join(map(str,minVersion))
            
        try:
            import xml
        except:
            raise Exception("!!!! WARNING !!!! Could not import the Python XML module. You must install Python xml version %(minver)s or greater." % {'minver' : minstr }  )
        else:
            mystr = xml.__version__
            myxmlver = map(int, mystr.split('.'))
            versionOK = self.versionAtLeast(myxmlver, minVersion)
            
            if (versionOK) : 
                version = mystr
            else :
                raise Exception("!!!! WARNING !!!! Python XML version %(myver)s is too old. Please upgrade to %(minver)s or greater." % {'myver' : mystr, 'minver' : minstr }  )
                    
        return version
    
    #==========================================================================
    # wxPython
    # Returns: installed version if version OK, else 0
    #==========================================================================
    def checkWxPythonVersion(self, minVersion = minWxPythonVer):
        version = 0
        minstr = '.'.join(map(str, minVersion))
        
        try:
            import wx
        except ImportError:
            raise Exception("!!!! WARNING !!!! Could not import the wxPython module. You must install wxPython version %(minver)s or greater." % {'minver' : minstr }  )        
        else:
            ## check version
            try:
                ## NEWER VERSIONS
                mystr = wx.__version__
                if mystr[-1] == 'u':
                    mystr = mystr[:-1]
                mywxver = map(int, mystr.split('.'))
            except:
                ## OLDER VERSIONS
                mywxver = wx.VERSION[:4]
                mystr = '.'.join(map(str, mywxver))
                
            versionOK = self.versionAtLeast(mywxver, minVersion)
            
            if (versionOK) : 
                version = mystr
            else :
                raise Exception("!!!! WARNING !!!! wxPython version %(myver)s is too old. Please upgrade to %(minver)s or greater." % {'myver' : mystr, 'minver' : minstr }  )
        
        return version
        
    #==========================================================================
    # wxPython
    # Displays a gui that the user must close 
    #==========================================================================
    def testWxPythonApp(self):
            ## test a wx app
            try:
                import wx
            except ImportError:
                raise Exception("!!!! WARNING !!!! Could not import the wxPython module." )        
            else:

                class MyApp(wx.App):
                    def OnInit(self):
                        self.frame = wx.Frame(None, -1, 'wxPython test window')
                        self.sizer = wx.BoxSizer()
        
                        button = wx.Button(self.frame, -1, 'CLOSE')
                        button.SetBackgroundColour(wx.RED)
                        self.sizer.Add(button, 1, border=50, flag=wx.ALL)
                        self.Bind(wx.EVT_BUTTON, self.test, button)
                        
                        self.extlist = wx.ListBox(self.frame, -1, style=wx.LB_EXTENDED)
                        self.extlist.InsertItems(['test1','test2','test3','test4','test5'],0)
                        sz = wx.GridBagSizer(2, 0)
                        label = wx.StaticText(self.frame, -1, 'A Scrollable Listbox')
                        sz.Add(label, (1, 0), (1, 4), wx.ALIGN_CENTER)
                        sz.Add(self.extlist, (2, 0), (1, 4), wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
        
                        self.szmain = wx.GridBagSizer(2, 2)
                        self.szmain.Add(sz, (0, 0), (1, 1), wx.EXPAND|wx.ALL, 10)
                        self.szmain.Add(self.sizer, (1, 0), (1, 1),wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 5)
                                    
                        self.frame.SetSizerAndFit(self.szmain)
                        self.SetTopWindow(self.frame)
                        self.frame.Show(True)
                        return True
        
                    def test(self, evt):
                        print 'User closed wxPython test App.'
                        self.frame.Close()
                       
                self.showMessage(' ')  
                self.showMessage('Testing a wxPython application.  Close the window that pops up...')
                try:
                    app = MyApp(0)
                    app.MainLoop()
                except:
                    raise Exception("!!!! WARNING !!!! Failed to start wx application.  This is usually because you do not have display permission." )
                self.showMessage('    wxPython test successful')
                
                return True
            
    #==========================================================================
    # This will look for a given configfilename under the python site packages
    # directory in the specified folder. It will also look in the users home
    # directory. 
    # Returns the paths to any config files found with the specified name.
    #==========================================================================
    def findConfigFiles(self, configfilename, folder):
        # get the python site-packages directory
        import distutils.sysconfig
        pySitePackDir =  distutils.sysconfig.get_python_lib()
        
        # get the user's home directory
        HOME = os.path.expanduser('~')
        
        config_locations = [
            os.path.join('/etc', configfilename),
            os.path.join(pySitePackDir, folder, configfilename),
            os.path.join(HOME, configfilename),
        ]

        # create a config parser to try to read the config file    
        configparser = ConfigParser.SafeConfigParser()
        try:
            configfiles = configparser.read(config_locations)
        except:
            raise Exception("!!!! WARNING !!!! Failed to read %(filename)s." % {'filename' : configfilename } )
        else:
            if not configfiles :
                raise Exception("!!!! WARNING !!!! Failed to locate %(filename)s." % {'filename' : configfilename } )

        return configfiles
        
    #==========================================================================
    # Check for sinedon.cfg
    #
    # look for the file in the python site-packages directory as well as the
    # users home directory
    #
    # If printPath is True, this function will print the paths to sinedon
    # config files found on the system.
    #==========================================================================
    def checkSinedonConfig(self, printPath = False):
            
        try:
            import sinedon.dbconfig
        except:
            raise Exception("!!!! WARNING !!!! Failed to import sinedon." )
        else:
            configfiles = sinedon.dbconfig.configfiles
    
        if not configfiles:
            raise Exception("!!!! WARNING !!!! Failed to locate sinedon.cfg." )
        elif printPath :
            msg = ' Found sinedon.cfg at the following locations:\n' 
            for configfile in configfiles:
                msg += ' \t%s\n' % (configfile,)
                
            self.showMessage(msg)
            
        return True

    #==========================================================================
    # Print the path to sinedon.cfg
    #==========================================================================
    def printSinedonCfgPath(self):     
        self.checkSinedonConfig(True)   

    #==========================================================================
    # Check for leginon.cfg
    #
    # look for the file in the python site-packages directory as well as the
    # users home directory
    # If printPath is true, the path to the cfg file will be printed.
    #==========================================================================
    def checkLeginonConfig(self, printPath = False):
        
        try:
            import leginon.configparser
        except:
            raise Exception("!!!! WARNING !!!! Failed to import leginon.configparser." )
        else:
            configfiles = leginon.configparser.configfiles
    
        if not configfiles:
            raise Exception("!!!! WARNING !!!! Failed to locate leginon.cfg." )
        elif printPath :
            msg = ' Found leginon.cfg at the following locations:\n' 
            for configfile in configfiles:
                msg += ' \t%s\n' % (configfile,)

            self.showMessage(msg)

        return True


    #==========================================================================
    # Print the path to leginon.cfg
    #==========================================================================
    def printLeginonCfgPath(self):     
        self.checkLeginonConfig(True)   
        
    #==========================================================================
    # Run EMAN tests
    # Display the Eman help window
    #==========================================================================
    def runEmanTest(self):    
        output = self.runCommand('proc2d help')
        stdoutdata = output[0]
        stderrdata = output[1]
        
        self.showMessage(stdoutdata)

        if (stderrdata):
            msg = "!!!! EMAN ERROR: !!!!\n" 
            msg += "%s\n" % (stderrdata,)
            msg += "You may install EMAN with the instructions found here:\n" 
            msg += "    http://ami.scripps.edu/redmine/projects/appion/wiki/Install_EMAN" 
            raise Exception(msg)
        
        return True
    
    
    #==========================================================================
    # Run XMIPP tests
    # Display Xmipp help
    #==========================================================================
    def runXmippTest(self):
        output = self.runCommand('xmipp_ml_align2d -h')
        stdoutdata = output[0]
        stderrdata = output[1]
        
        self.showMessage(stdoutdata)

        if (stderrdata):
            msg =  '!!!! Xmipp ERROR: !!!!\n'
            msg += "%s\n" % (stderrdata,)
            msg += ' You may install Xmipp with the instructions found here: \n'
            msg += '    http://ami.scripps.edu/redmine/projects/appion/wiki/Install_Xmipp'
            raise Exception(msg)
    
        return True
    
    
    #==========================================================================
    # Calls check.sh which imports libraries 
    # and check binaries that are part of Appion
    #==========================================================================
    def checkAppion(self):
        # TODO: use the current working dir (os.getcwd()) to find the path to myami
        # so this file does not need to live in myami/install forever. 
        os.chdir("../appion/")
        output = self.runCommand('./check.sh')
        os.chdir("../install/")

        stdoutdata = output[0]
        stderrdata = output[1]
        
        self.showMessage(stdoutdata)
        self.showMessage(stderrdata)


    def runAll(self):
        self.runValidation(self.function_map)        
        
        
if __name__ == "__main__":
    checkPackages = CheckPackages()
    checkPackages.runAll()
