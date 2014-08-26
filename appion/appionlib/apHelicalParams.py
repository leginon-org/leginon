## python
import os
import math

## appion
from appionlib import apDisplay

#=====================

def setupParams():
## Parameters for helical processing using Phoelix ##
## These are optional parameters which will mostly always stay the same ##
	master_params = {}
	master_params['batch'] = 1
	master_params['s_leginon'] = 0
	master_params['s_verbose'] = 0
	master_params['s_log'] = 1
	master_params['tflag'] = 0
	master_params['ctf'] = 0
	master_params['fres'] = 10
	master_params['rangefactor'] = 2
	master_params['cutres'] = 10
	master_params['calling_method'] = 'pfo'
	master_params['radfil'] = 5
	master_params['Aradfilbg'] = 400
	master_params['cs'] = 2.0
	master_params['nsdev'] = 2
	master_params['regno'] = 5
	master_params['range'] = 3
	master_params['prow'] = 128
	master_params['pcol'] = 600
	master_params['pflag'] = 18
	master_params['tag1'] = '"_"'
	master_params['xshift'] = 0
	master_params['yshift'] = 0
	master_params['rotation'] = 0
	master_params['shear'] = 0
	master_params['tilt'] = 0
	master_params['rmin'] = -0.1
	master_params['rmax'] = 0.1
	master_params['idump'] = 2
	master_params['merid'] = 1
	master_params['width'] = 1
	master_params['iphase'] = 0
	master_params['nl1'] = 0
	master_params['nl2'] = 255
	master_params['nr1'] = 0
	master_params['nr2'] = 255
	master_params['delta_amp'] = 50.0
	master_params['delta_radius'] = 5.0
	master_params['delta_separation'] = 6.0
	master_params['increment1'] = 0.5
	master_params['increment2'] = 0.1
	master_params['starttilt'] = -8.0
	master_params['numtilts'] = 45
	master_params['startshift'] = -5.0
	master_params['numshifts'] = 25
	master_params['maxphi'] = 40.01
	master_params['use_shift'] = '"yes"'
	master_params['use_tilt'] = '"yes"'
	master_params['final_tilt'] = 0
	master_params['final_shift'] = -0.5
	master_params['maxtilt'] = 3.0
	master_params['maxshift'] = 1.0
	master_params['maxtsresid'] = 50.0
	master_params['repnum'] = 1
	master_params['incnum'] = 6
	master_params['fitflag'] = '"no"'
	master_params['template'] = '" "'
	master_params['neartag'] = '"n"'
	master_params['fartag'] = '"f"'
	master_params['maxrscale'] = 1.099
	master_params['maxresid'] = 50.01
	master_params['maxresidset'] = '`echo 50 45 45 35 35 35 35 35 35 35`'
	master_params['finalresid'] = 45.01
	master_params['minupdown'] = 0.0
	master_params['auto_remove_files'] = 0

	return master_params

#=====================
def calculateParams(step, diameter, diaminner, replen, padval):
	master_params = setupParams()
	if step is None:
		apDisplay.printError("No stepsize specified")
	else:
		master_params['step'] = step
	if diameter is None:
		apDisplay.printError("No filament diameter specified")
	else:
		master_params['diameter'] = diameter
	if diaminner is None:
		apDisplay.printError("No inner filament diameter specified")
	else:
		master_params['diaminner'] = diaminner
	if replen is None:
		apDisplay.printError("No filament repleat length specified")
	else:
		master_params['replen'] = replen
	if padval is None:
		apDisplay.printError("No pad value specified")
	else:
		master_params['padval'] = padval
	master_params['xover'] = replen
	master_params['diamouter'] = diameter
	master_params['irad'] = math.floor((diaminner / step)/2) - 5
	master_params['orad'] = math.ceil((diameter / step)/2) + 5
	master_params['diamfil'] = (diameter / step) / 4
	master_params['Aradfil'] = (step * 1.01)
	master_params['pad1'] = (diameter / step)
	master_params['padrow'] = powtwo(master_params['pad1'])
	master_params['srow'] = master_params['padrow']
	master_params['frowsize'] = (master_params['srow'] * 2)
	master_params['delbr'] = (1.0 / (master_params['frowsize'] * step))
	master_params['snifwidth'] = int(math.ceil(((padval * step) / replen) / 2))

	return master_params

#=====================
def powtwo(n):
	x = int(pow(2, math.ceil(math.log(n, 2))))
	return x


	











