function [val, ellavg, rat, ang] = getprofile_ang(stig,medium,tempdir, startOrientn, sectorAngle); 
% DESCRIPTION : 
%     Calculates the 1D periodogram of an image. 
%
% USAGE: 
%     [val, ellavg, imfftabs, rat, ang] = getprofile(file,stig,medium)
%     
%
%     file      : Input image
%     stig    : Boolean switch to switch on or off astigmatism calculation. 
%     medium  : 'carbon' or 'ice'.
%     tempdir : Directory for temporary files. 
%     val     : The image resampled on a polar grid. 
%     ellavg  : 1D Elliptical average of the power spectrum. 
%     imfftabs: Absolute value of the Fourier Transform of the image
%     rat     : Ratio of major and minor axes. 
%     ang     : Angle of astigmatism. 
%
% Copyright 2004 Satya P. Mallick 

if nargin < 2
%  stig = 1;     
  stig = 0; 
  medium = 'carbon'; 
  tempdir = './'; 
elseif nargin < 3
  medium = 'carbon'; 
  tempdir = './'; 
elseif nargin < 3
  tempdir = './'; 
end 

%load fieldsize and overlap set by the user. 
load(strcat(tempdir,'aceconfig.mat'),'fieldsize'); 
load(strcat(tempdir,'aceconfig.mat'),'overlap'); 

if startOrientn==0
    load(strcat(tempdir,'file.mat'),'file');
    % Generating the square root of the power spectrum 
    if(strcmp(medium,'ice'))
        %if ice use overlapping fields to generate the power spectrum
        imfftabs = getstack(file,fieldsize,overlap);
    elseif(size(file,1)<=1024) 
        %if carbon image of size less than 1024x1024, use the entire image. The
        %fieldsize and overlap arguments are ignored. 
        imfftabs = abs(fftshift(fft2(file)));
    else 
        %if carbon image of size greater then 1024x1024 use the fieldsize and
        %overlap arguments to find imfft. 
        imfftabs = getstack(file,fieldsize,overlap);
    end
    clear file;
    [imheight imwidth] = size(imfftabs);

    % Removing the central horizontal and vertical slices to compensate for
    % boudary effects. 
    imfftabs(round(imwidth/2),:)= imfftabs(round(imwidth/2)-1,:);
    imfftabs(round(imwidth/2)+1,:)= imfftabs(round(imwidth/2)+2,:);
    imfftabs(:,round(imwidth/2),:)= imfftabs(:,round(imwidth/2)-1  );
    imfftabs(:,round(imwidth/2)+1,:)= imfftabs(:,round(imwidth/2)+2  );

    save(strcat(tempdir,'imfftabs.mat'),'imfftabs');

else
    load(strcat(tempdir,'imfftabs.mat'),'imfftabs');
    [imheight imwidth] = size(imfftabs);
end
%imfftabs = abs(imfft); % Check to see if the abs is required. 

c = floor(size(imfftabs)/2)+1; % Image center. 

%save(strcat(tempdir,'imfftabs.mat'),'imfftabs');

%[ang rat] = getellipse(imfftabs,medium,tempdir); 
%[ang rat] = estimateEllipse(sectorNum, sectorAngle, r_sector, tempdir,imfftabs, medium);

% if(stig==0)
%     % If astigmatism is turned off, set major and minor axes ratio to 1 and
%     % angle of astigmatism to 0
%     ang = 0;
%     rat = 1;
% end
ang=0;
rat=1;

if(rat==-1) 
    % If the ellipse fitting fails, return empty values. 
    val = [];
    ellavg=[];
    imrot = [];
    return
end

% Perform elliptical averaging
%imrot = imrotate(imfftabs,-ang,'bilinear','crop'); 
r_index = [0:round(imwidth/2)-1]; 
%theta_index = startOrientn:2*pi/(6*c(1)):startOrientn+sectorAngle; 
theta_index = startOrientn-sectorAngle:2*pi/(6*c(1)):startOrientn+sectorAngle; 
%theta_index = 0:2*pi/(6*c(1)):2*pi; 
[r theta] = meshgrid(r_index,theta_index); 
i =  c(1)+ (rat*r).*cos(theta); 
j =  c(2)+ (r).*sin(theta); 
i = i'; 
j = j'; 
val =  interp2(imfftabs,i,j,'bicubic');
%val =  interp2(imrot,i,j,'bicubic');
ellavg = mean(abs(val),2); 
    
clear imfftabs;