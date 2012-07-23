from appionlib import torqueHost
import sys
import re

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
        
        configDict = self.parseConfigFile(self.configFile)

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

    def parseConfigFile (self, configFile):
        confDict ={}
        try:
            cFile= file(configFile, 'r')
        except IOError, e:
            raise IOError ("Couldn't read configuration file " + configFile + ": " + str(e))
        
        #for line in cFile.readlines():          
        line = cFile.readline()
        while line:
            #get rid of an leading and trailing white space
            #line = line.strip()
            #Only process lines of the correct format, quietly ignore all others"
            matchedLine=re.match(r'\s*([A-Za-z]+)\s*=\s*(\S.*)\s*',line)
            if  matchedLine:
                #split the two parts of the line
                (key, value) = matchedLine.groups()
                #value strings can be spread across multiple lines if \n is escaped (\)
                #process these lines.              
                while '\\' == value[-1]:      
                    value = value[:-1]
                    line= cFile.readline()
                    value += line.rstrip('\n')
                #split comma separated values into a list
                if ',' in value:   
                    value = re.split(r'\s*,\s*', value)
                #put the key/value pair in the configuration dictionary    
                confDict[key]=value
            line = cFile.readline()
                
        return confDict
    
    ##
    #
    
    def Main(self,command):
        '''
        Execute one shell command on processingHost
        '''
        self.processingHost = self.createProcessingHost()
        self.processingHost.executeCommand(command)
