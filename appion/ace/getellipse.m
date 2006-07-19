function  [ang,rat]=getellipse(ctf2d,medium,tempdir) 
%
% DESCRIPTION: 
%     Estimates the parameters of the elliptical Thon rings. 
%         
% USAGE: 
%     [ang,rat]=getellipse(ctf2d,medium) 
%
%     ctf2d   : 2D power spectrum.
%     medium  : 'carbon' or 'ice'.
%     tempdir : Directory for temporary files. ( optional argument )  
%
% Copyright 2004-2005 Satya P. Mallick

if(nargin<3) 
  tempdir = './'; 
end 

  
sz = size(ctf2d); 
imwidth = sz(1);

if(isnan(ctf2d)) 
  ang = -1; 
  rat = -1; 

  return
end 

if(strcmp(medium,'ice'))
  load(strcat(tempdir,'aceconfig.mat'),'edgethice'); 
  load(strcat(tempdir,'aceconfig.mat'),'drange'); 
  cannyth = edgethice; 
  blurwidth = 5; 
  if(drange) 
      ctf2d = log(ctf2d); 
  end 

else 
  load(strcat(tempdir,'aceconfig.mat'),'edgethcarbon'); 
  cannyth = edgethcarbon; 
  blurwidth = 5*imwidth/512; 
  ctf2d = log(ctf2d); 
end 



ctr = round(size(ctf2d)/2); 
[edgeim,ax,ay] = imedge(ctf2d,'canny',cannyth ,blurwidth); 


w = 15*imwidth/512;
edgeim(ctr(1)-w:ctr(1)+w,ctr(2)-w:ctr(2)+w)=0; 
edgeflag = 1; 
while(sum(edgeim(:))<70*imwidth/512)
  cannyth = cannyth - 0.1; 
  [edgeim,ax,ay] = imedge(ctf2d,'canny',cannyth ,blurwidth);
  edgeim(ctr(1)-w:ctr(1)+w,ctr(2)-w:ctr(2)+w)=0; 
end 
  

[indy indx ] = find(edgeim==1); 





%indy=indy(3:end); 
%indx = indx(3:end); 

sz = size(edgeim); 
len = length(indx); 

p = ax(indy + (indx-1)*sz(1)); 
q = ay(indy + (indx-1)*sz(1)); 
r = sqrt(p.^2 + q.^2); 
p = p./r; 
q = q./r; 



indy = indy - sz(1)/2; 
indx = indx - sz(2)/2;
inliers = 0; 
th = 0.01; 
errfrac=0.0; 
for i=1:10000
  ind = 1+round((len-1)*rand(3,1)) ;
  A  = [ indx(ind).^2 indy(ind).^2 indx(ind).*indy(ind)]; 
  params = pinv(A)*ones(3,1); 
  err = (1-errfrac)*(params(1)*indx.^2 + params(2)*indy.^2 ...
      +params(3)*indx.*indy-1).^2+ ...
      errfrac*(-2*params(1)*indx.*p + ...
      2*params(2)*indy.*q + params(3)*(indx.*q -indy.*p)).^2;  
  
  err(find(err<th))=1; 
  err(find(err~=1))=0; 
  in = sum(err); 
  if(in>inliers) 
    inliers=in;
    inliersind = find(err==1); 
    fparams = params; 
  end 
  
end 
inlx = indx(inliersind) + sz(1)/2; 
inly = indy(inliersind) + sz(2)/2; 

save(strcat(tempdir,'indx'),'inlx'); 
save(strcat(tempdir,'indy'),'inly'); 

A =  [ indx(inliersind).^2 indy(inliersind).^2 indx(inliersind).*indy(inliersind)]; 
%A =  [ indx.^2 indy.^2 indx.*indy]; 
params = pinv(A)*ones(length(inliersind),1);
%params = pinv(A)*ones(length(indx),1);
y1 = (-params(3)*indx + sqrt(params(3)^3*indx.^2 -4*params(2)*(params(1)*indx.^2-1)))/(2*params(2));
y2 = (-params(3)*indx - sqrt(params(3)^3*indx.^2 - 4*params(2)*(params(1)*indx.^2-1)))/(2*params(2));  



%imshow(ctf2d,[]);
indy = indy+sz(1)/2; 
indx = indx+sz(2)/2; 
y1 = y1+sz(1)/2; 
y2 = y2+sz(1)/2; 


%hold on; 
%plot(indy,indx,'r.'); 
%plot(y1(inliersind),indx(inliersind),'b.'); 
%plot(y2(inliersind),indx(inliersind),'b.'); 

k1 = (params(1)+params(2) - sqrt((params(1)-params(2))^2 +params(3)^2))/2; 
k2 = (params(1)+params(2) + sqrt((params(1)-params(2))^2 +params(3)^2))/2; 
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
%imshow(imrot,[]); 
%sz = size(imrot); 
%imtemp = zeros(size(imrot)); 
%imtemp(imrot>0) = imrot(imrot>0)-mean(ctf2d(:)); 
%figure; 
%imshow(imtemp,[]); 
%hold on; 
%ind1 = [sz(2)/2 sz(2)/2]'; 
%ind2 = [sz(1)/2-sqrt(1/k1) sz(1)/2+sqrt(1/k1)]'; 
%ind3 = [sz(1)/2-sqrt(1/k2) sz(1)/2+sqrt(1/k2)]';
%line (ind1,ind2); 
%line(ind3,ind1); 
%saveeps('rotated_ellipse1.eps'); 
%k1=k2; 
save(strcat(tempdir,'k1'),'k1');
save(strcat(tempdir,'k2'), 'k2'); 
%figure
%subplot(1,2,1); 
%imshow(ctf2d,[]); 
%hold on; 
%plot(indx,indy,'r.'); 

%saveeps('edge_ellipse1.eps'); 
%subplot(1,2,2); 
%imshow(ctf2d,[])
%hold on; 
%quiver(256,256,-sqrt(1/k1)*sin(pi*ang/180),-sqrt(1/k1)*cos(pi*ang/180)); 
%quiver(256,256,sqrt(1/k1)*sin(pi*ang/180),sqrt(1/k1)*cos(pi*ang/180)); 
%quiver(256,256,sqrt(1/k2)*sin(pi*(ang+90)/180),sqrt(1/k2)*cos(pi*(ang+90)/180)); 
%quiver(256,256, -sqrt(1/k2)*sin(pi*(ang+90)/180),-sqrt(1/k2)*cos(pi*(ang+90)/180)); 

%%plot(indx(inliersind),indy(inliersind),'b.'); 




