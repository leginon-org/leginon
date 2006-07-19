function im = readmrc(filename)
%
% DESCRIPTION: 
%     Reads in an MRC file. 
%
% USAGE: 
%     im = readmrc(filename)
%        
%     filename : Filename of the mrc file
%     im       : image contained in the mrc file as a matrix. 
%
% NOTE: Only 2D MRC formats supported. 
%
% See also WRITEMRC. 
%
% Copyright 2004-2005 Satya P. Mallick. 

fid = fopen(filename); 

ncol = fread(fid,1,'int32'); 
nrow = fread(fid,1,'int32'); 
nz = fread(fid,1,'int32'); 

if(nz>1) 
  fprintf('Format not supported'); 
else   
  md = fread(fid,1,'int32') ; 
  
  if(md == 0) 
    sz = 'char'; 
  elseif(md==1) 
    sz = 'int16'; 
  elseif(md==2)
    sz = 'float32';
  else 
    fprintf('Format not supported'); 
  end

  
  fseek(fid,1024,-1); 
   
  im = fread(fid,ncol*nrow,sz); 
  im = reshape(im,[ncol nrow]); 
  
  
end 
fclose(fid); 
