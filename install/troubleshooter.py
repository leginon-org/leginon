#!/usr/bin/env python
# The line above will attempt to interpret this script in python.
# It uses the current environment, which must define a path to the python
# executable.

#==========================================================================
#  Processing Server Dependency Checker
#  This script will check Python and the Python modules installed
#  on this system to see if all processing server requirements are met.
#==========================================================================

# myami
import checkPackages

class Troubleshooter(object):
    
    # Create an instance of the CheckPackages class
    checkPkgs = checkPackages.CheckPackages()    
    
    def runWebServerCheck(self):
        # List the packages that are required for the web server
        packages = [ 'NUMPY', 
                'PIL', 
                'PYTHON', 
                'SCIPY',
                'WEBSERVER'
                ]
        
        msg = '*******************************************************************\n'
        msg += 'Checking Web Server package dependencies.'
        self.checkPkgs.showMessage(msg)
        self.checkPkgs.runValidation(packages)
        
    #==========================================================================
    # Implements a user interface to use checkPackages.py to ensure the 
    # Processing server requirements are met.
    #==========================================================================
    def runProcessingServerCheck(self):
    
        value = raw_input("Check Processing Server Python packages? (y/n): ")
        if 'y' in value:
            # List the packages that are required for the processing server
            packages = ['MYSQLDB', 
                        'NUMPY', 
                        'PIL', 
                        'PYTHON', 
                        'PYXML', 
                        'SCIPY', 
                        'WXPYTHON', 
                        'WXPYTHONAPP'] 
            
            msg = '*******************************************************************\n'
            msg += 'Checking Processing Server package dependencies.'
            self.checkPkgs.showMessage(msg)
            self.checkPkgs.runValidation(packages)
        
        value = raw_input("Print Python Path? (y/n): ")
        if 'y' in value:
            msg = '*******************************************************************\n'
            msg += 'Printing the Python path.'
            self.checkPkgs.showMessage(msg)
            self.checkPkgs.runValidation(['PYTHONPATH'])
    
        value = raw_input("Check Sinedon.cfg? (y/n): ")
        if 'y' in value:
            msg = '*******************************************************************\n'
            msg += 'Checking Sinedon Config.'
            self.checkPkgs.showMessage(msg)
            self.checkPkgs.runValidation(['SINEDONCFGPATH'])
        
        value = raw_input("Check Leginon.cfg? (y/n): ")
        if 'y' in value:
            msg = '*******************************************************************\n'
            msg += 'Checking Leginon Config.'
            self.checkPkgs.showMessage(msg)
            self.checkPkgs.runValidation(['LEGINONCFGPATH'])
        
        value = raw_input("Run Numpy test? (y/n): ")
        if 'y' in value:
            msg = '*******************************************************************\n'
            msg += 'Running Numpy Test.'
            self.checkPkgs.showMessage(msg)
            self.checkPkgs.runValidation(['NUMPYTEST'])
        
        value = raw_input("Run Scipy test? (y/n): ")
        if 'y' in value:
            msg = '*******************************************************************\n'
            msg += 'Running Scipy test.'
            self.checkPkgs.showMessage(msg)
            self.checkPkgs.runValidation(['SCIPYTEST'])
        
        value = raw_input("Run EMAN test? (y/n): ")
        if 'y' in value:
            msg = '*******************************************************************\n'
            msg += 'Displaying EMAN help window.'
            self.checkPkgs.showMessage(msg)
            self.checkPkgs.runValidation(['EMANTEST'])
        
        value = raw_input("Run XMIPP test? (y/n): ")
        if 'y' in value:
            msg = '*******************************************************************\n'
            msg += 'Displaying Xmipp help.'
            self.checkPkgs.showMessage(msg)
            self.checkPkgs.runValidation(['XMIPPTEST'])
        
        value = raw_input("Check Appion libraries and binaries? (y/n): ")
        if 'y' in value:
            msg = '*******************************************************************\n'
            msg += 'Checking Appion lib and bin.\n'
            msg += 'You can ignore EMAN, MATLAB, and UCSF Chimera errors at this point.'
            self.checkPkgs.showMessage(msg)
            self.checkPkgs.runValidation(['APPION'])
        
    
if __name__ == "__main__":
    troubleshooter = Troubleshooter()
    
    value = raw_input("Check Processing Server packages? (y/n): ")
    if 'y' in value:
        troubleshooter.runProcessingServerCheck()
    
    value = raw_input("Check Web Server packages? (y/n): ")
    if 'y' in value:
        troubleshooter.runWebServerCheck()
        