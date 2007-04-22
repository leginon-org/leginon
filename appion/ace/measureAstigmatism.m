function ctfparams = measureAstigmatism(imagename,filename,outfile,outimagedir, matfiledir, display,stig,medium,dforig,tempdir,resamplefr); 

outid  = fopen(outfile,'a'); 
outfile_sec = strrep(outfile, '.txt', '_sectors.txt');

sectorAngle =10*pi/180; %in degrees
sectorNum = 0; ctfparamsArr = []; display=0; brkFlag=0;
for startOrientn = 0:sectorAngle:pi-sectorAngle
  sectorNum = 1 + sectorNum;
  [ctfparams r_sector(sectorNum)] = aceAstig(filename,outfile_sec,display,stig,medium,dforig,tempdir, startOrientn, sectorAngle);
  ctfparamsArr = [ctfparamsArr; ctfparams];
  if unique(ctfparams)==-1
      brkFlag=1;
      break;
   end
  
%  save(strcat(matfiledir,imagename, '_', num2str(sectorNum),'.mat'),'ctfparams','scopeparams','dforig'); 
%  if(display) 
  %  pause(1); 
  %  figflag(gcf,0);
%     im1 = imread(strcat(tempdir,'im1.png')); 
%     imwrite(im1,sprintf('%s/%s.mrc_%03d_R%.1f.png',outimagedir,imagename, sectorNum, resamplefr)); 
%     clear im1;
%  end 
%  if(write2db) 
%    dbctf( expid, runname, legimgId, legpresetId, imagename,abs(dforig),ctfparams,strcat(outimagedir,imagename,'1.png'),...
%    strcat(outimagedir,imagename,'2.png'),strcat(matfiledir,imagename,'.mat')) 
%  end 
end % end of startOrientation variation.
if brkFlag
    fprintf(outid,'\n %s %s %s', filename, 'Could not process micrograph for some sectors', sprintf('R%.1f', resamplefr)); 
%    fprintf('%s %s %s\n', filename, 'Could not process micrograph for some sectors', sprintf('R%.1f', resamplefr));     
    return;
end
confArr = ctfparamsArr(:,17);
conf_dArr = ctfparamsArr(:,18);  

[ang,rat, k1, k2] = estimateEllipse(sectorNum, sectorAngle, r_sector, tempdir, medium);
% im1 = imread(strcat(tempdir,'im1.png')); 
% imwrite(im1,sprintf('%s/%s.mrc1.png',outimagedir,imagename)); 
% clear im1;

s_major = sqrt(1/k1);
s_minor = sqrt(1/k2);

load(strcat(tempdir,'freqfactor'),'freqfactor');
load(strcat(tempdir,'scopeparams.mat'), 'V', 'Cs');
V = V*1e3; 
Cs = Cs*1e-3; 
lambda = getlambda(V); 

s1 = s_major/freqfactor;
z_major = (2+Cs*lambda^3*s1^4)/(2*lambda*s1^2);
s1 = s_minor/freqfactor;
z_minor = (2+Cs*lambda^3*s1^4)/(2*lambda*s1^2);

startOrientn = 0;
[ctfparams] = aceFinalItr(filename,outfile_sec,display,stig,medium,dforig,tempdir, startOrientn, ang, rat);
ctfparams(1)=z_major;
ctfparams(2)=z_minor;
ctfparams(5)=-ang*pi/180;
ctfparams(17) = mean(confArr);
ctfparams(18) = mean(conf_dArr);

load(strcat(tempdir,'scopeparams.mat'));
scopeparams = [V Cs Ca];
save(strcat(matfiledir,'/',imagename, '.mrc', '.mat'), 'ctfparams', 'ctfparamsArr', 'resamplefr', 'dforig', 'scopeparams'); 

fprintf(outid,'\n %s %f %f %f %f %f %f %f %f %f %f %f %s', filename, abs(dforig)*1e6, rat, ang, s_major, s_minor, s_major/freqfactor, s_minor/freqfactor, z_major*1e6, z_minor*1e6, mean(confArr), mean(conf_dArr), sprintf('R%.1f', resamplefr)); 
fclose(outid);

load(strcat(tempdir, 'ctfMatchPlotData.mat'), 'ctffiltArr', 'ctffinalArr');
h1=figure('Visible', 'Off'); 
for i=1:18
    subplot(6,3,i), plot(ctffiltArr(:,i), '-');hold on; plot(ctffinalArr(:,i), 'r-');
    title(sprintf('%d degrees', (i-1)*10));
end
saveas(h1,strcat(tempdir, 'im2.png'));
close(h1);
