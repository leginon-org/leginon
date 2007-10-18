
import apDisplay
import os
import sys
import EMAN

def executeEmanCmd(emancmd, verbose=False):
	sys.stderr.write("EMAN: "+emancmd+"\n")
	try:
		if verbose is False:
			os.popen(emancmd)
		else:
			os.system(emancmd)
	except:
		apDisplay.printError("could not run eman command: "+emancmd)


def getNumParticlesInStack(stackname):
	numparticles = EMAN.fileCount(stackname)[0]
	return numparticles
