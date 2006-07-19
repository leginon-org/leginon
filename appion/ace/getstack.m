function imout = getstack(im,width,overlap)
%
% DESCRIPTION: 
%     Calculates the sqaure root of the mean power spectrum of overlapping 
%     regions cut out from a micrograph.
% 
% USAGE: 
%     ps = getstack(width,im)
%            
%     im     : Image data ( array ); 
%     width  : Width of the RMS power spectrum.
%     ps     : square root of mean power spectrum.
%
% Copyright 2004-2005 Satya P. Mallick. 
sz = size(im); 
im = im - mean(im(:)); 
ll=0; 
imfft = zeros(width); 
for i=1:width/overlap:sz(1)-width
  for j=1:width/overlap:sz(2)-width
     imfft = imfft + abs(fftshift(fft2(im(i:i-1+width,j:j-1+width)))); 
    ll=ll+1; 
  end 
  
end 

imout = imfft/ll; 

