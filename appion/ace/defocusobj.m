function err = defocusobj(param,ctf,s,V,Cs)
% DESCRIPTION: 
%     Internal objective function used for refining defocus estimate.
%
% USAGE: 
%     err = defocusobj(param,ctf,s,V,Cs)
%     
%     param : Vector of CTF parameters. 
%     ctf   : Estimated CTF sampled at frequencies s. 
%     s     : Frequency at which CTF is sampled. 
%     V     : Operating voltage. 
%     Cs    : Spherical Abberation. 
%     err   : Error between the estimated and calculated CTF. 
%
% Copyright 2004 Satya P. Mallick 

z = param(1);  
A = param(2);  

lambda = getlambda(V); 
gmma = getgamma(s,z, Cs, lambda); 
ctf_temp = getctf(gmma,A); 
err = norm(ctf_temp - ctf,2); 

