%SNR : Returns a number corresponding to the 
%      signal to noise ratio of the image. Bear 
%      in mind that the true signal to noise ration 
%      is frequency dependent. The number returned 
%      by this function is an average over the entire 
%      frequency range. SNR generates a list of snr   
%      of all files present in dirname/matfiles/ and 
%      outputs the result in snrfile.txt 
%      
% Edit this script using 
% edit snr
% The following variables can be changed. 
%
% dirname : The parent directory of the matfile directory.
% outfile : Name of the output file 
% list    : Should be changed if you have stored the matfiles in some 
%           other directory say matfiles1 or if you want only a 
%           a particular type of file. Example 
%
%           list = dir(strcat(dirname,'matfiles1/*foc*.mat'));
%
%           list would now contain the names of only the foc files 
%           in matlab1 directory inside the parent directory dirname.
%
% Note strcat is a matlab function for string concatenation. 
%
% Copyright 2004-2005 Satya P. Mallick. 

dirname = '/ctf/04apr14b/'; % directory
if(dirname(end)~='/'); 
  dirname = strcat(dirname,'/'); 
end
outfile = strcat(dirname,'snrfile.txt'); 
list = dir(strcat(dirname,'matfiles/*.mat')); 
outid = fopen(outfile,'w+'); 

for i=1:length(list) 
  
  load(strcat(dirname,'matfiles/',list(i).name));

  if(ctfparams~=-1) 
    if(abs(abs(dforig)-mean(ctfparams(1:2)))<1e-6)
    s = [25:100]'; 
    s = s*1e10/(512*scopeparams(3)); 
    A = [ones(length(s),1) sqrt(s) s s.^2];
    noise = exp(2*A*ctfparams(5:8)'); 
    env   = exp(2*A*ctfparams(9:end)'); 
    fprintf('%s %f\n',list(i).name(1:end-4),sum(env./noise)); 
    fprintf(outid,'%s %f\n',list(i).name(1:end-4),sum(env./noise)); 
    
    end
  end

  
end 
fclose(outid); 
