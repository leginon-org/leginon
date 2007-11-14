
import apDisplay
import os
import sys
#try:
#	import EMAN
#except ImportError:
#	apDisplay.printWarning("EMAN module did not get imported")
#pass

def executeEmanCmd(emancmd, verbose=False):
	sys.stderr.write(apDisplay.colorString("EMAN: ","magenta")+emancmd+"\n")
	try:
		if verbose is False:
			os.popen(emancmd)
		else:
			os.system(emancmd)
	except:
		apDisplay.printWarning("could not run eman command: "+emancmd)
		raise

def getNumParticlesInStack(stackname):
	numparticles = EMAN.fileCount(stackname)[0]
	return numparticles
