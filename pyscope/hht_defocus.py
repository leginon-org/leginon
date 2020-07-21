#!/usr/bin/env python
from pyscope import hitachi

focus_offset_file = hitachi.configs['defocus']['focus_offset_path']
df = open(focus_offset_file,'w')
h = hitachi.Hitachi()
try:
	h.findMagnifications()
except (RuntimeError,IOError):
	# RuntimeError of not finding zero_defocus is exactly what this script is doing.
	pass
mag0 = h.getMagnification()
mags = h.getMagnifications()
offsets = []
for m in mags:
	h.setMagnification(m)
	foc = h.getFocus()
	offsets.append(foc)
h.setMagnification(mag0)
ref_mag = hitachi.configs['defocus']['ref_magnification']
if not ref_mag in mags:
	raise ValueError('Reference magnification %s not a valid magnification' % (ref_mag,))
ref_mag_index = mags.index(ref_mag)
ref_zero = offsets[ref_mag_index]
h.saveEucentricFocusAtReference(ref_zero)
for i,m in enumerate(mags):
	defocus = offsets[i] - ref_zero
	df.write('%d\t%9.6f\n' % (m, defocus))
df.close()
	
	

