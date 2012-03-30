#!/usr/bin/env python
from appionlib import basicScript

class TomoMaker(basicScript.BasicScriptInstanceRun):
	def createInst(self, jobtype, optargs):
		if jobtype is None:
			from appionlib import apTomoMakerBase
			return apTomoMakerBase.TomoMaker(optargs)
		elif jobtype.lower() == 'imodwbp':
			from appionlib import apTomoFullRecon
			return apTomoFullRecon.ImodFullMaker(optargs)
		elif jobtype.lower() == 'etomosample':
			from appionlib import apTomoSample
			return apTomoSample.SampleMaker(optargs)
		elif jobtype.lower() == 'etomorecon':
			from appionlib import apTomoFullRecon
			return apTomoFullRecon.ETomoMaker(optargs)
		
if __name__ == '__main__':
	test = TomoMaker()
