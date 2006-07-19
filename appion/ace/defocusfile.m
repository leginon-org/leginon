%
% Generates a file containing the filename, the two estimated defoci 
% and the defocus set by the microscope. Open the file to edit it
% using the following command 
%
% edit defocusfile 
%
% Change the dirname to the directory where ctf estimation results are stored.
% Change filename to the output file you want. 
% Change the file filter in dir command to grab specific files only 
% For example 
%
% list = dir(strcat(dirname,'matfiles/*foc.mat')); 
%
% would make a list of foc files only.
%
% Copyright 2004-2005 Satya P. Mallick 

dirname = '/ctf/04apr14b/'; % directory
outfile = strcat(dirname,'defocusfile.txt'); 
list = dir(strcat(dirname,'matfiles/*.mat')); 
outid = fopen(outfile,'w+');
k=1;
%figure; 
hold on; 
for i=1:length(list)-1 
  
  load(strcat(dirname,'matfiles/',list(i).name));
  if(ctfparams~=-1)
  fprintf('%s %f %f %f\n',list(i).name(1:end-4),-dforig*1e6,ctfparams(1)*1e6,ctfparams(2)*1e6); 
  fprintf(outid,'%s %f %f %f\n',list(i).name(1:end-4),-dforig*1e6,ctfparams(1)*1e6,ctfparams(2)*1e6);
 % plot(abs(dforig)*1e6,ctfparams(1)*1e6,'*');
  dfo(k) = abs(dforig)*1e6; 
  dfc(k) = ctfparams(1)*1e6;
  k=k+1; 
end
end 
fclose(outid); 
%A = [dfo; dfc]';
%x = pinv(A)*ones(length(dfo),1); 
%dfo = [ 0 dfo];
%y = (-x(1)*dfo + 1)/x(2);  

%lot(dfo,y); 
%xlabel('Nominal defocus (\mum)')
%ylabel('Calculated defocus (\mum)')
