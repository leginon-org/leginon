#!/usr/bin/env python
import sys
import time
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

def saveFocusOffset(tem, submode):
	offsets = []
	mag0 = tem.getMagnification()
	mags = tem.submode_mags[submode]
	for m in mags:
		tem.setMagnification(m)
		foc = tem.getFocus()
		offsets.append(foc)
	tem.setMagnification(mag0)
	item_name = 'ref_magnification'
	ref_mag = hitachi.configs['optics'][item_name][submode.lower()]
	if not ref_mag in mags:
		raise ValueError('Reference magnification %s not a valid magnification' % (ref_mag,))
	ref_mag_index = mags.index(ref_mag)
	ref_zero = offsets[ref_mag_index]
	tem.saveEucentricFocusAtReference(submode,ref_zero)
	u_focus = ref_zero
	df = open(focus_offset_files[submode],'w')
	for i,m in enumerate(mags):
		defocus = offsets[i] - u_focus
		df.write('%d\t%9.6f\n' % (m, defocus))
	df.close()

p00 = h.getProbeMode()
s00 = h.getProjectionSubModeFromProbeMode(p00)
m00 = h.getMagnification()
print 'probemodes', h.getProbeModes()
for probe in h.getProbeModes():
	submode = h.getProjectionSubModeFromProbeMode(probe)
	h.setProbeMode(probe)
	# projection submode is normally set through setMagnification
	#h._setProjectionSubMode(submode)
	mags = h.submode_mags[submode]
	h.setMagnification(mags[0])
	print 'Set to %d of projection submode %s' % (mags[0], submode)
	try:
		raw_input('Set a magnification in %s where defocus is zero as reference and hit return. Ctrl-c to exit' % (submode,))
		new_submode = h.getProjectionSubModeName()
		if new_submode != submode:
			KeyboardInterrupt('submode changed to %s. Can not proceed' % new_submode)
		saveFocusOffset(h, submode)
	except KeyboardInterrupt:
		break
	# wait a bit befor changing probe and submode again
	time.sleep(2)
# reset
h.setProbeMode(p00)
#h._setProjectionSubMode(s00)
h.setMagnification(m00)
