function ctfcorrect(impath, matfile, tempdir, ctdimpath, outimagedir, imgname); 
% DESCRIPTION: 
%     CTF correction based on parameters estimated by ACE. 
%
% USAGE: 
%     im_correct = ctfcorrect(im,ctfparams,scopeparams,phaseonly); 
%           
%     im                 :  Input image ( an array ); 
%     ctfparams          :  12 parameter vector of CTF, Noise and Envelope
%                           function parameters  as calculated by ACE. 
%     scopeprams         :  3 vector of scope parameters.
%                                   [V(in kv), Spherical abberation in mm), Ca (pixel size in Angstroms/pixel)]  
%     phaseonly          :  Set to 1 for correcting on the phase. For 
%                                   phase and amplitude correction set it to 0. 
%     im_correct          : Corrected image. 
%
% See also LEGINON_ACE_CORRECT and ACEDEMO_CORRECT.
%
% Copyright 2004-2005 Satya P. Mallick 


phaseonly = 1; 


im = readmrc(impath);
% h=figure('Visible', 'Off'); imshow(double(im),[]); title('Orig im');
% saveas(h,strcat(outimagedir, '/', imgname, '_origIm.png'));
% close all;

display = 0; 
[imwidth imheight] = size(im); 

load(sprintf('%s', matfile), 'ctfparams', 'scopeparams');
defoci = ctfparams(1:2); 
ast_ang = pi/2+ctfparams(5); 

% load(sprintf('%s/scopeparams.mat',tempdir));
% V = V*1e3;
% Cs = Cs*1e-3;
% Ca = Ca*1e-10;

V = scopeparams(1)*1e3; 
Cs = scopeparams(2)*1e-3; 
Ca = scopeparams(3)*1e-10; 

if(mod(imwidth,2)==0)
 zro = imwidth/2+0.5; 
else 
  zro = ceil(imwidth/2);
end 

defocus_mean = (defoci(1)+defoci(2))/2; 
defocus_dev = abs(defoci(1)-defoci(2))/2; 
lambda = getlambda(V);

[s,gmma] = meshgrid(1:imwidth); 
s = s-zro; 
gmma = gmma-zro; 

a = atan2(s,gmma);
s =  sqrt((s.^2 + gmma.^2));
gmma = defocus_mean + defocus_dev*cos(2*(a+ast_ang)); 
s = s./(imwidth*Ca);
gmma = squeeze(getgamma(s,gmma,Cs,lambda)); 


if(phaseonly)
gmma(rem(gmma,2*pi)>pi)=-1;
gmma(gmma~=-1)=1;

%h=figure('Visible', 'Off'); imshow(double(gmma),[]); title('gmma');
%saveas(h,strcat(outimagedir, '/', imgname, '_ctf.png'));
%close all;

%im = medfilt2(im);
im = fftshift(fft2(im));  

% h=figure('Visible', 'Off'); imshow(log(abs(im)),[]); title('im after fftshit');
% saveas(h,strcat(outimagedir, '/', imgname, '_im.png'));
% close all;

flipInd = find(gmma==-1);
y = im(flipInd);y=y';
im(flipInd)=y;

% h=figure('Visible', 'Off'); imshow(log(abs(im)),[]); title('gmma.*im');
% saveas(h,strcat(outimagedir, '/', imgname, '_gmmaXim.png'));
% close all;

im = abs(ifft2(ifftshift(im))); 

%h=figure('Visible', 'Off'); imshow(double(im),[]); title('Corrected im');
%saveas(h,strcat(outimagedir, '/', imgname, '_crtdIm.png'));
%close all;

%h=figure('Visible', 'Off'); imshow(log(abs(fftshift(fft2(im)))),[]); title('FFT after correcting');
%saveas(h,strcat(outimagedir, '/', imgname, '_fftPstCrn.png'));
%close all;

else 
ii = sqrt(1-A^2)*sin(gmma)+A*cos(gmma);
gmma = exp(2*(noisep(1)+ noisep(2).*sqrt(s) + noisep(3).*s + noisep(4).*s.^2));
gmma = gmma./exp(2*(envp(1)+envp(2).*sqrt(s) + envp(3).*s + envp(4).*s.^2)); 
clear s
gmma = ii./(ii.^2 + gmma );
clear ii
im = fftshift(fft2(im));  
im = real(ifft2(ifftshift(( gmma.*im)))); 
end 

writemrc(im, ctdimpath, 'float');
