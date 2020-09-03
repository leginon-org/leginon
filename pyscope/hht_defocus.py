#!/usr/bin/env python
import sys
from pyscope import hitachi

from pyscope import instrumenttype
search_for = 'TEM'
try:
	h = instrumenttype.getInstrumentTypeInstance(search_for)
	if h.__class__.__name__ not in ('Hitachi','HT7800'):
		raise ValueError("TEM %s is not of Hitachi subclass" % h.__class__.__name__)
except Exception, e:
	print "Error", e
	sys.exit(1)

focus_offset_files = hitachi.configs['defocus']['focus_offset_path']
try:
	h.findMagnifications()
except (RuntimeError,IOError):
	# RuntimeError of not finding zero_defocus is exactly what this script is doing.
	pass

if h.zero_defocus_current:
	answer = raw_input('Aready has focus_offset files. Do you really want to redo this ? Y/N/y/n ')
	if 'n' in answer.lower():
		sys.exit(0)

def saveFocusOffset(tem, probe_mode):
	offsets = []
	mag0 = tem.getMagnification()
	mags = tem.probe_mags[probe_mode]
	for m in mags:
		tem.setMagnification(m)
		foc = tem.getFocus()
		offsets.append(foc)
	tem.setMagnification(mag0)
	item_name = 'probe_ref_magnification'
	ref_mag = hitachi.configs['optics'][item_name][probe_mode.lower()]
	if not ref_mag in mags:
		raise ValueError('Reference magnification %s not a valid magnification' % (ref_mag,))
	ref_mag_index = mags.index(ref_mag)
	ref_zero = offsets[ref_mag_index]
	tem.saveEucentricFocusAtReference(probe_mode,ref_zero)
	u_focus = ref_zero
	df = open(focus_offset_files[probe_mode],'w')
	for i,m in enumerate(mags):
		defocus = offsets[i] - u_focus
		df.write('%d\t%9.6f\n' % (m, defocus))
	df.close()

p00 = h.getProbeMode()
m00 = h.getMagnification()
for p in h.getProbeModes():
	h.setProbeMode(p)
	try:
		raw_input('Set a magnification in %s where defocus is zero as reference and hit return. Ctrl-c to exit' % (p,))
		probe_mode = h.getProbeMode()
		saveFocusOffset(h, probe_mode)
	except KeyboardInterrupt:
		break
# reset
h.setProbeMode(p00)
h.setMagnification(m00)
