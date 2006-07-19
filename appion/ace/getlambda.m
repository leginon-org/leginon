function lambda = getlambda(V) 
%
% DESCRIPTION: 
%     Calculates the wavelength of the electon at a given operating voltage. 
%
% USAGE: 
%     lambda = getlambda(V). 
%
%     V      : Operating voltage in volts. 
%     lambda : Wavelength of electron. 
%
% Copyright 2004-2005 Satya P. Mallick.

lambda = (1.226*1e-9)/sqrt(V + 0.9788*1e-6*V^2);


