#!/usr/bin/env python
from pyscope import tecnai
from pyami import fftfun
import time

t = tecnai.Tecnai()

print 'Load gold grating replica into the scope and set it to eucentric height and focus'
print 'Spread the beam to cover an area at a magnification in SA mode'
raw_input('hit enter when done')
print '---------------------------------------------------------------'
print 'Activate Diffraction Mode, change the camera length to'
print ' ~ 1.4 m with magnification knob'
print 'Focus the beam and center it with multi-function knobs.'
print 'The gold diffraction rings should show up sharply.'
print 'Identify the inner-most, i.e. <111>, diffraction ring.'
print '---------------------------------------------------------------'
raw_input('hit enter when ready to continue')

# calculate diffraction angle from high tension
ht = t.getHighTension()
wavelength = fftfun.getElectronWavelength(ht)
gold_diffraction = wavelength/0.236e-9
print 'gold <111> diffraction ring angle = %.3f mrad' % (gold_diffraction * 1e3)
beamtilt = {'x':gold_diffraction,'y':0.00}

# save original beam tilt
beamtilt0 = t.getBeamTilt()

scale_factor = 1.0
best_scale_factor = 1.0
while scale_factor > 0.001:
	print '---------------------------------------------------------------'
	new_beamtilt = {'x':beamtilt0['x']+beamtilt['x']*scale_factor}
	t.setBeamTilt(new_beamtilt)
	print 'current rotation_center_scale = %.1f' % (scale_factor,)
	best_scale_factor = scale_factor
	print 'Refine scale until the inner-most, i.e., <111>, gold diffraction ring'
	print ' is shifted to the center of the screen'
	scale_factor_string = raw_input('Enter new value such as 6.0. Enter 0 to exit--')
	try:
		scale_factor = float(scale_factor_string)
	except:
		print 'Invalid scale factor entered. Try again'

print '---------------------------------------------------------------'
t.setBeamTilt(beamtilt0)
print 'beam tilt is set back'

print '---------------------------------------------------------------'
print 'Write down the final rotation_center_scale %.2f ' % (best_scale_factor)
print 'and replace the default 1.0 in pyscope/tecnai.py with a text editor'
print '---------------------------------------------------------------'

raw_input('hit enter or close window to finish.')
time.sleep(2)
print 'done'
