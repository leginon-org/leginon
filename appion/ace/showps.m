function ps = showps(im)
%
% DESCRIPTION: 
%     Shows the power spectrum of an mrc file.
%
% USAGE: 
%     showps(filename)
%
% Copyright 2004-2005 Satya P. Mallick. 
if(isstr(im)); 
  im = readmrc(im); 
end


sz = size(im);  

if sz(1) > 1024
  ps = getstack(512,im);
  ps = ps.^2; 
  imshow(log(ps),[]); 
else 
  ps = abs(fftshift(fft2(im))).^2;
  imshow(log(ps),[]); 
end 

