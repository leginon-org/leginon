from appionlib import torqueHost
from appionlib import apConfig
import sys

class BasicAgent(object): 
    '''
    Base Class of apAgent that does not need database connection, just .appion.cfg
    style configuration file.
    '''
    def __init__(self, configFile=None):
        if configFile:
            self.configFile = configFile
        self.processingHost = None

    def createProcessingHost(self):
        if not self.configFile:
            raise ValueError ("Could not create processing host object, configuration file not defined") 
        
        configDict = apConfig.parseConfigFile(self.configFile)

        try:
            processingHostType = configDict['ProcessingHostType'].upper()
            if 'TORQUE' == processingHostType or 'PBS' == processingHostType:
                processingHost = torqueHost.TorqueHost(configDict)
            elif 'MOABTORQUE' == processingHostType or 'MOAB' == processingHostType:
                processingHost = torqueHost.MoabTorqueHost(configDict)
            else:
                sys.stderr.write("Unknown processing host type, using default\n")
                processingHost = torqueHost.TorqueHost(configDict)
            
        except (KeyError, AttributeError):
            sys.stderr.write("Couldn't determine processing host type, using default\n")
            processingHost = torqueHost.TorqueHost(configDict)
 
        return processingHost

##
    #
    
    def Main(self,command):
        '''
        Execute one shell command on processingHost
        '''
        self.processingHost = self.createProcessingHost()
        self.processingHost.executeCommand(command)
