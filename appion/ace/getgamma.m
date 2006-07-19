function gmma = getgamma(s,defocus,Cs, lambda); 
% DESCRIPTION: 
%     Calculates the gamma for getctf function. 
%
% USAGE: 
%     gmma = getgamma(s,defocus,Cs, lambda); 
%       
%     s       : A vector containing the frequency in Hz.  
%     defocus : Defocus setting of the microscope in meters 
%     Cs      : Spherical abbreation in meters. 
%     lambda  : wavelength in meters. 
%     gmma    : Output vector containing the angle gamma at
%                 each frequency s. 
%
% See also GETCTF

        
gmma = 2*pi*(0.25*Cs*(lambda.^3).*(s.^4) + 0.5*defocus.*lambda.*s.^2); 
