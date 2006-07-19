figure; imshow(log(imfftabs.^2)',[]); 
hold on; 
axis xy
sz = size(imfftabs);
maxp = max(pg1.^2); 
yp = pg1.^2/maxp*200 + 256; 
xp = [257:512]; 
h1 = plot(xp,yp,'k','linewidth',1); 
ang1 = ang;
rotate(h1,[0 0 1],ang1); 
ellipse(50,sqrt(k1/k2)*50,90-ang,sz(1)/2,sz(2)/2,30); 


annotation('arrow',[0.5 0.5 + 0.39*cos(ang1*pi/180)],[0.5 0.5 + 0.39*sin(ang1*pi/180)],'Color','k','linewidth',2); 
ang1 = ang1+90;
annotation('arrow',[0.5 0.5 + 0.39*cos(ang1*pi/180)],[0.5 0.5 + 0.39*sin(ang1*pi/180)],'Color','k','linewidth',2); 

line([304 245],[272 414],'Color','k');
plot([304 245],[272 414],'ko','MarkerSize',5,'Markerfacecolor','k');
gtext('Frequency','rotation',ang,'fontweight','bold');
gtext('Elliptically averaged power spectrum','rotation',90+ang,'fontweight','bold');
gtext('s','rotation',ang,'fontweight','bold');
gtext('I^2(s)','rotation',ang,'fontweight','bold');