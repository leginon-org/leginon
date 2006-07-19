function ctf = getctf(gmma, A) 
% DESCRIPTION:
%     Calculates the theoretical ctf for a given gamma and ampitude contrast. 
%
% USAGE: 
%     ctf = getctf(gmma, A) 
%      
%     gmma :  Vector containing the gamma. 
%     A    :  The amplitude contrast. 
%     ctf  :  The theoretical 1D ctf. 
% 
% See also GETGAMMA.
%
% Copyright 2004-2005 Satya P. Mallick.  

ctf = (sqrt(1-A^2)*sin(gmma) + A*cos(gmma)).^2;  


