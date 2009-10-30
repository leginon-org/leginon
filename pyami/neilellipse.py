#!/usr/bin/env python

import numpy

def directEllipse(points):
	"""
	takes a (N,2) numpy array containing ellipse points and 

	return the best least square fit for an ellipse
	values A,B,C
	where
	Ax^2 + Bxy +Cy^2 + Dx + Ey + F = 0
	D = E = 0 to center the ellipse on the origin
	F = -1 to force the general conic equation to be an ellipse
	"""

	### power twos
	p2 = numpy.power(points, 2.0)
	Sx2 = p2[:,0].sum()
	Sy2 = p2[:,1].sum()
	Sxy = (points[:,0]*points[:,1]).sum()
	### power fours
	p4 = numpy.power(points, 2.0)
	Sx4 = p4[:,0].sum()
	Sy4 = p4[:,1].sum()
	Sx2y2 = (p2[:,0]*p2[:,1]).sum()
	Sx3y = (numpy.power(points[:,0], 3.0)*points[:,1]).sum()
	Sxy3 = (points[:,0]*numpy.power(points[:,1], 3.0)).sum()
	
	### Calculate ellipse parameters
	A = (Sx3y*(Sxy3*Sy2-Sxy*Sy4)+Sx2y2*(Sx2*Sy4+Sxy*Sxy3)-numpy.power(Sx2y2,2.0)*Sy2-Sx2*numpy.power(Sxy3,2.0))/(Sx4*(Sx2y2*Sy4-numpy.power(Sxy3,2.0))-numpy.power(Sx3y,2.0)*Sy4+2.0*Sx2y2*Sx3y*Sxy3-numpy.power(Sx2y2,3.0));
	
	B = -(Sx4*(Sxy3*Sy2-Sxy*Sy4)+Sx3y*(Sx2*Sy4-Sx2y2*Sy2)-Sx2*Sx2y2*Sxy3+numpy.power(Sx2y2,2.0)*Sxy)/(Sx4*(Sx2y2*Sy4-numpy.power(Sxy3,2.0))-numpy.power(Sx3y,2.0)*Sy4+2.0*Sx2y2*Sx3y*Sxy3-numpy.power(Sx2y2,3.0));

	C = (Sx4*(Sx2y2*Sy2-Sxy*Sxy3)-numpy.power(Sx3y,2.0)*Sy2+Sx3y*(Sx2*Sxy3+Sx2y2*Sxy)-Sx2*numpy.power(Sx2y2,2.0))/(Sx4*(Sx2y2*Sy4-numpy.power(Sxy3,2.0))-numpy.power(Sx3y,2.0)*Sy4+2.0*Sx2y2*Sx3y*Sxy3-numpy.power(Sx2y2,3.0));

	return A, B, C
