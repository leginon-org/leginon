function savegcf(f)
%SAVEGCF: 
% 	Saves the current figure as an image
%
%USAGE: 
%      savegcf(filename)     
frame = getframe(gcf);
frame  = frame2im(frame);
imwrite(frame,f);
