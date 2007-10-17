#!/usr/bin/python -O

import sys
import os
import apDisplay
import apAlignment
import apParam

if __name__ == "__main__":
	params = apAlignment.defaults()
	params['appiondir'] = apParam.getAppionDir()
	apAlignment.cmdline(sys.argv[1:], params)
	apAlignment.conflicts(params)
	apAlignment.refconflicts(params)
	apAlignment.getStackInfo(params)
	apAlignment.createOutDir(params)
	
	if params['commit']is True:
		apAlignment.insertRefRun(params, insert=True)

        apAlignment.createSpiderFile(params)
	apAlignment.createSpiderRefFile(params)
	for i in range(params['iter']):
		itn=i+1
		itername='refine%d' % itn
		params['iterdir'] = os.path.join(params['rundir'],itername)
		apParam.createDirectory(params['iterdir'])
		os.chdir(params['iterdir'])
		apAlignment.createRefSpiderBatchFile(params,itn)
		apAlignment.runSpiderRefAli(params)
		apAlignment.makeRefMrc(params)
		if params['commit']is True:
			apAlignment.insertIterRun(params,itn,itername, insert=True)

