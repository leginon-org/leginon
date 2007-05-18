#!/usr/bin/python -O

import sys
#import re
import os
import apXml
import pprint
import optparse
import apDisplay

if __name__ == "__main__":

	if len(sys.argv) < 2:
		function = "pyace"
	else:
		function = sys.argv[1].strip()
		function = os.path.splitext(function)[0]
		
	xmldict = apXml.readTwoXmlFiles("allAppion.xml",function+".xml")

	params = apXml.generateParams(xmldict)

	cmddict = {}
	"""
	for arg in sys.argv[1:]:
		arg = arg.strip()
		if arg[-4:] == ".mrc":
			print "loaded MRC file:",apDisplay.shortenImageName(arg)
		elif '=' in arg:
			param,value = arg.split('=')
			param = param.lower()
			if param in xmldict:
				print param,"=",value
				cmddict[param] = value
			else:
				apDisplay.printError("'"+param+"' is not a valid commandline option")
		else:
			if arg in ('help','-h','--help'):
				apXml.printHelp(xmldict)
			elif arg in xmldict:
				print arg,"=",True
				cmddict[arg] = True
			else:
				apDisplay.printError("'"+arg+"' is NOT a valid argument")
	"""

	apXml.fancyPrintDict(cmddict)
	cmddict = apXml.checkParamDict(cmddict,xmldict)
	apXml.fancyPrintDict(cmddict)

	apXml.fancyPrintDict(params)
	apXml.overWriteDict(params,cmddict)
	apXml.fancyPrintDict(params)

	#pprint.pprint(xmldict)
	apXml.printHelp(xmldict)


