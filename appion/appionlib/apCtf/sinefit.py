#!/usr/bin/env python

import math
import numpy

def refineAmplitudeContrast(ws2, ctfdata):
	"""
	takes elliptical average data and fits it to the equation
	A cos(ws2) + B sin(ws2) + C
	yin = (sin(x + phi))^2
	    = [ 1 - cos(2*x + 2*phi) ]/2
	    = [ 1 - cos(2x)*cos(2phi) + sin(2x)*sin(2phi) ]/2
	    = A + B cos(2x) + C sin(2x)
	where A = 1/2; B = -cos(2phi)/2; C = +sin(2phi)/2
	ws2 -- s2 variable times all the parameters
		   pi*wavelength*defocus * s^2
		   in inverse Fourier unitless (use meters)
	ctfdata -- elliptically averaged powerspectra data
	"""
	onevec = numpy.ones(ws2.shape, dtype=numpy.float) #A
	cosvec = numpy.cos(2*ws2) #B
	sinvec = numpy.sin(2*ws2) #C
	d0 = numpy.array([onevec, cosvec, sinvec]).transpose()
	q, r = numpy.linalg.qr(d0)
	x0 = r/(numpy.transpose(q)*raddata)
	### x0 = (A,B,C)
	### Now convert to phi
	A,B,C = x0
	print "A,B,C = %.3f,%.3f,%.3f"%(A,B,C)
	if A > 0.7 or A < 0.3:
		apDisplay.printWarning("Fit out of range, value A != 1/2: %.3f"%(A))
		return None
	phi1 = math.acos(2*B)/2.
	phi2 = math.asin(2*C)/2.
	percent_error = abs(phi1 - phi2)/(phi1 + phi2)
	apDisplay.printMsg("Percent error in phase shift: %.3f (values: %.3f,%.3f)"
		%(percent_error, phi1, phi2))
	phi = (phi1 + phi2)/2.0
	
	### now convert to amplitude contrast
	amplitudecontrast = math.sin(-phi)
	return amplitudecontrast

"""
function [x0,iter] = sinefit4par(yin,t,ts,w,onevec,TOL,MAX_ITER)
    x0 = sinefit3par(yin,w*t,onevec);
    x0 = [x0;0];
    iter = 0;success = 0;
    while success == 0
        w=w+x0(4);
        wt=w*t;
        cosvec=cos(wt);
        sinvec=sin(wt);
        D0=[cosvec sinvec onevec -x0(1)*t.*sinvec+x0(2)*t.*cosvec];
        x0old = x0;
        %x0=inv(D0.'*D0)*(D0.'*yin);
        [Q,R] = qr(D0,0);
        x0 = R\(Q.'*yin);
        %x0=lscov(D0,yin);
        iter = iter + 1;
        
        %error term with dw normalized
        temp=abs(x0-x0old).*[1 1 1 ts].';
        err=max(temp);
        
        if err<TOL || iter > MAX_ITER %if iter>MAX_ITER, increase TOL and
            success = 1;              %re-visit this function later.
        end
    end
    x0(end)=w;  %place w in the position if w's increment
"""