#!/usr/bin/env python

import math
import time
import numpy
import scipy.stats
from appionlib import apDisplay

def refineAmplitudeContrast(ws2, ctfdata, original_amp_contrast=None):
	"""
	takes elliptical average data and fits it to the equation
	A + B cos(x) + C sin(x)
	ctfdata = (sin(x + phi))^2
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
	if numpy.linalg.det(r) == 0:
		apDisplay.printWarning("Singular matrix in calculation")
		return None
	denom = numpy.dot(numpy.transpose(q), ctfdata)
	#x0 = r\denom
	x0 = numpy.dot(numpy.linalg.inv(r), denom)
	### x0 = (A,B,C)
	### Now convert to phi
	A,B,C = x0
	print "A,B,C = %.8f,%.8f,%.8f"%(A,B,C)
	ctffit1 = A*onevec + B*cosvec + C*sinvec

	apDisplay.printColor("shift = %.8f"%(A), "cyan")

	trig_amplitude = math.sqrt(B**2 + C**2)
	apDisplay.printColor("trig_amplitude = %.8f"%(trig_amplitude), "cyan")


	#B cos(2x) + C sin(2x) = D * sin(2x + psi), where psi = atan2(B,C)
	psi = math.atan2(B,C)
	
	ctffit2a = A*onevec + trig_amplitude*numpy.sin(2*ws2 + psi)
	ctffit2b = 0.5 + 0.5*numpy.sin(2*ws2 + psi)

	apDisplay.printColor("psi = %.8f"%(psi), "cyan")
	# sin(2x + psi) = cos(2x + 2phi)
	# sin(z) = cos(z - pi/2) => sin(2x + psi) = cos(2x + psi - pi/2)
	# => cos(2x + psi - pi/2) = cos(2x + 2phi)
	# => psi - pi/2 = 2*phi
	# => phi = (2*psi - pi)/4
	phi = (2*psi + math.pi)/4
	apDisplay.printColor("phi = %.8f, %.8f, %.8f"%(phi-math.pi, phi, phi+math.pi), "cyan")

	ctffit3 = (numpy.sin(ws2 + phi))**2
	conf1 = scipy.stats.pearsonr(ctffit1, ctffit3)[0]
	print "Conf1 %.8f"%(conf1)
	apDisplay.printColor("ctffit1 <> ctffit3: %.8f"%(conf1), "green")

	### now convert to amplitude contrast
	#phi = -1.0*math.asin(amplitudecontrast)
	amplitudecontrast = math.sin(phi)
	ac = amplitudecontrast

	apDisplay.printColor("amplitude contrast = %.8f"%(amplitudecontrast), "cyan")
	ctffit4 = (math.sqrt(1 - ac**2)*numpy.sin(ws2) + ac*numpy.cos(ws2))**2

	from matplotlib import pyplot
	pyplot.clf()
	pyplot.plot(ws2, ctfdata, '.', color="black")
	pyplot.plot(ws2, ctffit1, '-', color="red")
	#pyplot.plot(ws2, ctffit2a, '-', color="yellow")
	#pyplot.plot(ws2, ctffit2b, '-', color="orange")
	pyplot.plot(ws2, ctffit3, '-', color="green")
	pyplot.plot(ws2, ctffit4, '-', color="blue")
	if original_amp_contrast is not None:
		ac = original_amp_contrast
		ctffit5 = (math.sqrt(1 - ac**2)*numpy.sin(ws2) + ac*numpy.cos(ws2))**2
		pyplot.plot(ws2, ctffit5, '--', color="purple")
	pyplot.show()

	if A > 0.65 or A < 0.4:
		apDisplay.printWarning("Fit out of range, value A != 1/2: %.8f"%(A))
		return None
	if trig_amplitude > 0.6 or trig_amplitude < 0.3:
		apDisplay.printWarning("Fit out of range, value trig_amplitude != 1/2: %.8f"%(trig_amplitude))
		return None
	if amplitudecontrast > 0.5 or amplitudecontrast < 0.0:
		apDisplay.printWarning("Fit out of range, value amplitudecontrast: %.8f"%(amplitudecontrast))
		return None

	return amplitudecontrast


def refineCTF(s2, ctfdata, initdefocus, initampcontrast):
	"""
	takes elliptical average data and fits it to the equation
	A + B cos(w*x) + C sin(w*x)
	ctfdata = (sin(w*x + phi))^2
	        = [ 1 - cos(2*w*x + 2*phi) ]/2
	        = [ 1 - cos(2wx)*cos(2phi) + sin(2wx)*sin(2phi) ]/2
	        = A + B cos(2wx) + C sin(2wx)
	Taylor series:
		cos(2*w*s2) = cos(2*wi*s2) - 2*s2*sin(2*wi*s2) * dw
		sin(2*w*s2) = cos(2*wi*s2) + 2*s2*cos(2*wi*s2) * dw
	Substitution:
		A + B cos(2*w*s2) + C sin(2*w*s2) - 2*Bi*s2*sin(2*wi*s2)*dw + 2*Ci*s2*cos(2*wi*s2)*dw
	Setup linear solve for A,B,C,dw
		1, cos(w*s2), sin(w*s2), -2*Bi*s2*sin(2*wi*s2) + 2*Ci*s2*cos(2*wi*s2)
	Note: in term 4: Bi,Ci,wi are estimates from previous interation
		this makes it an iterative process
	where A = 1/2; B = -cos(2phi)/2; C = +sin(2phi)/2
	s2 -- s2 variable times all the parameters, except defocus
		   pi*wavelength * s^2
		   in inverse Fourier meters
	ctfdata -- elliptically averaged powerspectra data
	"""
	## initial values
	
	phi = math.asin(initampcontrast)
	B = -math.cos(2*phi)/2 #B = -cos(2phi)/2
	C = math.sin(2*phi)/2 #C = +sin(2phi)/2
	w = initdefocus
	ac = initampcontrast
	initctffit = (math.sqrt(1 - ac**2)*numpy.sin(w*s2) + ac*numpy.cos(w*s2))**2
	initconf = scipy.stats.pearsonr(ctfdata, initctffit)[0]
	apDisplay.printColor("initial defocus = %.8e"%(w), "cyan")
	apDisplay.printColor("initial amplitude contrast = %.8f"%(initampcontrast), "cyan")
	apDisplay.printColor("initial confidence value: %.8f"%(initconf), "green")

	onevec = numpy.ones(s2.shape, dtype=numpy.float) #column 1
	numiter = 30
	defocus_tolerance = 1e-10
	dw = 1e100 #big number
	for i in range(numiter):
		if abs(dw) < defocus_tolerance:
			break
		cosvec = numpy.cos(2*w*s2) #column 2, fixed defocus from previous
		sinvec = numpy.sin(2*w*s2) #column 3, fixed defocus from previous
		dwvec = 2*C*s2*numpy.cos(2*w*s2) - 2*B*s2*numpy.sin(2*w*s2) #column 4: -2*Bi*s2*sin(2*wi*s2) + 2*Ci*s2*cos(2*wi*s2)
		d0 = numpy.array([onevec, cosvec, sinvec, dwvec]).transpose()
		q, r = numpy.linalg.qr(d0)
		if numpy.linalg.det(r) == 0:
			apDisplay.printWarning("Singular matrix in calculation")
			return None
		denom = numpy.dot(numpy.transpose(q), ctfdata)
		x0 = numpy.dot(numpy.linalg.inv(r), denom)
		A,B,C,dw = x0
		print "A,B,C,DW = %.8f,%.8f,%.8f,%.8e"%(A,B,C,dw)

		trig_amplitude = math.sqrt(B**2 + C**2)
		apDisplay.printColor("trig_amplitude = %.8f"%(trig_amplitude), "cyan")

		w = w + dw
		apDisplay.printColor("defocus = %.8e"%(w), "cyan")
		psi = math.atan2(B,C)
		phi = (2*psi + math.pi)/4
		amplitudecontrast = math.sin(phi)
		ac = amplitudecontrast
		apDisplay.printColor("amplitude contrast = %.8f"%(amplitudecontrast), "cyan")

		ctffit1 = A*onevec + B*cosvec + C*sinvec + dw*dwvec
		ctffit4 = (math.sqrt(1 - ac**2)*numpy.sin(w*s2) + ac*numpy.cos(w*s2))**2
		from matplotlib import pyplot
		pyplot.clf()
		pyplot.plot(w*s2, ctfdata, '.', color="black")
		pyplot.plot(w*s2, initctffit, '-', color="purple", linewidth=2)
		pyplot.plot(w*s2, ctffit1, '-', color="red")
		pyplot.plot(w*s2, ctffit4, '-', color="blue")
		pyplot.show()
		pyplot.draw()

		conf1 = scipy.stats.pearsonr(ctfdata, ctffit1)[0]
		conf2 = scipy.stats.pearsonr(ctfdata, ctffit4)[0]
		apDisplay.printColor("Confidence values: %.8f, %.8f"%(conf1, conf2), "green")

		time.sleep(3)

	if A > 0.65 or A < 0.4:
		apDisplay.printWarning("Fit out of range, value A != 1/2: %.8f"%(A))
		return None
	if trig_amplitude > 0.6 or trig_amplitude < 0.3:
		apDisplay.printWarning("Fit out of range, value trig_amplitude != 1/2: %.8f"%(trig_amplitude))
		return None

	apDisplay.printColor("final defocus = %.8e"%(w), "green")
	apDisplay.printColor("final amplitude contrast = %.8f"%(amplitudecontrast), "green")
	return w, amplitudecontrast

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
