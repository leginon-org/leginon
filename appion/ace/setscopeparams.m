function setscopeparams(V,Cs,Ca,tempdir) 
% DESCRIPTION: 
%     Sets the microscope parameters and stores the values in scopeparams.mat 
%     which is used by other functions.  
%
% USAGE: 
%     setscopeparams(V,Cs,Ca) 
%
%     V       : Operating Voltage in KV. 
%     Cs      : Spherical aberrations in mm 
%     Ca      : Sampling Rate ( Resolution ) in Angstroms/pixel
%     tempdir : Directory for storing the mat file(optional)
% 
% Copyright 2004-2005 Satya P. Mallick 

if(nargin<4) 
  tempdir = './'; 
end 
save(strcat(tempdir,'scopeparams'),'V','Cs','Ca'); 
