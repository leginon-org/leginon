function [ang,rat, k1, k2] = estimateEllipse(sectorNum, sectorAngle, r, tempdir, medium)
%clear A err indx indy inliersind fparams
load(strcat(tempdir,'imfftabs.mat'),'imfftabs'); 
ctf2d = imfftabs; clear imfftabs;

[imheight, imwidth] = size(ctf2d);
c = floor(size(ctf2d)/2)+1; % Image center. 

if(isnan(ctf2d)) 
  ang = -1; 
  rat = -1; 

  return
end 

% if(strcmp(medium,'ice'))
%   load(strcat(tempdir,'aceconfig.mat'),'drange'); 
%   if(drange) 
%       ctf2d = log(ctf2d); 
%   end 
% 
% else 
  ctf2d = log(ctf2d); 
%end 

sectorInd = 1:sectorNum;
theta = (sectorInd-1)*sectorAngle+sectorAngle/2;
for m=1:length(sectorInd)
    theta_m = (m-1)*sectorAngle+sectorAngle/2;
    r_m = r(m);
    indx(m,1) = round(c(1)+r_m*cos(theta_m)); 
    indy(m,1) = round(c(2)+r_m*sin(theta_m));
end
%**********************************
%indx = indx'; indy=indy';
len = length(indx); 

indx = indx - imwidth/2; 
indy = indy - imheight/2;
inliers = 0; 
th = 0.01; 
for m=1:10000
  ind = 1+round((len-1)*rand(3,1));
  while(length(unique(ind))<3)
    ind = 1+round((len-1)*rand(3,1));
  end
  A  = [ indx(ind).^2 indy(ind).^2 indx(ind).*indy(ind)]; 
  params = inv(A)*ones(3,1); 
%  params = pinv(A)*ones(3,1);   
%  params = A\ones(3,1); 
  err = (params(1)*indx.^2 + params(2)*indy.^2+params(3)*indx.*indy - 1).^2;
  
  err(find(err<th))=1; 
  err(find(err~=1))=0; 
  in = sum(err); 
  if(in>inliers) 
    inliers=in;
    inliersind = find(err==1); 
    fparams = params; 
  end 
%   if inliers>len/2
%       break;
%       sprintf('Broke Out on : %d', m)
%   end
end 

inlx = indx(inliersind) + imwidth/2; 
inly = indy(inliersind) + imheight/2; 

%save(strcat(tempdir,'indx'),'inlx'); 
%save(strcat(tempdir,'indy'),'inly');

A =  [ indx(inliersind).^2 indy(inliersind).^2 indx(inliersind).*indy(inliersind)]; 
params = pinv(A)*ones(length(inliersind),1);

y1 = (-params(3)*indx + sqrt(params(3)^2*indx.^2 -4*params(2)*(params(1)*indx.^2-1)))/(2*params(2));
y2 = (-params(3)*indx - sqrt(params(3)^2*indx.^2 - 4*params(2)*(params(1)*indx.^2-1)))/(2*params(2));  

%y1 = (-params(3)*indx + sqrt(params(3)^3*indx.^2 -4*params(2)*(params(1)*indx.^2-1)))/(2*params(2));
%y2 = (-params(3)*indx - sqrt(params(3)^3*indx.^2 - 4*params(2)*(params(1)*indx.^2-1)))/(2*params(2));  

indy = indy+imheight/2; 
indx = indx+imwidth/2;
y1 = y1+imheight/2; 
y2 = y2+imheight/2;

% figure; imagesc(ctf2d);
% hold on; 
% plot(indx,indy,'w*'); 
% plot(indx(inliersind), y1(inliersind),'k.-'); 
% plot(indx(inliersind), y2(inliersind),'k.-'); 
% %pause;

% figure; imshow(ctf2d,[]);
% hold on; 
% plot(indx,indy,'r*'); 
% plot(indx(inliersind), y1(inliersind),'b.-'); 
% plot(indx(inliersind), y2(inliersind),'b.-'); 
%pause;

% h=figure('Visible','off'); imshow(ctf2d,[]);
% hold on; 
% %plot(indx,indy,'r*'); 
% plot(indx(inliersind), y1(inliersind),'b-');  % y - height in the displayed image in matlab, x - width in the displayed image in matlab, origin in the display starts from upper left corner.
% %plot(indx(inliersind), y2(inliersind),'b.-'); 
% title('Sector Approach');
% saveas(h,strcat(tempdir, 'im1.png'));


% plot(indy,indx,'r*'); 
% plot(y1(inliersind),indx(inliersind),'b*'); 
% plot(y2(inliersind),indx(inliersind),'b*'); 




k1 = (params(1)+params(2) - sqrt((params(1)-params(2))^2 +params(3)^2))/2; 
k2 = (params(1)+params(2) + sqrt((params(1)-params(2))^2 +params(3)^2))/2; 
% save(strcat(tempdir,'k1'),'k1');
% save(strcat(tempdir,'k2'), 'k2'); 

if(params(3)^2-4*params(1)*params(2)>=0)
  ang = -1; 
  rat = -1; 
else 
  ang = 180*atan(2*(k2-params(1))/params(3))/pi;
  rat = sqrt(k1/k2);
  %rat = 1; 
end 
%imrot = imrotate(ctf2d,ang,'crop'); 
ang = -ang; 



 
h=figure('Visible','off');imshow(ctf2d,[]);hold on;
plot(indx(inliersind), y1(inliersind),'b-');
hold on; 
quiver(imwidth/2,imwidth/2,-sqrt(1/k1)*sin(pi*ang/180),-sqrt(1/k1)*cos(pi*ang/180)); 
quiver(imwidth/2,imwidth/2,sqrt(1/k1)*sin(pi*ang/180),sqrt(1/k1)*cos(pi*ang/180)); 
quiver(imwidth/2,imwidth/2,sqrt(1/k2)*sin(pi*(ang+90)/180),sqrt(1/k2)*cos(pi*(ang+90)/180)); 
quiver(imwidth/2,imwidth/2, -sqrt(1/k2)*sin(pi*(ang+90)/180),-sqrt(1/k2)*cos(pi*(ang+90)/180)); 
title('Ellipse fit based on sector approach','Fontsize',12,'Fontweight','b');
print(strcat('-f',num2str(h)),'-dpng','-r75',strcat(tempdir,'im1.png'));  
%saveas(h,strcat(tempdir, 'im1.png'));

close(h);
clear ctf2d;