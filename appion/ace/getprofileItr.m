function [val, ellavg] = getprofileItr(stig,medium,tempdir, startOrientn, sectorAngle, ang, rat); 
% DESCRIPTION : 
%     Calculates the 1D periodogram of an image. 
%
% USAGE: 
%     [val, ellavg, imfftabs, rat, ang] = getprofile(im,stig,medium)
%     
%
%     im      : Input image
%     stig    : Boolean switch to switch on or off astigmatism calculation. 
%     medium  : 'carbon' or 'ice'.
%     tempdir : Directory for temporary files. 
%     val     : The image resampled on a polar grid. 
%     ellavg  : 1D Elliptical average of the power spectrum. 
%     imfftabs: Absolute value of the Fourier Transform of the image
%     rat     : Ratio of major and minor axes. 
%     ang     : Angle of astigmatism. 
%

load(strcat(tempdir,'imfftabs.mat'),'imfftabs'); 
[imheight imwidth] = size(imfftabs);

c = floor(size(imfftabs)/2)+1; % Image center. 


% Perform elliptical averaging
imrot = imrotate(imfftabs,-ang,'bilinear','crop'); 
%figure; imshow(imrot, []);
r_index = [0:round(imwidth/2)-1]; 
theta_index = startOrientn-sectorAngle:2*pi/(6*c(1)):startOrientn+sectorAngle; 
[r theta] = meshgrid(r_index,theta_index); 
i =  c(1)+ (rat*r).*cos(theta); 
j =  c(2)+ (r).*sin(theta); 
i = i'; 
j = j'; 
%val =  interp2(imfftabs,i,j,'bicubic');
val =  interp2(imrot,i,j,'bicubic');
ellavg = mean(abs(val),2); 
    
clear imfftabs;