#!/usr/bin/python -O

import sys
import os
import apDisplay
import apAlignment

if __name__ == "__main__":
	params = apAlignment.defaults()
	apAlignment.getAppionDir(params)
	apAlignment.cmdline(sys.argv[1:], params)
	if params['classonly'] is True:
		apAlignment.overridecmd(params)
	apAlignment.conflicts(params)
	
	apAlignment.getStackInfo(params)
	apAlignment.createOutDir(params)

	if params['commit']is True:
		apAlignment.insertNoRefRun(params, insert=False)

	classfile = os.path.join(params['rundir'], "classes_avg.spi")
	if not os.path.isfile(classfile):
		apAlignment.createSpiderFile(params)
		apAlignment.averageTemplate(params)
		apAlignment.createNoRefSpiderBatchFile(params)
		apAlignment.runSpiderClass(params)
	else:
		apDisplay.printWarning("particles were already aligned for this runid, only redoing clustering") 
		apAlignment.createNoRefSpiderBatchFile(params)
		apAlignment.runSpiderClass(params, reclass=True)

	classfile = os.path.join(params['rundir'],params['classfile']+".spi")
	if not os.path.isfile(classfile):
		apDisplay.printError("failed to write classfile, "+classfile)

	apAlignment.convertClassfileToImagic(params)

	classfile = os.path.join(params['rundir'],params['classfile']+".hed")
	if params['commit']is True:
		apAlignment.insertNoRefRun(params, insert=True)
	if params['numclasses'] <= 80:
		apAlignment.classHistogram(params)
	apDisplay.printMsg("SUCCESS: classfile located at:\n"+classfile)
