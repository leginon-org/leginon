#!/usr/bin/python -O

import math
import sys

"""
relavent EMAN code:
	csym = dsym * 2.0
	float az, az0=0, az1=2.0*PI;
	float alt, alt0=0, alt1=PI/2.0;
	alt1 /= csym
	for (alt=alt0, j=0; alt<=alt1+angle_step*PI/180.0/2; alt+=angle_step*PI/180.0, j++) {
		float h=floor(360.0/(angle_step*1.1547));	// the 1.1547 makes the overall distribution more like a hexagonal mesh
		h = (int)floor(h*sin(alt)+.5);
		if (h==0) h=1;
		h=fabs((float)csym)*floor(h/fabs((float)csym)+.5);
		h=2.0*PI/h;
		if (alt>0 && (az1-az0)/h<2.8) h=(az1-az0)/2.1;
		if (alt==0) h=az1;
		for (az=az0+(j%1)?h/2.0:0; az<az1-h/4; az+=h) {
			if (! with_mirror && az>PI && alt>PI/2-.001 && alt<PI/2.0+.001) continue;	// ignore half of the equtor
			float az_final = az;
		}
	}
"""

def arange(start, stop=None, step=None):
    if stop is None:
        stop = float(start)
        start = 0.0
    if step is None:
        step = 1.0
    cur = float(start)
    while cur < stop:
        yield cur
        cur += step


def numProj(ang=5, sym='d7', with_mirror=False):
	csym = abs(float(sym[1:]))
	ang = abs(float(ang))
	angrad = ang*math.pi/180.0
	maxalt = math.pi/2.0 + angrad/1.99
	maxaz = 2.0*math.pi/csym
	if sym[0] == 'd':
		maxaz /= 2.0
	numproj = 0
	for i,alt in enumerate(arange(0.0, maxalt, angrad)):
		numsteps = math.floor(360.0/(ang*1.1547));
		numsteps = math.floor(numsteps * math.sin(alt) + 0.5)
		if numsteps < 1.0e-3:
			numsteps = 1.0
		numsteps = csym * math.floor(numsteps/csym + 0.5)
		if numsteps < 1.0e-3:
			numsteps = 1.0e-3
		azstep = 2.0*math.pi/numsteps
		if alt < 1.0e-6:
			azstep = maxaz
		elif (maxaz/azstep) < 2.8:
			### if less than 2.8 steps, use 2 steps
			azstep = maxaz/2.1
		for az in arange(0.0, maxaz-azstep/4.0, azstep):
			if not with_mirror and az > math.pi-1.0e-3 and abs(alt-math.pi/2.0) < 1.0e-3:
				### ignore half of the equtor
				#print "skip mirror"
				continue
			numproj+=1
			print "%d\t%.2f\t%.2f\t0.00" % (numproj, alt*180.0/math.pi, az*180.0/math.pi)

	print "Number of Projections: ",numproj
	return numproj

if __name__ == '__main__':
	numProj(sys.argv[1], sys.argv[2])
