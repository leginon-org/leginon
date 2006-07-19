function savegca(f)
%SAVEGCA  : Saves current axis as an image. 
%
%Usage    : 
%          savegca(filename)




frame = getframe(gca); 
frame  = frame2im(frame); 
imwrite(frame,f); 
