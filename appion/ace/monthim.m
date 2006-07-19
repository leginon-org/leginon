close all
load temp/indx1 
load temp/indy1
load temp/k1 
load temp/k2
ctf2d = log(genctf2d(512,[zsmall zfinal],Afinal,noiseparams,envparams,-ang*pi/180));
%figure; imshow(log(ctf2d),[]); 
%figure; imshow(2*log(imfftabs),[]);
%keyboard
ctf2d(:,257:end) = 2*log(imfftabs(:,257:end));
figure
imshow(ctf2d,[38 45]); 
  
hold on; 
quiver('v6',imwidth/2,imwidth/2,-sqrt(1/k1)*sin(pi*ang/180),...
    -sqrt(1/k1)*cos(pi*ang/180),'w'); 
quiver('v6',imwidth/2,imwidth/2,sqrt(1/k1)*sin(pi*ang/180),...
    sqrt(1/k1)*cos(pi*ang/180),'w');
quiver('v6',imwidth/2,imwidth/2,sqrt(1/k2)*sin(pi*(ang+90)/180),...
    sqrt(1/k2)*cos(pi*(ang+90)/180),'w');
quiver('v6',imwidth/2,imwidth/2, -sqrt(1/k2)*sin(pi*(ang+90)/180),...
    -sqrt(1/k2)*cos(pi*(ang+90)/180),'w');
  
plot(indy1,indx1,'g.','Markersize',4); 
hold on; 
axis xy
maxp = max(pg1.^2); 
yp = pg1.^2/maxp*200 + 256; 
xp = [257:512]; 

h1 = plot(xp,yp,'w','linewidth',2); 


xmat = ([x x]-pixeloff)+256; 
ymat = [0 200]+256; 
h2 = plot(xmat,ymat,'y--'); 

x11 = x+upcut;
x1mat = ([x11 x11]-pixeloff); 
h3 = plot(x1mat+256,ymat,'y--'); 

yp1 = exp(b_calc1)/maxp*200+256; 
h4 =plot([x:x+upcut-1]+256,yp1,'r','linewidth',2); 

yp2 = exp(b_calc1)+exp(b_calc2); 
yp2 = yp2/maxp*200+256; 

h5 = plot([x:x+upcut-1]+256,yp2,'color','b','linewidth',2);


rotate(h1,[0 0 1],-ang-90); 
rotate(h2,[0 0 1],-ang-90);
rotate(h3,[0 0 1],-ang-90); 
rotate(h4,[0 0 1],-ang-90); 
rotate(h5,[0 0 1],-ang-90); 
