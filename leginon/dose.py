# dose calculations

## CCD pixel sizes:
### 2k tietz camera:  24um
### 4k tietz camera:  15um
### 4k gatan camera:  15um

#Note:  FEI scopes have large screen with diameter of 160mm

## electrons per coulomb
coulomb = 6.2414e18
pi = 3.14159

# If we use the FEI method:
#      beam current = 2.15 * emulsion / meas. exp. time
# which gives a beam current that = 0.88 * measured screen current

def dose_from_screen(screen_mag, beam_current, beam_diameter):
	## electrons per screen area per second
	beam_area = pi * (beam_diameter/2.0)**2
	screen_electrons = beam_current * coulomb / beam_area
	print 'screen_electrons', screen_electrons

	## electrons per specimen area per second (dose)
	dose = screen_electrons * (screen_mag**2)
	print 'dose', dose

	return dose

def calc_camera(dose, camera_mag, camera_pixel_size, exposure_time, counts):
	camera_dose = float(dose) / float((camera_mag**2))
	print 'camera dose', camera_dose

	dose_per_pixel = camera_dose * (camera_pixel_size**2)
	print 'dose per pixel', dose_per_pixel

	electrons_per_pixel = dose_per_pixel * exposure_time

	counts_per_electron = float(counts) / electrons_per_pixel
	print 'counts per electron', counts_per_electron

	return counts_per_electron

def dose_from_camera(camera_mag, counts, camera_pixel_size, exp_time, camcal):
	totaldose = camera_mag**2 * counts / camera_pixel_size**2 / camcal
	print 'e-/A^2/s', totaldose / 1e20
	dose = totaldose * exp_time
	return dose
