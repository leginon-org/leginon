#!/usr/bin/env python
'''
This module attempts to import modules that define FFT Calculator classes.
It keeps a dictionary of these classes called "calculators".
'''

## try importing the fft calculators
## The order here determines the preference of which one should be used.

attempted = []
calculators = {}
priority = []

attempted.append('fftw3')
try:
	from calc_fftw3 import FFTW3Calculator
	calculators['fftw3'] = FFTW3Calculator
	priority.append('fftw3')
except:
	pass

attempted.append('fftpack')
try:
	from calc_fftpack import FFTPACKCalculator
	calculators['fftpack'] = FFTPACKCalculator
	priority.append('fftpack')
except:
	pass
