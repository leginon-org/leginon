function writemrc(im,filename,type)
% DESCRIPTION: 
%     Writes image data to a MRC file.
%
% USAGE: 
%     writemrc(im,filename,type)
%
%     im       : The image data to be written.  
%     filename : Filename of the mrc file.
%     type     : 'short' (unsigned integer 2 bytes/pixel) 
%                'float' (float 4 bytes/pixel). 
%
% NOTE: Only 2D MRC formats supported.
%
% See also READMRC.
%
% Copyright 2004-2005 Satya P. Mallick 

if(nargin<3) 
  type = 'float' ; 
end 


sz = size(im);
if(length(sz)>2)
 ferror('3D write not supported');
end
head(1:256) = 0;
head(1) = sz(2);
head(2) = sz(1);
head(3) = 1;
switch type 
  case  'short'
    typeno = 1;
    itype = 'uint16'; 
  case 'float'  
    typeno = 2; 
    itype = 'float32'; 
end 
head(4) = typeno;


fid = fopen(filename,'w');
fwrite(fid,head(1:256),'int32');
fseek(fid,1024,-1); 
fwrite(fid,im,itype); 
fclose(fid); 
